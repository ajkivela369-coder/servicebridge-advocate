from __future__ import annotations

from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from typing import Any

from .memory import LocalEmbeddingClient
from .runtime import (
    LocalOpenAICompatibleProvider,
    RuntimeMode,
    RuntimePolicy,
    runtime_snapshot,
)


@dataclass(frozen=True)
class GatewayConfig:
    host: str = "127.0.0.1"
    port: int = 8765
    mode: RuntimeMode = RuntimeMode.CREDITLESS
    llm_endpoint: str = "http://127.0.0.1:8080/v1/chat/completions"
    embedding_endpoint: str = "http://127.0.0.1:8080/v1/embeddings"
    model: str = "local-model"
    embedding_model: str = "local-embedding-model"

    def policy(self) -> RuntimePolicy:
        return RuntimePolicy(
            mode=self.mode,
            allow_external_network=False,
            allow_cloud_fallback=False,
        )


def make_handler(config: GatewayConfig):
    policy = config.policy()

    class Handler(BaseHTTPRequestHandler):
        server_version = "ServiceBridgeLocalRuntime/0.1"

        def log_message(self, format: str, *args: object) -> None:
            # Keep patient/evidence content out of default HTTP access logs.
            return

        def _send(self, status: int, payload: dict[str, Any]) -> None:
            raw = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def _body(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0") or 0)
            if length > 10 * 1024 * 1024:
                raise ValueError("Request is too large.")
            raw = self.rfile.read(length) if length else b"{}"
            parsed = json.loads(raw.decode("utf-8"))
            if not isinstance(parsed, dict):
                raise ValueError("JSON body must be an object.")
            return parsed

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/health":
                self._send(
                    200,
                    {
                        "status": "ok",
                        "mode": config.mode.value,
                        "external_network": False,
                        "cloud_fallback": False,
                    },
                )
                return

            if self.path == "/v1/runtime/status":
                self._send(200, runtime_snapshot(config.mode))
                return

            self._send(404, {"error": "not_found"})

        def do_POST(self) -> None:  # noqa: N802
            try:
                body = self._body()

                if self.path == "/v1/text/generate":
                    instructions = str(body.get("instructions", ""))
                    input_text = str(body.get("input", ""))
                    if not input_text.strip():
                        raise ValueError("input is required")
                    provider = LocalOpenAICompatibleProvider(
                        endpoint=config.llm_endpoint,
                        model=str(body.get("model") or config.model),
                        policy=policy,
                    )
                    text = provider.generate(
                        instructions=instructions,
                        input_text=input_text,
                    )
                    self._send(
                        200,
                        {
                            "text": text,
                            "provider": "local-openai-compatible",
                            "mode": config.mode.value,
                        },
                    )
                    return

                if self.path == "/v1/embeddings":
                    inputs = body.get("input", [])
                    if isinstance(inputs, str):
                        inputs = [inputs]
                    if not isinstance(inputs, list) or not all(
                        isinstance(x, str) for x in inputs
                    ):
                        raise ValueError("input must be a string or list of strings")
                    client = LocalEmbeddingClient(
                        endpoint=config.embedding_endpoint,
                        model=str(body.get("model") or config.embedding_model),
                        policy=policy,
                    )
                    vectors = client.embed(inputs)
                    self._send(
                        200,
                        {
                            "data": [
                                {"index": i, "embedding": vector}
                                for i, vector in enumerate(vectors)
                            ],
                            "provider": "local-openai-compatible",
                            "mode": config.mode.value,
                        },
                    )
                    return

                self._send(404, {"error": "not_found"})
            except PermissionError as exc:
                self._send(403, {"error": "policy_blocked", "detail": str(exc)})
            except Exception as exc:
                self._send(
                    400,
                    {
                        "error": "request_failed",
                        "detail": f"{type(exc).__name__}: {exc}",
                    },
                )

    return Handler


def serve(config: GatewayConfig | None = None) -> None:
    config = config or GatewayConfig()
    if config.host not in {"127.0.0.1", "localhost", "::1"}:
        raise PermissionError(
            "The default Local Runtime gateway may only bind to loopback."
        )
    server = ThreadingHTTPServer((config.host, int(config.port)), make_handler(config))
    print(
        f"ServiceBridge Local Runtime listening on http://{config.host}:{config.port} "
        f"mode={config.mode.value}"
    )
    server.serve_forever()
