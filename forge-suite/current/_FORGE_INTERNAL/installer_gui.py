from __future__ import annotations

import ctypes
import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
import traceback
import urllib.request
import webbrowser
import zipfile
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

VERSION = "0.5.6-workflow-recovery"
HERE = Path(__file__).resolve().parent
RUNTIME_SOURCE = HERE / "runtime"
LOGQ: queue.Queue[str] = queue.Queue()


def default_home() -> Path:
    # Prefer D: for model/storage growth, otherwise use the user's profile.
    if Path("D:/").exists():
        return Path("D:/Forge")
    return Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Forge"


def log(msg: str):
    LOGQ.put(str(msg))


def refresh_path():
    """Reload user/machine PATH after winget installs tools."""
    parts: list[str] = []
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment") as k:
            parts.append(winreg.QueryValueEx(k, "Path")[0])
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as k:
            try:
                parts.append(winreg.QueryValueEx(k, "Path")[0])
            except FileNotFoundError:
                pass
    except Exception:
        pass
    if parts:
        os.environ["PATH"] = ";".join(parts) + ";" + os.environ.get("PATH", "")


def run(cmd, cwd=None, check=True, env=None):
    shown = subprocess.list2cmdline([str(x) for x in cmd]) if isinstance(cmd, (list, tuple)) else str(cmd)
    log(f"> {shown}")
    p = subprocess.Popen(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
        shell=isinstance(cmd, str),
    )
    assert p.stdout is not None
    for line in p.stdout:
        log(line.rstrip())
    rc = p.wait()
    if check and rc != 0:
        raise RuntimeError(f"Command failed with exit code {rc}: {shown}")
    return rc


def winget_install(package_id: str, label: str) -> bool:
    refresh_path()
    if not shutil.which("winget"):
        log(f"WARNING: winget unavailable; skipped {label}.")
        return False
    log(f"Installing {label}...")
    rc = run([
        "winget", "install", "--id", package_id, "-e", "--source", "winget",
        "--accept-package-agreements", "--accept-source-agreements",
    ], check=False)
    refresh_path()
    if rc != 0:
        log(f"WARNING: {label} did not install (winget exit {rc}). Forge will continue with available fallbacks.")
        return False
    return True



def find_blender_windows() -> Path | None:
    refresh_path()
    p = shutil.which("blender")
    if p:
        return Path(p)
    base = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Blender Foundation"
    if base.exists():
        hits = sorted(base.glob("Blender */blender.exe"), reverse=True)
        if hits:
            return hits[0]
    return None


def install_media_3d_tools(home: Path):
    set_env(home)
    refresh_path()
    if not shutil.which("ffmpeg"):
        winget_install("Gyan.FFmpeg", "FFmpeg")
    blender = find_blender_windows()
    if blender:
        log(f"Blender already installed: {blender}")
    else:
        winget_install("BlenderFoundation.Blender", "Blender 3D")
        blender = find_blender_windows()
    config = home / "config"
    config.mkdir(parents=True, exist_ok=True)
    record = {
        "blender": str(blender) if blender else None,
        "ffmpeg": shutil.which("ffmpeg"),
        "purpose": ["MedForge 3D mechanism teaching", "GrimForge 3D previs/blockout"],
        "note": "ComfyUI remains the optional AI image/video generator; Blender is the shared 3D scene/animation renderer."
    }
    (config / "media-3d-tools.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    if blender:
        os.environ["FORGE_BLENDER"] = str(blender)
        log(f"MEDIA / 3D TOOLS READY. Blender: {blender}")
    else:
        log("WARNING: Blender is still unavailable. MedForge/GrimForge 3D buttons will explain how to install it.")
    return record

def set_env(home: Path):
    os.environ["FORGE_HOME"] = str(home)
    os.environ["HF_HOME"] = str(home / "models" / "huggingface")
    os.environ["OLLAMA_MODELS"] = str(home / "models" / "ollama")
    for d in [
        "models/huggingface", "models/ollama", "models/whisper", "models/tts",
        "projects", "vault", "exports", "logs", "backups", "cache", "tmp", "envs",
    ]:
        (home / d).mkdir(parents=True, exist_ok=True)


def _listener_pids(port: int = 8787) -> list[int]:
    if os.name != "nt":
        return []
    try:
        out = subprocess.check_output(
            ["netstat", "-ano", "-p", "tcp"],
            text=True, errors="replace", stderr=subprocess.DEVNULL,
        )
    except Exception:
        return []
    pids: list[int] = []
    for raw in out.splitlines():
        parts = raw.split()
        if len(parts) < 5 or parts[-2].upper() != "LISTENING":
            continue
        local = parts[1]
        if not local.endswith(f":{port}"):
            continue
        try:
            pid = int(parts[-1])
        except ValueError:
            continue
        if pid > 0 and pid not in pids:
            pids.append(pid)
    return pids


def stop_core(home: Path, *, require_forge_identity: bool = True) -> bool:
    """Stop the local Forge listener before replacing its runtime files."""
    health = api_health()
    if health is None:
        return True
    if require_forge_identity and health.get("name") != "Forge Core":
        raise RuntimeError(
            "Port 8787 is in use by something that does not identify itself as Forge Core. "
            "Forge will not terminate an unrelated process."
        )
    pids = _listener_pids(8787)
    if not pids:
        raise RuntimeError(
            "Forge Core answered on port 8787, but Windows did not reveal its listener PID. "
            "Close the old Forge Core window and try again."
        )
    log(f"Stopping previous Forge Core before update (PID(s): {', '.join(map(str, pids))})...")
    for pid in pids:
        run(["taskkill", "/PID", str(pid), "/T", "/F"], check=False)
    # The old START_FORGE.cmd parent normally exits as soon as its Python child ends.
    for _ in range(40):
        time.sleep(0.25)
        if api_health() is None and not _listener_pids(8787):
            log("Previous Forge Core stopped; runtime lock released.")
            return True
    raise RuntimeError(
        "Forge Core did not fully stop, so Windows is still protecting the runtime folder. "
        "Close any old Forge Core / START_FORGE command window and run the installer again."
    )


def _copy_runtime_tree(src: Path, dst: Path):
    shutil.copytree(
        src, dst, dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".venv"),
    )


def copy_runtime(home: Path) -> Path:
    runtime_dir = home / "runtime"
    current = runtime_dir / "current"
    backups = home / "backups" / "runtime"
    backups.mkdir(parents=True, exist_ok=True)
    current.parent.mkdir(parents=True, exist_ok=True)

    old = None
    if current.exists():
        # Updating a running service in-place is the Windows lock that caused v0.5.0
        # to fail with WinError 32. Stop Forge first, then preserve a rollback copy.
        stop_core(home)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        old = backups / f"runtime-{stamp}"
        log(f"Preserving previous runtime at {old}")
        _copy_runtime_tree(current, old)

        # Prefer a clean swap, but a shell/File Explorer may still keep the directory
        # itself as a working directory. In that case, safely overlay the new runtime
        # instead of failing solely because Windows refuses to remove the folder node.
        moved = False
        for attempt in range(8):
            try:
                shutil.rmtree(current)
                moved = True
                break
            except PermissionError as e:
                log(f"Runtime folder still busy (attempt {attempt + 1}/8): {e}")
                time.sleep(0.4)
        if not moved:
            log("Windows still holds the runtime directory itself. Using safe in-place update fallback.")
            _copy_runtime_tree(RUNTIME_SOURCE, current)
            if (old / "data").exists():_copy_runtime_tree(old / "data", current / "data")
            return current

    log("Deploying Forge runtime...")
    _copy_runtime_tree(RUNTIME_SOURCE, current)
    if old is not None and (old / "data").exists():
        _copy_runtime_tree(old / "data", current / "data")
    return current


def venv_python(home: Path) -> Path:
    return home / "envs" / "core" / "Scripts" / "python.exe"


def ensure_venv(home: Path, runtime: Path) -> Path:
    py = venv_python(home)
    if not py.exists():
        env_dir = home / "envs" / "core"
        env_dir.parent.mkdir(parents=True, exist_ok=True)
        log("Creating isolated Forge Python environment...")
        run([sys.executable, "-m", "venv", str(env_dir)])
    # Avoid making a pip upgrade a blocker.
    run([str(py), "-m", "pip", "install", "--upgrade", "pip"], check=False)
    run([str(py), "-m", "pip", "install", "-r", str(runtime / "requirements.txt")])
    return py


def api_health() -> dict | None:
    try:
        with urllib.request.urlopen("http://127.0.0.1:8787/api/health", timeout=1.5) as r:
            return json.load(r)
    except Exception:
        return None


def launcher_text(home: Path, url: str) -> str:
    start = home / "START_FORGE.cmd"
    return (
        "@echo off\n"
        "setlocal\n"
        'netstat -ano | findstr /R /C:":8787 .*LISTENING" >nul\n'
        f'if errorlevel 1 start "Forge Core" /min "{start}"\n'
        'timeout /t 2 /nobreak >nul\n'
        f'start "" "{url}"\n'
    )


def _known_windows_folder(csidl: int, fallback: Path) -> Path:
    if os.name == "nt":
        try:
            buf = ctypes.create_unicode_buffer(32768)
            rc = ctypes.windll.shell32.SHGetFolderPathW(None, csidl, None, 0, buf)
            if rc == 0 and buf.value:
                return Path(buf.value)
        except Exception:
            pass
    return fallback


def _ps_literal(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _create_shortcut(link: Path, target: Path, icon: Path, working_dir: Path, description: str):
    if os.name != "nt":
        return
    link.parent.mkdir(parents=True, exist_ok=True)
    script = (
        "$w=New-Object -ComObject WScript.Shell;"
        f"$s=$w.CreateShortcut({_ps_literal(link)});"
        f"$s.TargetPath={_ps_literal(target)};"
        f"$s.WorkingDirectory={_ps_literal(working_dir)};"
        f"$s.IconLocation={_ps_literal(str(icon) + ',0')};"
        f"$s.Description={_ps_literal(description)};"
        "$s.Save()"
    )
    subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def _remove_old_loose_shortcuts(desktop: Path):
    old_names = [
        "Forge Workspace.cmd", "Forge Workspace.lnk",
        "GrimForge Local.cmd", "GrimForge Local.lnk", "GrimForge.cmd", "GrimForge.lnk",
        "Elias Local.cmd", "Elias Local.lnk", "Elias.cmd", "Elias.lnk",
        "Evidence Auditor.cmd", "Evidence Auditor.lnk", "Elias Evidence Auditor.lnk",
        "MedForge Local.cmd", "MedForge Local.lnk", "MedForge.cmd", "MedForge.lnk",
        "Forge Learn.cmd", "Forge Learn.lnk",
        "Forge Setup and Repair.cmd", "Forge Setup and Repair.lnk", "Forge Setup & Repair.lnk",
    ]
    for name in old_names:
        p = desktop / name
        try:
            if p.is_file() or p.is_symlink():
                p.unlink()
                log(f"Removed old loose Desktop shortcut: {name}")
        except Exception as e:
            log(f"WARNING: couldn't remove old Desktop shortcut {name}: {e}")


def write_launchers(home: Path, runtime: Path, py: Path):
    home.mkdir(parents=True, exist_ok=True)
    start = home / "START_FORGE.cmd"
    start.write_text(
        "@echo off\n"
        "setlocal\n"
        f'set "FORGE_HOME={home}"\n'
        f'start "Forge Core" /min /D "{home}" "{py}" -m uvicorn --app-dir "{runtime}" forge_core.main:app --host 127.0.0.1 --port 8787\n'
        "exit /b 0\n",
        encoding="utf-8",
    )

    launchers = {
        "Forge Workspace.cmd": ("http://127.0.0.1:8787/", "forge-workspace.ico", "Forge Workspace — local system control and app hub"),
        "Elias.cmd": ("http://127.0.0.1:8787/static/apps/elias.html", "elias.ico", "Elias — local conversational AI assistant"),
        "Evidence Auditor.cmd": ("http://127.0.0.1:8787/static/apps/evidence.html", "evidence-auditor.ico", "Evidence Auditor — source-linked evidence workspace"),
        "MedForge.cmd": ("http://127.0.0.1:8787/static/apps/medforge.html", "medforge.ico", "MedForge — medical image and mechanism teaching workspace"),
        "GrimForge.cmd": ("http://127.0.0.1:8787/static/apps/grimforge.html", "grimforge.ico", "GrimForge — cinematic story and episode generator"),
        "Forge Learn.cmd": ("http://127.0.0.1:8787/learn", "forge-learn.ico", "Forge Learn — synchronized teaching companion"),
    }

    desktop = _known_windows_folder(0x10, Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop")
    programs = _known_windows_folder(0x02, Path(os.environ.get("APPDATA", str(Path.home()))) / "Microsoft/Windows/Start Menu/Programs")
    desktop.mkdir(parents=True, exist_ok=True)
    _remove_old_loose_shortcuts(desktop)

    desktop_folder = desktop / "Forge Apps"
    start_folder = programs / "Forge Apps"
    desktop_folder.mkdir(parents=True, exist_ok=True)
    start_folder.mkdir(parents=True, exist_ok=True)

    launcher_dir = home / "launchers"
    launcher_dir.mkdir(parents=True, exist_ok=True)
    icon_dir = home / "icons"
    icon_dir.mkdir(parents=True, exist_ok=True)
    packaged_icons = runtime / "assets" / "icons"
    if packaged_icons.exists():
        for src in packaged_icons.glob("*.ico"):
            try:
                shutil.copy2(src, icon_dir / src.name)
            except Exception as e:
                log(f"WARNING: couldn't copy app icon {src.name}: {e}")

    # Remove obsolete known shortcuts inside the Forge folders before rebuilding them.
    for folder in (desktop_folder, start_folder):
        for old in folder.glob("*.lnk"):
            try: old.unlink()
            except Exception: pass

    for filename, (url, icon_name, description) in launchers.items():
        body = launcher_text(home, url)
        target = launcher_dir / filename
        target.write_text(body, encoding="utf-8")
        display = filename.removesuffix(".cmd")
        icon = icon_dir / icon_name
        try:
            _create_shortcut(desktop_folder / f"{display}.lnk", target, icon, home, description)
            _create_shortcut(start_folder / f"{display}.lnk", target, icon, home, description)
        except Exception as e:
            log(f"WARNING: couldn't create Windows shortcut for {display}: {e}")

    control = home / "Forge Setup and Repair.cmd"
    gui = runtime / "installer_gui.py"
    control.write_text(
        "@echo off\n"
        f'"{sys.executable}" "{gui}"\n'
        "if errorlevel 1 pause\n",
        encoding="utf-8",
    )
    setup_icon = icon_dir / "forge-setup.ico"
    try:
        _create_shortcut(desktop_folder / "Forge Setup & Repair.lnk", control, setup_icon, home, "Forge Setup & Repair — install, update, Doctor, models and recovery")
        _create_shortcut(start_folder / "Forge Setup & Repair.lnk", control, setup_icon, home, "Forge Setup & Repair — install, update, Doctor, models and recovery")
    except Exception as e:
        log(f"WARNING: couldn't create Setup & Repair shortcut: {e}")

    try:
        (desktop_folder / "README.txt").write_text(
            "Forge Apps\n==========\n\nOpen any shortcut in this folder. It will start Forge Core automatically if needed.\n"
            "Elias and Evidence Auditor are separate apps. Forge Learn is the teaching companion.\n",
            encoding="utf-8",
        )
    except Exception:
        pass
    log(f"Desktop app folder ready: {desktop_folder}")
    log(f"Start Menu app folder ready: {start_folder}")


def base_install(home: Path):
    set_env(home)
    runtime = copy_runtime(home)
    py = ensure_venv(home, runtime)

    # These are helpers, not prerequisites for the dashboard itself.
    if not shutil.which("git"):
        winget_install("Git.Git", "Git")
    if not shutil.which("ffmpeg"):
        winget_install("Gyan.FFmpeg", "FFmpeg")
    if not shutil.which("ollama"):
        winget_install("Ollama.Ollama", "Ollama")
    refresh_path()

    write_launchers(home, runtime, py)
    data = runtime / "data"
    data.mkdir(parents=True, exist_ok=True)
    if not (data / "settings.json").exists():
        (data / "settings.json").write_text(
            json.dumps({"mode": "LOCAL_ONLY", "cloud_requires_confirmation": True}, indent=2),
            encoding="utf-8",
        )

    log("Running Forge base self-check...")
    run([str(py), "-c", "import fastapi,uvicorn,PIL; print('Forge Python runtime OK')"])
    log("Checking Workspace / Learn synchronization...")
    run([str(py), str(runtime / "forge_base" / "learning_sync.py")], cwd=runtime)
    run([str(py), str(runtime / "forge_base" / "feature_gate.py")], cwd=runtime)
    log("FORGE BASE INSTALLED. Workspace and Learn manifest are synchronized.")
    return runtime, py


def start_core(home: Path) -> bool:
    if api_health():
        log("Forge Core is already running.")
        return True
    runtime = home / "runtime" / "current"
    py = venv_python(home)
    if not py.exists() or not runtime.exists():
        raise RuntimeError("Forge is not installed yet.")
    set_env(home)
    flags = 0
    if os.name == "nt":
        flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "CREATE_NO_WINDOW", 0)
    subprocess.Popen(
        [str(py), "-m", "uvicorn", "--app-dir", str(runtime), "forge_core.main:app", "--host", "127.0.0.1", "--port", "8787"],
        cwd=str(home), env=os.environ.copy(), creationflags=flags,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(30):
        time.sleep(0.35)
        if api_health():
            log("Forge Core started successfully.")
            return True
    raise RuntimeError("Forge Core did not answer on port 8787 after installation.")


def install_local_ai(home: Path):
    runtime = home / "runtime" / "current"
    py = venv_python(home)
    if not py.exists():
        raise RuntimeError("Install Forge + Local Apps first.")
    set_env(home)
    log("Installing optional local AI components...")
    req = runtime / "requirements-local-ai.txt"
    if req.exists():
        run([str(py), "-m", "pip", "install", "-r", str(req)], check=False)
    run([str(py), "-m", "pip", "install", "pyttsx3", "pywin32"], check=False)
    refresh_path()
    ollama = shutil.which("ollama")
    if not ollama:
        winget_install("Ollama.Ollama", "Ollama")
        refresh_path()
        ollama = shutil.which("ollama")
    if ollama:
        # 3B defaults are appropriate for AJ's 16 GB EliteBook.
        for model in ["qwen2.5:3b", "qwen2.5-coder:3b", "nomic-embed-text", "qwen2.5vl:3b"]:
            log(f"Downloading local model: {model}")
            run([ollama, "pull", model], check=False)
    else:
        log("WARNING: Ollama unavailable. Forge remains usable with deterministic fallbacks.")
    log("OPTIONAL LOCAL AI SETUP COMPLETE.")


def quick_backup(home: Path) -> Path:
    if not home.exists():
        raise RuntimeError("Forge Home does not exist yet.")
    outdir = home / "backups"
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"Forge-Quick-Backup-{time.strftime('%Y%m%d-%H%M%S')}.zip"
    log(f"Creating backup: {out}")
    roots = ["projects", "vault", "exports", "runtime/current"]
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as z:
        for rel in roots:
            p = home / rel
            if not p.exists():
                continue
            if p.is_file():
                z.write(p, rel)
            else:
                for f in p.rglob("*"):
                    if f.is_file() and "__pycache__" not in f.parts:
                        z.write(f, f.relative_to(home))
    log("Backup complete.")
    return out


def request_admin_command(command: str):
    params = f'/c {command} & echo. & echo You may close this window when finished. & pause'
    rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", params, None, 1)
    if rc <= 32:
        raise RuntimeError("Windows did not start the Administrator task.")


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"Forge Easy Setup {VERSION}")
        try:
            setup_icon = RUNTIME_SOURCE / "assets" / "icons" / "forge-setup.ico"
            if setup_icon.exists(): self.root.iconbitmap(default=str(setup_icon))
        except Exception:
            pass
        self.root.geometry("980x760")
        self.root.minsize(800, 600)
        self.busy = False
        self.home_var = tk.StringVar(value=str(default_home()))
        self.media3d_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="Ready to install")
        self._style()
        self._build()
        self.poll_logs()
        self.refresh_status()

    def _style(self):
        self.root.configure(bg="#0b1422")
        s = ttk.Style()
        try:
            s.theme_use("clam")
        except Exception:
            pass
        s.configure("TFrame", background="#0b1422")
        s.configure("Card.TFrame", background="#142238")
        s.configure("TLabel", background="#0b1422", foreground="#e8f0f8", font=("Segoe UI", 10))
        s.configure("Card.TLabel", background="#142238", foreground="#e8f0f8", font=("Segoe UI", 10))
        s.configure("Title.TLabel", background="#0b1422", foreground="#e8f0f8", font=("Segoe UI Semibold", 22))
        s.configure("Sub.TLabel", background="#0b1422", foreground="#9fb0c4", font=("Segoe UI", 10))
        s.configure("Primary.TButton", font=("Segoe UI Semibold", 12), padding=15)
        s.configure("App.TButton", font=("Segoe UI Semibold", 10), padding=10)
        s.configure("TButton", font=("Segoe UI", 10), padding=8)
        s.configure("Horizontal.TProgressbar", troughcolor="#1b2d46", background="#55d7e8")

    def _build(self):
        outer = ttk.Frame(self.root, padding=22)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="Forge Suite Setup & Repair", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            outer,
            text="Install the shared Core once, then launch six distinct Forge products from one clean Forge Apps folder.",
            style="Sub.TLabel",
        ).pack(anchor="w", pady=(2, 16))

        card = ttk.Frame(outer, style="Card.TFrame", padding=16)
        card.pack(fill="x")
        ttk.Label(card, text="Forge location", style="Card.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Entry(card, textvariable=self.home_var).grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(5, 10))
        ttk.Button(card, text="Browse", command=self.browse).grid(row=1, column=1, pady=(5, 10))
        card.columnconfigure(0, weight=1)

        self.install_btn = ttk.Button(
            card,
            text="INSTALL FORGE + LOCAL APPS",
            style="Primary.TButton",
            command=lambda: self.task("Install Forge + Local Apps", self.install_everything),
        )
        self.install_btn.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 8))
        ttk.Checkbutton(card, text="Install shared Media / 3D Tools (Blender + FFmpeg) — recommended for MedForge & GrimForge", variable=self.media3d_var).grid(row=3, column=0, columnspan=2, sticky="w", pady=(2,6))
        ttk.Label(
            card,
            text="Installs the local runtime, starts Forge, creates a clean Forge Apps Desktop folder containing Workspace, Elias, Evidence Auditor, MedForge, GrimForge, Forge Learn, and Setup & Repair, then opens Forge Workspace. Blender is shared by MedForge and GrimForge rather than duplicated per app.",
            style="Card.TLabel",
            wraplength=760,
        ).grid(row=4, column=0, columnspan=2, sticky="w")

        ttk.Label(outer, text="Your local apps", style="Sub.TLabel").pack(anchor="w", pady=(16, 5))
        apps = ttk.Frame(outer)
        apps.pack(fill="x")
        app_buttons = [
            ("Forge Workspace", "home"), ("Open Elias", "elias"), ("Evidence Auditor", "evidence"),
            ("Open MedForge", "medforge"), ("Open GrimForge", "grimforge"), ("Open Forge Learn", "learn"),
        ]
        for i, (label, key) in enumerate(app_buttons):
            ttk.Button(apps, text=label, style="App.TButton", command=lambda k=key: self.open_app(k)).grid(
                row=i // 3, column=i % 3, sticky="ew", padx=4, pady=4
            )
        for col in range(3):
            apps.columnconfigure(col, weight=1)

        status = ttk.Frame(outer, style="Card.TFrame", padding=12)
        status.pack(fill="x", pady=(14, 10))
        ttk.Label(status, textvariable=self.status_var, style="Card.TLabel").pack(side="left")
        self.progress = ttk.Progressbar(status, mode="indeterminate", length=180)
        self.progress.pack(side="right")

        adv = ttk.LabelFrame(outer, text="Optional / Advanced", padding=10)
        adv.pack(fill="x", pady=(0, 10))
        advanced_actions = [
            ("Start Core", lambda: self.task("Start Forge Core", self.start_core_ui)),
            ("Stop Core", lambda: self.task("Stop Forge Core", self.stop_core_ui)),
            ("Install / update models", lambda: self.task("Install local AI models", self.local_ai)),
            ("Install Media / 3D Tools", lambda: self.task("Install Media / 3D Tools", self.media3d)),
            ("Run Doctor", lambda: self.task("Forge Doctor", self.doctor)),
            ("Backup", lambda: self.task("Backup", self.backup)),
            ("Install WSL2", lambda: self.task("WSL2 Setup", self.install_wsl)),
        ]
        for i, (label, command) in enumerate(advanced_actions):
            ttk.Button(adv, text=label, command=command).grid(row=i // 3, column=i % 3, sticky="ew", padx=4, pady=4)
        for col in range(3):
            adv.columnconfigure(col, weight=1)

        ttk.Label(outer, text="Installer log", style="Sub.TLabel").pack(anchor="w")
        self.logbox = tk.Text(
            outer, height=15, bg="#09111d", fg="#d9e7f2", insertbackground="white",
            relief="flat", font=("Consolas", 9), wrap="word",
        )
        self.logbox.pack(fill="both", expand=True, pady=(4, 0))
        log("Forge Setup GUI started successfully.")
        log(f"Python: {sys.executable}")

    def browse(self):
        p = filedialog.askdirectory(initialdir=self.home_var.get() or str(Path.home()))
        if p:
            self.home_var.set(p)

    def home(self) -> Path:
        return Path(self.home_var.get().strip())

    def task(self, name, fn):
        if self.busy:
            messagebox.showinfo("Forge", "Another Forge task is already running.")
            return
        self.busy = True
        self.status_var.set(name + "…")
        self.progress.start(10)

        def worker():
            try:
                log(f"\n=== {name} ===")
                fn()
                log(f"=== {name}: COMPLETE ===")
                self.root.after(0, lambda: self.status_var.set(name + " complete"))
            except Exception as e:
                log(f"ERROR: {e}")
                log(traceback.format_exc())
                self.root.after(0, lambda: messagebox.showerror(
                    "Forge Setup",
                    f"{name} did not finish.\n\n{e}\n\nPlease send a screenshot of this window or the installer log.",
                ))
                self.root.after(0, lambda: self.status_var.set(name + " failed — see log"))
            finally:
                self.root.after(0, self.done)

        threading.Thread(target=worker, daemon=True).start()

    def done(self):
        self.busy = False
        self.progress.stop()
        self.refresh_status()

    def install_everything(self):
        home = self.home()
        log(f"Forge Home: {home}")
        runtime, py = base_install(home)
        if self.media3d_var.get():
            install_media_3d_tools(home)
        log(f"Runtime deployed: {runtime}")
        log(f"Forge Python: {py}")
        start_core(home)
        log("Desktop\\Forge Apps folder created with unique shortcuts for Workspace, Elias, Evidence Auditor, MedForge, GrimForge, Forge Learn, and Setup & Repair.")
        log("INSTALLATION COMPLETE. Opening Forge Workspace...")
        webbrowser.open("http://127.0.0.1:8787/")
        self.root.after(0, lambda: messagebox.showinfo(
            "Forge is ready",
            "Forge is installed and running.\n\nYour Desktop now has one Forge Apps folder containing uniquely identified shortcuts for Workspace, Elias, Evidence Auditor, MedForge, GrimForge, Forge Learn, and Setup & Repair.\n\nForge Workspace is opening in your browser now.",
        ))

    def start_core_ui(self):
        start_core(self.home())

    def stop_core_ui(self):
        home = self.home()
        if api_health() is None:
            log("Forge Core is already stopped.")
            return
        stop_core(home)
        log("Forge Core stopped. Open any Forge app or click Start Core to start it again.")

    def local_ai(self):
        install_local_ai(self.home())

    def media3d(self):
        install_media_3d_tools(self.home())

    def ensure_running(self):
        if not api_health():
            start_core(self.home())

    def open_app(self, name: str):
        urls = {
            "home": "http://127.0.0.1:8787/",
            "grimforge": "http://127.0.0.1:8787/static/apps/grimforge.html",
            "elias": "http://127.0.0.1:8787/static/apps/elias.html",
            "evidence": "http://127.0.0.1:8787/static/apps/evidence.html",
            "medforge": "http://127.0.0.1:8787/static/apps/medforge.html",
            "learn": "http://127.0.0.1:8787/learn",
        }
        if name not in urls:
            return
        if not venv_python(self.home()).exists():
            messagebox.showinfo("Forge", "Install Forge + Local Apps first.")
            return
        try:
            self.ensure_running()
            webbrowser.open(urls[name])
        except Exception as e:
            messagebox.showerror("Forge", str(e))

    def doctor(self):
        home = self.home()
        runtime = home / "runtime" / "current"
        py = venv_python(home)
        if not py.exists():
            raise RuntimeError("Forge is not installed yet.")
        run([str(py), str(runtime / "forge_base" / "forge_base.py"), "doctor", "--home", str(home)], cwd=runtime, check=False)

    def backup(self):
        out = quick_backup(self.home())
        self.root.after(0, lambda: messagebox.showinfo("Forge Backup", f"Backup created:\n{out}"))

    def install_wsl(self):
        request_admin_command("wsl --install --no-distribution")
        log("WSL setup opened in an Administrator window. A reboot may be required.")

    def poll_logs(self):
        try:
            while True:
                m = LOGQ.get_nowait()
                self.logbox.insert("end", m + "\n")
                self.logbox.see("end")
                try:
                    h = self.home()
                    (h / "logs").mkdir(parents=True, exist_ok=True)
                    with open(h / "logs" / "easy-installer.log", "a", encoding="utf-8") as f:
                        f.write(m + "\n")
                except Exception:
                    pass
        except queue.Empty:
            pass
        self.root.after(150, self.poll_logs)

    def refresh_status(self):
        h = self.home()
        py = venv_python(h)
        health = api_health()
        if py.exists() and health:
            self.status_var.set("Forge installed • Core running • Local apps ready")
        elif py.exists():
            self.status_var.set("Forge installed • Core stopped — open any app to start it")
        else:
            self.status_var.set("Not installed yet — click INSTALL FORGE + LOCAL APPS")


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
