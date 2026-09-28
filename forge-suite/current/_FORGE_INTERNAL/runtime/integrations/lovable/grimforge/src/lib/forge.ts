export const FORGE_ENDPOINT="http://127.0.0.1:8787";
export async function forgeAvailable(){try{const r=await fetch(FORGE_ENDPOINT+"/api/health",{signal:AbortSignal.timeout(1200)});return r.ok}catch{return false}}
export async function localStoryboard(premise:string,scene_count=6){const r=await fetch(FORGE_ENDPOINT+"/api/grimforge/storyboard",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify({premise,scene_count})});if(!r.ok)throw new Error(await r.text());return r.json()}
export function exportForgeStoryboardJob(premise:string,scene_count=6){return{kind:"forge-job",version:1,task:"grimforge_storyboard",createdAt:new Date().toISOString(),payload:{premise,scene_count}}}
