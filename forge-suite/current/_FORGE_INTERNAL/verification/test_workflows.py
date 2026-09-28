import io, json, os, sys, tempfile, zipfile, time
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'runtime'));os.environ['FORGE_HOME']=str(ROOT/'test-home')
from fastapi.testclient import TestClient
from forge_core.main import app
from forge_core.services import assistant_engine,media_engine,episode
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from PIL import Image,ImageDraw
(ROOT/'test-output').mkdir(exist_ok=True)
client=TestClient(app);results=[]
def check(name,cond):
    if not cond:raise AssertionError(name)
    results.append({'test':name,'status':'passed'})
files=[]
b=io.BytesIO();c=canvas.Canvas(b);c.drawString(70,740,'Fixture record: function varies over time.');c.showPage();c.drawString(70,740,'Original second page retained.');c.save();files.append(('files',('record.pdf',b.getvalue(),'application/pdf')))
b=io.BytesIO();image=Image.new('RGB',(600,300),'white');ImageDraw.Draw(image).text((30,50),'Fixture image exhibit',fill='black');image.save(b,format='PNG');files.append(('files',('figure.png',b.getvalue(),'image/png')))
b=io.BytesIO()
with zipfile.ZipFile(b,'w') as z:z.writestr('word/document.xml','<w:document xmlns:w="urn:word"><w:p><w:t>Fixture provider note: recovery requires rest.</w:t></w:p></w:document>')
files.append(('files',('note.docx',b.getvalue(),'application/vnd.openxmlformats-officedocument.wordprocessingml.document')))
files.append(('files',('message.eml',b'From: fixture@example.test\nTo: recipient@example.test\nSubject: Fixture appointment\nDate: Mon, 28 Sep 2026 09:00:00 -0400\nContent-Type: text/plain\n\nAppointment record and follow-up.','message/rfc822')))
files.append(('files',('diary.txt',b'Fixture: attendance and endurance vary.','text/plain')))
u=client.post('/api/vault/upload-batch',files=files,data={'metadata_json':json.dumps({'date':'2026-09-28','provider':'Test fixture'})});check('five-file upload API succeeds',u.status_code==200 and u.json()['ok']);ids=[x['id'] for x in u.json()['results']];check('five originals preserved',len(ids)==5)
check('extraction/index for PDF DOCX EML TXT',all(x['indexing']['added'] for x in u.json()['results'] if x['name']!='figure.png'))
query=client.post('/api/evidence/query',json={'question':'attendance endurance','k':10}).json();check('search returns source-linked text',any(x['item_id'] in ids for x in query['hits']))
for kind in ('VBA','SSDI','APTD','ADA','CLINICIAN','CUSTOM'):
 r=client.post('/api/evidence/package',json={'kind':kind,'case_name':'Fixture '+kind,'source_ids':ids,'include_originals':True});check(kind+' actual PDF export',r.status_code==200 and Path(r.json()['pdf']).is_file());pdf=PdfReader(r.json()['pdf']);text='\n'.join(p.extract_text() or '' for p in pdf.pages);check(kind+' original second page present','Original second page retained' in text);check(kind+' source bookmarks',len(pdf.outline)>=6)
 if kind=='VBA':Path(ROOT/'test-output/pdf-result.json').write_text(json.dumps(r.json(),indent=2))
check('explicit unknown source rejected',client.post('/api/evidence/package',json={'source_ids':['missing']}).status_code==500)
z=io.BytesIO()
with zipfile.ZipFile(z,'w') as archive:archive.writestr('nested/record.txt','Fixture nested safe content');archive.writestr('../outside.txt','Must not escape extraction')
r=client.post('/api/vault/upload-batch',files=[('files',('bundle.zip',z.getvalue(),'application/zip'))]);check('archive traversal blocked',any('error' in x for x in r.json()['results']) and not (ROOT/'outside.txt').exists())
r=client.post('/api/assistant/document',files={'file':('standalone.txt',b'Elias document attachment context','text/plain')});check('Elias independent document extraction',r.status_code==200 and 'attachment context' in r.json()['text'])
with patch('forge_core.services.elias.model_chat',return_value={'engine':'fixture-only','text':'Fixture answer'}) as m:
 r=client.post('/api/elias/chat',json={'messages':[{'role':'user','content':'Hello'},{'role':'assistant','content':'Earlier reply'},{'role':'user','content':'Use the attachment'}],'context':'Standalone document context','model':'auto'});check('Elias preserves roles/history/document context',r.status_code==200 and m.call_args.args[0][2]['content']=='Earlier reply' and 'Standalone document' in m.call_args.args[0][0]['content'])
 r=client.post('/api/copilot/chat',json={'app':'evidence','messages':[{'role':'user','content':'endurance'}],'source_ids':[ids[-1]],'use_evidence':True});check('copilot retrieval scoped to selected source',all(h['item_id']==ids[-1] for h in r.json()['evidence']))
check('UI editor JSON rejected as workflow',client.post('/api/media/workflow',json={'kind':'video','workflow':{'nodes':[]}}).status_code==400)
with patch('forge_core.services.tts._kokoro',return_value=False),patch('forge_core.services.tts._espeak') as basic:
 from forge_core.services.tts import synthesize
 try:synthesize('test',ROOT/'test-output/voice.wav');raise AssertionError('Must fail')
 except RuntimeError:pass
 check('no silent basic voice downgrade',not basic.called)
# Real FFmpeg assembly, with synthetic fixtures replacing unavailable model/TTS/Comfy inference.
fixture=ROOT/'test-output/shot.png';Image.new('RGB',(320,180),(35,70,100)).save(fixture)
def fake_voice(text,path,voice,allow):
 import wave
 with wave.open(str(path),'wb') as w:w.setparams((1,2,24000,0,'NONE','not compressed'));w.writeframes(b'\0\0'*24000)
 return 'SYNTHETIC-SILENCE-FIXTURE'
workflow=media_engine.workflow_dir()/'image.json';workflow.write_text('{}')
script={'title':'Fixture film','continuity_bible':'Fixture','scenes':[{'visual':'Fixture shot','narration':'Fixture narration'}]}
with patch.object(episode,'chat',return_value={'text':json.dumps(script)}),patch.object(media_engine,'generate',return_value={'files':[str(fixture)],'kind':'image','engine':'FIXTURE'}),patch.object(episode,'synthesize',side_effect=fake_voice),patch.object(episode,'preflight',return_value={'ready':True,'exact_route_ready':True,'fallback_route':None,'message':'fixture','requested_style':'2.5d','ffmpeg_ready':True,'blender':{},'media':{},'auto_setup':{}}):
 movie=episode.build('fixture',1,'image');check('FFmpeg produces playable MP4 from fixture visual + audio',movie['duration_seconds']>=2 and Path(movie['video']).stat().st_size>0);check('captions emitted',Path(movie['captions']).exists())
# One-click 2.5D fallback must not dead-end when ComfyUI is offline but Blender is available.
import subprocess
fixture_video=ROOT/'test-output/blender-fixture.mp4'
subprocess.run(['ffmpeg','-y','-loglevel','error','-loop','1','-i',str(fixture),'-t','2','-vf','scale=320:180','-c:v','libx264','-pix_fmt','yuv420p',str(fixture_video)],check=True)
def fake_blender(kind,prompt,seconds,output_name,progress=lambda x:None):return {'video':str(fixture_video),'image':str(fixture),'blend':str(ROOT/'test-output/fixture.blend'),'boundary':'fixture blender still'}
with patch.object(episode,'chat',return_value={'text':json.dumps(script)}),patch.object(episode,'synthesize',side_effect=fake_voice),patch.object(episode.blender_engine,'find_blender',return_value=Path('/fake/blender')),patch.object(episode.blender_engine,'status',return_value={'installed':True}),patch.object(episode.blender_engine,'render',side_effect=fake_blender),patch.object(media_engine,'status',return_value={'online':False,'image_configured':False,'video_configured':False}),patch.object(media_engine,'ensure_image_workflow',return_value={'ok':False,'configured':False,'changed':False,'reason':'offline'}):
 fallback_movie=episode.build('fixture',1,'2.5d',allow_visual_fallback=True);check('2.5D one-click falls back to Blender stills instead of stopping',fallback_movie['requested_style']=='2.5d' and 'Blender-rendered scene stills' in fallback_movie['route_note'] and Path(fallback_movie['video']).exists())
# MedForge full package must complete even when optional media engines are absent.
buf=io.BytesIO();Image.new('RGB',(320,240),'white').save(buf,format='PNG')
med=client.post('/api/medforge/package',files={'file':('med.png',buf.getvalue(),'image/png')},data={'title':'Fixture MedForge','question':'Explain visible geometry','visual_mode':'auto','seconds':'2'});check('MedForge teaching package job accepted',med.status_code==200);
for _ in range(100):
 med_state=client.get('/api/jobs/'+med.json()['id']).json()
 if med_state['status'] in ('completed','failed','interrupted'):break
 time.sleep(.03)
check('MedForge teaching package produces PDF without optional renderer dead-end',med_state['status']=='completed' and Path(med_state['result']['pdf']).exists())
# Persistent asynchronous queue and result retrieval.
job=media_engine.submit(lambda progress: {'fixture':True})
for _ in range(50):
 state=media_engine.get_job(job['id'])
 if state['status']=='completed':break
 time.sleep(.02)
check('queued job completes and persists result',state['status']=='completed' and state['result']['fixture'])
workflow.unlink()
(ROOT/'test-output/workflow-results.json').write_text(json.dumps({'passed':results,'not_verified':['Real local model quality/context','Real ComfyUI imagery/video generation','Real Kokoro audio/accent','Windows upgrade and shortcut behavior','Medical image analysis accuracy','Premium connected TTS','3D geometry rendering']},indent=2))
print(json.dumps({'passed':len(results),'unverified':7,'report':'test-output/workflow-results.json'}))
