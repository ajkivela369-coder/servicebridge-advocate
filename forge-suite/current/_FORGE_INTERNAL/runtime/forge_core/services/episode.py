import json, re, shutil, subprocess, uuid
from pathlib import Path
from .assistant_engine import chat
from . import media_engine, blender_engine
from .tts import synthesize
from .render import OUTPUTS, _duration, _srt_time


def _fit_video(src: Path, wav: Path, duration: float, out: Path, style: str, scene_index: int):
    """Pair a rendered visual clip with narration and normalize to 720p H.264."""
    vf='scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=24,format=yuv420p'
    subprocess.run(['ffmpeg','-y','-loglevel','error','-stream_loop','-1','-i',str(src),'-i',str(wav),'-map','0:v:0','-map','1:a:0','-t',str(duration),'-vf',vf,'-c:v','libx264','-preset','fast','-crf','19','-c:a','aac','-ar','48000','-ac','2',str(out)],check=True,timeout=1200)


def _animate_still(src: Path, wav: Path, duration: float, out: Path, scene_index: int):
    """Create a 2.5D-style camera move from an image.

    This is a depth-inspired cinematic move, not reconstructed multilayer geometry.
    """
    frames=max(48,int(duration*24))
    if scene_index % 2:x="iw/2-(iw/zoom/2)+(on/%d)*24" % max(frames,1)
    else:x="iw/2-(iw/zoom/2)-(on/%d)*24" % max(frames,1)
    vf=("scale=1536:864:force_original_aspect_ratio=increase,crop=1536:864,"
        f"zoompan=z='min(zoom+0.0007,1.12)':x='{x}':y='ih/2-(ih/zoom/2)':d={frames}:s=1280x720:fps=24,"
        "eq=contrast=1.03:saturation=1.06,format=yuv420p")
    subprocess.run(['ffmpeg','-y','-loglevel','error','-loop','1','-i',str(src),'-i',str(wav),'-map','0:v:0','-map','1:a:0','-t',str(duration),'-vf',vf,'-c:v','libx264','-preset','fast','-crf','19','-c:a','aac','-ar','48000','-ac','2',str(out)],check=True,timeout=1200)


def _norm_style(animation_style):
    style=str(animation_style).lower().replace(' ','')
    aliases={'3d':'3d','2.5d':'2.5d','25d':'2.5d','2d':'2d','video':'2d','image':'2.5d'}
    style=aliases.get(style,style)
    if style not in ('3d','2.5d','2d'):raise ValueError('Animation style must be 3D, 2.5D, or 2D.')
    return style


def preflight(animation_style='2.5d'):
    style=_norm_style(animation_style)
    media=media_engine.status(); blender=blender_engine.status(); ffmpeg=bool(shutil.which('ffmpeg') and shutil.which('ffprobe'))
    image_ready=bool(media.get('online') and media.get('image_configured'))
    video_ready=bool(media.get('online') and media.get('video_configured'))
    # If ComfyUI is online with a checkpoint, configure the standard image route automatically.
    if style in ('2.5d','2d') and media.get('online') and not image_ready:
        setup=media_engine.ensure_image_workflow();media=media_engine.status();image_ready=bool(media.get('online') and media.get('image_configured'))
    else: setup={'changed':False}
    if style=='3d':
        exact=bool(blender.get('installed')); fallback='2.5d' if image_ready else ('2.5d-blender-still' if blender.get('installed') else ('2d' if video_ready else None))
    elif style=='2.5d':
        exact=image_ready; fallback='2.5d-blender-still' if blender.get('installed') else ('2d' if video_ready else None)
    else:
        exact=video_ready; fallback='2.5d' if image_ready else ('3d' if blender.get('installed') else None)
    return {'requested_style':style,'ffmpeg_ready':ffmpeg,'blender':blender,'media':media,'exact_route_ready':exact,'fallback_route':fallback,'auto_setup':setup,
            'ready':bool(ffmpeg and (exact or fallback)),
            'message':('Exact visual route ready.' if exact else (f'Exact route unavailable; one-click can fall back to {fallback}.' if fallback else 'No visual renderer is ready.'))}


def build(premise,scene_count=4,animation_style='2.5d',voice='bf_emma',model='auto',allow_basic_fallback=False,allow_visual_fallback=True,progress=lambda x:None):
    """Build a narrated episode with a non-dead-ending Simple-mode fallback ladder.

    Requested routes:
      3d   -> Blender-rendered genuine 3D scene motion.
      2.5d -> ComfyUI generated images + depth-inspired camera motion.
      2d   -> ComfyUI generated motion clips.

    If allow_visual_fallback is true, one-click Simple mode may use an installed fallback route
    rather than aborting. The result always records requested_style, actual_style and route notes.
    """
    requested=_norm_style(animation_style)
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):raise RuntimeError('Install FFmpeg and FFprobe in Setup & Repair before rendering.')
    pf=preflight(requested)
    if not pf['ready']:raise RuntimeError(pf['message']+' Open Media setup or Setup & Repair.')

    actual=requested;route_note='Exact requested route used.'
    if not pf['exact_route_ready']:
        if not allow_visual_fallback:raise RuntimeError(pf['message'])
        fallback=pf.get('fallback_route')
        if fallback=='2.5d-blender-still':actual='2.5d';route_note='2.5D requested; ComfyUI image generation was unavailable, so Blender-rendered scene stills were animated with cinematic depth motion.'
        elif fallback in ('2.5d','2d','3d'):actual=fallback;route_note=f'{requested} requested; exact route unavailable, so one-click used the installed {fallback} visual route.'
        else:raise RuntimeError('No installed visual fallback is available.')
    use_blender_stills=(requested=='2.5d' and not pf['exact_route_ready'] and pf.get('fallback_route')=='2.5d-blender-still')

    progress('Writing script, continuity bible, and production plan')
    response=chat([{'role':'system','content':'You write coherent cinematic scripts. Return only JSON: {"title":"...","continuity_bible":"...","music_sfx_plan":"...","scenes":[{"visual":"...","narration":"...","camera":"...","continuity":"..."}]}. Narration is spoken story prose, never camera instructions.'},{'role':'user','content':f'Write exactly {scene_count} scenes for a {actual} animated episode. Production brief: {premise}'}],model,4000)
    if not response.get('text'):raise RuntimeError(response.get('error','Script model unavailable'))
    raw=re.sub(r'^```(?:json)?\s*|\s*```$','',response['text'].strip())
    try:script=json.loads(raw)
    except Exception:raise RuntimeError('The model did not return a valid script. Nothing was rendered; retry with another model.')
    scenes=script.get('scenes',[])
    if len(scenes)!=scene_count or any(not s.get('visual') or not s.get('narration') for s in scenes):raise RuntimeError('Incomplete script: every requested scene needs a visual and narration.')

    run_id=uuid.uuid4().hex;work=OUTPUTS/('episode-'+run_id);work.mkdir(parents=True,exist_ok=True);(work/'script.json').write_text(json.dumps(script,indent=2))
    clips=[];timeline=[];cursor=0;assets=[]
    for i,scene in enumerate(scenes,1):
        wav=work/f'voice-{i}.wav';progress(f'Scene {i}/{len(scenes)}: recording {voice}')
        engine=synthesize(scene['narration'],wav,voice,allow_basic_fallback);duration=max(2,_duration(wav)+.35);clip=work/f'scene-{i}.mp4'
        continuity=scene.get('continuity') or script.get('continuity_bible','')
        prompt=f"{script.get('continuity_bible','')}\nContinuity for this scene: {continuity}\nVisual: {scene['visual']}\nCamera: {scene.get('camera','')}\nAnimation style: {actual}. Maintain character, costume, prop and environment continuity."
        if actual=='3d':
            progress(f'Scene {i}/{len(scenes)}: rendering genuine 3D animation in Blender')
            r=blender_engine.render('grimforge',prompt,min(duration,30),f'grimforge-3d-scene-{i}',progress);visual=Path(r['video']);_fit_video(visual,wav,duration,clip,actual,i);media={'engine':'Blender','files':[str(visual)],'blend':r.get('blend'),'still':r.get('image'),'boundary':r.get('boundary')}
        elif actual=='2.5d':
            if use_blender_stills:
                progress(f'Scene {i}/{len(scenes)}: rendering Blender scene still for 2.5D fallback')
                r=blender_engine.render('grimforge',prompt,2.0,f'grimforge-25d-still-{i}',progress);visual=Path(r['image']);media={'engine':'Blender still → 2.5D motion','files':[str(visual)],'blend':r.get('blend'),'boundary':'Fallback route: Blender-generated still animated with cinematic 2.5D camera motion.'}
            else:
                progress(f'Scene {i}/{len(scenes)}: generating illustrated shot')
                media=media_engine.generate('image','Cinematic layered composition with foreground, midground and background depth. '+prompt,progress);visual=Path(media['files'][0])
            _animate_still(visual,wav,duration,clip,i)
        else:
            progress(f'Scene {i}/{len(scenes)}: generating full 2D motion shot')
            media=media_engine.generate('video','High quality 2D cinematic animation, coherent illustrated characters and environment. '+prompt,progress);visual=Path(media['files'][0]);_fit_video(visual,wav,duration,clip,actual,i)
        clips.append(clip);assets.append({'scene':i,'requested_style':requested,'actual_style':actual,'media':media,'assembled_clip':str(clip)})
        timeline.append({'scene':i,'start':cursor,'end':cursor+duration,'narration':scene['narration'],'voice':engine,'media':media});cursor+=duration

    progress('Assembling final MP4 and captions')
    concat=work/'concat.txt';concat.write_text('\n'.join("file '"+p.as_posix()+"'" for p in clips))
    final=OUTPUTS/('grimforge-'+actual.replace('.','')+'-'+run_id+'.mp4')
    subprocess.run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(final)],check=True,timeout=1200)
    captions=final.with_suffix('.srt');captions.write_text('\n\n'.join(f"{t['scene']}\n{_srt_time(t['start'])} --> {_srt_time(t['end'])}\n{t['narration']}" for t in timeline),encoding='utf-8')
    labels={'3d':'Full 3D animation · Blender','2.5d':'2.5D cinematic depth animation','2d':'Full 2D animation · generated motion shots'}
    result={'video':str(final),'captions':str(captions),'duration_seconds':_duration(final),'requested_style':requested,'animation_style':actual,'render_type':labels[actual],'route_note':route_note,'voice':voice,'timeline':timeline,'assets':assets,'script':script,'preflight':pf,'music_status':'Music/SFX plan is preserved in the manifest; this build assembles narration and visual motion. Add/mix generated music/SFX in the Pro audio stage.'}
    manifest=final.with_suffix('.json');result['manifest']=str(manifest);manifest.write_text(json.dumps(result,indent=2));return result
