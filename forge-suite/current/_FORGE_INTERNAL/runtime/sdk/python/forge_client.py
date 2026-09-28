from __future__ import annotations
import json, urllib.request
class ForgeClient:
    def __init__(self,base_url='http://127.0.0.1:8787'):self.base_url=base_url.rstrip('/')
    def _req(self,path,payload=None):
        data=json.dumps(payload).encode() if payload is not None else None; req=urllib.request.Request(self.base_url+path,data=data,headers={'Content-Type':'application/json'} if data else {})
        with urllib.request.urlopen(req,timeout=180) as r:return json.load(r)
    def health(self):return self._req('/api/health')
    def capabilities(self):return self._req('/api/capabilities')
    def teach(self,title,source_text,output_name='teach-me-this'):return self._req('/api/teach/render',{'title':title,'source_text':source_text,'output_name':output_name,'prefer_ollama':True})
    def evidence(self,question,k=6):return self._req('/api/evidence/query',{'question':question,'k':k})
