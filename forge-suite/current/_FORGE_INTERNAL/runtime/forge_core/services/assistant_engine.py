"""Role-aware, explicitly selected local chat. Never substitutes a cloud service."""
import json
import urllib.request
from . import llm

OLLAMA = 'http://127.0.0.1:11434'

def models():
    try:
        with urllib.request.urlopen(OLLAMA+'/api/tags', timeout=3) as r:
            return [m['name'] for m in json.load(r).get('models', [])]
    except Exception:
        return []

def chat(messages, model='auto', max_tokens=2400):
    available = models()
    if model in ('smart','quality','auto-smart'):
        # Quality-first route for Elias when a larger local model is already installed.
        model = next((x for prefix in ('qwen2.5:7b','qwen2.5:8b','llama3.1:8b','llama3.2:8b','mistral:7b') for x in available if x.startswith(prefix)), None)
        if not model:
            model = next((x for prefix in ('qwen2.5:3b','llama3.2:3b') for x in available if x.startswith(prefix)), None)
    elif model == 'auto':
        # Memory-conscious route for general app copilots.
        model = next((x for prefix in ('qwen2.5:3b','llama3.2:3b','qwen2.5:7b') for x in available if x.startswith(prefix)), None)
        if not model:
            model = next((x for x in available if not any(t in x.lower() for t in ('embed','vision','vl:'))), None)
    elif model not in available:
        return {'engine':'none','text':None,'error':'Selected model is not installed or Ollama is offline. Choose an installed model in the selector.'}
    if model:
        try:
            payload={'model':model,'messages':messages,'stream':False,'options':{'num_predict':max_tokens,'num_ctx':8192,'temperature':0.3}}
            req=urllib.request.Request(OLLAMA+'/api/chat',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req,timeout=240) as r:
                d=json.load(r)
            text=d.get('message',{}).get('content')
            if text:return {'engine':'ollama:'+model,'text':text}
            return {'engine':'none','text':None,'error':'The selected model returned no message.'}
        except Exception:
            return {'engine':'none','text':None,'error':'The selected model could not finish. Check Ollama and available memory, or select a smaller model.'}
    if llm._ensure_llama_server():
        prompt='\n\n'.join(m['role'].upper()+': '+m['content'] for m in messages)
        text=llm._llama_server_request(prompt,max_tokens)
        if text:return {'engine':'llama.cpp:qwen2.5-3b-instruct-q4_k_m','text':text}
    return {'engine':'none','text':None,'error':'No local chat engine is ready. Start Ollama or install the local model from Setup & Repair.'}
