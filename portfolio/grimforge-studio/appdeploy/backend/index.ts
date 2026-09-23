import { ai, error, json, router, storage } from '@appdeploy/sdk';

type WorkMode = 'Quick' | 'Standard' | 'Deep';
const cinemaBridgeUrl=(process.env.GRIMFORGE_CINEMA_BRIDGE_URL||'').replace(/\/$/,'');
async function cinemaBridge(path:string,body?:unknown){
  if(!cinemaBridgeUrl)throw new Error('Cinema Bridge is not configured');
  const response=await fetch(`${cinemaBridgeUrl}${path}`,{
    method:body?'POST':'GET',
    headers:body?{'content-type':'application/json'}:undefined,
    body:body?JSON.stringify(body):undefined
  });
  const text=await response.text();
  if(!response.ok)throw new Error(text.slice(0,1500)||`Cinema Bridge HTTP ${response.status}`);
  try{return JSON.parse(text)}catch{return {raw:text}}
}
function mediaUrl(payload:any){
  return payload?.url||payload?.video_url||payload?.videoUrl||payload?.output_url||payload?.outputUrl||payload?.result?.url||payload?.result?.video_url||'';
}

const veyrSystem=`You are Archivist Veyr, the original AI creative director inside GrimForge Studio. You are highly capable, friendly, practical, canon-conscious and decisive. You operate the studio for users who do not want to manage every control, while respecting users who want full manual control. You are not a Games Workshop character and never impersonate a real creator.
Rules: separate CANON/SOURCE from INTERPRETATION, EDITORIAL and SPECULATION; never invent a source; when a claim needs verification say so. Study other channels only at the level of pacing, structure, chaptering, humor density, hook strategy, maps, visual grammar, packaging and beginner clarity. Never copy scripts, jokes, catchphrases, artwork, creator identity or voice. Speech-reference profiles describe abstract performance traits only: cadence, register, pause pattern, energy, rhetorical shape and sentence length. Never imitate, clone or impersonate a real person, celebrity, actor, creator or copyrighted character voice. Favor original, user-owned, licensed, public-domain/open-license or generated-original assets. For 5-minute episodes favor a sharp hook, minimum necessary lore, evidence ladder, counterpoint, payoff and next-episode bridge. Visual direction should feel premium and cinematic without frantic motion. Voice direction prioritizes clarity, intelligibility, gravitas, low fatigue and clean consonants. Challenge weak ideas and give a concrete better choice.`;
const referenceProfileSchema={type:'object',properties:{name:{type:'string'},url:{type:'string'},summary:{type:'string'},traits:{type:'string'},profile:{type:'array',items:{type:'number'}}},required:['name','url','summary','traits','profile']};
const episodeSchema={type:'object',properties:{title:{type:'string'},thesis:{type:'string'},hook:{type:'string'},world:{type:'string'},targetMinutes:{type:'number'},voice:{type:'string'},visualStyle:{type:'string'},youtubeTitle:{type:'string'},thumbnailText:{type:'string'},description:{type:'string'},nextBridge:{type:'string'},scenes:{type:'array',items:{type:'object',properties:{id:{type:'string'},title:{type:'string'},start:{type:'string'},duration:{type:'number'},narration:{type:'string'},dialogue:{type:'string'},claimType:{type:'string'},visualPrompt:{type:'string'},motion:{type:'string'},sound:{type:'string'},sourceNeed:{type:'string'}},required:['id','title','start','duration','narration','claimType','visualPrompt','motion','sound','sourceNeed']}}},required:['title','thesis','hook','world','targetMinutes','voice','visualStyle','youtubeTitle','thumbnailText','description','nextBridge','scenes']};
function thinking(mode?:WorkMode):'NONE'|'FAST'|'DEEP'{return mode==='Quick'?'NONE':mode==='Deep'?'DEEP':'FAST'}
function safeSlug(v:string){return v.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'').slice(0,60)||'grimforge-project'}
export const handler=router({
  'GET /api/_healthcheck':[async()=>json({message:'Success'})],
  'GET /api/cinema/status':[async()=>{
    if(!cinemaBridgeUrl)return json({configured:false,providers:[]});
    try{
      const health=await cinemaBridge('/health');
      const providers=await cinemaBridge('/v1/providers');
      return json({configured:true,health,providers:providers.providers||[]});
    }catch(e){
      return json({configured:true,error:e instanceof Error?e.message:'Cinema Bridge unavailable',providers:[]});
    }
  }],

  'POST /api/cinema/render-scene':[async({body})=>{
    const d=(body||{}) as {provider?:string;prompt?:string;imageUrl?:string;seconds?:number;fps?:number;width?:number;height?:number;metadata?:unknown};
    if(!d.provider||!d.prompt)return error('provider and prompt are required',400);
    if(!cinemaBridgeUrl)return error('Cinema Bridge is not configured',503);
    try{
      const result=await cinemaBridge('/v1/video/generate',{
        provider:d.provider,
        prompt:d.prompt,
        image_url:d.imageUrl,
        seconds:d.seconds||6,
        fps:d.fps||24,
        width:d.width||1280,
        height:d.height||720,
        metadata:d.metadata||{}
      });
      const url=mediaUrl(result);
      if(!url)return error('The configured video provider returned no playable media URL.',502);
      return json({url,provider:d.provider,raw:result});
    }catch(e){
      return error(e instanceof Error?e.message:'Cinema render failed',502);
    }
  }],

  'POST /api/simple-create':[async({body})=>{
    const d=(body||{}) as {referenceUrl?:string;prompt?:string;world?:string;targetMinutes?:number;voice?:string};
    if(!d.referenceUrl?.trim()&&!d.prompt?.trim())return error('Paste a public reference URL or tell Veyr what you want to make.',400);
    const minutes=Math.max(3,Math.min(20,d.targetMinutes||5));
    let referenceTitle='No external reference supplied';
    let accessibleText='';
    if(d.referenceUrl?.trim()){
      try{new URL(d.referenceUrl)}catch{return error('Please provide a valid public YouTube/video/website URL.',400)}
      try{
        const scraped=await ai.scrape({url:d.referenceUrl});
        if(scraped.status<400&&scraped.text.trim()){
          referenceTitle=scraped.title||d.referenceUrl;
          accessibleText=scraped.text.slice(0,18000);
        }else{
          referenceTitle=d.referenceUrl;
        }
      }catch{
        referenceTitle=d.referenceUrl;
      }
    }
    const result=await ai.generate({
      system:veyrSystem,
      prompt:`SIMPLE MODE: act as the complete creative director. Create one finished ORIGINAL cinematic episode package from the user's request and, when supplied, the accessible public reference material.

User request:
${d.prompt?.trim()||'Create an original episode inspired only by the broad topic and production grammar visible in the reference.'}

World / setting mode: ${d.world||'Warhammer 40K'}
Target runtime: ${minutes} minutes
Narrator direction: ${d.voice||'Eric'}

Reference URL: ${d.referenceUrl||'none'}
Reference page title: ${referenceTitle}
Accessible reference text:
${accessibleText||'(The page did not expose usable text. Do not pretend you watched or transcribed the video.)'}

Your job in Simple Mode is to do the technical decisions for the user:
1. Infer only high-level production traits that are actually observable from the accessible page: hook strategy, pacing, chapter rhythm, information density, visual grammar, use of maps/diagrams, humor density, and beginner clarity.
2. Use the reference topic/context only when it is visible in the accessible material. Do not reproduce the source script, dialogue, jokes, shot sequence, thumbnails, artwork, music, creator identity, catchphrases, or voice.
3. Write a complete original episode with 7-10 scenes and enough narration for approximately ${minutes} minutes.
4. Give every scene a cinematic visualPrompt containing shot size, subject/action, environment, lighting, foreground/midground/background depth, lens/camera feel, recurring motif, and continuity from the prior shot.
5. Give every scene a motion field with camera movement, subject movement, environmental movement, transition in/out, and cut rhythm.
6. Give every scene a sound field with ambience, effects, music energy, and a clean narration pocket.
7. Give every scene a dialogue field. Use it for character dialogue, quoted-on-screen dramatic lines, or 'None — narration only' when dialogue would be forced.
8. Keep narration and dialogue distinct. Narration should be directly usable as the voice-over script.
9. Keep claimType exactly CANON / SOURCE, INTERPRETATION, EDITORIAL or SPECULATION. Never invent citations; sourceNeed says what should be verified.
10. visualStyle should be 'Premium cinematic story-film'. Visual prompts must describe original archetypes/compositions and avoid named copyrighted character likenesses or copied creator styles.
11. Produce an accurate YouTube title, thumbnail text, description, and next-episode bridge.

Return the complete episode object only.`,
      schema:episodeSchema,
      thinkingMode:'DEEP',
      maxTokens:7600,
      temperature:.42
    });
    try{
      const episode=JSON.parse(result.text);
      return json({
        episode,
        referenceInfo:{
          url:d.referenceUrl||'',
          title:referenceTitle,
          accessible:Boolean(accessibleText),
          note:accessibleText?'Veyr used only accessible public-page text plus abstract production traits.':'The reference page did not expose usable text; Veyr did not claim to have watched or transcribed it.'
        }
      });
    }catch{return error('Veyr produced an invalid Simple Mode episode package. Please retry.',502);}
  }],

  'POST /api/generate-episode':[async({body})=>{const d=(body||{}) as {prompt?:string;world?:string;targetMinutes?:number;voice?:string;visualStyle?:string;referenceBlend?:unknown;speechProfile?:string;dialogueMode?:string;deliveryPrompt?:string}; if(!d.prompt?.trim())return error('Tell Veyr what episode to create.'); const minutes=Math.max(4,Math.min(20,d.targetMinutes||5)); const result=await ai.generate({system:veyrSystem,prompt:`Create one complete, original GrimForge episode production plan from this request: ${d.prompt}\nWorld: ${d.world||'Warhammer 40K'}\nTarget: ${minutes} minutes\nPreferred narrator direction: ${d.voice||'Eric'}\nSpeech delivery profile: ${d.speechProfile||'Strategic Cartographer'}\nDialogue writing mode: ${d.dialogueMode||'Strategic Chronicle'}\nExtra speech direction: ${d.deliveryPrompt||'Authoritative, human and low-fatigue.'}\nUse those speech settings as abstract performance/writing cues only; do not imitate a real or fictional named voice.\nPreferred visual style: ${d.visualStyle||'2.5D Motion Art'}\nReference-channel blend (high-level traits only): ${JSON.stringify(d.referenceBlend||{})}\nReturn 8 scenes unless the structure genuinely needs 7-10. Total durations should approximately equal ${minutes*60} seconds. Narration should be a usable full draft for the target runtime, not merely scene summaries. Label every scene claimType as exactly CANON / SOURCE, INTERPRETATION, EDITORIAL or SPECULATION. sourceNeed must state what kind of verification is needed and must never invent citations. Visual prompts must ask for original archetypes and compositions, never named copyrighted character likenesses. Titles/thumbnails must be accurate, sharp and not misleading.`,schema:episodeSchema,thinkingMode:'DEEP',maxTokens:6500,temperature:.45}); try{const episode=JSON.parse(result.text); return json({episode});}catch{return error('Veyr produced an invalid episode package. Please retry.',502);}}],
  'POST /api/copilot':[async({body})=>{const d=(body||{}) as {question?:string;episode?:unknown;preferences?:unknown;workMode?:WorkMode}; if(!d.question?.trim())return error('question is required'); const result=await ai.generate({system:veyrSystem,prompt:`Current episode:\n${JSON.stringify(d.episode||{},null,2).slice(0,22000)}\nPreferences:\n${JSON.stringify(d.preferences||{},null,2).slice(0,6000)}\nUser request:\n${d.question}`,thinkingMode:thinking(d.workMode),maxTokens:d.workMode==='Deep'?2200:1300,temperature:.45}); return json({answer:result.text});}],
  'POST /api/remix-episode':[async({body})=>{const d=(body||{}) as {episode?:unknown;selectedRefs?:Record<string,number>;importedRefs?:unknown[];blend?:unknown;world?:string;targetMinutes?:number;speechProfile?:string;dialogueMode?:string;deliveryPrompt?:string}; if(!d.episode)return error('episode is required'); const active=Object.entries(d.selectedRefs||{}).filter(([,weight])=>weight>0); if(!active.length&&!(d.importedRefs||[]).length)return error('Select or import at least one reference.'); const result=await ai.generate({system:veyrSystem,prompt:`Remix the CURRENT GrimForge episode using the selected channels only as high-level production references. Preserve the core thesis and factual/canon boundaries. Do not imitate creator wording, jokes, catchphrases, artwork, identity or voice. Use the weights to influence pacing, chapter structure, humor density, map use, hook strategy, packaging and newcomer clarity. Keep the result original and coherent, not a collage.\n\nSelected built-in channel weights: ${JSON.stringify(d.selectedRefs||{})}\nImported reference profiles and weights: ${JSON.stringify(d.importedRefs||[]).slice(0,9000)}\nComputed production blend: ${JSON.stringify(d.blend||{})}\nWorld: ${d.world||'Warhammer 40K'}\nTarget minutes: ${d.targetMinutes||5}\nSpeech delivery profile: ${d.speechProfile||'Strategic Cartographer'}\nDialogue mode: ${d.dialogueMode||'Strategic Chronicle'}\nExtra speech direction: ${d.deliveryPrompt||'Authoritative and human.'}\n\nCurrent episode:\n${JSON.stringify(d.episode,null,2).slice(0,26000)}\n\nReturn a complete revised episode using the same schema. Narration should remain a usable full draft. Keep claimType values exactly CANON / SOURCE, INTERPRETATION, EDITORIAL or SPECULATION, and do not invent citations.`,schema:episodeSchema,thinkingMode:'DEEP',maxTokens:6500,temperature:.42}); try{return json({episode:JSON.parse(result.text)});}catch{return error('Veyr produced an invalid remixed episode package. Please retry.',502);}}],
  'POST /api/rewrite-speech':[async({body})=>{const d=(body||{}) as {episode?:unknown;speechProfile?:string;dialogueMode?:string;deliveryPrompt?:string;delivery?:unknown}; if(!d.episode)return error('episode is required'); const result=await ai.generate({system:veyrSystem,prompt:`Rewrite only the NARRATION delivery of this existing GrimForge episode. Preserve the thesis, scene IDs, scene order, approximate scene durations, claimType classifications, sourceNeed requirements, visual prompts, motion and factual meaning. Do not add new facts, quotes, citations or claims.\n\nSpeech profile: ${d.speechProfile||'Strategic Cartographer'}\nDialogue writing mode: ${d.dialogueMode||'Strategic Chronicle'}\nExtra direction: ${d.deliveryPrompt||'Authoritative and human.'}\nPlayback-control reference: ${JSON.stringify(d.delivery||{})}\n\nTreat the speech profile as abstract cadence/register/energy guidance only. Never imitate or clone a real person, celebrity, actor, creator or named fictional character voice. Keep the narration natural, intelligible and appropriate to each scene's existing duration.\n\nEpisode:\n${JSON.stringify(d.episode,null,2).slice(0,26000)}\n\nReturn the complete episode using the same schema.`,schema:episodeSchema,thinkingMode:'DEEP',maxTokens:6500,temperature:.38}); try{return json({episode:JSON.parse(result.text)});}catch{return error('Veyr produced an invalid speech-directed episode. Please retry.',502);}}],
  'POST /api/reference-profile':[async({body})=>{const d=(body||{}) as {url?:string}; if(!d.url?.trim())return error('url is required'); try{new URL(d.url)}catch{return error('Please provide a valid public URL.')} const scraped=await ai.scrape({url:d.url}); if(scraped.status>=400||!scraped.text.trim())return error('That public page could not be read.',502); const result=await ai.generate({system:veyrSystem,prompt:`Build a reusable GrimForge REFERENCE PROFILE from this public page using only accessible material.

URL: ${d.url}
Title: ${scraped.title||d.url}
Accessible text:
${scraped.text.slice(0,18000)}

Return JSON with:
- name: concise source/channel/page label
- url: the supplied URL
- summary: 1-2 sentences describing high-level production approach
- traits: one compact string describing pacing, chaptering, hook strategy, humor density, visual grammar, map use, packaging, evidence posture and beginner clarity where observable
- profile: exactly six numbers 0-100 in this order: Depth, Humor, Motion, Pace, Hook, Beginner

If this is a YouTube channel or video page and transcripts/catalog detail are not exposed, do not pretend they are. Infer only from accessible text. Never reproduce scripts, jokes, catchphrases, artwork, creator identity, voice, thumbnails, or distinctive protected expression. This is an abstract production profile for generating original work.`,schema:referenceProfileSchema,thinkingMode:'FAST',maxTokens:1800,temperature:.22}); try{const profile=JSON.parse(result.text); profile.profile=(Array.isArray(profile.profile)?profile.profile:[]).slice(0,6).map((n:unknown)=>Math.max(0,Math.min(100,Number(n)||50))); while(profile.profile.length<6)profile.profile.push(50); return json({profile});}catch{return error('Veyr produced an invalid reference profile. Please retry.',502);}}],
  'POST /api/research-url':[async({body})=>{const d=(body||{}) as {url?:string;question?:string}; if(!d.url?.trim())return error('url is required'); try{new URL(d.url)}catch{return error('Please provide a valid public URL.')} const scraped=await ai.scrape({url:d.url}); if(scraped.status>=400)return error('That public page could not be read.',502); const result=await ai.generate({system:veyrSystem,prompt:`Analyze this public page for GrimForge. ${d.question||'Extract useful high-level production lessons.'}\nIf it is a YouTube page and transcript text is not exposed, state that. Do not reproduce long passages or imitate the creator.\nTitle: ${scraped.title||d.url}\nText:\n${scraped.text.slice(0,18000)}`,thinkingMode:'FAST',maxTokens:1500,temperature:.3}); return json({answer:result.text,url:d.url,title:scraped.title||d.url});}],
  'POST /api/cinematic-direct':[async({body})=>{const d=(body||{}) as {episode?:unknown;world?:string;referenceUrl?:string;intensity?:string}; if(!d.episode)return error('episode is required'); const result=await ai.generate({system:veyrSystem,prompt:`Turn this existing GrimForge episode into a premium cinematic story-film production plan. Use the supplied reference only as high-level production inspiration: dramatic visual storytelling, strong silhouettes, environmental scale, motivated camera movement, scene-to-scene continuity, atmospheric sound design and a clear visual arc. Never copy shots, dialogue, music, characters, artwork, creator identity or a copyrighted visual design.\n\nWorld: ${d.world||'Warhammer 40K'}\nReference URL for production context only: ${d.referenceUrl||'none'}\nCinematic intensity: ${d.intensity||'Epic but readable'}\n\nFor EVERY scene, preserve factual meaning, claimType, sourceNeed, scene ID, order and approximate duration. Rewrite visualPrompt so it contains: shot size, subject/action, environment, lighting, depth layers, recurring visual motif, continuity notes from the previous scene, and an original-franchise-safe design. Rewrite motion so it contains a specific camera move, subject motion, foreground/background motion, transition in, transition out, and approximate cut rhythm. Rewrite sound with ambience, effects, music energy and a clean narration pocket. Keep narration usable and do not add unsupported facts. Build a coherent visual bible across the full episode: consistent architecture/materials, weather, lens language, palette description and recurring army/character silhouettes. Return the complete episode in the same schema.`,schema:episodeSchema,thinkingMode:'DEEP',maxTokens:7000,temperature:.38}); try{return json({episode:JSON.parse(result.text)});}catch{return error('Veyr produced an invalid cinematic pass. Please retry.',502);}}],
  'POST /api/style-preview':[async({body})=>{const d=(body||{}) as {style?:string;world?:string;topic?:string;scene?:string;archetype?:string}; if(!d.style)return error('style is required'); const result=await ai.imageGen({prompt:`Create an ORIGINAL 2.39:1 widescreen premium dark-fantasy cinematic story-film frame. Treat the scene prompt as part of one continuous film: preserve recurring architecture, weather, materials, silhouette language and lighting logic whenever the prompt describes them. Setting mode: ${d.world||'dark science fantasy'}. Episode: ${d.topic||'grimdark history'}. Scene: ${d.scene||'hero establishing shot'}. Production style: ${d.style}. Character archetype: ${d.archetype||'armored chronicler'}, but do not depict any named franchise character, logo, heraldry, copied armor design, copyrighted likeness, creator art style or text. Make the archetype visually readable at thumbnail size. Sophisticated cinematic lighting, detailed materials, strong silhouette, grounded composition, restrained color, no watermark.`,maxOutputBytes:950000}); return json({imageBase64:result.image.data,mimeType:result.image.mimeType});}],
  'POST /api/save-project':[async({body})=>{const d=(body||{}) as {project?:{episode?:{title?:string}}}; if(!d.project)return error('project is required'); const title=d.project.episode?.title||'grimforge-project'; const path=`projects/${safeSlug(title)}-${Date.now()}.json`; const [ok]=await storage.write([{path,content:JSON.stringify(d.project,null,2),contentType:'application/json'}]); if(!ok)return error('Cloud save failed.',500); const [signed]=await storage.url([path]); return json({path,url:signed.url});}],
});
