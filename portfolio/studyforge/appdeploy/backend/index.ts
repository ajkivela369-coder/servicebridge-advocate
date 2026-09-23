import { ai, error, json, router } from '@appdeploy/sdk';

type ReferenceProfile={label?:string;sourceUrl?:string;summary?:string;traits?:string[];formatPatterns?:string[];teachingMoves?:string[];originalityBoundary?:string};
type BuildBody={track?:string;urls?:string;notes?:string;requiredTopics?:string[];manual?:string;verification?:string;referenceProfile?:ReferenceProfile|null};
type QuestionBody={track?:string;guide?:string;requiredTopics?:string[]};
type ReferenceBody={url?:string;label?:string};
type CopilotBody={question?:string;track?:string;guide?:string;questions?:unknown;weakTopics?:unknown;referenceProfile?:ReferenceProfile|null};

const labels:Record<string,string>={'abor-basic':'ABOR Basic Knowledge','abor-chem':'ABOR Chemistry','abor-heme':'ABOR Hematology','abor-immunology':'ABOR Immunology','abor-bloodbank':'ABOR Immunohematology','abor-micro':'ABOR Microbiology','abor-mdx':'ABOR Molecular Diagnostics','abor-andrology':'ABOR Andrology','abor-embryology':'ABOR Embryology','pa-science':'PA Science Refresh'};
const channels:Record<string,string[]>={'abor-basic':['CDC OneLab','ASCP'],'abor-chem':['Ninja Nerd','Medicosis Perfectionalis','Osmosis'],'abor-heme':['Ninja Nerd','Medicosis Perfectionalis'],'abor-immunology':['Ninja Nerd','Osmosis'],'abor-bloodbank':['Blood Bank Guy','ASCP'],'abor-micro':['Ninja Nerd','Osmosis','CDC'],'abor-mdx':['AK Lectures','Ninja Nerd'],'abor-andrology':['Osmosis','Ninja Nerd'],'abor-embryology':['Osmosis','Ninja Nerd'],'pa-science':['Khan Academy','The Organic Chemistry Tutor','Ninja Nerd']};

function cleanUrls(v:string){return v.split(/\r?\n/).map(x=>x.trim()).filter(x=>/^https?:\/\//i.test(x)).slice(0,8)}
function cleanTopics(v:unknown){return Array.isArray(v)?v.filter((x):x is string=>typeof x==='string').map(x=>x.trim()).filter(Boolean).slice(0,50):[]}
function parseJson(text:string){const clean=text.trim().replace(/^```json\s*/i,'').replace(/^```\s*/i,'').replace(/```$/,'').trim();const a=clean.indexOf('{'),b=clean.lastIndexOf('}');if(a<0||b<a)throw new Error('No JSON object');return JSON.parse(clean.slice(a,b+1))}
function profileText(profile?:ReferenceProfile|null){if(!profile)return 'No external teaching-style reference selected.';return `Reference label: ${profile.label||'Imported reference'}\nSummary: ${profile.summary||''}\nTeaching/production traits: ${(profile.traits||[]).join(' | ')}\nFormat patterns: ${(profile.formatPatterns||[]).join(' | ')}\nTeaching moves: ${(profile.teachingMoves||[]).join(' | ')}\nOriginality boundary: ${profile.originalityBoundary||'Use only abstract patterns; do not copy protected expression.'}`}

export const handler=router({
 'GET /api/_healthcheck':[async()=>json({message:'Success'})],
 'POST /api/analyze-reference':[async({body})=>{
   const input=(body||{}) as ReferenceBody;
   if(!input.url?.trim())return error('Paste a public YouTube channel, video, or website URL.',400);
   try{new URL(input.url)}catch{return error('Please provide a valid public URL.',400)}
   const scraped=await ai.scrape({url:input.url});
   if(scraped.status>=400||!scraped.text.trim())return error('That public page could not be read. Try a different public page or use a preset reference.',422);
   const result=await ai.generate({prompt:`Analyze this public reference for a STUDY DESIGN PROFILE, using only content accessible in the scraped page. If this is a YouTube page and transcripts or a full channel catalog are not exposed, clearly limit conclusions to what is actually accessible.

Reference: ${input.label||scraped.title||input.url}
URL: ${input.url}
Accessible text:
${scraped.text.slice(0,18000)}

Return ONLY valid JSON:
{"label":string,"sourceUrl":string,"summary":string,"traits":[string],"formatPatterns":[string],"teachingMoves":[string],"originalityBoundary":string}

Focus on high-level teaching and production patterns such as pacing, use of mechanisms, diagrams, analogies, recap structure, question style, beginner scaffolding, mnemonics, section length, and visual organization. Do NOT reproduce scripts, long wording, distinctive catchphrases, proprietary questions, artwork, or creator identity. The originalityBoundary must explicitly say generated material should be original rather than a clone.`,thinkingMode:'FAST',maxTokens:1800,temperature:.2});
   try{return json({profile:parseJson(result.text)})}catch{return error('Reference analysis returned an invalid format. Try again.',502)}
 }],
 'POST /api/build-guide':[async({body})=>{
   const input=(body||{}) as BuildBody,urls=cleanUrls(input.urls||''),notes=(input.notes||'').trim().slice(0,26000),topics=cleanTopics(input.requiredTopics),label=labels[input.track||'']||'Study topic';
   if(!urls.length&&!notes)return error('Add at least one valid URL or some pasted material.',400);
   const gathered:Array<{id:string;title:string;url:string;status:number;text:string}>=[];
   for(let i=0;i<urls.length;i++){try{const r=await ai.scrape({url:urls[i]});if(r.status<400&&r.text.trim())gathered.push({id:`S${i+1}`,title:r.title||urls[i],url:urls[i],status:r.status,text:r.text.slice(0,12000)})}catch(e){console.warn('scrape failed',urls[i],e)}}
   if(!gathered.length&&!notes)return error('None of the pages could be read. Paste source material directly.',422);
   const src=gathered.map(s=>`SOURCE [${s.id}] ${s.title}\n${s.text}`).join('\n---\n');
   const ch=channels[input.track||'']||['Ninja Nerd'];
   const prompt=`Create a source-grounded visual-first study pack for ${label}. Manual target: ${input.manual||'official materials'}. Verification: ${input.verification||'supplied sources'}.
Mandatory domains: ${topics.join(' | ')}.

REFERENCE DESIGN PROFILE:
${profileText(input.referenceProfile)}

Rules:
- AAB/official factual sources control exam scope and factual content.
- The reference profile controls only abstract presentation/teaching traits. Use it to shape pacing, organization, teaching moves, visual grammar, recap style, and explanation depth.
- Never copy reference wording, scripts, proprietary questions, catchphrases, creator persona, visual assets, or distinctive protected expression. Generate original study material.
- Cite gathered sources [S1] etc; notes are [NOTES]; do not invent hidden manual details; if detail is unavailable say Manual detail needed.
- Every mandatory domain must be explicitly named in the guide.
Return ONLY valid JSON with keys guide, visuals, flashcards.
guide must include Coverage dashboard, domain-by-domain high-yield review, calculations/procedures where supported, common traps, rapid review, manual gaps, and final completeness audit.
visuals must be 10 items with title, subtopic, visualType, content, takeaway; use text-based mini-flowcharts, comparison grids, pattern maps, arrow diagrams, or mnemonic layouts.
flashcards must be 16 items with front, back, visualCue, mnemonic, subtopic, videoQuery, channelHint.
videoQuery should be a specific YouTube search phrase for that card; channelHint should preferentially be one of: ${ch.join(', ')}. Never claim a video was vetted.
SOURCES:
${src||'(none)'}
NOTES:
${notes||'(none)'}`;
   const r=await ai.generate({prompt,thinkingMode:'DEEP',maxTokens:8000,temperature:.18});
   try{const p=parseJson(r.text);return json({guide:p.guide||'',visuals:Array.isArray(p.visuals)?p.visuals:[],flashcards:Array.isArray(p.flashcards)?p.flashcards:[],sources:gathered.map(({id,title,url,status})=>({id,title,url,status}))})}catch(e){console.error('study json parse',e,r.text);return error('Study pack returned an invalid format. Try again.',502)}
 }],
 'POST /api/build-questions':[async({body})=>{
   const input=(body||{}) as QuestionBody,guide=(input.guide||'').trim().slice(0,55000),topics=cleanTopics(input.requiredTopics),label=labels[input.track||'']||'the selected topic',ch=channels[input.track||'']||['Ninja Nerd'];
   if(!guide)return error('Generate a study guide first.',400);
   const prompt=`Using ONLY the guide below, create 14 original multiple-choice questions for ${label}. Spread them across supported required domains: ${topics.join(' | ')}. Never reproduce proprietary exam questions. Return ONLY valid JSON: {"questions":[{"question":string,"choices":[string,string,string,string],"answer":string,"explanation":string,"visualCue":string,"whyOthers":[string,string,string],"subtopic":string,"videoQuery":string,"channelHint":string}]}. answer must exactly match one choice. visualCue should be a memorable pattern/mini diagram/mental image. videoQuery should be a specific YouTube search phrase for the tested concept. channelHint should preferably be one of ${ch.join(', ')}. Never claim the linked search result is vetted.
GUIDE:
${guide}`;
   const r=await ai.generate({prompt,thinkingMode:'DEEP',maxTokens:7600,temperature:.28});
   try{const p=parseJson(r.text);return json({questions:Array.isArray(p.questions)?p.questions:[]})}catch(e){console.error('qbank json parse',e,r.text);return error('QBank returned an invalid format. Try again.',502)}
 }],
 'POST /api/copilot':[async({body})=>{
   const input=(body||{}) as CopilotBody;
   if(!input.question?.trim())return error('Ask the StudyForge copilot a question.',400);
   const label=labels[input.track||'']||'the selected study track';
   const result=await ai.generate({prompt:`You are Forge Tutor, the floating study copilot inside StudyForge. Help the learner study ${label}. Be concise, accurate, practical, and exam-oriented. Never invent an official exam rule or proprietary question. Distinguish official source content from generated teaching aids.

Selected reference design profile:
${profileText(input.referenceProfile)}

Current generated guide:
${(input.guide||'No guide generated yet.').slice(0,22000)}

Current QBank context:
${JSON.stringify(input.questions||[]).slice(0,7000)}

Weak topics:
${JSON.stringify(input.weakTopics||[]).slice(0,3000)}

Learner request:
${input.question}`,thinkingMode:'FAST',maxTokens:1600,temperature:.25});
   return json({answer:result.text});
 }]
});