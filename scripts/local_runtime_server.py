from __future__ import annotations

import argparse

from servicebridge.local_runtime import RuntimeMode
from servicebridge.local_runtime.gateway import GatewayConfig, serve


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the localhost ServiceBridge Local Runtime gateway.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--mode",
        choices=[x.value for x in RuntimeMode],
        default=RuntimeMode.CREDITLESS.value,
    )
    parser.add_argument(
        "--llm-endpoint",
        default="http://127.0.0.1:8080/v1/chat/completions",
    )
    parser.add_argument(
        "--embedding-endpoint",
        default="http://127.0.0.1:8080/v1/embeddings",
    )
    args = parser.parse_args()

    serve(
        GatewayConfig(
            host=args.host,
            port=args.port,
            mode=RuntimeMode(args.mode),
            llm_endpoint=args.llm_endpoint,
            embedding_endpoint=args.embedding_endpoint,
        )
    )


if __name__ == "__main__":
    main()
