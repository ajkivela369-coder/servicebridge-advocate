from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any
from urllib.request import Request, urlopen

from servicebridge.local_runtime import RuntimeMode

from .core import ForgeCore
from .scheduler import WorkClass


@dataclass
class ForgeSDK:
    """
    App-facing Forge contract.

    Default behavior is in-process/local so desktop apps do not need networking.
    Set FORGE_CORE_URL to use the same contract over HTTP.
    """

    app_id: str
    core_url: str = ""

    @classmethod
    def for_app(cls, app_id: str) -> "ForgeSDK":
        return cls(
            app_id=app_id,
            core_url=os.getenv("FORGE_CORE_URL", "").rstrip("/"),
        )

    @property
    def transport(self) -> str:
        return "http" if self.core_url else "in-process"

    def _http(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        url = f"{self.core_url}{path}"
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        req = Request(
            url,
            data=body,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        with urlopen(req, timeout=5.0) as response:
            return json.loads(response.read().decode("utf-8"))

    def status(self) -> dict[str, Any]:
        if self.core_url:
            return self._http("GET", "/v1/status")
        return ForgeCore().status()

    def hardware(self) -> dict[str, Any]:
        status = self.status()
        return {
            "hardware": status["hardware"],
            "memory_budget": status["memory_budget"],
        }

    def capabilities(self) -> list[dict[str, Any]]:
        if self.core_url:
            data = self._http("GET", "/v1/capabilities")
            return data["capabilities"]
        return ForgeCore().capability_status()

    def models(self) -> list[dict[str, Any]]:
        if self.core_url:
            data = self._http("GET", "/v1/models")
            return data["models"]
        return ForgeCore().list_models()

    def select_model(
        self,
        capability: str,
        *,
        work_class: WorkClass | str = WorkClass.STANDARD,
    ) -> dict[str, Any]:
        work_class = WorkClass(work_class)
        payload = {
            "capability": capability,
            "work_class": work_class.value,
            "requester": self.app_id,
        }
        if self.core_url:
            return self._http("POST", "/v1/models/select", payload)
        return ForgeCore().select_model(
            capability=capability,
            work_class=work_class,
            requester=self.app_id,
        )

    def unload(self, reservation_id: str) -> dict[str, Any]:
        if self.core_url:
            return self._http(
                "POST",
                "/v1/models/unload",
                {"reservation_id": reservation_id},
            )
        return ForgeCore().unload_model(reservation_id)

    def apps(self) -> list[dict[str, Any]]:
        if self.core_url:
            return self._http("GET", "/v1/apps")["apps"]
        return ForgeCore().apps()

    def vault_status(self) -> dict[str, Any]:
        if self.core_url:
            return self._http("GET", "/v1/vault/status")
        return ForgeCore().vault_status()

    def jobs(self) -> list[dict[str, Any]]:
        if self.core_url:
            return self._http("GET", "/v1/jobs")["jobs"]
        return ForgeCore().job_status()

    def cache_status(self) -> dict[str, Any]:
        if self.core_url:
            return self._http("GET", "/v1/cache/status")
        return ForgeCore().cache_status()
