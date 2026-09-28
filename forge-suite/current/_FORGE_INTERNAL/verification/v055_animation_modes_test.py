import json, os, tempfile, wave, math, struct, subprocess
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]/'runtime'
sys.path.insert(0,str(ROOT))
from forge_core.services import episode


def silence(path, seconds=.8, rate=24000):
    n=int(seconds*rate)
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate)
        w.writeframes(b''.join(struct.pack('<h',0) for _ in range(n)))


def main():
    results={}
    with tempfile.TemporaryDirectory() as td:
        td=Path(td);out=td/'outputs';out.mkdir();cfg=td/'workflows';cfg.mkdir();(cfg/'image.json').write_text('{}');(cfg/'video.json').write_text('{}')
        episode.OUTPUTS=out
        episode.media_engine.workflow_dir=lambda:cfg
        episode.chat=lambda messages, model='auto', max_tokens=4000:{'text':json.dumps({'title':'Fixture Film','continuity_bible':'same hero, same suit, same station','music_sfx_plan':'fixture plan','scenes':[{'visual':'Hero crosses station','narration':'The hero moves through the station.','camera':'slow push','continuity':'same suit'},{'visual':'Hero reaches reactor','narration':'The reactor comes into view.','camera':'tracking shot','continuity':'same suit'}]})}
        episode.synthesize=lambda text,path,voice,allow_basic_fallback=False:(silence(path), 'fixture-voice')[1]
        def gen(kind,prompt,progress=lambda x:None):
            if kind=='image':
                p=out/('fixture-'+str(len(list(out.glob('*.png'))))+'.png')
                subprocess.run(['ffmpeg','-y','-loglevel','error','-f','lavfi','-i','color=c=0x12304a:s=1280x720','-frames:v','1',str(p)],check=True)
            else:
                p=out/('fixture-'+str(len(list(out.glob('*.mp4'))))+'.mp4')
                subprocess.run(['ffmpeg','-y','-loglevel','error','-f','lavfi','-i','color=c=0x25113a:s=1280x720:r=24','-t','1','-pix_fmt','yuv420p',str(p)],check=True)
            return {'engine':'fixture','files':[str(p)]}
        episode.media_engine.generate=gen
        episode.blender_engine.find_blender=lambda:Path('/bin/true')
        def br(kind,prompt,seconds,output_name,progress=lambda x:None):
            mp4=out/(output_name+'.mp4');png=out/(output_name+'.png');blend=out/(output_name+'.blend')
            subprocess.run(['ffmpeg','-y','-loglevel','error','-f','lavfi','-i','color=c=0x3a240b:s=1280x720:r=24','-t','1','-pix_fmt','yuv420p',str(mp4)],check=True)
            subprocess.run(['ffmpeg','-y','-loglevel','error','-f','lavfi','-i','color=c=0x3a240b:s=1280x720','-frames:v','1',str(png)],check=True);blend.write_bytes(b'BLENDER_FIXTURE')
            return {'engine':'Blender-fixture','video':str(mp4),'image':str(png),'blend':str(blend),'boundary':'fixture'}
        episode.blender_engine.render=br
        for style in ('3d','2.5d','2d'):
            r=episode.build('fixture premise',2,style,'bf_emma','auto',False)
            video=Path(r['video']);caps=Path(r['captions']);manifest=Path(r['manifest'])
            results[style]={'ok':video.exists() and video.stat().st_size>0 and caps.exists() and manifest.exists(),'video':str(video),'bytes':video.stat().st_size,'render_type':r['render_type'],'assets':len(r['assets'])}
        print(json.dumps(results,indent=2))
        if not all(x['ok'] for x in results.values()): raise SystemExit(1)
if __name__=='__main__':main()
