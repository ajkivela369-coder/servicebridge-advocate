export const FORGE_ENDPOINT = "http://127.0.0.1:8787";
export type ForgeStatus={connected:boolean;mode:"LOCAL_ONLY"|"HYBRID"|"UNKNOWN";reason?:string;blockedByBrowser?:boolean};
async function get(path:string,ms=1800){const ctrl=new AbortController();const t=setTimeout(()=>ctrl.abort(),ms);try{const r=await fetch(FORGE_ENDPOINT+path,{signal:ctrl.signal});if(!r.ok)throw new Error(`HTTP ${r.status}`);return r.json()}finally{clearTimeout(t)}}
async function post(path:string,body:unknown){const r=await fetch(FORGE_ENDPOINT+path,{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify(body)});if(!r.ok)throw new Error(`Forge ${path} failed [${r.status}]`);return r.json()}
export async function checkForge():Promise<ForgeStatus>{const https=typeof window!=="undefined"&&location.protocol==="https:";try{const health=await get("/api/health");await get("/api/bridge/config").catch(()=>null);const m=health?.settings?.mode;return{connected:true,mode:m==="LOCAL_ONLY"||m==="HYBRID"?m:"UNKNOWN"}}catch(e){return{connected:false,mode:"UNKNOWN",blockedByBrowser:https,reason:https?"Browser policy may block this HTTPS page from reaching local Forge. Use the Forge Launcher or Export/Import.":(e as Error).message}}}
export const forge={
  queryEvidence:(question:string,k=6)=>post("/api/evidence/query",{question,k}),
  teachMe:(title:string,source_text:string,output_name="elias-teach-me")=>post("/api/teach/render",{title,source_text,output_name,prefer_ollama:true}),
  vaultItems:()=>get("/api/vault/items"),
  health:()=>get("/api/health"),
  bridge:()=>get("/api/bridge/config")
};
export type ForgeJob={kind:"forge-job";version:1;task:"evidence_query"|"teach_me_this";createdAt:string;payload:unknown;rules:string[]};
export function buildJob(task:ForgeJob["task"],payload:unknown):ForgeJob{return{kind:"forge-job",version:1,task,createdAt:new Date().toISOString(),payload,rules:["Process locally unless the user explicitly approves cloud use.","Preserve source IDs and provenance.","Do not promote unsupported synthesis to verified fact."]}}
export function parseResult(json:string){return JSON.parse(json)}
