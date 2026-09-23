import { ai, error, json, router } from '@appdeploy/sdk';

type Beat = { time?: string; action?: string; angle?: string };
type ReferenceProfile = { id?:string; label?:string; sourceUrl?:string; summary?:string; traits?:string[]; formatPatterns?:string[]; weight?:number; originalityBoundary?:string };
type CommentaryBody = { beats?: Beat[]; narrator?: string; narratorDescription?: string; energy?: number; jokes?: number; rights?: string; credit?: string; referenceProfiles?:ReferenceProfile[] };
type CopilotBody={question?:string;beats?:Beat[];script?:string;creatorPack?:unknown;narrator?:string;energy?:number;jokes?:number;referenceProfiles?:ReferenceProfile[];rights?:string};
type ReferenceBody={url?:string;label?:string};

const schema={type:'object',properties:{title:{type:'string'},hook:{type:'string'},script:{type:'string'},captions:{type:'array',items:{type:'string'}},postingCopy:{type:'string'},hashtags:{type:'array',items:{type:'string'}}},required:['title','hook','script','captions','postingCopy','hashtags']};

function parseJson(text:string){const clean=text.trim().replace(/^```json\s*/i,'').replace(/^```\s*/i,'').replace(/```$/,'').trim();const a=clean.indexOf('{'),b=clean.lastIndexOf('}');if(a<0||b<a)throw new Error('No JSON object');return JSON.parse(clean.slice(a,b+1))}
function blendText(list?:ReferenceProfile[]){const refs=Array.isArray(list)?list.slice(0,8):[];if(!refs.length)return 'No external reference blend selected.';return refs.map(r=>`- ${r.label||'Reference'} (${Math.max(5,Math.min(100,r.weight||25))}%): ${(r.traits||[]).join('; ')} | patterns: ${(r.formatPatterns||[]).join('; ')}`).join('\n')}

export const handler = router({
 'GET /api/_healthcheck':[async()=>json({message:'Success'})],

 'POST /api/analyze-reference':[async({body})=>{
   const input=(body||{}) as ReferenceBody;if(!input.url?.trim())return error('Paste a public YouTube channel, video, or website URL.',400);
   try{new URL(input.url)}catch{return error('Please provide a valid public URL.',400)}
   const scraped=await ai.scrape({url:input.url});
   if(scraped.status>=400||!scraped.text.trim())return error('That public page could not be read. Try another public page or use a preset.',422);
   const result=await ai.generate({prompt:`Analyze this public reference only for high-level SHORT-FORM PRODUCTION TRAITS that could inspire original animal/wildlife content.

Reference: ${input.label||scraped.title||input.url}
URL: ${input.url}
Accessible text:
${scraped.text.slice(0,18000)}

Return ONLY valid JSON:
{"label":string,"sourceUrl":string,"summary":string,"traits":[string],"formatPatterns":[string],"originalityBoundary":string}

Focus on pacing, hook structure, information density, visual/narrative rhythm, humor density, caption strategy, educational framing, scene progression, and audience accessibility. If the page does not expose transcripts or a full channel catalog, say so implicitly by limiting the profile to what is accessible. Do NOT reproduce scripts, quotes, catchphrases, creator persona, voice identity, thumbnails, artwork, or distinctive protected expression. The originalityBoundary must require original outputs.`,thinkingMode:'FAST',maxTokens:1700,temperature:.2});
   try{return json({profile:parseJson(result.text)})}catch{return error('Reference analysis returned an invalid format.',502)}
 }],

 'POST /api/write-commentary':[async({body})=>{
   const input=(body||{}) as CommentaryBody;
   const beats=Array.isArray(input.beats)?input.beats.slice(0,20):[];
   if(!beats.length)return error('Add at least one action beat first.',400);
   if(input.rights==='Other / Unknown')return error('Resolve the footage rights basis before generating publication-ready commentary.',400);
   const result=await ai.generate({prompt:`Create an ORIGINAL short-form animal/wildlife commentary package from the user's timed action beats.

Narrator preset: ${input.narrator||'Aussie Wildlife Commentator'}
Preset description: ${input.narratorDescription||'Original observational comedy'}
Energy: ${Math.max(1,Math.min(10,input.energy||7))}/10
Joke density: ${Math.max(1,Math.min(10,input.jokes||6))}/10
Rights basis: ${input.rights||'user confirmed'}
Attribution note: ${input.credit||'none provided'}

REFERENCE BLEND — use only abstract production traits:
${blendText(input.referenceProfiles)}

Action beats:
${beats.map((beat,index)=>`${index+1}. [${beat.time||'00:00'}] action=${beat.action||'unspecified'} | angle=${beat.angle||'none'}`).join('\n')}

Rules:
- Keep the script timestamped and aligned to supplied beats.
- Use the weighted references only for abstract pacing/structure/humor/information-density guidance.
- Write fresh jokes and phrasing. Never imitate, quote, clone, or recreate any real creator, narrator, celebrity, copyrighted character, channel script, catchphrase, thumbnail, or voice.
- Broad delivery directions may shape cadence but never reproduce a named person's persona.
- Do not invent facts about species, injuries, danger, or the clip that are not present in the beats.
- Make the hook strong within the first two seconds.
- Captions should be short on-screen punch lines, not a transcript dump.
- Return only the structured JSON requested.`,schema,thinkingMode:'FAST',maxTokens:2200,temperature:.62});
   try{return json({pack:JSON.parse(result.text)})}catch{return error('The commentary package returned an invalid format. Try again.',502)}
 }],

 'POST /api/copilot':[async({body})=>{
   const input=(body||{}) as CopilotBody;if(!input.question?.trim())return error('Ask Wild Copilot a question.',400);
   const result=await ai.generate({prompt:`You are Wild Copilot, a floating creative assistant inside a rights-aware animal/wildlife short-form studio. Help improve the user's current project while keeping output original and avoiding creator imitation.

Reference blend:
${blendText(input.referenceProfiles)}

Narrator preset: ${input.narrator||'none'}
Energy: ${input.energy||0}/10
Joke density: ${input.jokes||0}/10
Rights status: ${input.rights||'unknown'}

Action beats:
${JSON.stringify(input.beats||[]).slice(0,7000)}

Current script:
${(input.script||'').slice(0,12000)}

Current creator pack:
${JSON.stringify(input.creatorPack||{}).slice(0,5000)}

User request:
${input.question}

Rules: Be practical and concise. Suggest original hooks, captions, structure, cuts, and commentary. Do not imitate a named creator, reproduce source wording, or imply that unseen footage has been visually analyzed.`,thinkingMode:'FAST',maxTokens:1500,temperature:.45});
   return json({answer:result.text});
 }]
});