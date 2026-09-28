from __future__ import annotations
import argparse, hashlib, json, os, shutil, tempfile, zipfile
from datetime import datetime, timezone
from pathlib import Path


def home():return Path(os.environ.get("FORGE_HOME") or (Path.home()/"Forge")).expanduser().resolve()
def sha256(p:Path):
    h=hashlib.sha256();
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
    return h.hexdigest()

def create(out:Path,include_models=False):
    root=home(); include=["bin","downloads","manifests","projects","vault","templates"]+(["models"] if include_models else [])
    files=[]
    for rel in include:
        base=root/rel
        if base.exists():files.extend([p for p in base.rglob("*") if p.is_file()])
    manifest={"schema":1,"created_at":datetime.now(timezone.utc).isoformat(),"forge_home":str(root),"include_models":include_models,"files":[]}
    out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED,allowZip64=True) as z:
        for p in files:
            rel=p.relative_to(root).as_posix(); manifest["files"].append({"path":rel,"size":p.stat().st_size,"sha256":sha256(p)}); z.write(p,rel)
        z.writestr("FORGE_BUNDLE_MANIFEST.json",json.dumps(manifest,indent=2))
    return {"bundle":str(out),"files":len(files),"bytes":out.stat().st_size,"models_included":include_models}
def verify(bundle:Path):
    bad=[]
    with zipfile.ZipFile(bundle) as z:
        m=json.loads(z.read("FORGE_BUNDLE_MANIFEST.json"));
        for f in m["files"]:
            h=hashlib.sha256(z.read(f["path"])).hexdigest()
            if h!=f["sha256"]:bad.append(f["path"])
    return {"ok":not bad,"bad":bad,"files":len(m["files"])}
def restore(bundle:Path,target:Path,overwrite=False):
    target.mkdir(parents=True,exist_ok=True); v=verify(bundle)
    if not v["ok"]:raise RuntimeError(f"Bundle verification failed: {v['bad'][:5]}")
    restored=0; skipped=0
    with zipfile.ZipFile(bundle) as z:
        m=json.loads(z.read("FORGE_BUNDLE_MANIFEST.json"))
        for f in m["files"]:
            dest=target/f["path"]
            if dest.exists() and not overwrite:skipped+=1;continue
            dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(z.read(f["path"]));restored+=1
    return {"ok":True,"target":str(target),"restored":restored,"skipped":skipped}
def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest="cmd",required=True)
    p=sp.add_parser("create");p.add_argument("output");p.add_argument("--include-models",action="store_true")
    p=sp.add_parser("verify");p.add_argument("bundle")
    p=sp.add_parser("restore");p.add_argument("bundle");p.add_argument("--target",default=None);p.add_argument("--overwrite",action="store_true")
    a=ap.parse_args()
    if a.cmd=="create":r=create(Path(a.output),a.include_models)
    elif a.cmd=="verify":r=verify(Path(a.bundle))
    else:r=restore(Path(a.bundle),Path(a.target).expanduser().resolve() if a.target else home(),a.overwrite)
    print(json.dumps(r,indent=2))
if __name__=="__main__":main()
