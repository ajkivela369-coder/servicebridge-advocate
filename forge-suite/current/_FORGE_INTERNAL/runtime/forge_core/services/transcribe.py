from __future__ import annotations
import json, os, shutil, subprocess, tempfile
from pathlib import Path


def _forge_home(): return Path(os.environ.get("FORGE_HOME") or (Path.home()/"Forge"))

def transcribe(path: Path, quality="small.en") -> dict:
    path=Path(path)
    ffmpeg=shutil.which("ffmpeg")
    whisper=shutil.which("whisper-cli") or shutil.which("whisper")
    model=_forge_home()/"models"/"whisper"/f"ggml-{quality}.bin"
    if whisper and model.exists() and ffmpeg:
        with tempfile.TemporaryDirectory(prefix="forge-whisper-") as td:
            wav=Path(td)/"input.wav"; out=Path(td)/"transcript"
            subprocess.run([ffmpeg,"-y","-loglevel","error","-i",str(path),"-ar","16000","-ac","1","-c:a","pcm_s16le",str(wav)],check=True)
            cmd=[whisper,"-m",str(model),"-f",str(wav),"-otxt","-of",str(out)]
            p=subprocess.run(cmd,capture_output=True,text=True)
            txt=out.with_suffix(".txt")
            if p.returncode==0 and txt.exists(): return {"engine":f"whisper.cpp:{quality}","text":txt.read_text(errors="replace")}
    try:
        from faster_whisper import WhisperModel
        mdl=WhisperModel("base.en", device="cpu", compute_type="int8")
        segs,_=mdl.transcribe(str(path)); return {"engine":"faster-whisper:base.en","text":" ".join(s.text.strip() for s in segs)}
    except Exception as e:
        raise RuntimeError("No local transcription route is ready. Stage whisper.cpp + a model, or install faster-whisper.") from e
