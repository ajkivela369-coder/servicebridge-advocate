from __future__ import annotations

import json
from typing import Any
from urllib.request import Request, urlopen

from .runtime import RuntimePolicy


def build_vision_payload(
    *,
    model: str,
    image_data_uri: str,
    instructions: str,
    question: str,
) -> dict[str, Any]:
    if not image_data_uri.startswith("data:image/"):
        raise ValueError("Local vision input must be an image data URI.")
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": instructions},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_data_uri},
                    },
                ],
            },
        ],
        "stream": False,
    }


class LocalVisionClient:
    """OpenAI-compatible localhost multimodal client for local VLM servers."""

    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:8080/v1/chat/completions",
        model: str = "local-vision-model",
        policy: RuntimePolicy | None = None,
        timeout: float = 180.0,
    ):
        self.endpoint = endpoint
        self.model = model
        self.policy = policy or RuntimePolicy()
        self.timeout = float(timeout)
        self.policy.assert_url_allowed(endpoint)

    def analyze(
        self,
        *,
        image_data_uri: str,
        instructions: str,
        question: str,
    ) -> str:
        self.policy.assert_url_allowed(self.endpoint)
        payload = build_vision_payload(
            model=self.model,
            image_data_uri=image_data_uri,
            instructions=instructions,
            question=question,
        )
        req = Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        try:
            content = data["choices"][0]["message"]["content"]
        except Exception as exc:
            raise RuntimeError("Local VLM returned an unexpected response shape.") from exc

        if isinstance(content, str):
            return content
        if isinstance(content, list):
            texts = []
            for item in content:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    texts.append(item["text"])
            if texts:
                return "\n".join(texts)
        raise RuntimeError("Local VLM response did not contain readable text.")
