from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Any
from urllib.request import urlopen


@dataclass(frozen=True)
class ManagedProcessSpec:
    process_id: str
    name: str
    command: tuple[str, ...]
    health_url: str
    open_url: str


def default_process_specs(repo_root: str | Path = ".") -> dict[str, ManagedProcessSpec]:
    root = Path(repo_root).resolve()
    py = sys.executable
    return {
        "forge_core": ManagedProcessSpec(
            "forge_core",
            "Forge Core",
            (
                py, "-m", "uvicorn", "forge_core.api:app",
                "--host", "127.0.0.1", "--port", "8765",
            ),
            "http://127.0.0.1:8765/health",
            "http://127.0.0.1:8765/docs",
        ),
        "elias": ManagedProcessSpec(
            "elias",
            "Elias API",
            (
                py, "-m", "uvicorn", "servicebridge.api:app",
                "--host", "127.0.0.1", "--port", "8766",
            ),
            "http://127.0.0.1:8766/health",
            "http://127.0.0.1:8766/docs",
        ),
        "evidence_auditor": ManagedProcessSpec(
            "evidence_auditor",
            "Evidence Auditor",
            (
                py, "-m", "streamlit", "run",
                str(root / "portfolio/evidence-auditor/legacy-streamlit/dashboard.py"),
                "--server.headless", "true",
                "--server.address", "127.0.0.1",
                "--server.port", "8511",
            ),
            "http://127.0.0.1:8511/_stcore/health",
            "http://127.0.0.1:8511",
        ),
        "medforge": ManagedProcessSpec(
            "medforge",
            "MedForge",
            (
                py, "-m", "streamlit", "run",
                str(root / "apps/medforge-imaging-studio/app.py"),
                "--server.headless", "true",
                "--server.address", "127.0.0.1",
                "--server.port", "8512",
            ),
            "http://127.0.0.1:8512/_stcore/health",
            "http://127.0.0.1:8512",
        ),
        "grimforge": ManagedProcessSpec(
            "grimforge",
            "GrimForge",
            (
                py, "-m", "streamlit", "run",
                str(root / "apps/grimforge-war-theater/app.py"),
                "--server.headless", "true",
                "--server.address", "127.0.0.1",
                "--server.port", "8513",
            ),
            "http://127.0.0.1:8513/_stcore/health",
            "http://127.0.0.1:8513",
        ),
    }


class ProcessRegistry:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text() or "{}")
        except Exception:
            return {}

    def write(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2, sort_keys=True))

    def set(self, process_id: str, payload: dict[str, Any]) -> None:
        data = self.read()
        data[process_id] = payload
        self.write(data)

    def remove(self, process_id: str) -> None:
        data = self.read()
        data.pop(process_id, None)
        self.write(data)


class ForgeProcessManager:
    def __init__(
        self,
        *,
        repo_root: str | Path = ".",
        data_root: str | Path = "./private_data/forge",
    ):
        self.repo_root = Path(repo_root).resolve()
        self.data_root = Path(data_root).resolve()
        self.logs = self.data_root / "logs"
        self.logs.mkdir(parents=True, exist_ok=True)
        self.registry = ProcessRegistry(self.data_root / "processes.json")
        self.specs = default_process_specs(self.repo_root)

    @staticmethod
    def _alive(pid: int) -> bool:
        try:
            os.kill(int(pid), 0)
            return True
        except Exception:
            return False

    @staticmethod
    def _healthy(url: str, timeout: float = 0.5) -> bool:
        try:
            with urlopen(url, timeout=timeout) as response:
                return 200 <= int(response.status) < 500
        except Exception:
            return False

    def status(self, process_id: str) -> dict[str, Any]:
        spec = self.specs[process_id]
        entry = self.registry.read().get(process_id, {})
        pid = int(entry.get("pid", 0) or 0)
        alive = bool(pid and self._alive(pid))
        healthy = self._healthy(spec.health_url)
        if pid and not alive:
            self.registry.remove(process_id)
        return {
            "process_id": process_id,
            "name": spec.name,
            "pid": pid if alive else None,
            "alive": alive,
            "healthy": healthy,
            "health_url": spec.health_url,
            "open_url": spec.open_url,
            "log_path": str(self.logs / f"{process_id}.log"),
        }

    def all_status(self) -> list[dict[str, Any]]:
        return [self.status(key) for key in self.specs]

    def start(self, process_id: str, *, forge_mode: str = "creditless") -> dict[str, Any]:
        spec = self.specs[process_id]
        current = self.status(process_id)
        if current["alive"] or current["healthy"]:
            return current

        log_path = self.logs / f"{process_id}.log"
        env = os.environ.copy()
        env["FORGE_MODE"] = forge_mode
        env.setdefault("FORGE_DATA_ROOT", str(self.data_root))
        if process_id != "forge_core":
            env.setdefault("FORGE_CORE_URL", "http://127.0.0.1:8765")

        with open(log_path, "ab", buffering=0) as log:
            proc = subprocess.Popen(
                list(spec.command),
                cwd=str(self.repo_root),
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                creationflags=(
                    getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                    if os.name == "nt" else 0
                ),
                start_new_session=(os.name != "nt"),
            )
        self.registry.set(
            process_id,
            {
                "pid": int(proc.pid),
                "started_at": time.time(),
                "command": list(spec.command),
            },
        )
        return self.status(process_id)

    def stop(self, process_id: str) -> dict[str, Any]:
        current = self.status(process_id)
        pid = current.get("pid")
        if not pid:
            return current

        try:
            if os.name == "nt":
                os.kill(int(pid), signal.SIGTERM)
            else:
                os.killpg(int(pid), signal.SIGTERM)
        except Exception:
            try:
                os.kill(int(pid), signal.SIGTERM)
            except Exception:
                pass

        self.registry.remove(process_id)
        return self.status(process_id)
