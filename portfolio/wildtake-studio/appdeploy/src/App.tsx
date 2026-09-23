import { useMemo, useRef, useState } from 'react';
import { api } from '@appdeploy/client';
import {
  CheckCircle2,
  Clapperboard,
  FileVideo2,
  Mic2,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Volume2,
  Bot,
  X,
  Send,
  Globe2,
  Plus,
} from 'lucide-react';

type Beat = { time: string; action: string; angle: string };
type CreatorPack = { title: string; hook: string; script: string; captions: string[]; postingCopy: string; hashtags: string[] };
type ReferenceProfile = { id:string; label:string; sourceUrl?:string; summary:string; traits:string[]; formatPatterns:string[]; weight:number; originalityBoundary:string };
type Rights =
  | 'I own this footage'
  | 'Licensed'
  | 'Permission received'
  | 'Other / Unknown';
const narrators = {
  'Aussie Wildlife Commentator':
    'Original Australian-flavoured wildlife play-by-play: cheeky observational wit, quick escalation, sports-commentary energy, punchy payoff. Not an Ozzy Man imitation.',
  'Deadpan Naturalist': 'Dry documentary delivery with understated jokes.',
  'Sports Desk': 'Fast play-by-play with match-call structure.',
  'Chaotic Mate': 'High-energy friend reacting in real time.',
  'Family Friendly': 'Playful, clean, all-ages animal commentary.',
};
const referencePresets=[
  {id:'bbc-earth',label:'BBC Earth',url:'https://www.youtube.com/@bbcearth',summary:'Cinematic wildlife storytelling with clear natural-history context.',traits:['cinematic visual patience','behavior-first narration','clear factual framing'],formatPatterns:['visual hook → behavior → context → payoff']},
  {id:'brave-wilderness',label:'Brave Wilderness',url:'https://www.youtube.com/@BraveWilderness',summary:'Field-forward wildlife energy with curiosity, stakes, and accessible explanation.',traits:['fast curiosity hook','field-observation energy','simple educational framing'],formatPatterns:['hook → encounter → observation → takeaway']},
  {id:'tierzoo',label:'TierZoo',url:'https://www.youtube.com/@TierZoo',summary:'Analytical animal behavior explained through playful systems thinking.',traits:['comparative analysis','game-like conceptual framing','dense but accessible humor'],formatPatterns:['premise → comparison → mechanics → ranking-style synthesis']},
  {id:'natgeo',label:'National Geographic',url:'https://www.youtube.com/@NatGeo',summary:'Polished documentary pacing with factual context and dramatic visual emphasis.',traits:['documentary authority','environmental context','measured escalation'],formatPatterns:['scene setter → behavior → stakes → context → resolution']},
];

const initialBeats: Beat[] = [
  {
    time: '00:02',
    action: 'Animal notices something off-camera',
    angle: 'Confidence enters the chat.',
  },
  { time: '00:05', action: 'Animal approaches', angle: 'Bold strategy.' },
  {
    time: '00:08',
    action: 'Other animal reacts',
    angle: 'And there goes the plan.',
  },
  {
    time: '00:10',
    action: 'Retreat / reversal',
    angle: 'Immediate tactical withdrawal.',
  },
];

function App() {
  const [mode, setMode] = useState<'Simple' | 'Pro'>('Simple');
  const [rights, setRights] = useState<Rights>('I own this footage');
  const [credit, setCredit] = useState('');
  const [narrator, setNarrator] = useState<keyof typeof narrators>(
    'Aussie Wildlife Commentator'
  );
  const [beats, setBeats] = useState<Beat[]>(initialBeats);
  const [script, setScript] = useState(
    initialBeats.map(b => `[${b.time}] ${b.angle}`).join('\n')
  );
  const [creatorPack, setCreatorPack] = useState<CreatorPack | null>(null);
  const [aiBusy, setAiBusy] = useState(false);
  const [aiNotice, setAiNotice] = useState('');
  const [referenceUrl,setReferenceUrl]=useState('');
  const [referenceProfiles,setReferenceProfiles]=useState<ReferenceProfile[]>([]);
  const [referenceBusy,setReferenceBusy]=useState(false);
  const [copilotOpen,setCopilotOpen]=useState(false);
  const [copilotInput,setCopilotInput]=useState('');
  const [copilotAnswer,setCopilotAnswer]=useState('Ask me to punch up the hook, tighten pacing, suggest captions, or turn your references into an original production plan.');
  const [copilotBusy,setCopilotBusy]=useState(false);
  const [queue, setQueue] = useState<[string, string][]>([]);
  const [videoUrl, setVideoUrl] = useState('');
  const [fileName, setFileName] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const ready = rights !== 'Other / Unknown';
  const [energy, setEnergy] = useState(8);
  const [jokes, setJokes] = useState(7);
  const [quality, setQuality] = useState('Highest available');
  const [fps, setFps] = useState(30);
  const [bitrate, setBitrate] = useState('16 Mbps');
  const qc = useMemo(
    () =>
      [
        ['Rights preflight', ready],
        ['Source clip', Boolean(videoUrl)],
        ['AI commentary writer', true],
        ['Vision analysis provider', false],
        ['Premium narration provider', false],
        ['Render engine', false],
      ] as const,
    [ready, videoUrl]
  );
  const updateBeat = (i: number, key: keyof Beat, value: string) =>
    setBeats(x => x.map((b, n) => (n === i ? { ...b, [key]: value } : b)));
  const refreshScript = () =>
    setScript(beats.map(b => `[${b.time}] ${b.angle || b.action}`).join('\n'));
  const writeCommentary = async () => {
    if (!ready || aiBusy) return;
    setAiBusy(true);
    setAiNotice('');
    try {
      const { data } = await api.post('/api/write-commentary', { beats, narrator, narratorDescription: narrators[narrator], energy, jokes, rights, credit, referenceProfiles });
      const pack = data.pack as CreatorPack;
      setCreatorPack(pack);
      setScript(pack.script);
      setAiNotice('Original commentary package created. Everything remains editable before narration or rendering.');
    } catch (err) {
      const value = err as { response?: { data?: { error?: string } }; message?: string };
      setAiNotice(value.response?.data?.error || value.message || 'Commentary generation failed. Your manual beats and script are still intact.');
    } finally {
      setAiBusy(false);
    }
  };
  const addPreset=(preset:(typeof referencePresets)[number])=>{
    setReferenceProfiles(current=>current.some(x=>x.id===preset.id)?current:[...current,{id:preset.id,label:preset.label,sourceUrl:preset.url,summary:preset.summary,traits:preset.traits,formatPatterns:preset.formatPatterns,weight:30,originalityBoundary:'Use abstract production traits only. Generate original commentary, captions, hooks, and structure.'}]);
  };
  const analyzeReference=async()=>{
    if(!referenceUrl.trim()||referenceBusy)return;
    setReferenceBusy(true);setAiNotice('');
    try{const {data}=await api.post('/api/analyze-reference',{url:referenceUrl});const profile=data.profile as Omit<ReferenceProfile,'weight'|'id'>;const id='import-'+Date.now();setReferenceProfiles(current=>[...current,{...profile,id,weight:35}]);setAiNotice('Reference studied. Its high-level production traits are now available in the blend.');}
    catch(err){const value=err as {response?:{data?:{error?:string}},message?:string};setAiNotice(value.response?.data?.error||value.message||'Reference analysis failed.');}
    finally{setReferenceBusy(false);}
  };
  const updateReferenceWeight=(id:string,weight:number)=>setReferenceProfiles(current=>current.map(x=>x.id===id?{...x,weight}:x));
  const removeReference=(id:string)=>setReferenceProfiles(current=>current.filter(x=>x.id!==id));
  const askCopilot=async(q=copilotInput)=>{if(!q.trim()||copilotBusy)return;setCopilotBusy(true);try{const {data}=await api.post('/api/copilot',{question:q,beats,script,creatorPack,narrator,energy,jokes,referenceProfiles,rights});setCopilotAnswer(data.answer);setCopilotInput('');}catch{setCopilotAnswer('I could not complete that request. Your current WildTake project is still intact.');}finally{setCopilotBusy(false);}};
  const makeVideo = () =>
    setQueue([
      ['Rights Preflight', 'passed'],
      [
        'Analyze action beats',
        'manual beats ready · vision provider not connected',
      ],
      ['Write commentary', creatorPack ? 'AI draft ready · editable' : 'manual script ready for review'],
      ['Generate narration', 'blocked · premium TTS not connected'],
      ['Mix sound', 'waiting'],
      ['Render 1080×1920', 'waiting · render engine not connected'],
      ['Final QC', 'waiting'],
    ]);
  return (
    <main className="shell">
      <header className="hero">
        <div className="brand">
          <div className="icon">
            <Clapperboard size={30} />
          </div>
          <div>
            <p className="eyebrow">Original short-form video studio</p>
            <h1>WildTake Studio</h1>
            <p>
              Animal footage → action beats → comedy commentary → narration →
              captions → final Short.
            </p>
          </div>
        </div>
        <div className="mode">
          <button
            className={mode === 'Simple' ? 'active' : ''}
            onClick={() => setMode('Simple')}
          >
            Simple
          </button>
          <button
            className={mode === 'Pro' ? 'active' : ''}
            onClick={() => setMode('Pro')}
          >
            Pro
          </button>
        </div>
      </header>

      <div className="provider-strip">
        <div>
          <ShieldCheck size={17} />
          <span>Rights-first workflow</span>
        </div>
        <div className="warn">
          <Mic2 size={17} />
          <span>Premium TTS not connected</span>
        </div>
        <div>
          <Sparkles size={17} />
          <span>AI commentary writer connected</span>
        </div>
        <div className="warn">
          <Sparkles size={17} />
          <span>Vision analysis not connected</span>
        </div>
        <div className="warn">
          <FileVideo2 size={17} />
          <span>Render engine not connected</span>
        </div>
      </div>

      <section className="grid">
        <div className="stack">
          <section className="panel">
            <p className="eyebrow">1 · Source footage</p>
            <h2>Bring your clip</h2>
            <div className="drop" onClick={() => inputRef.current?.click()}>
              <FileVideo2 size={28} />
              <strong>{fileName || 'Choose an animal / wildlife clip'}</strong>
              <span>MP4, MOV, WebM — local preview only</span>
            </div>
            <input
              ref={inputRef}
              type="file"
              accept="video/*"
              hidden
              onChange={e => {
                const f = e.target.files?.[0];
                if (!f) return;
                if (videoUrl) URL.revokeObjectURL(videoUrl);
                setVideoUrl(URL.createObjectURL(f));
                setFileName(f.name);
              }}
            />
            {videoUrl && (
              <video className="source-video" src={videoUrl} controls />
            )}
          </section>

          <section className="panel">
            <p className="eyebrow">2 · Rights preflight</p>
            <h2>Confirm reuse basis</h2>
            <div className="rights">
              {(
                [
                  'I own this footage',
                  'Licensed',
                  'Permission received',
                  'Other / Unknown',
                ] as Rights[]
              ).map(r => (
                <button
                  key={r}
                  className={rights === r ? 'choice active' : 'choice'}
                  onClick={() => setRights(r)}
                >
                  {r}
                </button>
              ))}
            </div>
            <label>
              Source / attribution (optional)
              <input
                value={credit}
                onChange={e => setCredit(e.target.value)}
                placeholder="Creator, license, source URL, permission note…"
              />
            </label>
            {rights === 'Other / Unknown' && (
              <div className="alert">
                Unknown provenance is flagged. Commentary or transformation does
                not itself guarantee fair use.
              </div>
            )}
          </section>

          <section className="panel">
            <p className="eyebrow">3 · Narrator</p>
            <h2>Choose the voice personality</h2>
            <select
              value={narrator}
              onChange={e =>
                setNarrator(e.target.value as keyof typeof narrators)
              }
            >
              {Object.keys(narrators).map(n => (
                <option key={n}>{n}</option>
              ))}
            </select>
            <p className="desc">{narrators[narrator]}</p>
            {mode === 'Pro' && (
              <div className="pro-grid">
                <label>
                  Energy <strong>{energy}/10</strong>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={energy}
                    onChange={e => setEnergy(Number(e.target.value))}
                  />
                </label>
                <label>
                  Joke density <strong>{jokes}/10</strong>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={jokes}
                    onChange={e => setJokes(Number(e.target.value))}
                  />
                </label>
              </div>
            )}
          </section>

          <section className="panel reference-lab">
            <div className="section-head"><div><p className="eyebrow">4 · Reference Lab</p><h2>Study a channel or website</h2></div><Globe2 size={20}/></div>
            <p className="desc">Import a public YouTube channel/video or website. WildTake extracts accessible high-level production traits, then uses those traits to create original material — not cloned scripts, voices, catchphrases, or creator identity.</p>
            <div className="reference-import"><input value={referenceUrl} onChange={e=>setReferenceUrl(e.target.value)} placeholder="https://youtube.com/@channel or public website"/><button className="ai-write" onClick={analyzeReference} disabled={!referenceUrl.trim()||referenceBusy}>{referenceBusy?'Studying…':'Study reference'}</button></div>
            <div className="preset-grid">{referencePresets.map(p=><article key={p.id} className="preset-reference"><strong>{p.label}</strong><span>{p.summary}</span><small>{p.traits.slice(0,2).join(' · ')}</small><button onClick={()=>addPreset(p)} disabled={referenceProfiles.some(x=>x.id===p.id)}><Plus size={14}/>{referenceProfiles.some(x=>x.id===p.id)?'Added':'Add to blend'}</button></article>)}</div>
            {referenceProfiles.length>0&&<div className="active-blend"><div className="section-head"><div><p className="eyebrow">Active blend</p><h3>Production DNA mixer</h3></div><span className="badge">{referenceProfiles.length} reference{referenceProfiles.length===1?'':'s'}</span></div>{referenceProfiles.map(profile=><div className="blend-row" key={profile.id}><div><strong>{profile.label}</strong><small>{profile.traits.slice(0,3).join(' · ')}</small></div><label>Weight <b>{profile.weight}%</b><input type="range" min="5" max="100" value={profile.weight} onChange={e=>updateReferenceWeight(profile.id,Number(e.target.value))}/></label><button onClick={()=>removeReference(profile.id)}>Remove</button></div>)}</div>}
          </section>

          <section className="panel">
            <div className="section-head">
              <div>
                <p className="eyebrow">5 · Action beats</p>
                <h2>Time the story</h2>
              </div>
              <button
                className="ghost"
                onClick={() =>
                  setBeats(x => [
                    ...x,
                    {
                      time: '00:00',
                      action: 'Describe the action',
                      angle: 'Comedy angle',
                    },
                  ])
                }
              >
                + Add beat
              </button>
            </div>
            <div className="beats">
              {beats.map((b, i) => (
                <div className="beat" key={i}>
                  <input
                    aria-label={`Beat ${i + 1} time`}
                    value={b.time}
                    onChange={e => updateBeat(i, 'time', e.target.value)}
                  />
                  <input
                    aria-label={`Beat ${i + 1} action`}
                    value={b.action}
                    onChange={e => updateBeat(i, 'action', e.target.value)}
                  />
                  <input
                    aria-label={`Beat ${i + 1} angle`}
                    value={b.angle}
                    onChange={e => updateBeat(i, 'angle', e.target.value)}
                  />
                </div>
              ))}
            </div>
            <button className="ghost" onClick={refreshScript}>
              Refresh script from beats
            </button>
          </section>

          <section className="panel">
            <div className="section-head"><div><p className="eyebrow">6 · Commentary</p><h2>Write, generate, then edit</h2></div><button className="ai-write" disabled={!ready || aiBusy} onClick={writeCommentary}><Sparkles size={15} /> {aiBusy ? 'Writing…' : 'Write with AI'}</button></div>
            <p className="desc">WildTake can now turn your timed beats into an original commentary package. It does not analyze unseen video frames or imitate a real creator.</p>
            {aiNotice && <div className="ai-notice">{aiNotice}</div>}
            {creatorPack && <div className="creator-pack"><div><span>Suggested title</span><strong>{creatorPack.title}</strong></div><div><span>Hook</span><strong>{creatorPack.hook}</strong></div><div className="caption-pack"><span>Caption beats</span><div>{creatorPack.captions.map((caption, index) => <button key={`${caption}-${index}`} onClick={() => setScript(current => `${current}\n[CAPTION] ${caption}`)}>{caption}</button>)}</div></div><div><span>Posting copy</span><p>{creatorPack.postingCopy}</p><small>{creatorPack.hashtags.join(' ')}</small></div></div>}
            <textarea
              aria-label="Commentary script"
              rows={9}
              value={script}
              onChange={e => setScript(e.target.value)}
            />
            <p className="desc">
              AI-written text is labeled through the Creator Pack above. Manual edits remain yours, and generation never claims to have visually inspected footage unless a vision provider is actually connected.
            </p>
          </section>
        </div>

        <aside className="stack">
          <section className="panel preview">
            <div className="section-head">
              <div>
                <p className="eyebrow">9:16 output</p>
                <h2>Shorts preview</h2>
              </div>
              <span className="badge">1080 × 1920 target</span>
            </div>
            <div className="phone">
              {videoUrl ? (
                <video src={videoUrl} controls />
              ) : (
                <div>
                  <FileVideo2 size={38} />
                  <strong>WildTake Preview</strong>
                  <span>Upload a clip to preview it here.</span>
                </div>
              )}
            </div>
          </section>

          <section className="panel">
            <p className="eyebrow">Audio lanes</p>
            <h2>Mix plan</h2>
            {['Narration', 'Source ambience', 'Music', 'SFX'].map((x, i) => (
              <div className="lane" key={x}>
                <Volume2 size={16} />
                <strong>{x}</strong>
                <span>
                  {i === 0
                    ? 'Premium TTS not connected'
                    : i === 1
                      ? 'Preserve / duck under voice'
                      : 'Optional'}
                </span>
              </div>
            ))}
          </section>

          {mode === 'Pro' && (
            <section className="panel">
              <p className="eyebrow">Pro controls</p>
              <h2>Render intent</h2>
              <label>
                Quality
                <select
                  value={quality}
                  onChange={e => setQuality(e.target.value)}
                >
                  <option>Highest available</option>
                  <option>Balanced</option>
                  <option>Fast preview</option>
                </select>
              </label>
              <label>
                FPS
                <select
                  value={fps}
                  onChange={e => setFps(Number(e.target.value))}
                >
                  <option>24</option>
                  <option>25</option>
                  <option>30</option>
                  <option>60</option>
                </select>
              </label>
              <label>
                Video bitrate
                <select
                  value={bitrate}
                  onChange={e => setBitrate(e.target.value)}
                >
                  <option>6 Mbps</option>
                  <option>10 Mbps</option>
                  <option>16 Mbps</option>
                  <option>24 Mbps</option>
                </select>
              </label>
              <div className="intent">
                <SlidersHorizontal size={16} />
                {quality} · {fps} fps · {bitrate}
              </div>
            </section>
          )}

          <section className="panel">
            <p className="eyebrow">Quality control</p>
            <h2>Preflight</h2>
            {qc.map(([name, state]) => (
              <div className="qc" key={name}>
                <span className={state ? 'ok' : 'pending'}>
                  {state ? <CheckCircle2 size={17} /> : <span>○</span>}
                </span>
                <strong>{name}</strong>
              </div>
            ))}
          </section>
        </aside>
      </section>

      <section className="make">
        <button disabled={!ready} onClick={makeVideo}>
          <Sparkles size={22} />
          <span>MAKE MY VIDEO</span>
          <small>
            {ready
              ? 'Build the production queue'
              : 'Resolve rights preflight first'}
          </small>
        </button>
      </section>

      <section className="panel queue">
        <p className="eyebrow">Production queue</p>
        <h2>What is actually happening</h2>
        {queue.length ? (
          queue.map(([step, state], i) => (
            <div className="queue-row" key={step}>
              <span>{String(i + 1).padStart(2, '0')}</span>
              <strong>{step}</strong>
              <em>{state}</em>
            </div>
          ))
        ) : (
          <p className="desc">
            Nothing queued yet. WildTake will never label storyboard or
            placeholder output as a completed render.
          </p>
        )}
      </section>

      <button className="wild-copilot-fab" onClick={()=>setCopilotOpen(true)}><Bot size={20}/><div><strong>Wild Copilot</strong><small>Original creator assistant</small></div></button>
      {copilotOpen&&<aside className="wild-copilot"><header><div><p className="eyebrow">Floating creator copilot</p><h3>Wild Copilot</h3></div><button onClick={()=>setCopilotOpen(false)}><X size={17}/></button></header><div className="copilot-body"><div className="copilot-answer">{copilotBusy?'Reviewing your current cut…':copilotAnswer}</div><div className="copilot-tools">{['Give me 3 stronger hooks','Make the script funnier without copying anyone','Tighten this to 20 seconds','Give me 5 caption ideas','Use my reference blend to propose a new Short'].map(q=><button key={q} onClick={()=>askCopilot(q)}>{q}</button>)}</div></div><div className="copilot-compose"><textarea rows={2} value={copilotInput} onChange={e=>setCopilotInput(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();void askCopilot();}}} placeholder="Ask about this WildTake project…"/><button onClick={()=>void askCopilot()} disabled={!copilotInput.trim()||copilotBusy}><Send size={17}/></button></div></aside>}

      <footer>
        WildTake Studio uses original narrator presets. “Aussie Wildlife
        Commentator” describes a broad accent and comedy energy only; it does
        not imitate Ozzy Man Reviews / Ethan Marrell's voice, scripts,
        catchphrases, branding, or persona.
      </footer>
    </main>
  );
}
export default App;
