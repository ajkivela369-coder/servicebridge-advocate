from __future__ import annotations
import json, re
from .llm import generate

def _clean_title(text:str,index:int)->str:
    first=re.sub(r'\s+',' ',text.strip()).split('.')[0].strip()
    if not first:return f'Step {index}'
    return first[:58]+('…' if len(first)>58 else '')

def heuristic_lesson(title:str,text:str)->dict:
    paragraphs=[re.sub(r'\s+',' ',p).strip() for p in re.split(r'\n\s*\n',text) if p.strip()]
    if len(paragraphs)<2:
        sentences=re.split(r'(?<=[.!?])\s+',text.strip());size=max(1,len(sentences)//5);paragraphs=[' '.join(sentences[i:i+size]) for i in range(0,len(sentences),size)]
    paragraphs=paragraphs[:8];scenes=[]
    for i,p in enumerate(paragraphs,1):
        clauses=[x.strip(' -•') for x in re.split(r'[;:]\s+|\s+[—–]\s+',p) if x.strip()];bullets=clauses[:4] if len(clauses)>1 else [p]
        scenes.append({'title':_clean_title(p,i),'bullets':bullets,'narration':p})
    return {'title':title,'scenes':scenes,'builder':'heuristic-local'}

def local_llm_lesson(title:str,text:str)->dict|None:
    prompt=f'''Return ONLY valid JSON with this shape: {{"title":"...","scenes":[{{"title":"...","bullets":["..."],"narration":"..."}}]}}.
Create 5-8 short teaching scenes. Preserve factual content. No invented facts. Keep each scene narration under 90 words.
Lesson title: {title}
Source material:\n{text}'''
    r=generate(prompt,max_tokens=1800)
    if not r.get('text'):return None
    try:
        parsed=json.loads(r['text'])
        if parsed.get('scenes'):parsed['builder']=r['engine'];return parsed
    except Exception:return None
    return None

def build_lesson(title:str,text:str,prefer_ollama:bool=True)->dict:
    if prefer_ollama:
        via=local_llm_lesson(title,text)
        if via:return via
    return heuristic_lesson(title,text)
