from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any
from urllib.request import Request, urlopen

from servicebridge.local_runtime import RuntimeMode, RuntimePolicy

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



    # --- Standard execution surface used by all Forge-backed apps ---

    def reason(
        self,
        instructions: str,
        input_text: str,
        *,
        work_class: WorkClass | str = WorkClass.STANDARD,
    ) -> dict[str, Any]:
        work_class = WorkClass(work_class)
        if self.core_url:
            return self._http(
                "POST",
                "/v1/reason",
                {
                    "app_id": self.app_id,
                    "instructions": instructions,
                    "input": input_text,
                    "work_class": work_class.value,
                },
            )

        from servicebridge.providers import provider_for_runtime

        selection = self.select_model("reason", work_class=work_class)
        selected = selection.get("selected_model") or {}
        reservation_id = str(selection.get("reservation_id") or "")
        if not selected:
            raise RuntimeError(selection.get("reason") or "Forge could not admit a reasoning model.")
        model_id = str(selected["model_id"])
        try:
            provider = provider_for_runtime(
                mode=RuntimeMode.CREDITLESS,
                local_endpoint=os.getenv(
                    "FORGE_LLM_ENDPOINT",
                    "http://127.0.0.1:8080/v1/chat/completions",
                ),
                local_model=model_id,
                allow_external_network=False,
                allow_cloud_fallback=False,
            )
            text = provider.generate(
                instructions=instructions,
                input_text=input_text,
            )
            return {
                "text": text,
                "backend": "Forge Core",
                "model_id": model_id,
                "selection": selection,
                "cloud_used": False,
            }
        finally:
            if reservation_id:
                self.unload(reservation_id)

    def vision(
        self,
        *,
        image_data_uri: str,
        instructions: str,
        question: str,
        work_class: WorkClass | str = WorkClass.STANDARD,
    ) -> dict[str, Any]:
        work_class = WorkClass(work_class)
        if self.core_url:
            return self._http(
                "POST",
                "/v1/vision",
                {
                    "app_id": self.app_id,
                    "image_data_uri": image_data_uri,
                    "instructions": instructions,
                    "question": question,
                    "work_class": work_class.value,
                },
            )

        from servicebridge.local_runtime.vision import LocalVisionClient

        selection = self.select_model("vision", work_class=work_class)
        selected = selection.get("selected_model") or {}
        reservation_id = str(selection.get("reservation_id") or "")
        if not selected:
            raise RuntimeError(selection.get("reason") or "Forge could not admit a vision model.")
        model_id = str(selected["model_id"])
        try:
            client = LocalVisionClient(
                endpoint=os.getenv(
                    "FORGE_VLM_ENDPOINT",
                    "http://127.0.0.1:8080/v1/chat/completions",
                ),
                model=model_id,
                policy=RuntimePolicy(mode=RuntimeMode.CREDITLESS),
            )
            text = client.analyze(
                image_data_uri=image_data_uri,
                instructions=instructions,
                question=question,
            )
            return {
                "text": text,
                "backend": "Forge Core",
                "model_id": model_id,
                "selection": selection,
                "cloud_used": False,
            }
        finally:
            if reservation_id:
                self.unload(reservation_id)

    def transcribe(
        self,
        media_path: str,
        *,
        model_size: str = "small",
        device: str = "cpu",
        compute_type: str = "int8",
        language: str | None = None,
    ) -> dict[str, Any]:
        if self.core_url:
            return self._http(
                "POST",
                "/v1/transcribe",
                {
                    "app_id": self.app_id,
                    "media_path": media_path,
                    "model_size": model_size,
                    "device": device,
                    "compute_type": compute_type,
                    "language": language,
                },
            )

        from servicebridge.local_runtime.workers import transcribe_file

        result = transcribe_file(
            media_path,
            model_size=model_size,
            device=device,
            compute_type=compute_type,
            language=language,
        )
        result["backend"] = "Forge Core"
        result["cloud_used"] = False
        return result

    def tts(
        self,
        text: str,
        *,
        output_wav: str,
        piper_model: str | None = None,
        kokoro_voice: str = "af_heart",
    ) -> dict[str, Any]:
        if self.core_url:
            return self._http(
                "POST",
                "/v1/tts",
                {
                    "app_id": self.app_id,
                    "text": text,
                    "output_wav": output_wav,
                    "piper_model": piper_model,
                    "kokoro_voice": kokoro_voice,
                },
            )

        from servicebridge.local_runtime.speech import generate_speech_local_auto

        result = generate_speech_local_auto(
            text,
            output_wav=output_wav,
            piper_model=piper_model,
            kokoro_voice=kokoro_voice,
        )
        result["backend"] = "Forge Core"
        result["cloud_used"] = False
        return result

    def embed(self, texts: list[str]) -> dict[str, Any]:
        if self.core_url:
            return self._http(
                "POST",
                "/v1/embed",
                {"app_id": self.app_id, "texts": texts},
            )

        from servicebridge.local_runtime.memory import LocalEmbeddingClient

        selection = self.select_model("embed", work_class=WorkClass.TINY)
        selected = selection.get("selected_model") or {}
        reservation_id = str(selection.get("reservation_id") or "")
        if not selected:
            raise RuntimeError(selection.get("reason") or "Forge could not admit an embedding model.")
        model_id = str(selected["model_id"])
        try:
            client = LocalEmbeddingClient(
                endpoint=os.getenv(
                    "FORGE_EMBEDDING_ENDPOINT",
                    "http://127.0.0.1:8080/v1/embeddings",
                ),
                model=model_id,
                policy=RuntimePolicy(mode=RuntimeMode.CREDITLESS),
            )
            return {
                "vectors": client.embed(texts),
                "backend": "Forge Core",
                "model_id": model_id,
                "selection": selection,
                "cloud_used": False,
            }
        finally:
            if reservation_id:
                self.unload(reservation_id)

    def ocr(self, path: str) -> dict[str, Any]:
        if self.core_url:
            return self._http(
                "POST",
                "/v1/ocr",
                {"app_id": self.app_id, "path": path},
            )

        from pathlib import Path
        from servicebridge.local_runtime.documents import extract_pdf_text, paddle_ocr

        p = Path(path)
        if p.suffix.lower() == ".pdf":
            pages = extract_pdf_text(p)
            if any(bool(x.get("needs_ocr")) for x in pages):
                result = paddle_ocr(p)
                result["pages"] = pages
            else:
                result = {
                    "engine": "pypdf",
                    "source": str(p),
                    "pages": pages,
                    "text": "\n\n".join(
                        str(x.get("text", "")) for x in pages
                    ),
                }
        else:
            result = paddle_ocr(p)
        result["backend"] = "Forge Core"
        result["cloud_used"] = False
        return result

    def render_video(self, plan) -> dict[str, Any]:
        from dataclasses import asdict
        from servicebridge.local_runtime.render import LocalRenderPlan, render_plan

        if self.core_url:
            payload = plan if isinstance(plan, dict) else asdict(plan)
            return self._http(
                "POST",
                "/v1/video",
                {"app_id": self.app_id, "plan": payload},
            )

        if isinstance(plan, dict):
            plan = LocalRenderPlan.from_dict(plan)
        output = render_plan(plan)
        return {
            "output_path": str(output),
            "backend": "Forge Core",
            "render_mode": "deterministic-local",
            "cloud_used": False,
        }

    def vault_add_bytes(
        self,
        data: bytes,
        *,
        original_name: str,
        mime_type: str = "",
        metadata: dict[str, Any] | None = None,
        role: str = "source",
        locator: str = "",
    ) -> dict[str, Any]:
        if self.core_url:
            import base64
            source = self._http(
                "POST",
                "/v1/vault/source",
                {
                    "app_id": self.app_id,
                    "original_name": original_name,
                    "data_b64": base64.b64encode(data).decode("ascii"),
                    "mime_type": mime_type,
                    "metadata": metadata or {},
                    "role": role,
                    "locator": locator,
                },
            )
            return source

        from .vault import ForgeVault

        core = ForgeCore()
        with ForgeVault(core.paths.vault) as vault:
            source = vault.add_bytes(
                data,
                original_name=original_name,
                mime_type=mime_type,
                metadata=metadata,
            )
            vault.reference(
                self.app_id,
                source["source_id"],
                role=role,
                locator=locator,
            )
            source["references"] = vault.references_for(source["source_id"])
            source["backend"] = "Forge Core"
            return source



    def ingest_document_bytes(
        self,
        data: bytes,
        *,
        original_name: str,
        mime_type: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Vault the original once, then extract local page/text records."""
        from pathlib import Path
        import tempfile

        source = self.vault_add_bytes(
            data,
            original_name=original_name,
            mime_type=mime_type,
            metadata=metadata,
            role="ingested-source",
        )

        suffixes = "".join(Path(original_name).suffixes) or ".bin"
        pages: list[dict[str, Any]] = []
        with tempfile.NamedTemporaryFile(suffix=suffixes) as tmp:
            tmp.write(data)
            tmp.flush()
            path = Path(tmp.name)
            lower = original_name.lower()
            if lower.endswith(".pdf"):
                from servicebridge.local_runtime.documents import extract_pdf_text

                pages = extract_pdf_text(path)
                if any(bool(x.get("needs_ocr")) for x in pages):
                    try:
                        ocr_result = self.ocr(str(path))
                        ocr_text = str(ocr_result.get("text", "")).strip()
                        if ocr_text:
                            pages = [{
                                "page": 1,
                                "text": ocr_text,
                                "needs_ocr": False,
                                "ocr_fallback": True,
                            }]
                    except Exception:
                        # Embedded text remains available even when optional OCR
                        # is not installed.
                        pass
            elif lower.endswith((".txt", ".md", ".csv", ".json")):
                pages = [{
                    "page": 1,
                    "text": data.decode("utf-8", errors="replace"),
                    "needs_ocr": False,
                }]
            else:
                try:
                    ocr_result = self.ocr(str(path))
                    pages = [{
                        "page": 1,
                        "text": str(ocr_result.get("text", "")),
                        "needs_ocr": False,
                        "ocr_fallback": True,
                    }]
                except Exception:
                    pages = []

        for page in pages:
            page["source_id"] = source["source_id"]
            page["sha256"] = source["sha256"]
            page["source_name"] = original_name

        return {
            "source": source,
            "pages": pages,
            "backend": "Forge Core",
        }
