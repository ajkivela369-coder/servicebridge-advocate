from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, sys, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REG = json.loads((HERE / "model_registry.json").read_text(encoding="utf-8"))


def forge_home() -> Path:
    return Path(os.environ.get("FORGE_HOME") or (Path.home() / "Forge")).expanduser().resolve()


def ollama_tags() -> set[str]:
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=1.2) as r:
            data = json.load(r)
        return {m.get("name", "") for m in data.get("models", [])}
    except Exception:
        return set()


def model_status(root: Path) -> dict:
    installed = ollama_tags()
    ollama = []
    for m in REG["ollama_models"]:
        name = m["name"]
        present = name in installed or (name.endswith(":7b-instruct") and name.replace(":7b-instruct", ":7b") in installed)
        ollama.append({**m, "present": present})
    whisper_dir = root / "models" / "whisper"
    whisper = []
    for m in REG["whisper_models"]:
        p = whisper_dir / m["filename"]
        whisper.append({**m, "path": str(p), "present": p.exists(), "size": p.stat().st_size if p.exists() else 0})
    try:
        import importlib.util
        kokoro_present = importlib.util.find_spec("kokoro") is not None
    except Exception:
        kokoro_present = False
    return {"forge_home": str(root), "ollama": ollama, "whisper": whisper, "kokoro_package": kokoro_present}


def _sha1(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download_whisper(root: Path, names: list[str], force=False) -> list[dict]:
    target = root / "models" / "whisper"
    target.mkdir(parents=True, exist_ok=True)
    wanted = [m for m in REG["whisper_models"] if m["id"] in names or "all" in names]
    results = []
    for m in wanted:
        dest = target / m["filename"]
        if dest.exists() and not force and _sha1(dest) == m["sha1"]:
            results.append({"model": m["id"], "status": "cached", "path": str(dest)})
            continue
        tmp = dest.with_suffix(dest.suffix + ".part")
        if tmp.exists(): tmp.unlink()
        print(f"Downloading Whisper {m['id']} -> {dest}", flush=True)
        urllib.request.urlretrieve(m["url"], tmp)
        got = _sha1(tmp)
        if got != m["sha1"]:
            tmp.unlink(missing_ok=True)
            raise RuntimeError(f"SHA1 mismatch for {m['id']}: expected {m['sha1']} got {got}")
        tmp.replace(dest)
        results.append({"model": m["id"], "status": "downloaded", "path": str(dest)})
    return results


def pull_ollama(include_vision=False, include_low_memory=False) -> list[dict]:
    exe = shutil.which("ollama")
    if not exe:
        raise RuntimeError("Ollama is not installed or is not on PATH.")
    selected = [m for m in REG["ollama_models"] if m.get("required")]
    if include_vision:
        selected += [m for m in REG["ollama_models"] if m["id"] == "vision-7b"]
    if include_low_memory:
        selected += [m for m in REG["ollama_models"] if m["id"] == "general-low-memory"]
    out = []
    seen = set()
    for m in selected:
        if m["name"] in seen: continue
        seen.add(m["name"])
        print(f"Pulling {m['name']} ...", flush=True)
        p = subprocess.run([exe, "pull", m["name"]])
        out.append({"model": m["name"], "ok": p.returncode == 0})
        if p.returncode:
            raise RuntimeError(f"ollama pull failed for {m['name']}")
    return out


def main():
    ap = argparse.ArgumentParser(description="Forge model/cache manager")
    sp = ap.add_subparsers(dest="command", required=True)
    sp.add_parser("status")
    p = sp.add_parser("whisper"); p.add_argument("models", nargs="*", default=["base.en", "small.en"]); p.add_argument("--force", action="store_true")
    p = sp.add_parser("ollama"); p.add_argument("--vision", action="store_true"); p.add_argument("--low-memory", action="store_true")
    args = ap.parse_args()
    root = forge_home(); (root / "models").mkdir(parents=True, exist_ok=True)
    if args.command == "status": result = model_status(root)
    elif args.command == "whisper": result = download_whisper(root, args.models, args.force)
    else: result = pull_ollama(args.vision, args.low_memory)
    print(json.dumps(result, indent=2))

if __name__ == "__main__": main()
