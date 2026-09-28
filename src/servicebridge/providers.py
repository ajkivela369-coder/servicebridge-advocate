from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

from .local_runtime import LocalOpenAICompatibleProvider, RuntimeMode, RuntimePolicy


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



def provider_for_runtime(
    *,
    mode: RuntimeMode | str = RuntimeMode.CREDITLESS,
    local_endpoint: str = "http://127.0.0.1:8080/v1/chat/completions",
    local_model: str = "local-model",
    cloud_model: str | None = None,
    allow_external_network: bool = False,
    allow_cloud_fallback: bool = False,
) -> TextProvider:
    """
    Shared provider gate used by Elias/ServiceBridge.

    Creditless mode can only create a local provider. Hybrid mode may use a
    local provider first and only allows cloud when the caller explicitly
    opts into external networking/fallback. Cloud mode remains explicit.
    """
    mode = RuntimeMode(mode)
    policy = RuntimePolicy(
        mode=mode,
        allow_external_network=allow_external_network,
        allow_cloud_fallback=allow_cloud_fallback,
    )

    if mode == RuntimeMode.CREDITLESS:
        return LocalOpenAICompatibleProvider(
            endpoint=local_endpoint,
            model=local_model,
            policy=policy,
        )

    if mode == RuntimeMode.CLOUD:
        if not policy.cloud_allowed:
            raise PermissionError(
                "Cloud runtime requires allow_external_network=True and "
                "allow_cloud_fallback=True."
            )
        return OpenAIProvider(model=cloud_model)

    # Hybrid starts local. A higher-level orchestrator may choose cloud later
    # only after an explicit local failure and policy check.
    return LocalOpenAICompatibleProvider(
        endpoint=local_endpoint,
        model=local_model,
        policy=policy,
    )
