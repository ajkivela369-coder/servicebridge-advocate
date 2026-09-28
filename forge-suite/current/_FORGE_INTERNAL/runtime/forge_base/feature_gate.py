from __future__ import annotations
import json
from pathlib import Path
try:
    from .learning_sync import check as learning_check
except ImportError:
    from learning_sync import check as learning_check
try:
    from .ui_regression_gate import check as ui_check
except ImportError:
    from ui_regression_gate import check as ui_check
HERE=Path(__file__).resolve().parent

def check():
    reg=json.loads((HERE/'feature_registry.json').read_text())
    failures=[];rows=[]
    for f in reg['features']:
        ok=bool(f.get('local_routes')) and bool(f.get('fallback_routes')) and bool(f.get('offline_assets'))
        if not ok:failures.append(f['id'])
        rows.append({'id':f['id'],'ok':ok,'local_routes':len(f.get('local_routes',[])),'fallback_routes':len(f.get('fallback_routes',[])),'offline_assets':len(f.get('offline_assets',[]))})
    learning=learning_check()
    if not learning['ok']:
        failures.append('learning_sync')
    ui=ui_check()
    if not ui['ok']:
        failures.append('ui_regression')
    return {'ok':not failures,'failures':failures,'features':rows,'learning':learning,'ui_regression':ui}
if __name__=='__main__':
    r=check();print(json.dumps(r,indent=2));raise SystemExit(0 if r['ok'] else 1)
