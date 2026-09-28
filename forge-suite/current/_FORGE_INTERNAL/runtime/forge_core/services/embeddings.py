from __future__ import annotations
import hashlib, json, math, re, urllib.request
from collections import Counter

DIMS=512

def _ollama_embed(texts:list[str],model='nomic-embed-text')->list[list[float]]|None:
    try:
        body=json.dumps({'model':model,'input':texts}).encode();req=urllib.request.Request('http://127.0.0.1:11434/api/embed',data=body,headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=120) as r:data=json.load(r)
        return data.get('embeddings')
    except Exception:return None

def _hashing(texts:list[str])->list[list[float]]:
    out=[]
    for text in texts:
        toks=re.findall(r"[a-z0-9]+",text.lower());c=Counter(toks);v=[0.0]*DIMS
        for tok,count in c.items():
            h=hashlib.blake2b(tok.encode(),digest_size=8).digest();n=int.from_bytes(h,'big');idx=n%DIMS;sign=-1.0 if (n>>1)&1 else 1.0;v[idx]+=sign*(1.0+math.log(max(1,count)))
        norm=math.sqrt(sum(x*x for x in v)) or 1.0;out.append([x/norm for x in v])
    return out

def embed(texts:list[str],force_engine:str|None=None)->dict:
    if force_engine in {None,'ollama:nomic-embed-text'}:
        result=_ollama_embed(texts)
        if result is not None:return {'engine':'ollama:nomic-embed-text','vectors':result}
        if force_engine=='ollama:nomic-embed-text':return {'engine':'unavailable','vectors':[]}
    return {'engine':'hashing-local','vectors':_hashing(texts)}
