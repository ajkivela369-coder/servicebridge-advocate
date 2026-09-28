from __future__ import annotations
import json, os, shutil, subprocess, time, urllib.request
from pathlib import Path

def _ollama(prompt:str,model:str,max_tokens:int=1024):
    try:
        body=json.dumps({'model':model,'prompt':prompt,'stream':False,'options':{'num_predict':max_tokens}}).encode();req=urllib.request.Request('http://127.0.0.1:11434/api/generate',data=body,headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=180) as r:d=json.load(r)
        return d.get('response')
    except Exception:return None

def _llama_server_request(prompt:str,max_tokens:int=1024):
    try:
        body=json.dumps({'model':'local','messages':[{'role':'user','content':prompt}],'max_tokens':max_tokens,'temperature':0.2}).encode();req=urllib.request.Request('http://127.0.0.1:8080/v1/chat/completions',data=body,headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=180) as r:d=json.load(r)
        return d.get('choices',[{}])[0].get('message',{}).get('content')
    except Exception:return None

def _ensure_llama_server()->bool:
    try:
        with urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=.5) as r:return r.status==200
    except Exception:pass
    exe=shutil.which('llama-server') or shutil.which('llama-server.exe')
    root=Path(os.environ.get('FORGE_HOME') or (Path.home()/'Forge'));model=root/'models'/'llama.cpp'/'qwen2.5-3b-instruct-q4_k_m.gguf'
    if not exe or not model.exists():return False
    kwargs={'stdout':subprocess.DEVNULL,'stderr':subprocess.DEVNULL}
    if os.name=='nt':kwargs['creationflags']=subprocess.CREATE_NO_WINDOW|subprocess.DETACHED_PROCESS
    subprocess.Popen([exe,'-m',str(model),'--host','127.0.0.1','--port','8080','-c','8192'],**kwargs)
    for _ in range(30):
        time.sleep(.5)
        try:
            with urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=.5) as r:
                if r.status==200:return True
        except Exception:pass
    return False

def generate(prompt:str,preferred_model='qwen2.5:7b-instruct',max_tokens=1024)->dict:
    out=_ollama(prompt,preferred_model,max_tokens)
    if out:return {'engine':f'ollama:{preferred_model}','text':out}
    if _ensure_llama_server():
        out=_llama_server_request(prompt,max_tokens)
        if out:return {'engine':'llama.cpp:qwen2.5-3b-instruct-q4_k_m','text':out}
    return {'engine':'none','text':None}
