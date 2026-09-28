from __future__ import annotations
import importlib.util, json, os, platform, shutil, subprocess, urllib.request
from pathlib import Path


def _which(name: str): return shutil.which(name)

def _version(cmd: list[str]) -> str | None:
    try:
        out=subprocess.run(cmd,capture_output=True,text=True,timeout=2)
        text=(out.stdout or out.stderr).strip().splitlines()
        return text[0][:180] if text else None
    except Exception: return None

def _ollama_status():
    path=_which("ollama"); running=False; models=[]
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags",timeout=.6) as r:
            payload=json.load(r); running=True; models=[m.get("name") for m in payload.get("models",[]) if m.get("name")]
    except Exception: pass
    return {"installed":bool(path),"path":path,"running":running,"models":models,"version":_version([path,"--version"]) if path else None}

def _ram_gb():
    try:
        if os.name=="nt":
            p=subprocess.run(["powershell","-NoProfile","-Command","[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB,1)"],capture_output=True,text=True,timeout=3)
            return float(p.stdout.strip())
        pages=os.sysconf("SC_PHYS_PAGES"); page=os.sysconf("SC_PAGE_SIZE"); return round(pages*page/1024**3,1)
    except Exception: return None

def capabilities():
    ffmpeg=_which("ffmpeg"); ffprobe=_which("ffprobe"); espeak=_which("espeak-ng") or _which("espeak")
    whisper=_which("whisper-cli") or _which("whisper")
    llama_server=_which("llama-server") or _which("llama-server.exe")
    manim=_which("manim"); mmdc=_which("mmdc"); powershell=_which("powershell") or _which("pwsh")
    kokoro_py=importlib.util.find_spec("kokoro") is not None; pillow=importlib.util.find_spec("PIL") is not None
    faster=importlib.util.find_spec("faster_whisper") is not None
    forge=Path(os.environ.get("FORGE_HOME") or (Path.home()/"Forge")); wmodels=forge/"models"/"whisper"
    whisper_models={p.name:str(p) for p in wmodels.glob("ggml-*.bin")} if wmodels.exists() else {}
    return {
        "platform":{"system":platform.system(),"machine":platform.machine(),"ram_gb":_ram_gb()},
        "video":{"ready":bool(ffmpeg and ffprobe),"ffmpeg":ffmpeg,"ffprobe":ffprobe,"version":_version([ffmpeg,"-version"]) if ffmpeg else None},
        "voice":{"ready":bool(kokoro_py or espeak or (os.name=="nt" and powershell)),"preferred":"kokoro" if kokoro_py else ("espeak" if espeak else ("windows-sapi" if os.name=="nt" and powershell else None)),"kokoro_python":kokoro_py,"espeak":espeak,"windows_sapi":bool(os.name=="nt" and powershell)},
        "llm":_ollama_status(),
        "llama_cpp":{"installed":bool(llama_server),"path":llama_server,"version":_version([llama_server,"--version"]) if llama_server else None},
        "transcription":{"ready":bool(whisper or faster),"path":whisper,"faster_whisper":faster,"models":whisper_models},
        "diagram":{"mermaid_cli":mmdc,"manim":manim,"pillow":pillow,"ready":bool(pillow or mmdc or manim)},
        "containers":{"podman":_which("podman"),"docker":_which("docker")},
        "linux_escape":{"wsl":_which("wsl.exe")},
        "local_only_capable":bool(ffmpeg and ffprobe and pillow and (kokoro_py or espeak or (os.name=="nt" and powershell)))
    }
