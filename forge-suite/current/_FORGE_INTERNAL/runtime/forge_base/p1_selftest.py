from __future__ import annotations
import json, os, tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from forge_base.forge_base import forge_home, init, report, inventory
from forge_base.bundle import create, verify
from forge_base.model_manager import model_status
from forge_core.services.detect import capabilities
from forge_core.services.router import routing_summary
from forge_core.services.embeddings import embed
from forge_core.services.flow import animate_flow
from forge_core.services.lesson import heuristic_lesson
from forge_core.services.render import render_lesson
from forge_core.services.design import design_status, render_local_page
from forge_base.feature_gate import check as feature_gate

def main():
    root=forge_home();init(root);checks={};details={}
    r=report(root);checks['doctor_manifest']=(root/'manifests'/'doctor-latest.json').exists();details['doctor']=r
    gate=feature_gate();checks['feature_release_gate']=gate['ok'];details['feature_gate']=gate
    routes=routing_summary();checks['router_has_core_tasks']=all(k in routes for k in ['general','coding','embeddings','vision','transcription','speech','video','diagram']);details['routes']=routes
    ms=model_status(root);checks['model_registry']=len(ms['ollama'])>=4 and len(ms['whisper'])>=2;details['models']=ms
    emb=embed(['forge local runtime','local runtime cache']);checks['embeddings_fallback']=len(emb['vectors'])==2;details['embedding_engine']=emb['engine']
    caps=capabilities();details['capabilities']=caps
    outdir=Path(__file__).resolve().parents[1]/'data'/'outputs';outdir.mkdir(parents=True,exist_ok=True)
    ds=design_status(); sample=render_local_page('Forge Design Fallback','Offline UI path',[{'title':'Status','body':'Local design fallback is working.'}],outdir/'p1-design-fallback.html');checks['design_fallback']=ds['fallback_ready'] and sample.exists();details['design']=ds
    if caps.get('video',{}).get('ready') and caps.get('diagram',{}).get('pillow'):
        flow=animate_flow(['Epic/RIS','Scanner','DICOM','PACS','Viewer'],outdir/'p1-flow-selftest.mp4','P1 flow self-test',0.45);checks['flow_render']=Path(flow['video']).exists();details['flow']=flow
    else: checks['flow_render']=None
    if caps.get('local_only_capable'):
        lesson=heuristic_lesson('P1 local render','Identify the issue.\n\nScope the issue.\n\nCheck upstream and downstream.\n\nResolve or escalate safely.')
        rendered=render_lesson(lesson,'p1-selftest');checks['lesson_render']=Path(rendered['video']).exists();details['lesson']=rendered
    else: checks['lesson_render']=None
    inventory(root);bundle=root/'backups'/'p1-selftest-offline.zip';b=create(bundle,include_models=False);v=verify(bundle);checks['bundle_verify']=v['ok'];details['bundle']=b
    required=[v for v in checks.values() if v is not None];ok=all(required)
    result={'ok':ok,'checks':checks,'details':details};(root/'manifests'/'p1-selftest-latest.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
    raise SystemExit(0 if ok else 1)
if __name__=='__main__':main()
