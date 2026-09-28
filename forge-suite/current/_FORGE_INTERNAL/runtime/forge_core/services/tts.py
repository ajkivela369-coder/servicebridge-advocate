from __future__ import annotations
from pathlib import Path
import os, shutil, subprocess, tempfile

PRONUNCIATIONS = {
    "DICOM":"die-com", "PACS":"packs", "HL7":"H L seven", "Ambra":"am-bruh",
    "Qwen":"kwen", "Ollama":"oh-lah-ma", "Kokoro":"ko-ko-ro"
}

def apply_pronunciations(text:str) -> str:
    for a,b in PRONUNCIATIONS.items(): text=text.replace(a,b)
    return text

def _kokoro(text: str, out_path: Path, voice='bf_emma') -> bool:
    try:
        import numpy as np, soundfile as sf
        from kokoro import KPipeline
        pipeline=KPipeline(lang_code="b" if voice.startswith("b") else "a"); chunks=[]
        for _gs,_ps,audio in pipeline(text,voice=voice,speed=1.0): chunks.append(np.asarray(audio))
        if not chunks:return False
        sf.write(str(out_path),np.concatenate(chunks),24000); return out_path.exists() and out_path.stat().st_size>0
    except Exception:return False

def _espeak(text: str, out_path: Path) -> bool:
    exe=shutil.which("espeak-ng") or shutil.which("espeak")
    if not exe:return False
    p=subprocess.run([exe,"-s","155","-w",str(out_path),text],capture_output=True,text=True)
    return p.returncode==0 and out_path.exists() and out_path.stat().st_size>0

def _pyttsx3(text:str,out_path:Path)->bool:
    if os.name!="nt": return False
    try:
        import pyttsx3
        engine=pyttsx3.init()
        engine.setProperty("rate",155)
        engine.save_to_file(text,str(out_path))
        engine.runAndWait()
        engine.stop()
        return out_path.exists() and out_path.stat().st_size>0
    except Exception:
        return False

def _sapi(text:str,out_path:Path)->bool:
    if os.name!="nt":return False
    ps=shutil.which("powershell") or shutil.which("pwsh")
    if not ps:return False
    escaped=text.replace("'","''"); path=str(out_path).replace("'","''")
    script=f"Add-Type -AssemblyName System.Speech; $s=New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.SetOutputToWaveFile('{path}'); $s.Speak('{escaped}'); $s.Dispose()"
    p=subprocess.run([ps,"-NoProfile","-Command",script],capture_output=True,text=True)
    return p.returncode==0 and out_path.exists() and out_path.stat().st_size>0

def synthesize(text: str, out_path: Path, voice: str = "bf_emma", allow_basic_fallback: bool = False) -> str:
    out_path.parent.mkdir(parents=True,exist_ok=True); text=apply_pronunciations(text)
    if voice not in {"bf_emma","bm_george","af_heart"}:raise ValueError("Unsupported local voice")
    if _kokoro(text,out_path,voice):return "kokoro:"+voice
    if allow_basic_fallback:
        if _espeak(text,out_path):return "BASIC FALLBACK:espeak"
        if _pyttsx3(text,out_path):return "BASIC FALLBACK:windows-pyttsx3"
        if _sapi(text,out_path):return "BASIC FALLBACK:windows-sapi"
    raise RuntimeError("Selected Kokoro voice is unavailable. Install/warm Kokoro in Setup & Repair. Basic system speech is disabled unless explicitly selected as a fallback.")
