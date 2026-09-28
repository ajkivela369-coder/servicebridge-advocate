from __future__ import annotations
import hashlib, json, mimetypes, os, shutil, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path
from .embeddings import embed

def forge_home(): return Path(os.environ.get('FORGE_HOME') or (Path.home()/'Forge')).expanduser()
def vault_root():
    p=forge_home()/'vault'; (p/'originals').mkdir(parents=True,exist_ok=True); (p/'derived').mkdir(parents=True,exist_ok=True); return p
def db_path(): return vault_root()/'vault.sqlite3'
def _db():
    con=sqlite3.connect(db_path()); con.row_factory=sqlite3.Row
    con.execute('CREATE TABLE IF NOT EXISTS items(id TEXT PRIMARY KEY,sha256 TEXT UNIQUE,name TEXT,mime TEXT,size INTEGER,stored_path TEXT,created_at TEXT,source TEXT,metadata TEXT)')
    con.execute('CREATE TABLE IF NOT EXISTS chunks(id TEXT PRIMARY KEY,item_id TEXT,text TEXT,metadata TEXT,vector TEXT)')
    con.execute('CREATE TABLE IF NOT EXISTS claims(id TEXT PRIMARY KEY,statement TEXT,source_ids TEXT,created_at TEXT,metadata TEXT)')
    return con

def _sha(path:Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
    return h.hexdigest()

def import_file(path:Path,metadata:dict|None=None,source='upload'):
    path=Path(path); digest=_sha(path); con=_db(); row=con.execute('SELECT * FROM items WHERE sha256=?',(digest,)).fetchone()
    if row:return dict(row)|{'deduplicated':True}
    item_id=str(uuid.uuid4()); ext=path.suffix.lower(); dest=vault_root()/'originals'/f'{digest}{ext}'; shutil.copy2(path,dest)
    rec={'id':item_id,'sha256':digest,'name':path.name,'mime':mimetypes.guess_type(path.name)[0] or 'application/octet-stream','size':path.stat().st_size,'stored_path':str(dest),'created_at':datetime.now(timezone.utc).isoformat(),'source':source,'metadata':json.dumps(metadata or {})}
    con.execute('INSERT INTO items VALUES(?,?,?,?,?,?,?,?,?)',tuple(rec.values())); con.commit(); return rec|{'deduplicated':False}

def add_text(item_id:str,text:str,metadata:dict|None=None):
    con=_db(); chunks=[part[j:j+2400] for part in text.replace('\r','').split('\n\n') if part.strip() for j in range(0,len(part),2400)]
    if not chunks:return {'added':0}
    vectors=[]
    for n in range(0,len(chunks),32):vectors.extend(embed(chunks[n:n+32])['vectors'])
    if len(vectors)!=len(chunks):raise ValueError('Embedding count mismatch; existing index retained')
    con.execute('DELETE FROM chunks WHERE item_id=?',(item_id,))
    for i,(chunk,vec) in enumerate(zip(chunks,vectors)):
        cid=f'{item_id}:{i}'; con.execute('INSERT OR REPLACE INTO chunks VALUES(?,?,?,?,?)',(cid,item_id,chunk,json.dumps(metadata or {}),json.dumps(vec)))
    con.commit(); return {'added':len(chunks)}

def list_items(limit=200):
    con=_db(); rows=con.execute('SELECT * FROM items ORDER BY created_at DESC LIMIT ?',(limit,)).fetchall(); return [dict(r) for r in rows]

def search(text:str,k=5,source_ids=None):
    q=embed([text])['vectors'][0]; con=_db(); rows=con.execute('SELECT c.*,i.name,i.sha256 FROM chunks c JOIN items i ON i.id=c.item_id').fetchall(); scored=[]
    for r in rows:
        if source_ids and r['item_id'] not in source_ids:continue
        v=json.loads(r['vector']); score=sum(a*b for a,b in zip(q,v)); scored.append((score,dict(r)))
    scored.sort(key=lambda x:x[0],reverse=True); return [{'score':round(s,5),**r} for s,r in scored[:k]]

def add_claim(statement:str,source_ids:list[str],metadata:dict|None=None):
    con=_db(); cid=str(uuid.uuid4()); rec={'id':cid,'statement':statement,'source_ids':json.dumps(source_ids),'created_at':datetime.now(timezone.utc).isoformat(),'metadata':json.dumps(metadata or {})}; con.execute('INSERT INTO claims VALUES(?,?,?,?,?)',tuple(rec.values())); con.commit(); return rec

def claims():
    con=_db(); return [dict(r) for r in con.execute('SELECT * FROM claims ORDER BY created_at DESC').fetchall()]
