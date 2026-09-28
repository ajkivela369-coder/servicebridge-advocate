from __future__ import annotations
import argparse, json, os, shutil, subprocess, zipfile
from datetime import datetime, timezone
from pathlib import Path


def root(): return Path(os.environ.get("FORGE_HOME") or (Path.home()/"Forge")).expanduser().resolve()
def _run(cmd,cwd=None): return subprocess.run(cmd,cwd=cwd,capture_output=True,text=True)

def backup_project(project:Path,outdir:Path):
    project=project.resolve(); outdir.mkdir(parents=True,exist_ok=True); stamp=datetime.now().strftime("%Y%m%d-%H%M%S")
    git=project/".git"
    if git.exists() and shutil.which("git"):
        out=outdir/f"{project.name}-{stamp}.bundle"; p=_run(["git","bundle","create",str(out),"--all"],project)
        if p.returncode: raise RuntimeError(p.stderr)
        return {"type":"git-bundle","path":str(out)}
    out=outdir/f"{project.name}-{stamp}.zip"
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
        for p in project.rglob("*"):
            if p.is_file() and ".git" not in p.parts and "node_modules" not in p.parts and ".venv" not in p.parts:
                z.write(p,p.relative_to(project.parent))
    return {"type":"zip","path":str(out)}

def restore(backup:Path,destination:Path):
    destination=destination.resolve(); destination.parent.mkdir(parents=True,exist_ok=True)
    if backup.suffix==".bundle":
        if destination.exists(): raise RuntimeError("Destination exists; choose an empty destination for git-bundle restore")
        p=_run(["git","clone",str(backup),str(destination)])
        if p.returncode: raise RuntimeError(p.stderr)
        return {"ok":True,"type":"git-bundle","path":str(destination)}
    destination.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(backup) as z:z.extractall(destination.parent)
    return {"ok":True,"type":"zip","path":str(destination)}

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest="cmd",required=True)
    p=sp.add_parser("backup");p.add_argument("project");p.add_argument("--out",default=None)
    p=sp.add_parser("restore");p.add_argument("backup");p.add_argument("destination")
    a=ap.parse_args()
    if a.cmd=="backup": res=backup_project(Path(a.project),Path(a.out) if a.out else root()/"backups"/"projects")
    else: res=restore(Path(a.backup),Path(a.destination))
    print(json.dumps(res,indent=2))
if __name__=="__main__":main()
