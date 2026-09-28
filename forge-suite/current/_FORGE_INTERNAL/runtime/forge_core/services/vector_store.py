from __future__ import annotations
import json, math, os, sqlite3, uuid
from pathlib import Path
from .embeddings import embed

def db_path()->Path:
    root=Path(os.environ.get('FORGE_HOME') or (Path.home()/'Forge'));p=root/'cache'/'vector'/'forge_vectors.sqlite3';p.parent.mkdir(parents=True,exist_ok=True);return p

def _conn():
    c=sqlite3.connect(db_path());c.execute('CREATE TABLE IF NOT EXISTS documents (id TEXT PRIMARY KEY, collection TEXT, text TEXT, metadata TEXT, vector TEXT, engine TEXT)');c.execute('CREATE INDEX IF NOT EXISTS idx_collection ON documents(collection)');return c

def add(collection:str,texts:list[str],metadata:list[dict]|None=None)->dict:
    metadata=metadata or [{} for _ in texts];e=embed(texts);ids=[]
    with _conn() as c:
        for text,meta,vec in zip(texts,metadata,e['vectors']):
            i=str(uuid.uuid4());ids.append(i);c.execute('INSERT INTO documents VALUES(?,?,?,?,?,?)',(i,collection,text,json.dumps(meta),json.dumps(vec),e['engine']))
    return {'collection':collection,'ids':ids,'engine':e['engine'],'count':len(ids)}

def _cos(a,b):
    if not a or not b or len(a)!=len(b):return -1.0
    return sum(x*y for x,y in zip(a,b))/(math.sqrt(sum(x*x for x in a))*math.sqrt(sum(y*y for y in b)) or 1.0)

def query(collection:str,text:str,k:int=5)->dict:
    with _conn() as c: raw=list(c.execute('SELECT id,text,metadata,vector,engine FROM documents WHERE collection=?',(collection,)))
    query_vectors={};warnings=[];rows=[]
    for engine in sorted({r[4] for r in raw}):
        q=embed([text],force_engine=engine)
        if not q['vectors']:
            warnings.append(f'Query route unavailable for stored engine {engine}; those rows were skipped.')
        else: query_vectors[engine]=q['vectors'][0]
    for i,t,m,v,eng in raw:
        if eng not in query_vectors:continue
        rows.append({'id':i,'text':t,'metadata':json.loads(m),'score':_cos(query_vectors[eng],json.loads(v)),'stored_engine':eng})
    rows.sort(key=lambda x:x['score'],reverse=True)
    return {'collection':collection,'query_engines':list(query_vectors),'warnings':warnings,'results':rows[:k]}

def clear(collection:str)->dict:
    with _conn() as c:r=c.execute('DELETE FROM documents WHERE collection=?',(collection,));return {'collection':collection,'deleted':r.rowcount}
