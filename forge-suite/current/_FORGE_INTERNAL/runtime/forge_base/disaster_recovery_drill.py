from __future__ import annotations
import hashlib, json, os, shutil, tempfile
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from forge_base.forge_base import init, inventory
from forge_base.bundle import create, verify
from forge_core.services.router import choose

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    base=Path(tempfile.mkdtemp(prefix='forge-drill-src-')); restore=Path(tempfile.mkdtemp(prefix='forge-drill-dst-')); old=os.environ.get('FORGE_HOME')
    try:
        os.environ['FORGE_HOME']=str(base); init(base); pr=base/'projects'/'demo'; pr.mkdir(parents=True); (pr/'README.md').write_text('Forge recovery drill source marker: 42')
        marker=sha(pr/'README.md'); inventory(base); bundle=base/'backups'/'drill.zip'; created=create(bundle,include_models=False); verified=verify(bundle)
        shutil.unpack_archive(str(bundle),str(restore))
        candidates=list(restore.rglob('README.md')); restored=next((p for p in candidates if 'recovery drill source marker' in p.read_text(errors='ignore')),None)
        fake={'llm':{'models':[]},'llama_cpp':{'installed':False},'voice':{},'transcription':{},'video':{},'diagram':{},'linux_escape':{},'containers':{}}
        route=choose('general',fake)
        result={'ok':verified['ok'] and restored is not None and sha(restored)==marker and route['selected']=='heuristic-local','bundle_verified':verified['ok'],'restored_marker_match':restored is not None and sha(restored)==marker,'forced_primary_failure_route':route,'bundle':created}
        out=Path(__file__).resolve().parents[1]/'DISASTER_RECOVERY_DRILL.json'; out.write_text(json.dumps(result,indent=2),encoding='utf-8'); print(json.dumps(result,indent=2)); raise SystemExit(0 if result['ok'] else 1)
    finally:
        if old is None:os.environ.pop('FORGE_HOME',None)
        else:os.environ['FORGE_HOME']=old
        shutil.rmtree(base,ignore_errors=True); shutil.rmtree(restore,ignore_errors=True)
if __name__=='__main__':main()
