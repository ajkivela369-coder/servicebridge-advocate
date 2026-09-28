from __future__ import annotations
import json, re
from .llm import generate
from .render import render_lesson


def storyboard(premise: str, scene_count: int = 6):
    scene_count = max(1, min(12, scene_count))
    prompt = (
        'Return ONLY JSON: {"title":"...","logline":"...","scenes":[{"beat":"...","visual":"...",'
        '"camera":"...","audio":"...","continuity":["..."]}]}. '
        f'Make exactly {scene_count} scenes. Preserve continuity, escalation and a coherent ending. Premise/production brief: {premise}'
    )
    r = generate(prompt, preferred_model='qwen2.5:3b', max_tokens=2200)
    if r.get('text'):
        txt = re.sub(r'^```(?:json)?|```$', '', r['text'].strip(), flags=re.M).strip()
        try:
            return {'engine': r['engine'], 'plan': json.loads(txt)}
        except Exception:
            pass
    beats = []
    for i in range(scene_count):
        phase='Opening' if i==0 else ('Finale' if i==scene_count-1 else f'Escalation {i}')
        beats.append({
            'beat': f'{phase} · Scene {i+1}',
            'visual': premise if i == 0 else f'Continue the established world and action, advancing the objective in beat {i+1}.',
            'camera': 'Motivated cinematic coverage with readable geography',
            'audio': 'Dialogue / ambience / score as appropriate',
            'continuity': ['Preserve character appearance', 'Preserve geography and props', 'Carry forward damage / costume state'],
        })
    return {'engine': 'template-local', 'plan': {'title': 'Local Storyboard', 'logline': premise[:220], 'scenes': beats}}


def _render_storyboard(sb:dict, output_name:str):
    scenes=[]
    for i, scene in enumerate(sb['plan'].get('scenes', []), 1):
        continuity = scene.get('continuity') or []
        bullets = [
            f"Visual: {scene.get('visual', '')}",
            f"Camera: {scene.get('camera', '')}",
            f"Audio: {scene.get('audio', '')}",
        ]
        if continuity: bullets.append('Continuity: ' + '; '.join(str(x) for x in continuity[:4]))
        narration=(f"Scene {i}. {scene.get('beat', '')}. Visual plan: {scene.get('visual', '')}. "
                   f"Camera: {scene.get('camera', '')}. Continuity remains locked to the established world and prior scene state.")
        scenes.append({'title': scene.get('beat') or f'Scene {i}','bullets':bullets,'narration':narration})
    lesson={'title':sb['plan'].get('title') or 'GrimForge Local Episode','builder':f"grimforge-{sb.get('engine','local')}",'scenes':scenes}
    return render_lesson(lesson,output_name)


def animatic(premise: str, scene_count: int = 4, output_name: str = 'grimforge-local-animatic'):
    sb=storyboard(premise,scene_count); rendered=_render_storyboard(sb,output_name)
    return {'storyboard':sb,'render':rendered}


def full_episode(premise:str, scene_count:int=6, output_name:str='grimforge-full-episode')->dict:
    """One click: plan once, preserve that exact plan, then render the local episode animatic."""
    sb=storyboard(premise,scene_count)
    rendered=_render_storyboard(sb,output_name)
    return {
        'ok':True,
        'render_type':'Local Animatic',
        'storyboard':sb,
        'render':rendered,
        'pipeline':['production brief','continuity-aware storyboard','director plan','local narration','FFmpeg episode animatic'],
        'note':'External cinematic engines remain optional shot-replacement boosters; this local animatic path does not require hosted video credits.'
    }
