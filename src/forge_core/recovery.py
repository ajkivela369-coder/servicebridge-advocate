from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any
import zipfile

from servicebridge.local_runtime.archive import safe_extract_zip
from servicebridge.local_runtime.offline import verify_offline_pack


@dataclass(frozen=True)
class RecoveryReport:
    status: str
    pack_verified: bool
    clean_restore_directory: bool
    restored_code_compiles: bool
    forge_imports_from_restore: bool
    primary_executable_removed_from_path: bool
    network_isolation_confirmed: bool
    representative_project_rendered: bool
    rendered_output: str
    details: tuple[str, ...]
    created_at: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_recovery_status(path: str | Path) -> dict[str, Any]:
    report_path = Path(path)
    if not report_path.is_file():
        return {
            "status": "NOT_RUN",
            "verified_restore": False,
            "detail": "No disaster-recovery drill report exists yet.",
        }
    try:
        data = json.loads(report_path.read_text())
    except Exception as exc:
        return {
            "status": "INVALID",
            "verified_restore": False,
            "detail": f"Recovery report could not be read: {exc}",
        }
    return {
        **data,
        "verified_restore": data.get("status") == "PASS",
    }


def _restricted_path_without(executable: str) -> tuple[str, bool]:
    original = os.environ.get("PATH", "")
    exe = shutil.which(executable)
    if not exe:
        return original, True

    exe_dir = str(Path(exe).resolve().parent)
    parts = [
        part for part in original.split(os.pathsep)
        if part and Path(part).resolve() != Path(exe_dir).resolve()
    ]
    restricted = os.pathsep.join(parts)
    return restricted, shutil.which(executable, path=restricted) is None


def run_recovery_drill(
    pack_path: str | Path,
    *,
    report_path: str | Path,
    work_root: str | Path | None = None,
    primary_executable: str = "ollama",
    network_isolation_confirmed: bool = False,
) -> RecoveryReport:
    """
    Restore Forge into a new empty directory and render a representative MP4.

    PASS is intentionally strict: archive verification, clean restore, compile,
    restored-code import, missing-primary-executable fallback, real render, and
    explicit network isolation confirmation must all be true.
    """
    verification = verify_offline_pack(pack_path)
    details: list[str] = []

    root_parent = Path(work_root).resolve() if work_root else None
    temp_cm = tempfile.TemporaryDirectory(
        prefix="forge-recovery-",
        dir=str(root_parent) if root_parent else None,
    )
    with temp_cm as directory:
        restore_root = Path(directory).resolve()
        clean = not any(restore_root.iterdir())

        with zipfile.ZipFile(Path(pack_path).resolve()) as zf:
            safe_extract_zip(zf, restore_root)

        repo = restore_root / "repo"
        if not repo.is_dir():
            details.append("offline pack did not contain repo/")
        compile_ok = False
        import_ok = False
        render_ok = False
        output_path = restore_root / "recovery-output.mp4"

        if repo.is_dir():
            compile_proc = subprocess.run(
                [sys.executable, "-m", "compileall", "-q", str(repo / "src")],
                capture_output=True,
                text=True,
            )
            compile_ok = compile_proc.returncode == 0
            if not compile_ok:
                details.append(compile_proc.stderr[-2000:])

            env = os.environ.copy()
            env["PYTHONPATH"] = str(repo / "src")
            env["HF_HUB_OFFLINE"] = "1"
            env["TRANSFORMERS_OFFLINE"] = "1"
            env["PIP_NO_INDEX"] = "1"
            env["FORGE_MODE"] = "creditless"

            restricted_path, removed = _restricted_path_without(primary_executable)
            env["PATH"] = restricted_path

            import_proc = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "import forge_core, pathlib; "
                        "print(pathlib.Path(forge_core.__file__).resolve())"
                    ),
                ],
                cwd=str(repo),
                env=env,
                capture_output=True,
                text=True,
            )
            import_ok = (
                import_proc.returncode == 0
                and str((repo / "src" / "forge_core").resolve())
                in import_proc.stdout
            )
            if not import_ok:
                details.append("Forge did not import from restored repo: " + import_proc.stderr[-1000:])

            smoke = repo / "scripts" / "forge_recovery_smoke.py"
            project = repo / "config" / "recovery" / "representative_project.json"
            if smoke.is_file() and project.is_file() and shutil.which("ffmpeg", path=restricted_path):
                render_proc = subprocess.run(
                    [
                        sys.executable,
                        str(smoke),
                        "--project",
                        str(project),
                        "--output",
                        str(output_path),
                    ],
                    cwd=str(repo),
                    env=env,
                    capture_output=True,
                    text=True,
                )
                render_ok = (
                    render_proc.returncode == 0
                    and output_path.is_file()
                    and output_path.stat().st_size > 0
                )
                if not render_ok:
                    details.append("Recovery render failed: " + render_proc.stderr[-2000:])
            else:
                details.append("Restored smoke project or FFmpeg was unavailable.")

        else:
            removed = False

        checks = [
            bool(verification.get("ok")),
            clean,
            compile_ok,
            import_ok,
            removed,
            bool(network_isolation_confirmed),
            render_ok,
        ]
        status = "PASS" if all(checks) else "PARTIAL"
        report = RecoveryReport(
            status=status,
            pack_verified=bool(verification.get("ok")),
            clean_restore_directory=clean,
            restored_code_compiles=compile_ok,
            forge_imports_from_restore=import_ok,
            primary_executable_removed_from_path=removed,
            network_isolation_confirmed=bool(network_isolation_confirmed),
            representative_project_rendered=render_ok,
            rendered_output=str(output_path) if render_ok else "",
            details=tuple(x for x in details if x),
            created_at=time.time(),
        )

        report_file = Path(report_path)
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        return report
