from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol


class TextProvider(Protocol):
    model: str | None

    def generate(self, *, instructions: str, input_text: str) -> str: ...


@dataclass(slots=True)
class PromptOnlyProvider:
    """Return an inspectable prompt bundle without sending data to any service."""

    model: str | None = None

    def generate(self, *, instructions: str, input_text: str) -> str:
        return (
            "# Prompt-only mode\n\n"
            "No information was sent to an external model. Review or pass the following "
            "bundle to an approved provider.\n\n"
            "## Instructions\n\n"
            f"{instructions}\n\n"
            "## Request and evidence\n\n"
            f"{input_text}"
        )


class OpenAIProvider:
    def __init__(self, model: str | None = None):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("OpenAI support requires: pip install 'servicebridge-advocate[ai]'") from exc
        self.model = model or os.getenv("SERVICEBRIDGE_MODEL", "gpt-5.4-mini")
        self._client = OpenAI()

    def generate(self, *, instructions: str, input_text: str) -> str:
        response = self._client.responses.create(
            model=self.model,
            instructions=instructions,
            input=input_text,
            store=False,
        )
        return response.output_text
