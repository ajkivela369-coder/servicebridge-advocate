from __future__ import annotations
import base64, json, mimetypes, urllib.request
from pathlib import Path


def analyze_image(path: Path, prompt: str, model="qwen2.5vl:7b") -> dict:
    path=Path(path)
    if not path.exists(): raise FileNotFoundError(path)
    b64=base64.b64encode(path.read_bytes()).decode("ascii")
    payload={"model":model,"messages":[{"role":"user","content":prompt,"images":[b64]}],"stream":False}
    try:
        req=urllib.request.Request("http://127.0.0.1:11434/api/chat",data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
        with urllib.request.urlopen(req, timeout=180) as r: data=json.load(r)
        return {"engine":f"ollama:{model}","text":data.get("message",{}).get("content","")}
    except Exception as e:
        return {"engine":"metadata-only-local","text":f"Local vision model unavailable. File: {path.name}; MIME: {mimetypes.guess_type(path.name)[0]}; bytes: {path.stat().st_size}","warning":str(e)}
