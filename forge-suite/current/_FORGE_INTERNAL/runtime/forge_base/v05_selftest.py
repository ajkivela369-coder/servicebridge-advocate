from __future__ import annotations
import json, os, shutil, tempfile
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from forge_base.forge_base import init, report, inventory
from forge_base.bundle import create, verify
from forge_base.feature_gate import check as feature_gate
from forge_core.services.hardware import current_hardware
from forge_core.services.router import routing_summary, choose
from forge_core.services.vault import import_file, add_text, search, add_claim
from forge_core.services.evidence import query_evidence, packet_outline
from forge_core.services.medforge import make_lesson
from forge_core.services.grimforge import storyboard
from forge_core.services.bridge import bridge_config
from forge_core.services.system_ops import status as system_status, backup as system_backup

def main():
    old=os.environ.get('FORGE_HOME'); tmp=Path(tempfile.mkdtemp(prefix='forge-v05-selftest-')); os.environ['FORGE_HOME']=str(tmp)
    checks={}; details={}
    try:
        init(tmp); r=report(tmp); checks['doctor']=bool(r.get('forge_home')); details['doctor']=r
        gate=feature_gate(); checks['release_gate']=gate['ok']; details['gate']=gate
        hw=current_hardware(); checks['hardware_profile']=hw['declared_profile'].get('memory',{}).get('installed_gb')==16.0; details['hardware']=hw
        routes=routing_summary(); checks['routes']=all(k in routes for k in ['general','coding','embeddings','vision','transcription','speech','video','diagram']); details['routes_detail']=routes
        fake_caps={'llm':{'models':[]},'llama_cpp':{'installed':False},'voice':{},'transcription':{},'video':{},'diagram':{},'linux_escape':{},'containers':{}}
        checks['reasoning_fallback']=choose('general',fake_caps)['selected']=='heuristic-local'
        f=tmp/'sample.txt'; f.write_text('June 1 functional capacity evaluation. Endurance for competitive eight hour work was the key issue.\n\nObjective findings must stay linked to the source.')
        item=import_file(f,{'date':'2026-06-01'}); add_text(item['id'],f.read_text(),{'date':'2026-06-01'}); hit=search('competitive endurance',3); checks['vault_search']=bool(hit) and hit[0]['item_id']==item['id']; details['vault_hit']=hit
        add_claim('Endurance was identified as a key functional issue.',[item['id']],{'date':'2026-06-01'}); eq=query_evidence('What was the endurance issue?',3); checks['evidence_query']=bool(eq['hits']); checks['packet_outline']=len(packet_outline()['sections'])>=8
        ml=make_lesson('MedForge test','Observed findings should be separated from interpretation.\n\nVerify the source before forming a mechanism hypothesis.'); checks['medforge_lesson']=bool(ml.get('scenes'))
        gp=storyboard('A medic crosses a damaged station.',3); checks['grimforge_storyboard']=len(gp['plan']['scenes'])==3
        checks['bridge']=bridge_config()['version']=='0.5.2'
        ss=system_status(); checks['system_status']=ss.get('forge_home')==str(tmp); details['system_status']=ss
        wb=system_backup(False); checks['workspace_backup']=bool(wb.get('verification',{}).get('ok')); details['workspace_backup']=wb
        inventory(tmp); b=tmp/'backups'/'v05-selftest.zip'; create(b,include_models=False); checks['offline_bundle']=verify(b)['ok']
        ok=all(checks.values()); result={'ok':ok,'checks':checks,'details':details}; out=Path(__file__).resolve().parents[1]/'V05_CORE_SELFTEST.json'; out.write_text(json.dumps(result,indent=2),encoding='utf-8'); print(json.dumps(result,indent=2)); raise SystemExit(0 if ok else 1)
    finally:
        if old is None: os.environ.pop('FORGE_HOME',None)
        else: os.environ['FORGE_HOME']=old
        shutil.rmtree(tmp,ignore_errors=True)
if __name__=='__main__':main()
