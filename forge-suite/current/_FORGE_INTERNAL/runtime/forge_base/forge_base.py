from __future__ import annotations
import argparse, hashlib, json, os, platform, shutil, subprocess, sys, socket
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
REGISTRY=json.loads((HERE/"tool_registry.json").read_text())

def forge_home()->Path:return Path(os.environ.get("FORGE_HOME") or (Path.home()/"Forge")).expanduser().resolve()

def dirs(root:Path):
    names=["bin","downloads/installers","downloads/wheelhouse","downloads/npm-cache","downloads/npm-packages","downloads/containers","downloads/sources","models/ollama","models/whisper","models/huggingface","models/tts","tools/12ui","templates/design","cache/uv","cache/pip","envs","projects","exports","logs","manifests","backups","tmp"]
    return [root/n for n in names]

def init(root:Path):
    for p in dirs(root):p.mkdir(parents=True,exist_ok=True)
    env=root/"forge-env.ps1"
    env.write_text(
        "$env:FORGE_HOME = '"+str(root).replace("'","''")+"'\n"
        "$env:HF_HOME = Join-Path $env:FORGE_HOME 'models\\huggingface'\n"
        "$env:OLLAMA_MODELS = Join-Path $env:FORGE_HOME 'models\\ollama'\n"
        "$env:UV_CACHE_DIR = Join-Path $env:FORGE_HOME 'cache\\uv'\n"
        "$env:PIP_CACHE_DIR = Join-Path $env:FORGE_HOME 'cache\\pip'\n"
        "$env:npm_config_cache = Join-Path $env:FORGE_HOME 'downloads\\npm-cache'\n"
        "$env:PATH = (Join-Path $env:FORGE_HOME 'bin') + ';' + $env:PATH\n",encoding="utf-8")
    return env

def which_any(names):
    for n in names:
        p=shutil.which(n)
        if p:return p
    return None

def first_line(cmd,timeout=3):
    try:
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout); t=(r.stdout or r.stderr).strip().splitlines(); return t[0][:240] if t else None
    except Exception:return None

def tool_status(root:Path):
    out=[]; portable=str(root/"bin"); old=os.environ.get("PATH","")
    if portable not in old.split(os.pathsep):os.environ["PATH"]=portable+os.pathsep+old
    for t in REGISTRY["tools"]:
        path=which_any(t["commands"]); command=Path(path).name if path else None
        version=first_line([path,"--version"]) if path and command not in {"wsl.exe"} else None
        if path and command=="wsl.exe":version=first_line([path,"--status"])
        out.append({**t,"installed":bool(path),"path":path,"version":version})
    return out

def disk(root:Path):
    anchor=root if root.exists() else root.parent; anchor.mkdir(parents=True,exist_ok=True); usage=shutil.disk_usage(anchor); gb=1024**3
    return {"total_gb":round(usage.total/gb,1),"free_gb":round(usage.free/gb,1)}

def ram():
    try:
        if os.name=="nt":
            r=subprocess.run(["powershell","-NoProfile","-Command","[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB,1)"],capture_output=True,text=True,timeout=4); return float(r.stdout.strip())
        return round(os.sysconf("SC_PHYS_PAGES")*os.sysconf("SC_PAGE_SIZE")/1024**3,1)
    except Exception:return None

def network_probe():
    hosts=["registry.npmjs.org","pypi.org","huggingface.co","github.com"]
    rows=[]
    for host in hosts:
        try:
            ip=socket.gethostbyname(host); rows.append({"host":host,"dns":True,"ip":ip})
        except Exception as e:
            rows.append({"host":host,"dns":False,"error":str(e)[:180]})
    return {"online_dns_ready":any(r["dns"] for r in rows),"targets":rows}

def gpu():
    n=shutil.which("nvidia-smi")
    if not n:return {"nvidia":False}
    try:
        r=subprocess.run([n,"--query-gpu=name,memory.total,driver_version","--format=csv,noheader"],capture_output=True,text=True,timeout=4); rows=[x.strip() for x in r.stdout.splitlines() if x.strip()]; return {"nvidia":bool(rows),"devices":rows}
    except Exception:return {"nvidia":True,"devices":[]}

def _route_state(t,tools_by_id):
    if t["installed"]:return "Ready"
    # Portable and alternate host routes can be prepared even if not installed yet.
    if t.get("fallbacks"):return "Primary unavailable; fallback available"
    return "Missing and blocking"

def report(root:Path):
    env=init(root); tools=tool_status(root); by={t["id"]:t for t in tools}; missing=[t["id"] for t in tools if not t["installed"]]
    routes={}
    for t in tools:
        routes[t["capability"]]={"status":_route_state(t,by),"ready":t["installed"],"primary":t["id"],"fallbacks":t["fallbacks"],"offline_strategy":t["offline_strategy"]}
    d=disk(root); storage_state="Ready" if d["free_gb"]>=50 else ("Missing but recoverable" if d["free_gb"]>=20 else "Missing and blocking")
    data={"timestamp":datetime.now(timezone.utc).isoformat(),"forge_home":str(root),"env_script":str(env),"platform":{"system":platform.system(),"release":platform.release(),"machine":platform.machine(),"python":sys.version.split()[0],"ram_gb":ram()},"disk":d,"storage_status":storage_state,"gpu":gpu(),"network":network_probe(),"tools":tools,"missing":missing,"capability_routes":routes,"policy":{"default":"LOCAL_ONLY","cloud":"explicit approval only","completion_rule":"feature requires a tested local route, fallback route, and restorable offline route","do_not_bypass":["security controls","licenses","authentication","service limits"]}}
    out=root/"manifests"/"doctor-latest.json"; out.write_text(json.dumps(data,indent=2),encoding="utf-8"); return data

def sha256(path:Path):
    h=hashlib.sha256();
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def inventory(root:Path):
    records=[]
    for base in [root/"bin",root/"downloads",root/"models",root/"manifests"]:
        if not base.exists():continue
        for p in base.rglob("*"):
            if p.is_file():
                try:records.append({"path":str(p.relative_to(root)),"size":p.stat().st_size,"sha256":sha256(p)})
                except OSError:pass
    payload={"timestamp":datetime.now(timezone.utc).isoformat(),"files":records}; out=root/"manifests"/"offline-inventory.json"; out.write_text(json.dumps(payload,indent=2),encoding="utf-8"); return payload

def main():
    ap=argparse.ArgumentParser(description="Forge Base local resilience manager"); ap.add_argument("command",choices=["init","doctor","inventory","paths"]); ap.add_argument("--home",default=None); args=ap.parse_args(); root=Path(args.home).expanduser().resolve() if args.home else forge_home()
    if args.command=="init":print(json.dumps({"ok":True,"forge_home":str(root),"env_script":str(init(root))},indent=2))
    elif args.command=="doctor":print(json.dumps(report(root),indent=2))
    elif args.command=="inventory":print(json.dumps(inventory(root),indent=2))
    else:init(root); print("\n".join(str(x) for x in dirs(root)))
if __name__=="__main__":main()
