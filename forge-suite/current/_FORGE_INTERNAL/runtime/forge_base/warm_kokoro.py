from pathlib import Path
import os, tempfile
os.environ.setdefault("HF_HOME", str(Path(os.environ.get("FORGE_HOME") or (Path.home()/"Forge"))/"models"/"huggingface"))
try:
    import numpy as np, soundfile as sf
    from kokoro import KPipeline
    p=KPipeline(lang_code="b"); chunks=[]
    for _,_,audio in p("Forge Core local voice self test.", voice="bf_emma"):chunks.append(np.asarray(audio))
    if not chunks:raise RuntimeError("Kokoro returned no audio")
    out=Path(os.environ.get("FORGE_HOME") or (Path.home()/"Forge"))/"manifests"/"kokoro-selftest.wav";out.parent.mkdir(parents=True,exist_ok=True);sf.write(out,np.concatenate(chunks),24000)
    print(f"Kokoro ready: {out}")
except Exception as e:
    raise SystemExit(f"Kokoro warm-up failed: {e}")
