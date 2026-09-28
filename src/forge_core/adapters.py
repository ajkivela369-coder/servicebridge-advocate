from __future__ import annotations

from dataclasses import dataclass

from .sdk import ForgeSDK


@dataclass
class ForgeTextProvider:
    sdk: ForgeSDK

    def generate(self, *, instructions: str, input_text: str) -> str:
        return self.sdk.reason(
            instructions,
            input_text,
        )["text"]


@dataclass
class ForgeEmbeddingProvider:
    sdk: ForgeSDK

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self.sdk.embed(texts)["vectors"]
