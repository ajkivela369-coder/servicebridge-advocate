from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STATIC=ROOT/'forge_core'/'static'; LEARN=ROOT/'learning'/'web'/'index.html'
CHECKS={
 'workspace':{'path':STATIC/'index.html','min_bytes':9000,'markers':['Your local AI command center','Forge Apps','System health','Storage & recovery','Elias','Evidence Auditor','MedForge','GrimForge','Forge Learn']},
 'elias':{'path':STATIC/'apps'/'elias.html','min_bytes':10000,'markers':['New chat','Message Elias','Local-first AI assistant','Use Evidence Auditor context','/api/elias/chat','eliasModel','forge-shared.js']},
 'evidence':{'path':STATIC/'apps'/'evidence.html','min_bytes':22000,'markers':['Upload Evidence → Build Packet','multiple','VBA','SSDI','APTD','ADA','Source inventory','Chronology','Create source-linked claim','/api/vault/upload-batch','/api/evidence/package','forge-shared.js']},
 'medforge':{'path':STATIC/'apps'/'medforge.html','min_bytes':11000,'markers':['Image Lab','Mechanism Builder','Teach Me This','Mechanism Flow','Generate teaching visual','Open 3D Studio','forge-shared.js']},
 'grimforge':{'path':STATIC/'apps'/'grimforge.html','min_bytes':15000,'markers':['Simple','Pro','Surprise me','Animation style','3D · Blender cinematic animation','2.5D · cinematic depth animation','2D · illustrated full-motion animation','GENERATE FULL EPISODE','productionRail','/api/grimforge/render','Director\'s Notes','forge-shared.js']},
 'learn':{'path':LEARN,'min_bytes':9000,'markers':['Forge Learn','Every feature has a lesson','Feature library','How Forge evolved','Coding vocabulary in context','Failure simulator','Teach me this']},
}
def check():
 out={};fail=[]
 for name,spec in CHECKS.items():
  p=spec['path'];text=p.read_text(encoding='utf-8',errors='replace') if p.exists() else '';missing=[m for m in spec['markers'] if m.lower() not in text.lower()];size=len(text.encode())
  ok=p.exists() and size>=spec['min_bytes'] and not missing
  out[name]={'path':str(p.relative_to(ROOT)) if p.exists() else str(p),'exists':p.exists(),'bytes':size,'min_bytes':spec['min_bytes'],'missing_markers':missing,'ok':ok}
  if not ok:fail.append(name)
 return {'ok':not fail,'scope':'v0.5.6 workflow recovery product surface regression: required workflows and product identity markers; live media quality still requires user review','failures':fail,'surfaces':out}
if __name__=='__main__':
 r=check();print(json.dumps(r,indent=2));raise SystemExit(0 if r['ok'] else 1)
