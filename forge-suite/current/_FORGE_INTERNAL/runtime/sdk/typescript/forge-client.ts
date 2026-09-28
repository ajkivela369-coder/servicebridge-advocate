export type ForgeMode = 'LOCAL_ONLY' | 'HYBRID';
export class ForgeClient {
  baseUrl: string;
  constructor(baseUrl = 'http://127.0.0.1:8787'){ this.baseUrl = baseUrl.replace(/\/$/, ''); }
  private async req(path:string, init?:RequestInit){ const r=await fetch(this.baseUrl+path,init); if(!r.ok) throw new Error(await r.text()); return r.json(); }
  health(){ return this.req('/api/health'); }
  capabilities(){ return this.req('/api/capabilities'); }
  bridge(){ return this.req('/api/bridge/config'); }
  setMode(mode:ForgeMode){ return this.req('/api/mode',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mode})}); }
  teach(title:string, source_text:string, output_name='teach-me-this'){ return this.req('/api/teach/render',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title,source_text,output_name,prefer_ollama:true})}); }
  evidence(question:string,k=6){ return this.req('/api/evidence/query',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question,k})}); }
  grimforge(premise:string,scene_count=6){ return this.req('/api/grimforge/storyboard',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({premise,scene_count})}); }
  async isAvailable(){ try{ const r=await fetch(this.baseUrl+'/api/health',{signal:AbortSignal.timeout(900)}); return r.ok; }catch{return false;} }
}
