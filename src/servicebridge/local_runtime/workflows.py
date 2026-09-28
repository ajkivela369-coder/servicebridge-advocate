from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LocalWorkflow:
    workflow_id: str
    kind: str
    path: str
    min_vram_gb: float = 0.0
    notes: str = ""
    sha256: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LocalWorkflowCatalog:
    """Registry for already-present local ComfyUI/workflow JSON files."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text(json.dumps({"workflows": []}, indent=2))

    def list(self) -> list[LocalWorkflow]:
        data = json.loads(self.path.read_text() or "{}")
        return [LocalWorkflow(**x) for x in data.get("workflows", [])]

    def save(self, items: list[LocalWorkflow]) -> None:
        self.path.write_text(
            json.dumps(
                {"workflows": [x.to_dict() for x in items]},
                indent=2,
                sort_keys=True,
            )
        )

    def add(self, workflow: LocalWorkflow, *, replace: bool = False) -> None:
        path = Path(workflow.path).expanduser()
        if not path.is_file():
            raise FileNotFoundError(path)
        json.loads(path.read_text())
        items = self.list()
        if any(x.workflow_id == workflow.workflow_id for x in items) and not replace:
            raise ValueError(f"Workflow already registered: {workflow.workflow_id}")
        items = [x for x in items if x.workflow_id != workflow.workflow_id]
        items.append(workflow)
        items.sort(key=lambda x: (x.kind, x.workflow_id))
        self.save(items)

    def load(self, workflow_id: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        workflow = next((x for x in self.list() if x.workflow_id == workflow_id), None)
        if workflow is None:
            raise KeyError(workflow_id)
        path = Path(workflow.path).expanduser()
        data = json.loads(path.read_text())
        return substitute_variables(data, variables or {})

    def verify(self, workflow_id: str) -> dict[str, Any]:
        workflow = next((x for x in self.list() if x.workflow_id == workflow_id), None)
        if workflow is None:
            raise KeyError(workflow_id)
        path = Path(workflow.path).expanduser()
        exists = path.is_file()
        digest = file_sha256(path) if exists else ""
        valid_json = False
        if exists:
            try:
                json.loads(path.read_text())
                valid_json = True
            except Exception:
                valid_json = False
        return {
            "workflow_id": workflow_id,
            "exists": exists,
            "valid_json": valid_json,
            "sha256": digest,
            "hash_match": (
                digest.lower() == workflow.sha256.lower()
                if workflow.sha256 and digest
                else None
            ),
        }


def substitute_variables(value: Any, variables: dict[str, Any]) -> Any:
    if isinstance(value, dict):
        return {k: substitute_variables(v, variables) for k, v in value.items()}
    if isinstance(value, list):
        return [substitute_variables(v, variables) for v in value]
    if isinstance(value, str):
        out = value
        for key, replacement in variables.items():
            out = out.replace("{{" + str(key) + "}}", str(replacement))
        return out
    return value


def file_sha256(path: str | Path) -> str:
    return sha256(Path(path).read_bytes()).hexdigest()
