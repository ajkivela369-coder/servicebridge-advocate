from __future__ import annotations
import csv, io, json, os, re, shutil, zipfile
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from .vault import search as vault_search, claims as vault_claims, list_items as vault_items, forge_home


def query_evidence(question:str,k=6):
    return {'question':question,'hits':vault_search(question,k),'grounding_rule':'Generated conclusions must point back to a stored source item/chunk; no unsupported claim is promoted to verified fact.'}

def timeline():
    rows=[]
    for c in vault_claims():
        meta=json.loads(c.get('metadata') or '{}'); date=meta.get('date') or meta.get('service_date')
        if date:rows.append({'date':date,'statement':c['statement'],'source_ids':json.loads(c['source_ids']),'metadata':meta})
    rows.sort(key=lambda x:x['date']); return rows

def _sections(kind:str):
    k=(kind or 'GENERAL').upper()
    if k=='VBA':
        return ['Cover / issues presented','Source inventory','Service and duty chronology','In-service injury / aggravation evidence','Medical chronology and objective findings','Current functional impact','Medical opinions / nexus material','Contradictions, missing evidence, and unresolved questions','Requested review points','Source-linked appendix']
    if k=='APTD':
        return ['Cover / requested review','Source inventory','Medical chronology','Objective findings','Sustained functioning and episodic variability','Contradictions and evidence gaps','Questions for reviewer','Source-linked appendix']
    if k=='ADA':
        return ['Cover / accommodation purpose','Source inventory','Functional limitations','Requested accommodations','Supporting records','Source-linked appendix']
    if k=='CLINICIAN':
        return ['Clinical summary','Source inventory','Medical chronology','Observed findings','Symptoms and functioning','Questions for clinician','Source-linked appendix']
    if k=='SSDI':
        return ['Cover / claimant summary','Source inventory','Medically determinable impairments','Longitudinal treatment chronology','Objective findings','Symptoms and episodic variability','Function over a sustained work schedule','Attendance, recovery time, endurance and reliability','Conflicts / gaps requiring review','Source-linked appendix']
    return ['Executive summary','Source inventory','Chronology','Objective findings','Functional impact','Mechanism / issue map','Contradictions and gaps','Questions for reviewer','Source-linked appendix']

def packet_outline(case_name='Evidence Packet',kind='GENERAL'):
    return {'title':case_name,'kind':kind.upper(),'sections':_sections(kind),'rule':'Every material statement should retain source/page or source/chunk provenance.'}

def _meta(item):
    try:return json.loads(item.get('metadata') or '{}')
    except Exception:return {}

def _safe_name(name:str)->str:
    s=re.sub(r'[^A-Za-z0-9._-]+','_',name or 'source').strip('._')
    return s[:140] or 'source'

def build_packet(kind:str='VBA',case_name:str='Evidence Packet',source_ids:list[str]|None=None,include_originals:bool=False)->dict:
    kind=(kind or 'VBA').upper()
    if kind not in {'VBA','SSDI','APTD','ADA','CLINICIAN','CUSTOM','GENERAL'}: kind='GENERAL'
    all_items=vault_items(1000)
    wanted=set(source_ids or [])
    items=[i for i in all_items if not wanted or i.get('id') in wanted]
    if not items:raise ValueError('Upload or select at least one source before building a packet.')
    if wanted - {i['id'] for i in items}:raise ValueError('Some selected sources were not found. Refresh the source inventory.')
    claims=vault_claims()
    if wanted:
        filt=[]
        for c in claims:
            try:sids=set(json.loads(c.get('source_ids') or '[]'))
            except Exception:sids=set()
            if sids and sids.issubset(wanted):filt.append(c)
        claims=filt
    tl=[]
    for c in claims:
        meta=json.loads(c.get('metadata') or '{}'); date=meta.get('date') or meta.get('service_date')
        if date:tl.append({'date':date,'statement':c['statement'],'source_ids':json.loads(c.get('source_ids') or '[]'),'metadata':meta})
    tl.sort(key=lambda x:str(x.get('date','')))
    outdir=forge_home()/'exports';outdir.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')
    slug=_safe_name(case_name)
    base=f'{slug}-{kind}-{stamp}'
    work=outdir/(base+'-files'); work.mkdir(parents=True,exist_ok=True)
    manifest={'schema_version':1,'created_at':datetime.now(timezone.utc).isoformat(),'kind':kind,'case_name':case_name,'source_count':len(items),'claim_count':len(claims),'include_originals':bool(include_originals),'sources':[],'claims':claims,'timeline':tl,'outline':packet_outline(case_name,kind)}
    for item in items:
        m=_meta(item)
        manifest['sources'].append({k:item.get(k) for k in ['id','name','sha256','mime','size','created_at','source']}|{'metadata':m})
    (work/'packet_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    # CSV inventory.
    with (work/'source_inventory.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f);w.writerow(['source_id','name','date','category','provider','record_type','sha256','mime','size_bytes'])
        for i in items:
            m=_meta(i);w.writerow([i.get('id'),i.get('name'),m.get('date') or m.get('source_date'),m.get('category'),m.get('provider'),m.get('record_type') or m.get('type'),i.get('sha256'),i.get('mime'),i.get('size')])
    with (work/'claims.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f);w.writerow(['claim_id','statement','source_ids','date','issue'])
        for c in claims:
            m=json.loads(c.get('metadata') or '{}');w.writerow([c.get('id'),c.get('statement'),c.get('source_ids'),m.get('date') or m.get('service_date'),m.get('issue')])
    sections=_sections(kind)
    md=[f'# {case_name}',f'**Packet type:** {kind}',f'**Generated:** {manifest["created_at"]}','', '> Draft organization aid. Verify every material statement against the retained source before submission.','']
    for sec in sections:
        md += [f'## {sec}','']
        if sec.lower().startswith('source inventory'):
            for i in items:
                m=_meta(i); md.append(f'- **{i.get("name")}** — {m.get("date") or m.get("source_date") or "date not entered"} · {m.get("category") or "uncategorized"} · SHA-256 `{i.get("sha256")}`')
        elif 'chronology' in sec.lower():
            for row in tl: md.append(f'- **{row.get("date")}** — {row.get("statement")}  \n  Sources: {", ".join(row.get("source_ids") or [])}')
        elif 'appendix' in sec.lower():
            md.append('See `source_inventory.csv`, `claims.csv`, and `packet_manifest.json` for the source-linked appendix data.')
        else:
            related=[]
            for c in claims:
                m=json.loads(c.get('metadata') or '{}');issue=str(m.get('issue') or '').lower(); st=str(c.get('statement') or '')
                if issue and any(word in sec.lower() for word in issue.split() if len(word)>3): related.append(c)
            if related:
                for c in related[:30]:md.append(f'- {c.get("statement")}  \n  Sources: {c.get("source_ids")}')
            else:md.append('_No source-linked claims have been added to this section yet._')
        md.append('')
    (work/'packet_draft.md').write_text('\n'.join(md),encoding='utf-8')
    # Print-friendly HTML preview.
    source_rows=''.join(f"<tr><td>{escape(str(i.get('name') or ''))}</td><td>{escape(str((_meta(i).get('date') or _meta(i).get('source_date') or '')))}</td><td>{escape(str(_meta(i).get('category') or ''))}</td><td><code>{escape(str(i.get('sha256') or ''))}</code></td></tr>" for i in items)
    claim_rows=''.join(f"<li>{escape(str(c.get('statement') or ''))}<br><small>Sources: {escape(str(c.get('source_ids') or ''))}</small></li>" for c in claims)
    html=f'''<!doctype html><html><head><meta charset="utf-8"><title>{escape(case_name)}</title><style>body{{font:14px/1.5 Arial,sans-serif;color:#18202a;max-width:980px;margin:40px auto;padding:0 24px}}h1,h2{{color:#0b3656}}table{{width:100%;border-collapse:collapse}}th,td{{border:1px solid #ccd7df;padding:7px;vertical-align:top}}code{{font-size:10px;word-break:break-all}}.note{{padding:12px;background:#fff7d8;border-left:4px solid #d3a51c}}@media print{{body{{margin:0;max-width:none}}}}</style></head><body><h1>{escape(case_name)}</h1><p><b>Packet type:</b> {kind}</p><div class="note">Draft organizational packet. Verify every material statement and any program-specific legal/medical conclusion before submission.</div><h2>Source inventory</h2><table><tr><th>Source</th><th>Date</th><th>Category</th><th>SHA-256</th></tr>{source_rows}</table><h2>Source-linked claims</h2><ul>{claim_rows or '<li>No source-linked claims saved yet.</li>'}</ul><h2>Packet sections</h2><ol>{''.join('<li>'+escape(s)+'</li>' for s in sections)}</ol></body></html>'''
    (work/'packet_preview.html').write_text(html,encoding='utf-8')
    if include_originals:
        od=work/'originals';od.mkdir(exist_ok=True)
        for i in items:
            p=Path(i.get('stored_path') or '')
            if p.exists():
                dest=od/_safe_name(i.get('name') or p.name)
                if dest.exists():dest=od/(i.get('sha256','')[:10]+'-'+dest.name)
                shutil.copy2(p,dest)
    from .packet_pdf import make_packet_pdf
    pdf_result=make_packet_pdf(items,claims,case_name,kind,outdir/(base+'.pdf'))
    manifest['pdf']=pdf_result
    (work/'packet_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    shutil.copy2(pdf_result['pdf'],work/'evidence_packet.pdf')
    zip_path=outdir/(base+'.zip')
    with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,allowZip64=True) as z:
        for f in work.rglob('*'):
            if f.is_file():z.write(f,f.relative_to(work))
    return {**pdf_result,'ok':True,'kind':kind,'case_name':case_name,'sources':len(items),'claims':len(claims),'zip':str(zip_path),'preview':str(work/'packet_preview.html'),'draft':str(work/'packet_draft.md'),'manifest':str(work/'packet_manifest.json')}
