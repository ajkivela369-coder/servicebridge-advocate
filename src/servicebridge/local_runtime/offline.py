from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import zipfile
from typing import Iterable


SAFE_TOP_LEVELS = {"src", "apps", "portfolio", "scripts", "docs", "config", "tests", ".github"}
SAFE_ROOT_FILES = {"pyproject.toml", "README.md", "LICENSE", ".gitignore"}
SAFE_EXTENSIONS = {
    ".py", ".md", ".json", ".toml", ".txt", ".yaml", ".yml",
    ".ps1", ".sh", ".html", ".css", ".js", ".ts", ".tsx", ".jsx", ".ipynb",
}
DENY_PARTS = {
    ".git", ".venv", ".venv-creditless", "private_data", "node_modules",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist", "build",
}
DENY_NAMES = {".env", ".env.local", ".env.production", "secrets.toml"}


@dataclass(frozen=True)
class PackEntry:
    archive_path: str
    source_path: str
    size: int
    sha256: str
    category: str

    def to_dict(self):
        return asdict(self)


def file_sha256(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = sha256()
    with open(Path(path), "rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _safe_repo_file(repo_root: Path, path: Path) -> bool:
    try:
        rel = path.resolve().relative_to(repo_root.resolve())
    except Exception:
        return False
    if any(part in DENY_PARTS for part in rel.parts):
        return False
    if path.name in DENY_NAMES or path.name.startswith(".env"):
        return False
    if len(rel.parts) == 1:
        return path.name in SAFE_ROOT_FILES
    if rel.parts[0] not in SAFE_TOP_LEVELS:
        return False
    return path.suffix.lower() in SAFE_EXTENSIONS


def repo_code_entries(repo_root: str | Path) -> list[PackEntry]:
    root = Path(repo_root).resolve()
    entries: list[PackEntry] = []
    for path in root.rglob("*"):
        if not path.is_file() or not _safe_repo_file(root, path):
            continue
        rel = path.relative_to(root).as_posix()
        entries.append(
            PackEntry(
                archive_path=f"repo/{rel}",
                source_path=str(path),
                size=path.stat().st_size,
                sha256=file_sha256(path),
                category="repo-code",
            )
        )
    entries.sort(key=lambda x: x.archive_path)
    return entries


def wheelhouse_entries(path: str | Path | None) -> list[PackEntry]:
    if not path:
        return []
    root = Path(path).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(root)
    entries = []
    for wheel in sorted(root.glob("*.whl")):
        entries.append(
            PackEntry(
                archive_path=f"wheelhouse/{wheel.name}",
                source_path=str(wheel),
                size=wheel.stat().st_size,
                sha256=file_sha256(wheel),
                category="wheel",
            )
        )
    return entries


def catalog_model_entries(
    catalog_path: str | Path | None,
    *,
    include_models: bool,
) -> tuple[list[PackEntry], list[dict]]:
    if not catalog_path:
        return [], []
    path = Path(catalog_path).expanduser().resolve()
    if not path.is_file():
        return [], []
    data = json.loads(path.read_text() or "{}")
    model_records = data.get("models", [])
    entries = []
    if include_models:
        for record in model_records:
            model_path = Path(str(record.get("path", ""))).expanduser()
            if not model_path.is_file():
                continue
            entries.append(
                PackEntry(
                    archive_path=f"models/{record['model_id']}/{model_path.name}",
                    source_path=str(model_path.resolve()),
                    size=model_path.stat().st_size,
                    sha256=file_sha256(model_path),
                    category="explicit-model",
                )
            )
    return entries, model_records


def workflow_entries(catalog_path: str | Path | None) -> tuple[list[PackEntry], list[dict]]:
    if not catalog_path:
        return [], []
    path = Path(catalog_path).expanduser().resolve()
    if not path.is_file():
        return [], []
    data = json.loads(path.read_text() or "{}")
    records = data.get("workflows", [])
    entries = []
    for record in records:
        workflow_path = Path(str(record.get("path", ""))).expanduser()
        if not workflow_path.is_file():
            continue
        entries.append(
            PackEntry(
                archive_path=f"workflows/{record['workflow_id']}/{workflow_path.name}",
                source_path=str(workflow_path.resolve()),
                size=workflow_path.stat().st_size,
                sha256=file_sha256(workflow_path),
                category="explicit-workflow",
            )
        )
    return entries, records


def build_offline_pack(
    output_zip: str | Path,
    *,
    repo_root: str | Path,
    model_catalog: str | Path | None = None,
    workflow_catalog: str | Path | None = None,
    wheelhouse: str | Path | None = None,
    include_models: bool = False,
) -> dict:
    """
    Build a portable creditless-runtime pack from explicitly safe sources.

    Evidence databases, .env files, private_data, arbitrary user files, and Git
    metadata are never swept into the repository snapshot.
    """
    repo_entries = repo_code_entries(repo_root)
    wheels = wheelhouse_entries(wheelhouse)
    models, model_records = catalog_model_entries(
        model_catalog,
        include_models=include_models,
    )
    workflows, workflow_records = workflow_entries(workflow_catalog)

    entries = repo_entries + wheels + models + workflows
    output = Path(output_zip).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "schema_version": 1,
        "pack_type": "ServiceBridge Forge Creditless Offline Pack",
        "models_included": bool(include_models),
        "privacy_rule": (
            "Repository snapshot is extension/top-level whitelisted. "
            ".env, private_data, caches, arbitrary user files, and evidence databases are excluded."
        ),
        "registered_models": model_records,
        "registered_workflows": workflow_records,
        "entries": [entry.to_dict() for entry in entries],
    }

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for entry in entries:
            zf.write(entry.source_path, entry.archive_path)
        zf.writestr("OFFLINE_PACK_MANIFEST.json", json.dumps(manifest, indent=2))
        zf.writestr(
            "README_OFFLINE_PACK.txt",
            (
                "ServiceBridge / Forge Creditless Offline Pack\n\n"
                "Verify this pack before restoring it.\n"
                "Model files are included only when explicitly requested.\n"
                "Evidence databases and environment-secret files are intentionally excluded.\n"
            ),
        )

    return {
        "output_zip": str(output),
        "entry_count": len(entries),
        "repo_files": len(repo_entries),
        "wheels": len(wheels),
        "models": len(models),
        "workflows": len(workflows),
        "bytes": output.stat().st_size,
    }


def verify_offline_pack(path: str | Path) -> dict:
    pack = Path(path).expanduser().resolve()
    with zipfile.ZipFile(pack) as zf:
        manifest = json.loads(zf.read("OFFLINE_PACK_MANIFEST.json"))
        problems = []
        checked = 0
        for entry in manifest.get("entries", []):
            archive_path = entry["archive_path"]
            try:
                raw = zf.read(archive_path)
            except KeyError:
                problems.append(f"missing: {archive_path}")
                continue
            digest = sha256(raw).hexdigest()
            if digest != entry["sha256"]:
                problems.append(f"hash mismatch: {archive_path}")
            if len(raw) != int(entry["size"]):
                problems.append(f"size mismatch: {archive_path}")
            checked += 1

    return {
        "pack": str(pack),
        "checked_entries": checked,
        "ok": not problems,
        "problems": problems,
        "models_included": bool(manifest.get("models_included", False)),
    }
