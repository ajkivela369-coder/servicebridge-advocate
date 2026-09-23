import { useEffect, useMemo, useRef, useState } from 'react';
import { KokoroTTS } from 'kokoro-js';
import { api } from '@appdeploy/client';

type WorkMode = 'Quick' | 'Standard' | 'Deep';
type StudioMode = 'Simple' | 'Pro';
type QualityTier = 'Draft' | 'Cinema' | 'Cinematic Max';
type ClaimType = 'CANON / SOURCE' | 'INTERPRETATION' | 'EDITORIAL' | 'SPECULATION';
type Scene = { id: string; title: string; start: string; duration: number; narration: string; dialogue?: string; claimType: ClaimType; visualPrompt: string; motion: string; sound: string; sourceNeed: string };
type Episode = { title: string; thesis: string; hook: string; world: string; targetMinutes: number; voice: string; visualStyle: string; youtubeTitle: string; thumbnailText: string; description: string; nextBridge: string; scenes: Scene[] };
type VoiceDirection = { name: string; role: string; tone: string; rate: number; pitch: number; bestFor: string; scores: number[] };
type ChannelRef = { name: string; url: string; traits: string; profile: number[]; example?: string };
type ImportedRef = { id:string; name:string; url:string; summary:string; traits:string; profile:number[]; weight:number };
type VisualStyle = { name: string; short: string; blurb: string; archetype: string; motion: string };
type CreatorPreset = { id: string; name: string; style: string; artSource: string; browserVoiceName: string; voiceRate: number; voicePitch: number; voicePause: number; voiceEnergy: number; selectedRefs: Record<string,number>; voiceDirection?: string; voiceLocaleFilter?: string; speechProfile?: string; dialogueMode?: string; deliveryPrompt?: string; kokoroVoice?: string };
type KokoroVoiceMeta = { name?: string; language?: string; gender?: string; traits?: string };
type KokoroVoiceChoice = { id: string; name: string; detail: string };

type ChatMessage = { role: 'user' | 'assistant'; text: string };

const voices: VoiceDirection[] = [
  { name: 'George', role: 'Warm Storyteller', tone: 'measured, humane, dry warmth', rate: .92, pitch: .98, bestFor: 'human-scale tragedy and reflective narration', scores: [9,8,10,8,8,9,9,8,9] },
  { name: 'Daniel', role: 'Steady Broadcaster', tone: 'clear, authoritative, neutral', rate: .94, pitch: .96, bestFor: 'dense lore, maps, chronology and source-heavy episodes', scores: [10,8,7,9,6,9,10,9,8] },
  { name: 'Charlie', role: 'Energetic Analyst', tone: 'younger, alert, controlled energy', rate: 1, pitch: 1.02, bestFor: 'fast explainers, hooks and newcomer-friendly compression', scores: [9,7,8,10,9,8,9,9,7] },
  { name: 'Brian', role: 'Deep Chronicler', tone: 'resonant, weighty, restrained', rate: .88, pitch: .9, bestFor: 'mythic scale and premium cinematic sequences', scores: [8,10,7,7,6,7,8,10,9] },
  { name: 'Eric', role: 'Smooth Historian', tone: 'clean, trustworthy, low-fatigue', rate: .93, pitch: .98, bestFor: 'balanced documentary narration and long listening sessions', scores: [10,8,9,9,7,10,10,9,9] },
  { name: 'Callum', role: 'Dark Archive Voice', tone: 'husky, ominous, controlled', rate: .86, pitch: .9, bestFor: 'short dark passages and Old World atmosphere', scores: [7,10,6,6,7,6,7,9,10] },
];

const deliveryPresets: Record<string, { pause: number; energy: number }> = {
  George: { pause: 280, energy: 38 },
  Daniel: { pause: 185, energy: 46 },
  Charlie: { pause: 105, energy: 78 },
  Brian: { pause: 330, energy: 28 },
  Eric: { pause: 205, energy: 42 },
  Callum: { pause: 360, energy: 24 },
};

const googleCloudVoiceOptions = [
  { name: 'Achird', model: 'Chirp 3 HD', note: 'male · premium HD' },
  { name: 'Charon', model: 'Chirp 3 HD', note: 'male · premium HD' },
  { name: 'Fenrir', model: 'Chirp 3 HD', note: 'male · premium HD' },
  { name: 'Orus', model: 'Chirp 3 HD', note: 'male · premium HD' },
  { name: 'Puck', model: 'Chirp 3 HD', note: 'male · premium HD' },
  { name: 'Schedar', model: 'Chirp 3 HD', note: 'male · premium HD' },
  { name: 'Gemini-TTS', model: 'Google Gemini TTS', note: 'prompt-controlled delivery · premium cloud' },
];

const cloudLocaleOptions = [
  ['en-US','English · United States'],['en-GB','English · United Kingdom'],['en-AU','English · Australia'],['en-IN','English · India'],
  ['fr-FR','French · France'],['fr-CA','French · Canada'],['it-IT','Italian · Italy'],['es-ES','Spanish · Spain'],['es-US','Spanish · United States'],
  ['de-DE','German · Germany'],['pt-BR','Portuguese · Brazil'],['nl-NL','Dutch · Netherlands'],['pl-PL','Polish · Poland'],['ja-JP','Japanese · Japan'],['ko-KR','Korean · South Korea']
] as const;

const voiceCharacterDirections = [
  { name: 'Suave Futurist', note: 'confident · witty · precise · polished', rate: .98, pitch: .94, pause: 150, energy: 74 },
  { name: 'Classic Hero', note: 'steady · noble · clear · reassuring', rate: .90, pitch: .84, pause: 240, energy: 60 },
  { name: 'Laid-back West Coast', note: 'relaxed · conversational · dry humor', rate: .84, pitch: .96, pause: 300, energy: 34 },
  { name: 'Elegant Continental', note: 'measured · articulate · cultured', rate: .89, pitch: 1.03, pause: 270, energy: 42 },
  { name: 'Old World Chronicler', note: 'slow · dark · mythic · low-fatigue', rate: .78, pitch: .78, pause: 420, energy: 24 },
  { name: 'Imperial Officer', note: 'commanding · concise · controlled', rate: .94, pitch: .86, pause: 175, energy: 58 },
];

const speechReferenceProfiles = [
  { name: 'Velvet Aristocrat', source: 'Reference A', note: 'low-register · theatrical · elegant · deliberate emphasis', rate: .84, pitch: .82, pause: 320, energy: 56 },
  { name: 'Rapid Lore Host', source: 'Reference B', note: 'brighter · fast · presenter energy · wide emphasis range', rate: 1.12, pitch: 1.04, pause: 120, energy: 84 },
  { name: 'Cathedral Warlord', source: 'Reference C', note: 'heavy · ominous · forceful · sustained intensity', rate: .76, pitch: .72, pause: 420, energy: 72 },
  { name: 'Strategic Cartographer', source: 'Reference D', note: 'low · restrained · documentary · map-friendly cadence', rate: .86, pitch: .80, pause: 360, energy: 38 },
];

const dialogueModes = [
  { name: 'Cinematic Monologue', note: 'short declarative lines, rhetorical turns, dramatic restraint', sample: 'The fortress still stands. That is not the same thing as victory. Sometimes survival only teaches a system how to endure the next disaster.' },
  { name: 'Rapid Lore Host', note: 'compressed context, quick pivots, punchy explanations', sample: 'Here is the problem. The Imperium survives enormous losses, calls that survival a victory, and immediately starts preparing to do the same thing again.' },
  { name: 'Commander Briefing', note: 'mission-first, concise, authoritative, tactical', sample: 'Situation: the line holds. Cost: reserves are depleted. Assessment: tactical success, strategic position worsening. Recommendation: stop treating endurance as the objective.' },
  { name: 'Dark Sermon', note: 'solemn repetition, ominous imagery, controlled menace', sample: 'The walls rise because the enemy returns. The walls thicken because the fear remains. And one day the fortress discovers it has built a prison around itself.' },
  { name: 'Strategic Chronicle', note: 'historian cadence, causal links, measured pauses', sample: 'The important point is not that the Imperium fails to survive. It is that each successful emergency response can make the next emergency more expensive.' },
  { name: 'Dry-Wit Banter', note: 'understated humor, conversational pivots, no meme overload', sample: 'Technically, the planet survived. The reserves did not, the supply route is on fire, and everyone responsible has promoted survival to a strategic doctrine.' },
  { name: 'Heroic Rally', note: 'clear momentum, conviction, controlled uplift', sample: 'Survival matters. But humanity deserves more than another day purchased at any price. The goal is a tomorrow that is easier to defend than today.' },
  { name: 'Courtly Old World', note: 'formal diction, restrained flourish, chronicle-like rhythm', sample: 'Thus was the realm preserved, though preservation carried its own tithe. For a kingdom may outlast the siege and yet be diminished by the manner of its salvation.' },
];

const kokoroModelId = 'onnx-community/Kokoro-82M-v1.0-ONNX';
const kokoroProfileVoice: Record<string,string> = {
  'Velvet Aristocrat': 'bm_george',
  'Rapid Lore Host': 'af_heart',
  'Cathedral Warlord': 'am_adam',
  'Strategic Cartographer': 'bm_lewis',
};

const channelRefs: ChannelRef[] = [
  { name: 'Luetin09', url: 'https://www.youtube.com/@Luetin09', traits: 'deep structure · chaptering · caveats · authority', profile: [98,18,48,44,70,62] },
  { name: 'WesHammer', url: 'https://www.youtube.com/@weshammer', traits: 'newcomer clarity · compression · strong hooks', profile: [72,55,78,84,90,98] },
  { name: 'Arbitor Ian', url: 'https://www.youtube.com/@arbitorian', traits: 'historical framing · research-forward explanation', profile: [92,35,52,58,76,78] },
  { name: 'Majorkill', url: 'https://www.youtube.com/@majorkill', traits: 'compact opinion · punchy premise · fast delivery', profile: [62,84,76,92,94,86] },
  { name: 'PancreasNoWork', url: 'https://www.youtube.com/@PancreasNoWork', traits: 'cross-setting comparison · personality · humor', profile: [70,95,62,82,88,84] },
  { name: 'KrakDuk', url: 'https://www.youtube.com/@KrakDuk', traits: 'rapid visual comedy · compressed lore · aggressive pace', profile: [58,96,95,98,94,82] },
  { name: 'Book of Choyer', url: 'https://www.youtube.com/@TheBookofChoyer', traits: 'Old World chronicle · causal history · atmospheric pacing', profile: [91,12,76,54,72,68] },
  { name: 'Tales From The Void', url: 'https://www.youtube.com/@TalesFromTheVoid', traits: 'dark atmosphere · compact narration · cinematic mood', profile: [74,24,91,70,82,72] },
  { name: 'NightHaunter', url: 'https://www.youtube.com/@NightHaunter', traits: 'dark character focus · dramatic framing · concise lore', profile: [72,35,83,76,86,78] },
  { name: 'Adeptus Ridiculous', url: 'https://www.youtube.com/@Adeptusridiculous', traits: 'conversational accessibility · humor · memorable framing', profile: [58,96,54,78,88,94] },
  { name: 'Wizards and Warriors', url: 'https://www.youtube.com/@WizardsandWarriors', traits: 'map-led chronology · campaign clarity · historical structure', profile: [88,12,90,64,70,80] },
];

const visualStyles: VisualStyle[] = [
  { name: 'Premium 3D Character', short: '3D', blurb: 'Hero-scale dimensional character, volumetric light, armor detail, restrained camera orbit.', archetype: 'armored', motion: 'slow orbit + depth + volumetric haze' },
  { name: '2.5D Motion Art', short: '2.5D', blurb: 'Layered painted character art with parallax, drifting atmosphere and selective movement.', archetype: 'commander', motion: 'parallax + camera push + particles' },
  { name: 'Tactical Holo-Map', short: 'Map', blurb: 'Readable fronts, routes, worlds and threat rings with military-map motion.', archetype: 'strategist', motion: 'map travel + routes + overlays' },
  { name: 'Archive Dossier', short: 'Dossier', blurb: 'Inquisitorial-style archive mood using an original robed investigator archetype and source cards.', archetype: 'scholar', motion: 'page depth + evidence highlights' },
  { name: 'Old World Manuscript', short: 'Old World', blurb: 'Original armored cavalry and dark-medieval illustration with parchment, ink and candlelight.', archetype: 'cavalry', motion: 'ink travel + layered tableau' },
  { name: 'Necromantic Chronicle', short: 'Dark Magic', blurb: 'Original occult scholar silhouette, ruined architecture and eerie atmospheric motion.', archetype: 'necromancer', motion: 'fog layers + rune drift + slow dolly' },
];

const fallbackEpisode: Episode = {
  title: 'Survival Is Not Victory',
  thesis: 'The Imperium can survive crisis after crisis without converting survival into strategic victory.',
  hook: 'What if the greatest proof of Imperial strength is also evidence that it is trapped?',
  world: 'Warhammer 40K', targetMinutes: 5, voice: 'George', visualStyle: '2.5D Motion Art',
  youtubeTitle: 'Why the Imperium Never Truly Wins | Warhammer 40K', thumbnailText: 'SURVIVING ≠ WINNING',
  description: 'A five-minute GrimForge analysis separating canon anchors from editorial interpretation.', nextBridge: 'If survival is not victory, who is actually steering the Imperium?',
  scenes: [
    ['Cold Open','00:00',30,'There is a comforting lie at the heart of the Imperium: that survival is the same thing as victory.','EDITORIAL','An original armored void commander before a damaged fortress, cinematic silhouette.','Slow push-in, drifting ash.','Low room tone, one distant impact.','No source needed: clearly editorial.'],
    ['Orientation','00:30',36,'Across the Imperium, mortal armies are drawn from innumerable worlds while wars rage across the galaxy.','CANON / SOURCE','Original star map with troop-source nodes feeding multiple fronts.','Map routes illuminate in sequence.','Restrained mechanical pulse.','Attach current official Astra Militarum source.'],
    ['Threat Scale','01:06',42,'The enemies are real. The setting surrounds humanity with threats capable of destroying worlds and systems.','CANON / SOURCE','Three abstract threat signatures around a human light, no copied faction art.','Threat rings close inward.','Three short tonal motifs.','Attach current official overview sources.'],
    ['The Loop','01:48',42,'Under those conditions, the Imperium is rewarded for whatever gets it through the day, even when the cost is pushed into tomorrow.','INTERPRETATION','Circular crisis-to-sacrifice-to-survival machine diagram.','Loop accelerates once, then locks.','Mechanical rhythm becomes circular.','Label as interpretation.'],
    ['Strategic Cost','02:30',42,'A world can be saved while the larger strategic position becomes poorer, thinner and more desperate.','INTERPRETATION','One world brightens while supply corridors and reserves dim.','Light transfers from reserves to one world.','Music thins after the word saved.','Label as interpretation.'],
    ['Double Edge','03:12',42,'Institutions can be both understandable survival mechanisms and sources of long-term rigidity.','EDITORIAL','Split card: SURVIVAL FUNCTION versus LONG-TERM COST.','Measured card reveal.','Archive clicks, no trailer boom.','Editorial model.'],
    ['Payoff','03:54',42,'Eventually survival stops being a temporary measure and becomes the definition of success.','INTERPRETATION','Fortress thickens its walls while interior living space narrows.','Camera tracks inward as walls close.','Human ambience under machinery.','Interpretation.'],
    ['Bridge','04:36',24,'A civilization can become very good at not dying without becoming good at living. So who is actually steering it?','EDITORIAL','Fortress becomes a node in a vast command web.','Pull back into network.','Pulse stops; sustained tone.','Editorial bridge.'],
  ].map((x,i)=>({ id:`scene-${i+1}`, title:x[0] as string, start:x[1] as string, duration:x[2] as number, narration:x[3] as string, claimType:x[4] as ClaimType, visualPrompt:x[5] as string, motion:x[6] as string, sound:x[7] as string, sourceNeed:x[8] as string }))
};

function App() {
  const [episode, setEpisode] = useState<Episode>(fallbackEpisode);
  const [studioMode,setStudioMode]=useState<StudioMode>('Simple');
  const [simpleReferenceUrl,setSimpleReferenceUrl]=useState('');
  const [qualityTier,setQualityTier]=useState<QualityTier>('Cinema');
  const [sceneVideos,setSceneVideos]=useState<Record<string,string>>({});
  const [cinemaStatus,setCinemaStatus]=useState<{configured:boolean;providers?:Array<{id:string;configured:boolean}>;error?:string}>({configured:false});
  const [simpleReferenceNote,setSimpleReferenceNote]=useState('');
  const [simpleStep,setSimpleStep]=useState('');
  const [prompt, setPrompt] = useState('Make a 5-minute episode about why survival is not the same as victory for the Imperium.');
  const [world, setWorld] = useState('Warhammer 40K');
  const [length, setLength] = useState(5);
  const [voice, setVoice] = useState('George');
  const [style, setStyle] = useState('2.5D Motion Art');
  const [workMode, setWorkMode] = useState<WorkMode>('Deep');
  const [busy, setBusy] = useState('');
  const [notice, setNotice] = useState('');
  const [manualOpen, setManualOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('YouTube Mixer');
  const [selectedRefs, setSelectedRefs] = useState<Record<string,number>>({ Luetin09: 30, WesHammer: 25, 'Arbitor Ian': 25, 'Book of Choyer': 20 });
  const [mixerDirty, setMixerDirty] = useState(true);
  const [mixerApplied, setMixerApplied] = useState(false);
  const [browserVoices, setBrowserVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [browserVoiceName, setBrowserVoiceName] = useState('Auto');
  const [voiceRate, setVoiceRate] = useState(.92);
  const [voicePitch, setVoicePitch] = useState(.98);
  const [voicePause, setVoicePause] = useState(280);
  const [voiceEnergy, setVoiceEnergy] = useState(38);
  const [voiceLocaleFilter, setVoiceLocaleFilter] = useState('all');
  const [voiceDirection, setVoiceDirection] = useState('Custom');
  const [speechProfile, setSpeechProfile] = useState('Strategic Cartographer');
  const [dialogueMode, setDialogueMode] = useState('Strategic Chronicle');
  const [deliveryPrompt, setDeliveryPrompt] = useState('Authoritative and human. Avoid trailer-voice exaggeration. Let important ideas breathe.');
  const [kokoroStatus, setKokoroStatus] = useState('Not loaded · first use downloads the free model');
  const [kokoroVoice, setKokoroVoice] = useState('bm_george');
  const [kokoroVoices, setKokoroVoices] = useState<KokoroVoiceChoice[]>([]);
  const [kokoroAudioUrl, setKokoroAudioUrl] = useState('');
  const [kokoroOutputLabel, setKokoroOutputLabel] = useState('');
  const [artSource, setArtSource] = useState('AI Generated Original');
  const [sceneImages, setSceneImages] = useState<Record<string,string>>({});
  const [previewIndex, setPreviewIndex] = useState(0);
  const [previewPlaying, setPreviewPlaying] = useState(false);
  const [mp4Url, setMp4Url] = useState('');
  const [narrationUrl, setNarrationUrl] = useState('');
  const [copilotOpen, setCopilotOpen] = useState(false);
  const [copilotInput, setCopilotInput] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([{role:'assistant',text:'I am Archivist Veyr. Tell me what you want to make, or hit “Create Full Episode” and I will operate the studio for you.'}]);
  const [researchUrl, setResearchUrl] = useState('');
  const [importedRefs,setImportedRefs]=useState<ImportedRef[]>([]);
  const [compareStyles, setCompareStyles] = useState(false);
  const [cinematicReference] = useState('https://youtu.be/Fiu8H2TWZ-w');
  const [cinematicIntensity, setCinematicIntensity] = useState('Epic but readable');
  const [cinematicMode, setCinematicMode] = useState(false);
  const [storyboardProgress, setStoryboardProgress] = useState('');
  const [presetName, setPresetName] = useState('My GrimForge preset');
  const [favoritePresets, setFavoritePresets] = useState<CreatorPreset[]>(()=>{
    try { return JSON.parse(localStorage.getItem('grimforge-presets')||'[]') as CreatorPreset[]; }
    catch { return []; }
  });
  const previewTimer = useRef<number | null>(null);
  const speechRunRef = useRef(0);
  const kokoroRef = useRef<KokoroTTS | null>(null);

  useEffect(()=>{
    const load=()=>setBrowserVoices(window.speechSynthesis?.getVoices?.()??[]); load();
    if ('speechSynthesis' in window) window.speechSynthesis.onvoiceschanged=load;
    return()=>{ if ('speechSynthesis' in window) window.speechSynthesis.onvoiceschanged=null; };
  },[]);

  useEffect(()=>{
    const preset=voices.find((item)=>item.name===voice)??voices[0];
    const delivery=deliveryPresets[preset.name]??{pause:220,energy:45};
    setVoiceRate(preset.rate);
    setVoicePitch(preset.pitch);
    setVoicePause(delivery.pause);
    setVoiceEnergy(delivery.energy);
  },[voice]);

  useEffect(()=>{
    if (!previewPlaying) return;
    const scene=episode.scenes[previewIndex];
    if (!scene) return;
    speak(scene.narration);
    previewTimer.current=window.setTimeout(()=>{
      if (previewIndex < episode.scenes.length-1) setPreviewIndex((v)=>v+1); else setPreviewPlaying(false);
    },Math.max(4000,scene.duration*1000));
    return()=>{ if (previewTimer.current) window.clearTimeout(previewTimer.current); };
  },[previewPlaying,previewIndex]);

  const selectedVoice=voices.find((v)=>v.name===voice)??voices[0];
  const selectedStyle=visualStyles.find((v)=>v.name===style)??visualStyles[0];
  const selectedDialogueMode=dialogueModes.find((item)=>item.name===dialogueMode)??dialogueModes[0];
  const googleBrowserVoices=useMemo(()=>browserVoices.filter((v)=>/google|microsoft|natural|online/i.test(v.name)),[browserVoices]);
  const detectedGoogleLocales=useMemo(()=>Array.from(new Set(googleBrowserVoices.map((v)=>v.lang))).sort(),[googleBrowserVoices]);
  const filteredGoogleVoices=useMemo(()=>voiceLocaleFilter==='all'?googleBrowserVoices:googleBrowserVoices.filter((v)=>v.lang===voiceLocaleFilter),[googleBrowserVoices,voiceLocaleFilter]);
  const refBlend=useMemo(()=>{
    const builtin=channelRefs.filter((c)=>(selectedRefs[c.name]??0)>0).map(c=>({profile:c.profile,weight:selectedRefs[c.name]??0}));
    const imported=importedRefs.filter(r=>r.weight>0).map(r=>({profile:r.profile,weight:r.weight}));
    const active=[...builtin,...imported];
    const total=Math.max(1,active.reduce((s,c)=>s+c.weight,0));
    return ['Depth','Humor','Motion','Pace','Hook','Beginner'].map((label,i)=>({label,value:Math.round(active.reduce((s,c)=>s+(c.profile[i]??50)*c.weight,0)/total)}));
  },[selectedRefs,importedRefs]);

  const bestBrowserVoice=()=>{
    const candidates=filteredGoogleVoices.length?filteredGoogleVoices:googleBrowserVoices;
    const score=(v:SpeechSynthesisVoice)=>{ const n=v.name.toLowerCase(); let s=v.lang.toLowerCase().startsWith('en-us')?6:0; if(/natural|neural|premium|enhanced|online/.test(n))s+=40; if(!v.localService)s+=3; return s; };
    return [...candidates].sort((a,b)=>score(b)-score(a))[0];
  };

  const applyVoiceDirection=(name:string)=>{
    const preset=voiceCharacterDirections.find((item)=>item.name===name);
    setVoiceDirection(name);
    if(!preset)return;
    setVoiceRate(preset.rate);
    setVoicePitch(preset.pitch);
    setVoicePause(preset.pause);
    setVoiceEnergy(preset.energy);
  };

  const applySpeechReference=(name:string)=>{
    const preset=speechReferenceProfiles.find((item)=>item.name===name);
    setSpeechProfile(name);
    if(!preset)return;
    const preferred=kokoroProfileVoice[name];
    if(preferred&&kokoroVoices.some((item)=>item.id===preferred))setKokoroVoice(preferred);
    setVoiceDirection(name);
    setVoiceRate(preset.rate);
    setVoicePitch(preset.pitch);
    setVoicePause(preset.pause);
    setVoiceEnergy(preset.energy);
  };

  const stopSpeaking=()=>{
    speechRunRef.current+=1;
    window.speechSynthesis?.cancel();
  };

  const speak=(text:string,raw=false,forced?:{rate:number;pitch:number;pause:number;energy:number})=>{
    if (narrationUrl) return;
    if (!('speechSynthesis' in window)) return;
    stopSpeaking();
    const runId=speechRunRef.current;
    const chosen=browserVoiceName==='Auto'?bestBrowserVoice():googleBrowserVoices.find((item)=>item.name===browserVoiceName)??bestBrowserVoice();
    if(!chosen){setNotice('No Google browser voice is exposed by this browser. Chrome voice availability varies by device; use an uploaded narration track until Google Cloud TTS is connected.');return;}
    const settings=forced??{rate:voiceRate,pitch:voicePitch,pause:voicePause,energy:voiceEnergy};
    const sentences=text.match(/[^.!?]+[.!?]+|[^.!?]+$/g)?.map((item)=>item.trim()).filter(Boolean)??[text];
    const play=(index:number)=>{
      if(runId!==speechRunRef.current||index>=sentences.length)return;
      const utterance=new SpeechSynthesisUtterance(sentences[index]);
      const cadence=((index%3)-1)*(settings.energy/100)*.10;
      const pitchMotion=(index%2?1:-1)*(settings.energy/100)*.07;
      utterance.rate=raw?1:Math.max(.5,Math.min(1.6,settings.rate+cadence));
      utterance.pitch=raw?1:Math.max(.5,Math.min(1.5,settings.pitch+pitchMotion));
      utterance.volume=raw?1:Math.max(.72,Math.min(1,.82+(settings.energy/100)*.18));
      utterance.voice=chosen;
      utterance.lang=chosen.lang;
      utterance.onend=()=>window.setTimeout(()=>play(index+1),raw?0:settings.pause+(sentences[index].endsWith('?')?120:0));
      utterance.onerror=()=>{ if(runId===speechRunRef.current)setNotice('Browser voice playback stopped. Try another Google voice or locale.'); };
      window.speechSynthesis.speak(utterance);
    };
    play(0);
  };

  const loadKokoro=async()=>{
    if(kokoroRef.current)return kokoroRef.current;
    setBusy('Loading free Kokoro neural voice model…');
    setKokoroStatus('Downloading model · first load may take a while');
    try{
      let tts:KokoroTTS;
      try{
        tts=await KokoroTTS.from_pretrained(kokoroModelId,{dtype:'fp32',device:'webgpu'});
        setKokoroStatus('Ready · WebGPU acceleration');
      }catch{
        setKokoroStatus('WebGPU unavailable · loading WASM fallback');
        tts=await KokoroTTS.from_pretrained(kokoroModelId,{dtype:'q8',device:'wasm'});
        setKokoroStatus('Ready · WASM fallback');
      }
      kokoroRef.current=tts;
      const catalog=tts.voices as Record<string,KokoroVoiceMeta>;
      const choices=Object.entries(catalog).map(([id,meta])=>({id,name:meta.name||id,detail:[meta.language,meta.gender,meta.traits].filter(Boolean).join(' · ')}));
      setKokoroVoices(choices);
      const preferred=kokoroProfileVoice[speechProfile];
      if(preferred&&catalog[preferred])setKokoroVoice(preferred); else if(choices[0])setKokoroVoice(choices[0].id);
      return tts;
    }catch(err){
      const message=err instanceof Error?err.message:'Local neural engine could not load.';
      setKokoroStatus('Load failed · browser voice fallback still available');
      setNotice(`Kokoro could not load: ${message}`);
      return null;
    }finally{
      setBusy('');
    }
  };

  const generateKokoroWav=async(text:string,label:string,useAsNarration=false)=>{
    if(!text.trim())return;
    const tts=await loadKokoro();
    if(!tts)return;
    setBusy(`Generating ${label} locally with Kokoro…`);
    try{
      const audio=await tts.generate(text,{voice:kokoroVoice,speed:Math.max(.5,Math.min(2,voiceRate))});
      const url=URL.createObjectURL(audio.toBlob());
      setKokoroAudioUrl(url);
      setKokoroOutputLabel(label);
      if(useAsNarration)setNarrationUrl(url);
      setNotice(`${label} generated locally. No paid TTS API was used.`);
    }catch(err){
      const message=err instanceof Error?err.message:'Generation failed.';
      setNotice(`Kokoro generation failed: ${message}`);
    }finally{
      setBusy('');
    }
  };

  const previewSelectedDelivery=()=>generateKokoroWav(selectedDialogueMode.sample,'speech preview');

  const refreshCinemaStatus=async()=>{
    try{const {data}=await api.get('/api/cinema/status');setCinemaStatus(data);}
    catch{setCinemaStatus({configured:false});}
  };

  const createSimpleEpisode=async()=>{
    if((!simpleReferenceUrl.trim()&&!prompt.trim())||busy)return;
    setBusy('Veyr is building the complete cinematic episode…');
    setSimpleStep('Analyzing reference + writing episode');
    setNotice('');
    setSimpleReferenceNote('');
    setStoryboardProgress('');
    try{
      const {data}=await api.post('/api/simple-create',{
        referenceUrl:simpleReferenceUrl.trim(),
        prompt,
        world,
        targetMinutes:length,
        voice
      });
      const nextEpisode=data.episode as Episode;
      setEpisode(nextEpisode);
      setVoice(nextEpisode.voice||voice);
      setStyle('Premium 3D Character');
      setCinematicMode(true);
      setPreviewIndex(0);
      setPreviewPlaying(false);
      setSceneImages({});
      setSceneVideos({});
      setSimpleReferenceNote(data.referenceInfo?.note||'Reference processing complete.');
      const generated:Record<string,string>={};
      const generatedVideo:Record<string,string>={};
      const provider=qualityTier==='Cinematic Max'?'ltx2':'wan22';
      const wantsMotion=qualityTier!=='Draft';
      const providerReady=Boolean(cinemaStatus.providers?.find((item)=>item.id===provider&&item.configured));

      for(let i=0;i<nextEpisode.scenes.length;i+=1){
        const scene=nextEpisode.scenes[i];
        setSimpleStep(`Creating scene ${i+1}/${nextEpisode.scenes.length} · ${qualityTier}`);
        setStoryboardProgress(`Scene ${i+1} of ${nextEpisode.scenes.length} · ${scene.title}`);
        let imageUrl='';
        try{
          const art=await api.post('/api/style-preview',{
            style:'Premium cinematic story-film',
            world:nextEpisode.world||world,
            topic:nextEpisode.title,
            scene:scene.visualPrompt,
            archetype:'original armored cinematic chronicler'
          });
          imageUrl=`data:${art.data.mimeType};base64,${art.data.imageBase64}`;
          generated[scene.id]=imageUrl;
          setSceneImages({...generated});
        }catch{
          // Keep the written scene even if the still frame fails.
        }

        if(wantsMotion&&providerReady){
          setSimpleStep(`Rendering motion shot ${i+1}/${nextEpisode.scenes.length} with ${provider==='ltx2'?'LTX Cinematic Max':'Wan Cinema'}`);
          try{
            const rendered=await api.post('/api/cinema/render-scene',{
              provider,
              prompt:`${scene.visualPrompt}. Motion: ${scene.motion}. Sound intent: ${scene.sound}. Preserve continuity with the approved character and set bibles. Original composition only.`,
              imageUrl:imageUrl||undefined,
              seconds:Math.max(4,Math.min(10,scene.duration||6)),
              fps:qualityTier==='Cinematic Max'?30:24,
              width:qualityTier==='Cinematic Max'?1920:1280,
              height:qualityTier==='Cinematic Max'?1080:720,
              metadata:{sceneId:scene.id,title:scene.title,qualityTier}
            });
            if(rendered.data?.url){
              generatedVideo[scene.id]=rendered.data.url;
              setSceneVideos({...generatedVideo});
            }
          }catch{
            // Motion providers are optional. Fall back to the generated still/animatic rather than faking a clip.
          }
        }
      }
      setSimpleStep('Episode ready');
      const motionCount=Object.keys(generatedVideo).length;
      setNotice(`Veyr created “${nextEpisode.title}” with ${nextEpisode.scenes.length} directed scenes, full narration/dialogue, cinematography, sound direction, ${Object.keys(generated).length} generated scene image${Object.keys(generated).length===1?'':'s'} and ${motionCount} rendered motion clip${motionCount===1?'':'s'}. ${wantsMotion&&!providerReady?'The Cinema Bridge is not connected for this quality tier, so GrimForge kept the honest animatic fallback.':''}`);
      window.setTimeout(()=>document.getElementById('preview')?.scrollIntoView({behavior:'smooth'}),100);
    }catch(err){
      const e=err as {response?:{data?:{error?:string}},message?:string};
      setNotice(e.response?.data?.error||e.message||'Simple Mode episode generation failed.');
      setSimpleStep('');
    }finally{
      setStoryboardProgress('');
      setBusy('');
    }
  };

  const createEpisode=async()=>{
    if(!prompt.trim()||busy)return; setBusy('Veyr is creating the full episode…'); setNotice('');
    try{
      const {data}=await api.post('/api/generate-episode',{prompt,world,targetMinutes:length,voice,visualStyle:style,referenceBlend:{channels:selectedRefs,imported:importedRefs},speechProfile,dialogueMode,deliveryPrompt});
      setEpisode(data.episode); setVoice(data.episode.voice||voice); setStyle(data.episode.visualStyle||style); setPreviewIndex(0); setSceneImages({}); setNotice('Episode created. Watch it now, or open Edit manually to tune every scene.');
    }catch(err){ const e=err as {response?:{data?:{error?:string}},message?:string}; setNotice(e.response?.data?.error||e.message||'Episode generation failed.'); }
    finally{setBusy('');}
  };

  const askVeyr=async(q:string)=>{
    if(!q.trim()||busy)return; setMessages((m)=>[...m,{role:'user',text:q}]); setCopilotInput(''); setBusy('Veyr is reviewing your episode…');
    try{ const {data}=await api.post('/api/copilot',{question:q,episode,preferences:{world,length,voice,style,selectedRefs,importedRefs,referenceBlend:refBlend,speechProfile,dialogueMode,deliveryPrompt,voiceDirection,voiceRate,voicePitch,voicePause,voiceEnergy},workMode}); setMessages((m)=>[...m,{role:'assistant',text:data.answer}]); }
    catch{ setMessages((m)=>[...m,{role:'assistant',text:'I could not complete that request. Try again or use the manual controls.'}]); }
    finally{setBusy('');}
  };

  const generateSceneArt=async(scene:Scene)=>{
    if(busy)return; setBusy(`Generating original ${style} art for “${scene.title}”…`);
    try{ const {data}=await api.post('/api/style-preview',{style,world,topic:episode.title,scene:scene.visualPrompt,archetype:selectedStyle.archetype}); setSceneImages((m)=>({...m,[scene.id]:`data:${data.mimeType};base64,${data.imageBase64}`})); }
    catch{setNotice('Art generation failed. You can retry or switch asset source.');} finally{setBusy('');}
  };

  const applyCinematicPass=async()=>{
    if(busy)return;
    setBusy('Veyr is directing the cinematic cut…');
    setNotice('');
    try{
      const {data}=await api.post('/api/cinematic-direct',{episode,world,referenceUrl:cinematicReference,intensity:cinematicIntensity});
      setEpisode(data.episode);
      setStyle('Premium 3D Character');
      setCinematicMode(true);
      setSceneImages({});
      setPreviewIndex(0);
      setNotice('Cinematic cut applied. Every scene now has continuity-aware shot design, camera motion, transitions and sound direction.');
    }catch(err){const e=err as {response?:{data?:{error?:string}},message?:string};setNotice(e.response?.data?.error||e.message||'The cinematic pass could not be applied.');}
    finally{setBusy('');}
  };

  const generateFullStoryboard=async()=>{
    if(busy||!episode.scenes.length)return;
    setBusy('Forging the cinematic storyboard…');
    setNotice('');
    try{
      const generated:Record<string,string>={};
      for(let i=0;i<episode.scenes.length;i+=1){
        const scene=episode.scenes[i];
        setStoryboardProgress(`Shot ${i+1} of ${episode.scenes.length} · ${scene.title}`);
        const {data}=await api.post('/api/style-preview',{style:cinematicMode?'Premium cinematic story-film':style,world,topic:episode.title,scene:scene.visualPrompt,archetype:selectedStyle.archetype});
        generated[scene.id]=`data:${data.mimeType};base64,${data.imageBase64}`;
        setSceneImages({...generated});
      }
      setNotice(`Storyboard complete: ${episode.scenes.length} cinematic frames are loaded into the episode player.`);
    }catch{setNotice('Storyboard generation stopped early. The completed scene frames are still available; retry to continue.');}
    finally{setStoryboardProgress('');setBusy('');}
  };

  const analyzeUrl=async()=>{
    if(!researchUrl.trim()||busy)return; setBusy('Veyr is building a reusable reference profile…');
    try{
      const {data}=await api.post('/api/reference-profile',{url:researchUrl});
      const p=data.profile as Omit<ImportedRef,'id'|'weight'>;
      const next:ImportedRef={...p,id:`ref-${Date.now()}`,weight:30};
      setImportedRefs(current=>[...current,next].slice(-8));
      setMixerDirty(true);setMixerApplied(false);
      setMessages((m)=>[...m,{role:'assistant',text:`Reference Lab added “${next.name}”. I learned only high-level production traits: ${next.traits}. It is now a weighted source in the YouTube Mixer.`}]);
      setCopilotOpen(true);
      setNotice('Reference profile added to the production mixer. Adjust its weight in Reference Lab, then apply the mix.');
    }catch{setNotice('That public URL could not be turned into a reference profile. Try another public page.');}
    finally{setBusy('');}
  };
  const updateImportedWeight=(id:string,weight:number)=>{setImportedRefs(current=>current.map(r=>r.id===id?{...r,weight}:r));setMixerDirty(true);setMixerApplied(false);};
  const removeImportedRef=(id:string)=>{setImportedRefs(current=>current.filter(r=>r.id!==id));setMixerDirty(true);setMixerApplied(false);};

  const applyMixer=async()=>{
    if(busy)return;
    const active=Object.entries(selectedRefs).filter(([,weight])=>weight>0);
    if(!active.length&&!importedRefs.some(r=>r.weight>0)){setNotice('Select or import at least one reference before applying the mixer.');return;}
    setBusy('Veyr is applying the YouTube production mix to the current episode…');
    setNotice('');
    try{
      const {data}=await api.post('/api/remix-episode',{episode,selectedRefs,importedRefs,blend:refBlend,world,targetMinutes:length,speechProfile,dialogueMode,deliveryPrompt});
      setEpisode(data.episode);
      setMixerDirty(false);
      setMixerApplied(true);
      setPreviewIndex(0);
      setNotice('Reference mix applied to the episode. The script/scene plan was remixed using high-level traits only.');
    }catch(err){const e=err as {response?:{data?:{error?:string}},message?:string};setNotice(e.response?.data?.error||e.message||'The reference mix could not be applied.');}
    finally{setBusy('');}
  };

  const applySpeechStyle=async()=>{
    if(busy)return;
    setBusy('Veyr is directing the episode dialogue…');
    setNotice('');
    try{
      const {data}=await api.post('/api/rewrite-speech',{episode,speechProfile,dialogueMode,deliveryPrompt,delivery:{rate:voiceRate,pitch:voicePitch,pause:voicePause,energy:voiceEnergy}});
      setEpisode(data.episode);
      setPreviewIndex(0);
      setNotice(`Applied ${speechProfile} + ${dialogueMode} to the episode narration.`);
    }catch(err){const e=err as {response?:{data?:{error?:string}},message?:string};setNotice(e.response?.data?.error||e.message||'Speech direction could not be applied.');}
    finally{setBusy('');}
  };

  const saveCloud=async()=>{
    if(busy)return; setBusy('Saving GrimForge project to cloud…');
    try{const {data}=await api.post('/api/save-project',{project:{episode,world,length,voice,style,selectedRefs,importedRefs,referenceBlend:refBlend,artSource,speechProfile,dialogueMode,deliveryPrompt,voiceDirection,voiceRate,voicePitch,voicePause,voiceEnergy,kokoroVoice}}); setNotice(`Cloud project saved: ${data.path}`);}catch{setNotice('Cloud save failed.');}finally{setBusy('');}
  };

  const saveFavoritePreset=()=>{
    const name=presetName.trim()||`Preset ${favoritePresets.length+1}`;
    const preset:CreatorPreset={id:`preset-${Date.now()}`,name,style,artSource,browserVoiceName,voiceRate,voicePitch,voicePause,voiceEnergy,selectedRefs:{...selectedRefs},voiceDirection,voiceLocaleFilter,speechProfile,dialogueMode,deliveryPrompt,kokoroVoice};
    const next=[...favoritePresets.filter((item)=>item.name!==name),preset].slice(-8);
    setFavoritePresets(next);
    localStorage.setItem('grimforge-presets',JSON.stringify(next));
    setPresetName(name);
    setNotice(`Saved creator preset “${name}”.`);
  };

  const applyFavoritePreset=(preset:CreatorPreset)=>{
    setStyle(preset.style);
    setArtSource(preset.artSource);
    setBrowserVoiceName(preset.browserVoiceName==='Auto'||googleBrowserVoices.some((item)=>item.name===preset.browserVoiceName)?preset.browserVoiceName:'Auto');
    setVoiceRate(preset.voiceRate);
    setVoicePitch(preset.voicePitch);
    setVoicePause(preset.voicePause);
    setVoiceEnergy(preset.voiceEnergy);
    setVoiceDirection(preset.voiceDirection||'Custom');
    setVoiceLocaleFilter(preset.voiceLocaleFilter||'all');
    setSpeechProfile(preset.speechProfile||'Strategic Cartographer');
    setDialogueMode(preset.dialogueMode||'Strategic Chronicle');
    setDeliveryPrompt(preset.deliveryPrompt||'Authoritative and human. Avoid trailer-voice exaggeration. Let important ideas breathe.');
    setKokoroVoice(preset.kokoroVoice||'bm_george');
    setSelectedRefs({...preset.selectedRefs});
    setMixerDirty(true);
    setMixerApplied(false);
    setNotice(`Applied creator preset “${preset.name}”. Apply the YouTube mix when you want it to rewrite the episode.`);
  };

  const removeFavoritePreset=(id:string)=>{
    const next=favoritePresets.filter((item)=>item.id!==id);
    setFavoritePresets(next);
    localStorage.setItem('grimforge-presets',JSON.stringify(next));
  };

  const updateScene=(id:string,patch:Partial<Scene>)=>setEpisode((e)=>({...e,scenes:e.scenes.map((s)=>s.id===id?{...s,...patch}:s)}));
  const currentScene=episode.scenes[previewIndex]??episode.scenes[0];
  const sceneCount=episode.scenes.length;
  const artCount=episode.scenes.filter((scene)=>Boolean(sceneImages[scene.id])).length;
  const scriptReady=sceneCount>0&&episode.scenes.every((scene)=>scene.narration.trim().length>20&&scene.visualPrompt.trim().length>10);
  const storyboardReady=sceneCount>0&&artCount===sceneCount;
  const narrationReady=Boolean(narrationUrl);
  const preRenderSteps=[scriptReady,cinematicMode,storyboardReady,narrationReady];
  const preRenderScore=Math.round((preRenderSteps.filter(Boolean).length/preRenderSteps.length)*100);
  const mp4Input=(file:File|undefined)=>{ if(!file)return; if(mp4Url.startsWith('blob:'))URL.revokeObjectURL(mp4Url); setMp4Url(URL.createObjectURL(file)); };
  const narrationInput=(file:File|undefined)=>{ if(!file)return; if(narrationUrl.startsWith('blob:'))URL.revokeObjectURL(narrationUrl); setNarrationUrl(URL.createObjectURL(file)); };

  return <div className='appShell'>
    {busy&&<div className='busyOverlay'><div className='forgeLoader'><div className='spinner'/><strong>{busy}</strong><span>Controls are temporarily locked so you do not accidentally start the same job twice.</span></div></div>}
    <header className='topbar'><div className='brand'>GRIMFORGE <span>XIII</span></div><div className='topActions'><div className='studioModeToggle'><button className={studioMode==='Simple'?'active':''} onClick={()=>{setStudioMode('Simple');setManualOpen(false);}}>Simple</button><button className={studioMode==='Pro'?'active':''} onClick={()=>setStudioMode('Pro')}>Pro</button></div><button className='ghost' onClick={()=>setCopilotOpen(true)}>Ask Veyr</button></div></header>
    <main>
      {studioMode==='Pro'&&<section className='commandDeck'>
        <div className='deckIntro'><div className='kicker'>Old World War Table</div><h2>Quick Edit Controls</h2><p>Jump straight into the controls you use most. Veyr stays optional.</p></div>
        <div className='deckButtons'>
          <button className={cinematicMode?'cinematicQuick active':''} onClick={applyCinematicPass}><span>FILM</span><strong>Cinematic Forge</strong><small>Story-film camera · continuity · sound</small></button>
          <button onClick={()=>{setManualOpen(true);setActiveTab('YouTube Mixer');window.setTimeout(()=>document.getElementById('manual-studio')?.scrollIntoView({behavior:'smooth'}),0);}}><span>YT</span><strong>YouTube Mixer</strong><small>Mix channel production DNA</small></button>
          <button onClick={()=>{setManualOpen(true);setActiveTab('Voice & Sound');window.setTimeout(()=>document.getElementById('manual-studio')?.scrollIntoView({behavior:'smooth'}),0);}}><span>VOX</span><strong>Voice Studio</strong><small>Free neural + browser + premium</small></button>
          <button onClick={()=>{setManualOpen(true);setActiveTab('Art Style');window.setTimeout(()=>document.getElementById('manual-studio')?.scrollIntoView({behavior:'smooth'}),0);}}><span>ART</span><strong>Art Style</strong><small>3D · 2.5D · maps · manuscripts</small></button>
          <button onClick={()=>{setManualOpen(true);setActiveTab('Scenes');window.setTimeout(()=>document.getElementById('manual-studio')?.scrollIntoView({behavior:'smooth'}),0);}}><span>SCN</span><strong>Scenes</strong><small>Edit narration and motion</small></button>
          <button onClick={()=>{setManualOpen(true);setActiveTab('Research');window.setTimeout(()=>document.getElementById('manual-studio')?.scrollIntoView({behavior:'smooth'}),0);}}><span>REF</span><strong>Reference Lab</strong><small>Import channel/site DNA</small></button>
          <button onClick={()=>{setManualOpen(true);setActiveTab('Rights');window.setTimeout(()=>document.getElementById('manual-studio')?.scrollIntoView({behavior:'smooth'}),0);}}><span>LAW</span><strong>Rights</strong><small>Publication provenance</small></button>
          <button onClick={()=>{setManualOpen(true);setActiveTab('Presets');window.setTimeout(()=>document.getElementById('manual-studio')?.scrollIntoView({behavior:'smooth'}),0);}}><span>★</span><strong>Favorite Presets</strong><small>Reuse voice · art · channel mix</small></button>
        </div>
      </section>}
      {studioMode==='Simple'?<section className='hero simpleHero simpleModeLanding'>
        <div className='kicker'>Simple Mode · Veyr makes the technical decisions</div><h1>Paste a video. Tell Veyr what you want. Get the episode.</h1>
        <p className='simpleLead'>Start with a YouTube video/channel or any public webpage you like. Veyr studies whatever public text/metadata is actually accessible, learns only the high-level production grammar, and creates a new original cinematic episode from your request.</p>
        <label className='simpleReferenceInput'><span>1 · Paste a YouTube video, channel, or website</span><input value={simpleReferenceUrl} onChange={(e)=>setSimpleReferenceUrl(e.target.value)} placeholder='https://youtube.com/watch?v=…  or  https://youtube.com/@channel'/><small>Veyr will not pretend it watched/transcribed material the public page does not expose.</small></label>
        <label className='simplePromptBox'><span>2 · What should Veyr make?</span><textarea className='masterPrompt' value={prompt} onChange={(e)=>setPrompt(e.target.value)} placeholder='Example: Make an original 5-minute episode about a doomed fortress defense. Use the reference only for broad pacing/cinematography. Give me premium narration, dramatic character dialogue, cinematic shots and scene art.'/></label>
        <div className='qualityTierRow'><button className={qualityTier==='Draft'?'active':''} onClick={()=>setQualityTier('Draft')}><strong>Draft</strong><span>Fast storyboard + animatic</span></button><button className={qualityTier==='Cinema'?'active':''} onClick={()=>{setQualityTier('Cinema');void refreshCinemaStatus();}}><strong>Cinema</strong><span>Wan motion + expressive voices + finishing</span></button><button className={qualityTier==='Cinematic Max'?'active':''} onClick={()=>{setQualityTier('Cinematic Max');void refreshCinemaStatus();}}><strong>Cinematic Max</strong><span>LTX high-end motion/audio when connected</span></button></div>
        <div className='cinemaConnection'><span className={cinemaStatus.configured?'dot on':'dot'}/><b>{cinemaStatus.configured?'Cinema Bridge detected':'Cinema Bridge not connected'}</b><small>{qualityTier==='Draft'?'Draft works without GPU video providers.':cinemaStatus.configured?'Configured providers will be used when available.':'GrimForge will create the full directed animatic and preserve every shot for later rendering.'}</small><button onClick={()=>void refreshCinemaStatus()}>Check engines</button></div>
        <div className='simpleOptions'><label>World<select value={world} onChange={(e)=>setWorld(e.target.value)}><option>Warhammer 40K</option><option>Old World / Warhammer Fantasy</option></select></label><label>Length<select value={length} onChange={(e)=>setLength(+e.target.value)}><option value={5}>5 minutes</option><option value={8}>8 minutes</option><option value={12}>12 minutes</option></select></label></div>
        <div className='simpleDeliverables'><span>✓ Full narration</span><span>✓ Character dialogue</span><span>✓ Cinematography</span><span>✓ Generated scene art</span><span>✓ Sound direction</span><span>✓ Title + thumbnail package</span></div>
        <button className='primary simpleCreateButton' disabled={!!busy||(!prompt.trim()&&!simpleReferenceUrl.trim())} onClick={createSimpleEpisode}>✦ Veyr — Make the Full Cinematic Episode</button>
        {(simpleStep||simpleReferenceNote)&&<div className='simpleStatus'>{simpleStep&&<strong>{simpleStep}</strong>}{simpleReferenceNote&&<span>{simpleReferenceNote}</span>}</div>}
        <div className='primaryActions'><button className='watchBtn' onClick={()=>{setPreviewIndex(0);setPreviewPlaying(true);document.getElementById('preview')?.scrollIntoView({behavior:'smooth'});}}>▶ Watch Episode</button><button onClick={()=>setStudioMode('Pro')}>⚙ Refine in Pro</button><button onClick={saveCloud}>☁ Save Project</button></div>
      </section>:<section className='hero proHero'><div className='kicker'>Pro Studio</div><h1>Direct every layer yourself.</h1><p>Use the full reference mixer, scene editor, cinematography, art, narration, voice, source, rights and production controls below.</p><textarea className='masterPrompt' value={prompt} onChange={(e)=>setPrompt(e.target.value)} placeholder='Describe the episode you want Veyr to build…'/><div className='creatorQuick'><label>World<select value={world} onChange={(e)=>setWorld(e.target.value)}><option>Warhammer 40K</option><option>Old World / Warhammer Fantasy</option></select></label><label>Length<select value={length} onChange={(e)=>setLength(+e.target.value)}><option value={5}>5 minutes</option><option value={8}>8 minutes</option><option value={12}>12 minutes</option></select></label><button className='primary mega' disabled={!!busy||!prompt.trim()} onClick={createEpisode}>✦ Generate Episode Plan</button></div></section>}
      {notice&&<div className='notice'>{notice}</div>}

      {studioMode==='Pro'&&<section className='productionReadiness'>
        <div className='readinessHead'><div><div className='kicker'>Production Readiness</div><h2>Know exactly what is ready to ship.</h2><p>GrimForge tracks the editable production stages separately from the final external MP4 render.</p></div><div className='readinessScore'><strong>{preRenderScore}%</strong><span>pre-render ready</span></div></div>
        <div className='pipelineGrid'>
          <article className={scriptReady?'ready':''}><span>01</span><div><strong>Script + scenes</strong><small>{scriptReady?`${sceneCount} scenes structured and editable`:'Episode needs narration / visual direction'}</small></div><b>{scriptReady?'READY':'CHECK'}</b></article>
          <article className={cinematicMode?'ready':''}><span>02</span><div><strong>Cinematic direction</strong><small>{cinematicMode?'Continuity-aware shot grammar applied':'Direct the episode into a coherent film sequence'}</small></div>{cinematicMode?<b>READY</b>:<button onClick={applyCinematicPass} disabled={!!busy}>Direct cut</button>}</article>
          <article className={storyboardReady?'ready':''}><span>03</span><div><strong>Storyboard</strong><small>{artCount}/{sceneCount} generated scene frames</small></div>{storyboardReady?<b>READY</b>:<button onClick={generateFullStoryboard} disabled={!!busy}>Generate storyboard</button>}</article>
          <article className={narrationReady?'ready':''}><span>04</span><div><strong>Full narration</strong><small>{narrationReady?'Narration track loaded into the player':'Generate a local Kokoro WAV or load your own audio'}</small></div>{narrationReady?<b>READY</b>:<button onClick={()=>generateKokoroWav(episode.scenes.map((scene)=>scene.narration).join('\n\n'),'full episode narration',true)} disabled={!!busy}>Generate narration</button>}</article>
          <article className={mp4Url?'ready finalStage':''}><span>05</span><div><strong>Final MP4</strong><small>{mp4Url?'Real rendered video loaded':'External motion render still required — GrimForge does not fake this stage'}</small></div>{mp4Url?<b>LOADED</b>:<button onClick={()=>document.getElementById('preview')?.scrollIntoView({behavior:'smooth'})}>Load / review</button>}</article>
        </div>
      </section>}

      {studioMode==='Pro'&&<section className={cinematicMode?'cinematicForge active':'cinematicForge'}>
        <div><div className='kicker'>Cinematic Story-Film Mode</div><h2>Turn the episode into a directed film sequence.</h2><p>Inspired by the reference video's broad production grammar rather than copied shots: scale, atmosphere, continuity, motivated camera moves, layered battle imagery and stronger sound direction.</p></div>
        <div className='cinematicControls'><label>Intensity<select value={cinematicIntensity} onChange={(e)=>setCinematicIntensity(e.target.value)}><option>Epic but readable</option><option>Slow-burn prestige</option><option>Relentless battle momentum</option><option>Dark atmospheric chronicle</option></select></label><button className='primary' disabled={!!busy} onClick={applyCinematicPass}>{cinematicMode?'Re-direct Cinematic Cut':'✦ Direct Cinematic Cut'}</button><button disabled={!!busy} onClick={generateFullStoryboard}>Generate Full Storyboard</button></div>
        <div className='cinematicMeta'><span>Reference grammar</span><b>cinematic scale · continuity · environmental motion · dramatic silhouettes</b><span>Output today</span><b>directed animatic + generated scene frames</b><span>True motion render</span><b>requires a connected video-render engine</b></div>
        {storyboardProgress&&<div className='storyboardProgress'>{storyboardProgress}</div>}
      </section>}

      {(studioMode==='Pro'||simpleStep==='Episode ready')&&<><section className='episodeSummary'><div><div className='kicker'>Current Episode</div><h2>{episode.title}</h2><p>{episode.thesis}</p></div><div className='summaryBadges'><span>{episode.targetMinutes} min</span><span>Kokoro Local Neural</span><span>{speechProfile}</span><span>{dialogueMode}</span><span>{style}</span></div></section>

      {studioMode==='Simple'&&simpleStep==='Episode ready'&&<section className='simpleEpisodePackage'><div className='sectionHead'><div><div className='kicker'>Veyr Delivery</div><h2>Your complete episode package</h2><p>Each scene includes the generated image plus the narration, dialogue, cinematography, camera movement and sound plan that Pro mode can refine later.</p></div><button onClick={()=>setStudioMode('Pro')}>Open Pro controls</button></div><div className='simpleSceneGrid'>{episode.scenes.map((scene,index)=><article key={scene.id} className='simpleSceneCard'>{sceneVideos[scene.id]?<video src={sceneVideos[scene.id]} poster={sceneImages[scene.id]} controls playsInline/>:sceneImages[scene.id]?<img src={sceneImages[scene.id]} alt={`Generated art for ${scene.title}`}/>:<div className='simpleScenePlaceholder'>Scene visual unavailable · retry in Pro</div>}<div className='simpleSceneCopy'><span>Scene {index+1} · {scene.start}</span><h3>{scene.title}</h3><b>Narration</b><p>{scene.narration}</p>{scene.dialogue&&scene.dialogue!=='None — narration only'&&<><b>Dialogue</b><blockquote>{scene.dialogue}</blockquote></>}<details><summary>Cinematography + sound</summary><small><strong>Shot:</strong> {scene.visualPrompt}</small><small><strong>Motion:</strong> {scene.motion}</small><small><strong>Sound:</strong> {scene.sound}</small></details></div></article>)}</div></section>}

      <section className='previewStudio' id='preview'>
        <div className='sectionHead'><div><div className='kicker'>Watch & Tweak</div><h2>Episode Preview Player</h2><p>Generated episodes play as an editable animatic. If you already have a rendered MP4, load it below and watch the real video inside GrimForge.</p></div><div className='playerButtons'><button className='primary' onClick={()=>setPreviewPlaying(!previewPlaying)}>{previewPlaying?'Ⅱ Pause':'▶ Play Episode'}</button><button onClick={()=>{setPreviewPlaying(false);window.speechSynthesis?.cancel();setPreviewIndex(0);}}>■ Stop</button></div></div>
        {mp4Url?<div className='mp4Box'><video src={mp4Url} controls playsInline/><div className='playerStrip'><strong>Loaded MP4</strong><a href={mp4Url} download={`${episode.title.replace(/[^a-z0-9]+/gi,'-').toLowerCase()}.mp4`}>Download MP4</a></div></div>:<div className='animatic'>
          <div className={`animaticFrame ${selectedStyle.archetype} ${cinematicMode?'cinematicFrame':''}`}>{sceneVideos[currentScene.id]?<video className={cinematicMode?'cinematicImage':''} src={sceneVideos[currentScene.id]} poster={sceneImages[currentScene.id]} controls playsInline/>:sceneImages[currentScene.id]?<img className={cinematicMode?'cinematicImage':''} src={sceneImages[currentScene.id]} alt='Generated scene art'/>:<div className='characterStage'><div className='characterGlow'/><div className={`figure ${selectedStyle.archetype}`}><i/><b/><em/></div><div className='stageLabel'>{style}</div></div>}<div className='caption'><small>{currentScene.start} · {currentScene.claimType}</small><strong>{currentScene.title}</strong><p>{currentScene.narration}</p>{currentScene.dialogue&&currentScene.dialogue!=='None — narration only'&&<blockquote><b>Dialogue</b>{currentScene.dialogue}</blockquote>}</div></div>
          <div className='sceneRail'>{episode.scenes.map((s,i)=><button className={i===previewIndex?'active':''} key={s.id} onClick={()=>{setPreviewPlaying(false);window.speechSynthesis?.cancel();setPreviewIndex(i);}}><span>{i+1}</span><small>{s.title}</small></button>)}</div>
        </div>}
        {studioMode==='Pro'?<><div className='mediaInputs'><label>Load / replace rendered MP4<input type='file' accept='video/mp4,video/*' onChange={(e)=>mp4Input(e.target.files?.[0])}/></label><label>Use your own final narration<input type='file' accept='audio/*' onChange={(e)=>narrationInput(e.target.files?.[0])}/></label>{narrationUrl&&<audio src={narrationUrl} controls/>}</div><p className='fine'>Important: GrimForge's generated preview is an editable directed animatic, not a claim of full AI motion rendering. A true moving MP4 still requires a connected video-render engine; any real MP4 you load plays here.</p></>:<p className='simplePreviewNote'>Simple mode gives you the complete directed animatic package immediately. The generated images, narration, dialogue and shot plan are real outputs; true moving-video MP4 rendering remains a separate provider step.</p>}
      </section></>}

      {studioMode==='Pro'&&<section className='visualChooser' id='visual-style'>
        <div className='sectionHead'><div><div className='kicker'>Visual Direction</div><h2>Pick the look by grimdark character example</h2><p>Original GrimForge archetypes designed to read like dark science-fantasy / Old World characters at a glance—never copied named characters or official artwork.</p></div><div className='visualTools'><label className='assetSource'>Artwork source<select value={artSource} onChange={(e)=>setArtSource(e.target.value)}><option>AI Generated Original</option><option>Public Domain / Open License</option><option>User-Owned Upload</option><option>Licensed Asset</option><option>Mixed</option></select></label><button className='ghost' onClick={()=>setCompareStyles((value)=>!value)}>{compareStyles?'Hide Comparison':'Compare Styles'}</button></div></div>
        <div className='visualGrid'>{visualStyles.map((v)=><button className={style===v.name?'visualCard selected':'visualCard'} key={v.name} onClick={()=>setStyle(v.name)}><div className={`archetypeThumb ${v.archetype}`}><div className='characterGlow'/><div className={`figure ${v.archetype}`}><i/><b/><em/></div><span>{v.short}</span></div><strong>{v.name}</strong><p>{v.blurb}</p><small>{v.motion}</small></button>)}</div>
        {compareStyles&&<div className='styleCompare'><div className='compareHead'><strong>Same scene · six visual treatments</strong><span>{currentScene.title}</span></div><div className='compareGrid'>{visualStyles.map((v)=><article key={`compare-${v.name}`} className={style===v.name?'compareCard selected':'compareCard'}><div className={`miniArchetype ${v.archetype}`}><div className={`figure ${v.archetype}`}><i/><b/><em/></div></div><strong>{v.short}</strong><small>{v.motion}</small><button onClick={()=>setStyle(v.name)}>Use this style</button></article>)}</div></div>}
        <div className='sourceExplainer'>{artSource==='AI Generated Original'?<><strong>AI Generated Original</strong><span>GrimForge sends Veyr's scene prompt to the image generator with an originality guardrail: no named characters, logos, copied artwork or creator visual identity.</span></>:artSource==='Public Domain / Open License'?<><strong>Public Domain / Open License</strong><span>Use repositories such as Wikimedia Commons, Library of Congress and other collections only when the individual item's license/source record permits reuse. GrimForge does not treat random web images as public domain. Automatic retrieval is not connected yet; source and license metadata must be recorded before publication.</span></>:<><strong>{artSource}</strong><span>These assets should be uploaded or linked with ownership/license information. Rights Guard remains part of the manual studio.</span></>}</div>
        <button className='primary' onClick={()=>generateSceneArt(currentScene)}>Generate Better Art for Current Scene</button>
      </section>}

      {studioMode==='Pro'&&manualOpen&&<section className='manualStudio' id='manual-studio'>
        <div className='sectionHead'><div><div className='kicker'>War Table Controls</div><h2>Manual Studio</h2><p>YouTube Mixer, voice and art controls are first. Nothing is hidden from you here.</p></div></div>
        <nav className='tabs'>{['YouTube Mixer','Voice & Sound','Art Style','Presets','Scenes','Research','Rights'].map((t)=><button className={activeTab===t?'active':''} key={t} onClick={()=>setActiveTab(t)}>{t}</button>)}</nav>
        {activeTab==='Presets'&&<div className='presetStudio'><div className='presetComposer'><div><h3>Favorite Creator Presets</h3><p className='helper'>Save the current art style, Google voice settings, audio delivery modifiers and YouTube channel mix. Reapply the whole creative setup to the next episode in one click.</p></div><label>Preset name<input value={presetName} onChange={(e)=>setPresetName(e.target.value)} placeholder='Dark Chronicle'/></label><button className='primary' onClick={saveFavoritePreset}>★ Save Current Preset</button></div>{favoritePresets.length?<div className='presetGrid'>{favoritePresets.map((preset)=><article className='presetCard' key={preset.id}><strong>{preset.name}</strong><span>{preset.style}</span><small>{preset.browserVoiceName==='Auto'?'Auto Google voice':preset.browserVoiceName}</small><small>{Object.values(preset.selectedRefs).filter((value)=>value>0).length} channel references</small><div><button className='primary' onClick={()=>applyFavoritePreset(preset)}>Apply</button><button onClick={()=>removeFavoritePreset(preset.id)}>Remove</button></div></article>)}</div>:<div className='emptyPreset'>No saved presets yet. Tune a mix you like, then save it here.</div>}</div>}
        {activeTab==='Art Style'&&<><div className='sectionHead'><div><h3>Grimdark Art Deck</h3><p>Pick the production treatment by recognizable original archetype: armored knight, corrupted warlord, battlefield commander, interrogator, cavalry champion, or grave sorcerer.</p></div><div className='visualTools'><label className='assetSource'>Artwork source<select value={artSource} onChange={(e)=>setArtSource(e.target.value)}><option>AI Generated Original</option><option>Public Domain / Open License</option><option>User-Owned Upload</option><option>Licensed Asset</option><option>Mixed</option></select></label><button className='ghost' onClick={()=>setCompareStyles((value)=>!value)}>{compareStyles?'Hide Comparison':'Compare Styles'}</button></div></div><div className='visualGrid fantasyCardGrid'>{visualStyles.map((v)=><button className={style===v.name?'visualCard fantasyArtCard selected':'visualCard fantasyArtCard'} key={v.name} onClick={()=>setStyle(v.name)}><div className={`archetypeThumb ${v.archetype}`}><div className='characterGlow'/><div className={`figure ${v.archetype}`}><i/><b/><em/></div><span>{v.short}</span></div><div className='cardRibbon'>GrimForge Visual School</div><strong>{v.name}</strong><p>{v.blurb}</p><small>{v.motion}</small></button>)}</div>{compareStyles&&<div className='styleCompare compact'><div className='compareGrid'>{visualStyles.map((v)=><article key={`manual-compare-${v.name}`} className={style===v.name?'compareCard selected':'compareCard'}><div className={`miniArchetype ${v.archetype}`}><div className={`figure ${v.archetype}`}><i/><b/><em/></div></div><strong>{v.short}</strong><button onClick={()=>setStyle(v.name)}>Use</button></article>)}</div></div>}<button className='primary' onClick={()=>generateSceneArt(currentScene)}>Generate Current Scene in This Style</button></>}
        {activeTab==='Scenes'&&<div>{episode.scenes.map((s)=><article className='sceneEditor' key={s.id}><div className='sceneEditorHead'><strong>{s.start} · {s.title}</strong><span>{s.claimType}</span></div><label>Narration<textarea value={s.narration} onChange={(e)=>updateScene(s.id,{narration:e.target.value})}/></label><label>Dialogue<textarea value={s.dialogue||''} onChange={(e)=>updateScene(s.id,{dialogue:e.target.value})} placeholder='Character dialogue or None — narration only'/></label><div className='editGrid'><label>Visual prompt<textarea value={s.visualPrompt} onChange={(e)=>updateScene(s.id,{visualPrompt:e.target.value})}/></label><label>Motion<textarea value={s.motion} onChange={(e)=>updateScene(s.id,{motion:e.target.value})}/></label><label>Sound<textarea value={s.sound} onChange={(e)=>updateScene(s.id,{sound:e.target.value})}/></label><label>Source / claim note<textarea value={s.sourceNeed} onChange={(e)=>updateScene(s.id,{sourceNeed:e.target.value})}/></label></div><button onClick={()=>generateSceneArt(s)}>Generate Scene Art</button></article>)}</div>}
        {activeTab==='YouTube Mixer'&&<><div className='mixerToolbar'><div><h3>Warhammer YouTube Production Mixer</h3><p className='helper'>Choose the channels, set the weights, then click Apply Mix. Veyr will actually remix the current episode's pacing, structure, humor density, hook strength, map use and newcomer clarity. It never copies scripts, jokes, artwork, creator identity or voices.</p></div><div><button className='primary' disabled={!mixerDirty||!!busy} onClick={applyMixer}>{mixerDirty?'Apply Mix to Episode':'Mix Applied ✓'}</button><span className={mixerDirty?'mixState dirty':'mixState applied'}>{mixerDirty?'Changes not applied yet':mixerApplied?'Applied to current episode':'Ready'}</span></div></div><div className='channelGrid'>{channelRefs.map((c)=>{const w=selectedRefs[c.name]??0;return <article className={w?'channelCard selected':'channelCard'} key={c.name}><div><strong>{c.name}</strong><p>{c.traits}</p></div><button onClick={()=>{setSelectedRefs((m)=>({...m,[c.name]:w?0:30}));setMixerDirty(true);setMixerApplied(false);}}>{w?'Remove':'Add'}</button>{w>0&&<label>Weight <b>{w}%</b><input type='range' min='5' max='100' value={w} onChange={(e)=>{setSelectedRefs((m)=>({...m,[c.name]:+e.target.value}));setMixerDirty(true);setMixerApplied(false);}}/></label>}<a href={c.url} target='_blank' rel='noreferrer'>Open channel ↗</a></article>})}</div><div className='metrics'>{refBlend.map((m)=><div key={m.label}><small>{m.label}</small><strong>{m.value}</strong></div>)}</div></>}
        {activeTab==='Voice & Sound'&&<><div className='kokoroStudio'><div className='kokoroHead'><div><h3>Kokoro Free Neural · Default</h3><p>Runs on your device with no per-episode API charge. First use downloads the open model; later loads can use browser caching.</p></div><span className='kokoroStatus'>{kokoroStatus}</span></div><div className='kokoroControls'><button className='primary' onClick={loadKokoro}>{kokoroRef.current?'Engine Ready ✓':'Load Free Neural Engine'}</button><label>Neural voice<select value={kokoroVoice} onChange={(e)=>setKokoroVoice(e.target.value)} disabled={!kokoroVoices.length}>{kokoroVoices.length?kokoroVoices.map((item)=><option value={item.id} key={item.id}>{item.name}{item.detail?` · ${item.detail}`:''}</option>):<option value={kokoroVoice}>Load engine to see voices</option>}</select></label><label>Speech speed<input type='range' min='.5' max='1.6' step='.02' value={voiceRate} onChange={(e)=>setVoiceRate(+e.target.value)}/><b>{voiceRate.toFixed(2)}×</b></label></div><div className='kokoroActions'><button onClick={()=>generateKokoroWav(selectedDialogueMode.sample,'speech preview')}>▶ Generate Preview WAV</button><button onClick={()=>generateKokoroWav(currentScene.narration,'current scene WAV')}>Generate Current Scene WAV</button><button className='primary' onClick={()=>generateKokoroWav(episode.scenes.map((scene)=>scene.narration).join('\n\n'),'full episode narration',true)}>Generate Full Episode WAV</button></div>{kokoroAudioUrl&&<div className='kokoroPlayer'><div><strong>{kokoroOutputLabel}</strong><small>Generated locally with Kokoro</small></div><audio src={kokoroAudioUrl} controls/><a className='buttonLink' href={kokoroAudioUrl} download={`${episode.title.replace(/[^a-z0-9]+/gi,'-').toLowerCase()}-kokoro.wav`}>Download WAV</a></div>}<p className='fine'>Kokoro controls speed directly. Voice timbre comes from the selected neural voice; Veyr's Speech Director controls cadence, sentence shape and delivery direction.</p></div><div className='voiceEngineBanner'><div><strong>Veyr Speech Director + Free Browser Fallback</strong><span>GrimForge detected {googleBrowserVoices.length} Google browser voice(s) across {detectedGoogleLocales.length} locale(s). The browser voice is the instrument; Veyr's speech profile controls how the narration is written and directed.</span></div><span className='engineBadge'>Kokoro default · browser fallback</span></div><div className='speechDirector'><div className='speechDirectorHead'><div><h3>Reference-derived speech profiles</h3><p>Built from the delivery qualities in your four example clips. These describe cadence and performance only — they do not clone the original voices.</p></div><button className='primary' disabled={!!busy} onClick={applySpeechStyle}>Apply Speech Style to Episode</button></div><div className='speechProfileGrid'>{speechReferenceProfiles.map((preset)=><button className={speechProfile===preset.name?'speechProfileCard selected':'speechProfileCard'} key={preset.name} onClick={()=>applySpeechReference(preset.name)}><span>{preset.source}</span><strong>{preset.name}</strong><small>{preset.note}</small><em>{preset.rate.toFixed(2)}× · pitch {preset.pitch.toFixed(2)} · {preset.pause}ms pause</em></button>)}</div><div className='dialogueDirector'><div><h3>Dialogue writing mode</h3><p>Veyr uses this when creating or rewriting narration. It changes sentence shape, rhetoric, pacing and attitude without changing canon facts.</p></div><div className='dialogueModeGrid'>{dialogueModes.map((mode)=><button className={dialogueMode===mode.name?'dialogueModeCard selected':'dialogueModeCard'} key={mode.name} onClick={()=>setDialogueMode(mode.name)}><strong>{mode.name}</strong><small>{mode.note}</small></button>)}</div><label className='speechPrompt'>Extra direction<textarea value={deliveryPrompt} onChange={(e)=>setDeliveryPrompt(e.target.value)} placeholder='Example: calm authority, dry intelligence, no trailer voice, pause before the final sentence.'/></label><div className='speechActions'><button onClick={previewSelectedDelivery}>▶ Preview Selected Delivery</button><button onClick={()=>askVeyr(`Explain how you would direct ${speechProfile} with ${dialogueMode} for this episode. Extra direction: ${deliveryPrompt}`)}>Ask Veyr About This Style</button></div></div></div><div className='voiceLocaleBar'><label>Working locale / accent<select value={voiceLocaleFilter} onChange={(e)=>{setVoiceLocaleFilter(e.target.value);setBrowserVoiceName('Auto');}}><option value='all'>All detected Google locales</option>{detectedGoogleLocales.map((locale)=><option key={locale} value={locale}>{locale}</option>)}</select></label><div className='localeHint'>Browser voices are device-dependent. Australian, Italian, French, etc. only appear here if Chrome exposes them.</div></div><div className='googleVoiceGrid'>{filteredGoogleVoices.length?filteredGoogleVoices.map((v)=><button className={browserVoiceName===v.name?'googleVoiceCard selected':'googleVoiceCard'} key={`${v.name}-${v.lang}`} onClick={()=>setBrowserVoiceName(v.name)}><strong>{v.name}</strong><span>{v.lang}</span><small>{v.localService?'local Google voice':'online Google voice'}</small></button>):<div className='emptyVoice'><strong>No Google voice detected for this locale</strong><span>Choose another detected locale or use the Cloud catalog below as the target for the premium TTS connection.</span></div>}</div><div className='directionShelf'><h3>Original character directions</h3><p>Performance directions only — not celebrity or character impersonations.</p><div className='directionGrid'>{voiceCharacterDirections.map((preset)=><button className={voiceDirection===preset.name?'directionCard selected':'directionCard'} key={preset.name} onClick={()=>applyVoiceDirection(preset.name)}><strong>{preset.name}</strong><small>{preset.note}</small></button>)}</div></div><div className='voiceModifierGrid'><label>Speed <b>{voiceRate.toFixed(2)}×</b><input type='range' min='.55' max='1.45' step='.01' value={voiceRate} onChange={(e)=>{setVoiceRate(+e.target.value);setVoiceDirection('Custom');}}/></label><label>Depth / pitch <b>{voicePitch.toFixed(2)}</b><input type='range' min='.55' max='1.45' step='.01' value={voicePitch} onChange={(e)=>{setVoicePitch(+e.target.value);setVoiceDirection('Custom');}}/></label><label>Sentence pause <b>{voicePause} ms</b><input type='range' min='0' max='1000' step='10' value={voicePause} onChange={(e)=>{setVoicePause(+e.target.value);setVoiceDirection('Custom');}}/></label><label>Delivery energy <b>{voiceEnergy}%</b><input type='range' min='0' max='100' step='1' value={voiceEnergy} onChange={(e)=>{setVoiceEnergy(+e.target.value);setVoiceDirection('Custom');}}/></label></div><div className='modifierReadout'><strong>{voiceDirection}</strong><span>{voiceRate.toFixed(2)}× speed · {voicePitch.toFixed(2)} pitch · {voicePause} ms pause · {voiceEnergy}% energy</span></div><div className='voiceQuality'><label>Google playback voice<select value={browserVoiceName} onChange={(e)=>setBrowserVoiceName(e.target.value)}><option value='Auto'>Auto · best voice in locale</option>{filteredGoogleVoices.map((v)=><option value={v.name} key={`${v.name}-${v.lang}`}>{v.name} · {v.lang}</option>)}</select></label><div className='voiceAB'><button onClick={()=>speak('The Imperium survives because it can endure losses that would destroy a smaller civilization. Survival is what keeps the war possible.',true)}>A · Raw</button><button className='primary' onClick={()=>speak('The Imperium survives because it can endure losses that would destroy a smaller civilization. Survival is what keeps the war possible.')}>B · Current Modifiers</button><button onClick={()=>speak('The Imperium survives because it can endure losses that would destroy a smaller civilization. Survival is what keeps the war possible.',false,{rate:.68,pitch:.68,pause:620,energy:88})}>C · Extreme Test</button><button onClick={stopSpeaking}>Stop</button></div><div className='mastering'><span>Dialogue target</span><b>-16 to -14 LUFS</b><span>True peak</span><b>≤ -1 dBTP</b><span>Priority</span><b>clear consonants · low fatigue · narration above music</b></div></div><div className='cloudVoiceShelf'><div><h3>Optional Premium · Google Cloud</h3><p>You do not need this to use GrimForge. Kokoro is now the free default; Chirp/Gemini remain optional if you ever want them.</p></div><div className='cloudLocaleGrid'>{cloudLocaleOptions.map(([code,label])=><article className='cloudLocaleCard' key={code}><strong>{label}</strong><span>{code}</span><em>Cloud connection required</em></article>)}</div><h4>Premium voice families</h4><div className='cloudVoiceGrid'>{googleCloudVoiceOptions.map((v)=><article className='cloudVoiceCard' key={`${v.model}-${v.name}`}><strong>{v.name}</strong><span>{v.model}</span><small>{v.note}</small><em>connection required</em></article>)}</div></div><div className='qualityWarning'>If Raw and Current Modifiers still sound identical, that specific browser voice is ignoring one or more Web Speech controls. The Extreme Test makes the difference intentionally obvious. For Italian- or French-flavored English, a non-English browser locale can be tried experimentally, but proper accent direction belongs in the future Cloud/Gemini-TTS path rather than being faked as a guaranteed browser feature.</div></>}
        {activeTab==='Research'&&<><div className='referenceLab'><div className='sectionHead'><div><h3>Reference Lab</h3><p>Import a public YouTube channel/video or website. Veyr extracts accessible high-level production traits and adds them to the same weighted mixer as the built-in channels.</p></div><span className='engineBadge'>original output only</span></div><div className='researchBox'><label>Public reference URL<input value={researchUrl} onChange={(e)=>setResearchUrl(e.target.value)} placeholder='https://www.youtube.com/@channel or any public page'/></label><button className='primary' disabled={!researchUrl.trim()||!!busy} onClick={analyzeUrl}>Study + Add to Mixer</button></div><p className='fine'>Veyr may only analyze what the public page exposes. A channel page does not automatically provide every video transcript. Imported references influence structure, pacing, hook strategy, visual grammar, humor density and beginner clarity — never copied scripts, jokes, voices, artwork or creator identity.</p>{importedRefs.length>0&&<div className='importedRefGrid'>{importedRefs.map(ref=><article className='importedRefCard' key={ref.id}><div><span>Imported reference</span><strong>{ref.name}</strong><p>{ref.summary}</p><small>{ref.traits}</small></div><label>Weight <b>{ref.weight}%</b><input type='range' min='5' max='100' value={ref.weight} onChange={e=>updateImportedWeight(ref.id,+e.target.value)}/></label><div className='importedRefActions'><a href={ref.url} target='_blank' rel='noreferrer'>Open source ↗</a><button onClick={()=>removeImportedRef(ref.id)}>Remove</button></div></article>)}</div>}<div className='metrics'>{refBlend.map(m=><div key={'ref-lab-'+m.label}><small>{m.label}</small><strong>{m.value}</strong></div>)}</div></div><div className='researchActions'><button onClick={()=>askVeyr('Audit the current episode and separate canon/source claims from interpretation and speculation. List every claim that needs verification.')}>Canon Audit</button><button onClick={()=>askVeyr('Improve the episode flow and retention without making it frantic. Identify the weakest scene and fix it.')}>Retention Audit</button><button onClick={()=>askVeyr('Give me a source plan for every CANON / SOURCE scene in this episode.')}>Source Plan</button></div></>}
        {activeTab==='Rights'&&<div className='rightsPanel'><h3>Publication rule</h3><p>Generated-original, user-owned, licensed, public-domain/open-license assets with recorded provenance can move forward. Third-party reference material can inform analysis but does not silently become a publication asset.</p><div className='status good'>Current art mode: {artSource}</div></div>}
      </section>}

      {studioMode==='Pro'&&<section className='publishStudio' id='publish'><div className='sectionHead'><div><div className='kicker'>Finish</div><h2>Download or Publish</h2></div></div><div className='publishGrid'><article><h3>Watch first</h3><p>Review the animatic or loaded MP4 above, tweak scenes, then come back here.</p><button onClick={()=>document.getElementById('preview')?.scrollIntoView({behavior:'smooth'})}>Open Player</button></article><article><h3>Cloud project</h3><p>Save the editable episode, controls and reference blend.</p><button className='primary' onClick={saveCloud}>Save Project</button></article><article><h3>Download video</h3><p>{mp4Url?'A real MP4 is loaded and ready to download.':'No real MP4 exists yet. Load a rendered MP4 above or connect a render engine.'}</p>{mp4Url?<a className='buttonLink' href={mp4Url} download={`${episode.title.replace(/[^a-z0-9]+/gi,'-').toLowerCase()}.mp4`}>Download MP4</a>:<button disabled>MP4 render engine not connected</button>}</article><article><h3>YouTube</h3><p>Direct account upload requires YouTube OAuth. Until that connector is added, review your MP4 here and publish through YouTube Studio.</p><button onClick={()=>window.open('https://studio.youtube.com','_blank')}>Open YouTube Studio ↗</button><button disabled>Direct Upload · connect OAuth</button></article></div></section>
      <footer>Original creative-production tool · channel traits are references, not cloning · no unauthorized voice cloning · no uncleared publication assets.</footer>
    </main>

    <button className='veyFab' onClick={()=>setCopilotOpen(true)}><span>V</span><div><strong>Archivist Veyr</strong><small>One-click creative copilot</small></div></button>
    {copilotOpen&&<aside className='copilotPanel'><header><div><div className='kicker'>GrimForge Copilot</div><h3>Archivist Veyr</h3></div><button onClick={()=>setCopilotOpen(false)}>×</button></header><div className='modeRow'>{(['Quick','Standard','Deep'] as WorkMode[]).map((m)=><button className={workMode===m?'active':''} key={m} onClick={()=>setWorkMode(m)}>{m}</button>)}</div><div className='oneClickTools'>{[['Make full episode',`Create a complete ${length}-minute episode from this idea: ${prompt}`],['Improve hook','Give me three stronger opening hooks for this exact episode.'],['Fix flow','Audit the scene order and fix the weakest retention point.'],['Check canon','Separate canon, interpretation and speculation and flag anything needing verification.'],['Improve visuals','Upgrade the visual plan with one premium 3D shot and coherent recurring motif.'],['Title + thumbnail','Give me five accurate title/thumbnail pairs without misleading clickbait.'],['Direct speech',`Direct the current narration using ${speechProfile} delivery and ${dialogueMode} dialogue style. Extra direction: ${deliveryPrompt}`]].map(([l,q])=><button key={l} onClick={()=>askVeyr(q)}>{l}</button>)}</div><div className='chatStream'>{messages.slice(-10).map((m,i)=><div className={m.role==='assistant'?'veyMsg':'userMsg'} key={i}>{m.text}</div>)}</div><div className='copilotComposer'><textarea value={copilotInput} onChange={(e)=>setCopilotInput(e.target.value)} onKeyDown={(e)=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();askVeyr(copilotInput);}}} placeholder='Ask Veyr anything about the episode…'/><button className='primary' onClick={()=>askVeyr(copilotInput)}>Send</button></div></aside>}
  </div>;
}

export default App;
