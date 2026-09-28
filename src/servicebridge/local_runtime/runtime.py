from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
import json
from pathlib import Path
import platform
import shutil
import sqlite3
import subprocess
import time
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class RuntimeMode(str, Enum):
    CREDITLESS = "creditless"
    HYBRID = "hybrid"
    CLOUD = "cloud"


LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


@dataclass(frozen=True)
class HardwareProfile:
    os: str
    machine: str
    cpu_count: int
    ram_gb: float | None
    gpu_name: str | None
    gpu_vram_gb: float | None
    nvidia_smi: bool
    tier: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ServiceStatus:
    service_id: str
    kind: str
    installed: bool
    healthy: bool
    endpoint: str = ""
    executable: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RuntimePolicy:
    mode: RuntimeMode = RuntimeMode.CREDITLESS
    allow_external_network: bool = False
    allow_cloud_fallback: bool = False
    allowed_external_hosts: tuple[str, ...] = ()

    def assert_url_allowed(self, url: str) -> None:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()

        if host in LOCAL_HOSTS:
            return

        if self.mode == RuntimeMode.CREDITLESS:
            raise PermissionError(
                f"Creditless Mode blocks non-local endpoint: {host or url}"
            )

        if not self.allow_external_network:
            raise PermissionError(
                f"External networking is disabled for runtime mode {self.mode.value}."
            )

        if self.allowed_external_hosts and host not in self.allowed_external_hosts:
            raise PermissionError(f"External host is not allow-listed: {host}")

    @property
    def cloud_allowed(self) -> bool:
        return (
            self.mode != RuntimeMode.CREDITLESS
            and self.allow_external_network
            and self.allow_cloud_fallback
        )


DEFAULT_SERVICES = {
    "llama_cpp": {
        "kind": "text",
        "executable": "llama-server",
        "endpoint": "http://127.0.0.1:8080/health",
        "notes": "Local OpenAI-compatible LLM/VLM server.",
    },
    "piper": {
        "kind": "tts",
        "executable": "piper",
        "endpoint": "",
        "notes": "Local neural text-to-speech.",
    },
    "ffmpeg": {
        "kind": "render",
        "executable": "ffmpeg",
        "endpoint": "",
        "notes": "Local deterministic video/audio renderer.",
    },
    "comfyui": {
        "kind": "image_video",
        "executable": "",
        "endpoint": "http://127.0.0.1:8188/system_stats",
        "notes": "Local image/video workflow server.",
    },
    "ollama": {
        "kind": "text",
        "executable": "ollama",
        "endpoint": "http://127.0.0.1:11434/api/tags",
        "notes": "Optional local model runner.",
    },
    "blender": {
        "kind": "3d_render",
        "executable": "blender",
        "endpoint": "",
        "notes": "Local 3D scene builder, animation, and renderer.",
    },
}


def _ram_gb() -> float | None:
    # Linux/macOS/Windows without psutil: prefer sysconf where available.
    try:
        import os

        pages = os.sysconf("SC_PHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
        return round((pages * page_size) / (1024**3), 2)
    except Exception:
        return None


def _nvidia_profile() -> tuple[str | None, float | None, bool]:
    exe = shutil.which("nvidia-smi")
    if not exe:
        return None, None, False
    try:
        proc = subprocess.run(
            [
                exe,
                "--query-gpu=name,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=4,
            check=True,
        )
        first = proc.stdout.strip().splitlines()[0]
        name, memory_mb = [x.strip() for x in first.split(",", 1)]
        return name, round(float(memory_mb) / 1024, 2), True
    except Exception:
        return None, None, True


def detect_hardware() -> HardwareProfile:
    import os

    gpu_name, gpu_vram_gb, has_smi = _nvidia_profile()
    ram = _ram_gb()
    cpu_count = os.cpu_count() or 1

    if gpu_vram_gb is not None and gpu_vram_gb >= 16:
        tier = "local-ai-large"
    elif gpu_vram_gb is not None and gpu_vram_gb >= 8:
        tier = "local-ai-medium"
    elif ram is not None and ram >= 16:
        tier = "cpu-local"
    else:
        tier = "lightweight-local"

    return HardwareProfile(
        os=platform.system(),
        machine=platform.machine(),
        cpu_count=cpu_count,
        ram_gb=ram,
        gpu_name=gpu_name,
        gpu_vram_gb=gpu_vram_gb,
        nvidia_smi=has_smi,
        tier=tier,
    )


def _healthcheck(url: str, timeout: float = 1.5) -> bool:
    try:
        req = Request(url, headers={"User-Agent": "ServiceBridge-LocalRuntime/1.0"})
        with urlopen(req, timeout=timeout) as response:
            return 200 <= int(response.status) < 500
    except Exception:
        return False


def discover_services(services: dict[str, dict[str, str]] | None = None) -> list[ServiceStatus]:
    services = services or DEFAULT_SERVICES
    out: list[ServiceStatus] = []
    for service_id, spec in services.items():
        executable = spec.get("executable", "")
        endpoint = spec.get("endpoint", "")
        exe_path = shutil.which(executable) if executable else None
        healthy = _healthcheck(endpoint) if endpoint else bool(exe_path)
        out.append(
            ServiceStatus(
                service_id=service_id,
                kind=spec.get("kind", ""),
                installed=bool(exe_path) or healthy,
                healthy=healthy,
                endpoint=endpoint,
                executable=exe_path or "",
                notes=spec.get("notes", ""),
            )
        )
    return out


class LocalOpenAICompatibleProvider:
    """Talk to a local llama.cpp/Ollama-compatible chat endpoint using stdlib only."""

    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:8080/v1/chat/completions",
        model: str = "local-model",
        policy: RuntimePolicy | None = None,
        timeout: float = 120.0,
    ):
        self.endpoint = endpoint
        self.model = model
        self.policy = policy or RuntimePolicy()
        self.timeout = timeout
        self.policy.assert_url_allowed(endpoint)

    def generate(self, *, instructions: str, input_text: str) -> str:
        self.policy.assert_url_allowed(self.endpoint)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": input_text},
            ],
            "stream": False,
        }
        req = Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        try:
            return data["choices"][0]["message"]["content"]
        except Exception as exc:
            raise RuntimeError("Local model returned an unexpected response shape.") from exc


class AssetCache:
    """Content-addressed local asset vault shared by every app."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.blobs = self.root / "blobs"
        self.blobs.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.root / "assets.sqlite3")
        self.db.row_factory = sqlite3.Row
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS assets (
                asset_id TEXT PRIMARY KEY,
                sha256 TEXT NOT NULL,
                kind TEXT NOT NULL,
                path TEXT NOT NULL,
                parents_json TEXT NOT NULL,
                provenance_json TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_assets_sha256 ON assets(sha256);
            """
        )

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> "AssetCache":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def put(
        self,
        data: bytes,
        *,
        kind: str,
        suffix: str = ".bin",
        parents: list[str] | None = None,
        provenance: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        digest = sha256(data).hexdigest()
        asset_id = f"{kind}:{digest[:20]}"
        safe_suffix = suffix if suffix.startswith(".") else f".{suffix}"
        path = self.blobs / f"{digest}{safe_suffix}"
        if not path.exists():
            path.write_bytes(data)
        with self.db:
            self.db.execute(
                """
                INSERT OR REPLACE INTO assets
                (asset_id, sha256, kind, path, parents_json, provenance_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    asset_id,
                    digest,
                    kind,
                    str(path),
                    json.dumps(parents or [], sort_keys=True),
                    json.dumps(provenance or {}, sort_keys=True),
                    time.time(),
                ),
            )
        return self.get(asset_id) or {}

    def get(self, asset_id: str) -> dict[str, Any] | None:
        row = self.db.execute(
            "SELECT * FROM assets WHERE asset_id = ?", (asset_id,)
        ).fetchone()
        if row is None:
            return None
        return {
            "asset_id": row["asset_id"],
            "sha256": row["sha256"],
            "kind": row["kind"],
            "path": row["path"],
            "parents": json.loads(row["parents_json"]),
            "provenance": json.loads(row["provenance_json"]),
            "created_at": row["created_at"],
        }


class JobQueue:
    """Tiny SQLite job queue for local workers."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                status TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
            """
        )

    def close(self) -> None:
        self.db.close()

    def enqueue(self, kind: str, payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, sort_keys=True)
        job_id = f"{kind}:{sha256((raw + str(time.time_ns())).encode()).hexdigest()[:16]}"
        now = time.time()
        with self.db:
            self.db.execute(
                "INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?)",
                (job_id, kind, "queued", raw, "{}", now, now),
            )
        return job_id

    def update(self, job_id: str, status: str, result: dict[str, Any] | None = None) -> None:
        with self.db:
            self.db.execute(
                "UPDATE jobs SET status=?, result_json=?, updated_at=? WHERE job_id=?",
                (status, json.dumps(result or {}, sort_keys=True), time.time(), job_id),
            )

    def get(self, job_id: str) -> dict[str, Any] | None:
        row = self.db.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        if row is None:
            return None
        return {
            "job_id": row["job_id"],
            "kind": row["kind"],
            "status": row["status"],
            "payload": json.loads(row["payload_json"]),
            "result": json.loads(row["result_json"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


def runtime_snapshot(mode: RuntimeMode = RuntimeMode.CREDITLESS) -> dict[str, Any]:
    return {
        "mode": mode.value,
        "hardware": detect_hardware().to_dict(),
        "services": [x.to_dict() for x in discover_services()],
        "cloud_fallback": False if mode == RuntimeMode.CREDITLESS else None,
    }
