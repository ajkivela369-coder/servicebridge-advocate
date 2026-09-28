from __future__ import annotations
from pathlib import Path
import json, os, tempfile
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .services.detect import capabilities
from .services.lesson import build_lesson
from .services.render import render_lesson
from .services.router import routing_summary
from .services.embeddings import embed
from .services.flow import animate_flow
from .services.policy import model_policy
from .services.transcribe import transcribe as transcribe_file
from .services.vision import analyze_image
from .services.vector_store import add as vector_add, query as vector_query, clear as vector_clear
from .services.design import design_status, render_local_page
from .services.hardware import current_hardware
from .services.bridge import bridge_config
from .services.learning import manifest as learning_manifest, coverage as learning_coverage, feature as learning_feature
from .services.vault import import_file as vault_import, add_text as vault_add_text, list_items as vault_list, search as vault_search, add_claim as vault_add_claim, claims as vault_claims
from .services.evidence import query_evidence, timeline as evidence_timeline, packet_outline, build_packet
from .services.medforge import inspect_image as medforge_inspect_image, make_lesson as medforge_make_lesson
from .services.medforge_package import build as build_medforge_package
from .services.grimforge import storyboard as grimforge_storyboard, animatic as grimforge_animatic, full_episode as grimforge_full_episode
from .services.system_ops import status as system_status, backup as system_backup, open_desktop_controls
from .services.document_text import extract_text
from .services.elias import chat as elias_chat
from forge_base.forge_base import forge_home as resilience_home, init as resilience_init, report as resilience_report
from forge_base.model_manager import model_status

ROOT=Path(__file__).resolve().parents[1]
STATIC=Path(__file__).resolve().parent/'static'
LEARN=ROOT/'learning'/'web'
SETTINGS=ROOT/'data'/'settings.json'
OUTPUTS=ROOT/'data'/'outputs'
UPLOADS=ROOT/'data'/'uploads'
app=FastAPI(title='Forge Core',version='0.5.6-Workflow-Recovery',docs_url='/docs')
app.add_middleware(CORSMiddleware,allow_origins=['http://127.0.0.1:8787','http://localhost:8787'],allow_origin_regex=r'https://.*\.lovable\.app|https://.*\.lovableproject\.com|http://localhost(:\d+)?|http://127\.0\.0\.1(:\d+)?',allow_methods=['*'],allow_headers=['*'],allow_credentials=False)
app.mount('/static',StaticFiles(directory=STATIC),name='static')

class LessonRequest(BaseModel):
    title:str=Field(min_length=1,max_length=180); source_text:str=Field(min_length=1,max_length=50000); output_name:str=Field(default='teach-me-this',pattern=r'^[A-Za-z0-9._-]+$'); prefer_ollama:bool=True
class ModeRequest(BaseModel): mode:str
class EmbedRequest(BaseModel): texts:list[str]=Field(min_length=1,max_length=64)
class FlowRequest(BaseModel): title:str='Find where the chain broke'; nodes:list[str]=Field(min_length=2,max_length=10); output_name:str=Field(default='flow',pattern=r'^[A-Za-z0-9._-]+$'); seconds_per_step:float=Field(default=1.4,ge=.4,le=10)
class VectorAddRequest(BaseModel): collection:str=Field(min_length=1,max_length=120); texts:list[str]=Field(min_length=1,max_length=256); metadata:list[dict]|None=None
class VectorQueryRequest(BaseModel): collection:str=Field(min_length=1,max_length=120); text:str=Field(min_length=1,max_length=20000); k:int=Field(default=5,ge=1,le=50)
class VaultTextRequest(BaseModel): item_id:str; text:str=Field(min_length=1,max_length=500000); metadata:dict|None=None
class VaultSearchRequest(BaseModel): text:str=Field(min_length=1,max_length=20000); k:int=Field(default=5,ge=1,le=50)
class ClaimRequest(BaseModel): statement:str=Field(min_length=1,max_length=30000); source_ids:list[str]=Field(min_length=1,max_length=100); metadata:dict|None=None
class EvidenceQueryRequest(BaseModel): question:str=Field(min_length=1,max_length=20000); k:int=Field(default=6,ge=1,le=50)
class EvidencePacketRequest(BaseModel): kind:str='VBA'; case_name:str='Evidence Packet'; source_ids:list[str]|None=None; include_originals:bool=False
class EliasChatRequest(BaseModel): messages:list[dict]=Field(min_length=1,max_length=64); use_evidence:bool=False; evidence_k:int=Field(default=6,ge=1,le=20); model:str="auto"; context:str=Field(default="",max_length=16000)
class MedLessonRequest(BaseModel): title:str=Field(min_length=1,max_length=180); source_text:str=Field(min_length=1,max_length=50000)
class GrimRequest(BaseModel): premise:str=Field(min_length=1,max_length=30000); scene_count:int=Field(default=6,ge=1,le=12)
class GrimAnimaticRequest(BaseModel): premise:str=Field(min_length=1,max_length=30000); scene_count:int=Field(default=4,ge=1,le=8); output_name:str=Field(default='grimforge-local-animatic',pattern=r'^[A-Za-z0-9._-]+$')
class GrimEpisodeRequest(BaseModel): premise:str=Field(min_length=1,max_length=30000); scene_count:int=Field(default=6,ge=1,le=12); output_name:str=Field(default='grimforge-full-episode',pattern=r'^[A-Za-z0-9._-]+$')


def read_settings(): return json.loads(SETTINGS.read_text()) if SETTINGS.exists() else {'mode':'LOCAL_ONLY','cloud_requires_confirmation':True}

@app.get('/')
def home(): return FileResponse(STATIC/'index.html')
@app.get('/workspace')
def workspace_home(): return FileResponse(STATIC/'index.html')
@app.get('/learn')
def learn_home(): return FileResponse(LEARN/'index.html')
@app.get('/api/health')
def health(): return {'ok':True,'name':'Forge Core','version':'0.5.6-Workflow-Recovery','settings':read_settings(),'surfaces':{'workspace':'/','learn':'/learn'}}
@app.get('/api/capabilities')
def get_capabilities(): return capabilities()
@app.get('/api/router')
def get_routes(): return routing_summary()
@app.get('/api/models')
def get_models(): return model_status(resilience_home())
@app.get('/api/policy')
def get_policy(): return model_policy()
@app.get('/api/hardware')
def get_hardware(): return current_hardware()
@app.get('/api/bridge/config')
def get_bridge(): return bridge_config()
@app.get('/api/design/status')
def get_design_status(): return design_status()
@app.get('/api/learning/manifest')
def get_learning_manifest(): return learning_manifest()
@app.get('/api/learning/coverage')
def get_learning_coverage(): return learning_coverage()
@app.get('/api/learning/feature/{feature_id}')
def get_learning_feature(feature_id:str):
    item=learning_feature(feature_id)
    if not item: raise HTTPException(404,'Learning feature not found')
    return item
@app.get('/api/resilience')
def resilience(): return resilience_report(resilience_home())
@app.get('/api/system/status')
def get_system_status(): return system_status()
@app.post('/api/system/backup')
def create_system_backup(include_models:bool=False):
    try:return system_backup(include_models)
    except Exception as e: raise HTTPException(500,str(e))
@app.post('/api/system/open-controls')
def launch_desktop_controls():
    try:return open_desktop_controls()
    except Exception as e: raise HTTPException(500,str(e))
@app.post('/api/workspace/init')
def init_workspace():
    root=resilience_home(); env=resilience_init(root); return {'ok':True,'forge_home':str(root),'env_script':str(env)}
@app.post('/api/mode')
def set_mode(body:ModeRequest):
    if body.mode not in {'LOCAL_ONLY','HYBRID'}: raise HTTPException(400,'Mode must be LOCAL_ONLY or HYBRID')
    settings={'mode':body.mode,'cloud_requires_confirmation':True}; SETTINGS.parent.mkdir(parents=True,exist_ok=True); SETTINGS.write_text(json.dumps(settings,indent=2)); return settings
@app.post('/api/teach/render')
def teach(body:LessonRequest):
    lesson=build_lesson(body.title,body.source_text,prefer_ollama=body.prefer_ollama)
    try: result=render_lesson(lesson,body.output_name)
    except Exception as e: raise HTTPException(500,str(e))
    return {'settings':read_settings(),'lesson':lesson,'result':result}
@app.post('/api/embeddings')
def embeddings(body:EmbedRequest): return embed(body.texts)
@app.post('/api/diagram/animate')
def flow(body:FlowRequest):
    OUTPUTS.mkdir(parents=True,exist_ok=True); out=OUTPUTS/f'{body.output_name}.mp4'
    try:return animate_flow(body.nodes,out,body.title,body.seconds_per_step)
    except Exception as e: raise HTTPException(500,str(e))
@app.post('/api/vector/add')
def vec_add(body:VectorAddRequest):
    if body.metadata is not None and len(body.metadata)!=len(body.texts): raise HTTPException(400,'metadata length must match texts')
    return vector_add(body.collection,body.texts,body.metadata)
@app.post('/api/vector/query')
def vec_query(body:VectorQueryRequest): return vector_query(body.collection,body.text,body.k)
@app.delete('/api/vector/{collection}')
def vec_clear(collection:str): return vector_clear(collection)
@app.post('/api/transcribe')
async def transcribe_upload(file:UploadFile=File(...),quality:str=Form('small.en')):
    UPLOADS.mkdir(parents=True,exist_ok=True); safe=Path(file.filename or 'audio.bin').name; path=UPLOADS/safe; path.write_bytes(await file.read())
    try:return transcribe_file(path,quality)
    except Exception as e:raise HTTPException(500,str(e))
    finally:path.unlink(missing_ok=True)
@app.post('/api/vision')
async def vision_upload(file:UploadFile=File(...),prompt:str=Form('Describe only what is visibly present. Separate observation from interpretation.')):
    UPLOADS.mkdir(parents=True,exist_ok=True); safe=Path(file.filename or 'image.bin').name; path=UPLOADS/safe; path.write_bytes(await file.read())
    try:return analyze_image(path,prompt,model='qwen2.5vl:3b')
    except Exception as e:raise HTTPException(500,str(e))
    finally:path.unlink(missing_ok=True)

# Forge Vault / Evidence Auditor
@app.post('/api/vault/upload')
async def vault_upload(file:UploadFile=File(...),metadata_json:str=Form('{}'),auto_index:bool=Form(True)):
    UPLOADS.mkdir(parents=True,exist_ok=True); safe=Path(file.filename or 'source.bin').name; path=UPLOADS/safe; path.write_bytes(await file.read())
    try:
        try:meta=json.loads(metadata_json)
        except Exception:meta={}
        rec=vault_import(path,meta,'forge-api-upload'); extraction=extract_text(path) if auto_index else {'text':'','method':'disabled','warning':None}
        if extraction.get('text'):
            idx=vault_add_text(rec['id'],extraction['text'],meta)
        else:idx={'added':0}
        return rec|{'text_extraction':{'method':extraction.get('method'),'characters':len(extraction.get('text','')),'warning':extraction.get('warning')},'indexing':idx}
    finally:path.unlink(missing_ok=True)
@app.post('/api/vault/upload-batch')
async def vault_upload_batch(files:list[UploadFile]=File(...),metadata_json:str=Form('{}'),auto_index:bool=Form(True)):
    from .services.ingestion import ingest
    from starlette.concurrency import run_in_threadpool
    try:meta=json.loads(metadata_json)
    except Exception:meta={}
    if not isinstance(meta,dict):raise HTTPException(400,'Metadata must be an object')
    if len(files)>100:raise HTTPException(413,'Upload at most 100 files at a time.')
    results=[]
    with tempfile.TemporaryDirectory() as td:
        for n,file in enumerate(files):
            folder=Path(td)/str(n);folder.mkdir();path=folder/Path(file.filename or 'source.bin').name
            data=await file.read(50*1024*1024+1)
            if len(data)>50*1024*1024:
                results.append({'name':path.name,'error':'File exceeds 50 MB upload limit.'});continue
            path.write_bytes(data)
            try:results.extend(await run_in_threadpool(ingest,path,meta,auto_index))
            except Exception as e:results.append({'name':path.name,'error':str(e)})
    return {'ok':all('error' not in x for x in results),'count':len(results),'results':results}
@app.post('/api/vault/text')
def vault_text(body:VaultTextRequest): return vault_add_text(body.item_id,body.text,body.metadata)
@app.get('/api/vault/items')
def vault_items(limit:int=200): return {'items':vault_list(min(max(limit,1),500))}
@app.post('/api/vault/search')
def vault_search_api(body:VaultSearchRequest): return {'hits':vault_search(body.text,body.k)}
@app.post('/api/vault/claim')
def vault_claim(body:ClaimRequest): return vault_add_claim(body.statement,body.source_ids,body.metadata)
@app.get('/api/vault/claims')
def get_claims(): return {'claims':vault_claims()}
@app.post('/api/evidence/query')
def evidence_query(body:EvidenceQueryRequest): return query_evidence(body.question,body.k)
@app.get('/api/evidence/timeline')
def evidence_timeline_api(): return {'timeline':evidence_timeline()}
@app.get('/api/evidence/packet')
def evidence_packet(case_name:str='Evidence Packet',kind:str='GENERAL'): return packet_outline(case_name,kind)
@app.post('/api/evidence/package')
def evidence_package(body:EvidencePacketRequest):
    try:return build_packet(body.kind,body.case_name,body.source_ids,body.include_originals)
    except Exception as e:raise HTTPException(500,str(e))

# Elias local assistant
@app.post('/api/elias/chat')
def elias_chat_api(body:EliasChatRequest):
    try:return elias_chat(body.messages,body.use_evidence,body.evidence_k,body.model,"elias",body.context)
    except Exception as e:raise HTTPException(500,str(e))

# MedForge
@app.post('/api/medforge/lesson')
def medforge_lesson(body:MedLessonRequest): return medforge_make_lesson(body.title,body.source_text)
@app.post('/api/medforge/vision')
async def medforge_vision(file:UploadFile=File(...),question:str=Form('Teach me what is visibly present and what should be verified next.')):
    UPLOADS.mkdir(parents=True,exist_ok=True); safe=Path(file.filename or 'medical-image.bin').name; path=UPLOADS/safe; path.write_bytes(await file.read())
    try:return medforge_inspect_image(path,question)
    finally:path.unlink(missing_ok=True)

@app.post('/api/medforge/package')
async def medforge_package(file:UploadFile=File(...),title:str=Form('MedForge Teaching Package'),question:str=Form('Teach me what is visibly present and what should be verified next.'),visual_mode:str=Form('auto'),seconds:float=Form(7.0)):
    UPLOADS.mkdir(parents=True,exist_ok=True)
    suffix=Path(file.filename or 'medical-image.png').suffix or '.png'
    path=UPLOADS/f'medforge-package-{os.urandom(8).hex()}{suffix}'
    data=await file.read(50*1024*1024+1)
    if len(data)>50*1024*1024:raise HTTPException(413,'MedForge image limit is 50 MB.')
    path.write_bytes(data)
    # The worker owns the staged copy and removes it after completion.
    def run(staged,title,question,visual_mode,seconds,progress=lambda x:None):
        try:return build_medforge_package(staged,title,question,visual_mode,seconds,progress)
        finally:Path(staged).unlink(missing_ok=True)
    return media_engine.submit(run,str(path),title,question,visual_mode,seconds)

# GrimForge
@app.post('/api/grimforge/storyboard')
def grimforge_plan(body:GrimRequest): return grimforge_storyboard(body.premise,body.scene_count)
@app.post('/api/grimforge/animatic')
def grimforge_animatic_api(body:GrimAnimaticRequest):
    try:return grimforge_animatic(body.premise,body.scene_count,body.output_name)
    except Exception as e:raise HTTPException(500,str(e))
@app.post('/api/grimforge/episode')
def grimforge_episode_api(body:GrimEpisodeRequest):
    try:return grimforge_full_episode(body.premise,body.scene_count,body.output_name)
    except Exception as e:raise HTTPException(500,str(e))

@app.get('/api/outputs')
def list_outputs(limit:int=24):
    OUTPUTS.mkdir(parents=True,exist_ok=True)
    allowed={'.mp4':'video','.webm':'video','.mov':'video','.png':'image','.jpg':'image','.jpeg':'image','.webp':'image','.pdf':'document','.blend':'3d','.json':'manifest','.srt':'captions'}
    rows=[]
    for p in sorted((x for x in OUTPUTS.iterdir() if x.is_file() and x.suffix.lower() in allowed),key=lambda x:x.stat().st_mtime,reverse=True)[:max(1,min(limit,100))]:
        st=p.stat();rows.append({'name':p.name,'kind':allowed[p.suffix.lower()],'bytes':st.st_size,'modified':st.st_mtime,'url':'/api/outputs/'+p.name})
    return {'items':rows}

@app.get('/api/outputs/{filename}')
def output_file(filename:str):
    safe=Path(filename).name; path=OUTPUTS/safe
    if not path.exists():raise HTTPException(404,'Output not found')
    return FileResponse(path)

@app.get('/api/exports/{filename}')
def export_file(filename:str):
    safe=Path(filename).name; path=resilience_home()/'exports'/safe
    if not path.exists():raise HTTPException(404,'Export not found')
    return FileResponse(path,filename=safe)

# v0.5.4 shared assistant, tools and media services.
from .services import media_engine
from .services import blender_engine
from .services.episode import build as build_media_episode
from .services.assistant_engine import models as assistant_models
from typing import Literal

class CopilotRequest(BaseModel):
    messages:list[dict]=Field(min_length=1,max_length=64)
    app:Literal['elias','evidence','medforge','grimforge','workspace']='elias'
    context:str=Field(default='',max_length=16000)
    model:str=Field(default='auto',max_length=120)
    use_evidence:bool=False
    source_ids:list[str]=Field(default_factory=list,max_length=1000)

class MediaRequest(BaseModel):
    kind:Literal['image','video']='image'
    prompt:str=Field(min_length=1,max_length=16000)

class WorkflowRequest(BaseModel):
    kind:Literal['image','video']
    workflow:dict

class CheckpointRequest(BaseModel):
    checkpoint:str=Field(min_length=1,max_length=240)

class BlenderRenderRequest(BaseModel):
    product:Literal['medforge','grimforge']
    prompt:str=Field(default='',max_length=16000)
    seconds:float=Field(default=6.0,ge=2.0,le=30.0)
    output_name:str=Field(default='forge-3d-render',pattern=r'^[A-Za-z0-9._-]+$')

class EpisodeRequest(BaseModel):
    premise:str=Field(min_length=1,max_length=16000)
    scene_count:int=Field(default=4,ge=1,le=12)
    animation_style:Literal['3d','2.5d','2d']='2.5d'
    voice:Literal['bf_emma','bm_george','af_heart']='bf_emma'
    model:str=Field(default='auto',max_length=120)
    allow_basic_fallback:bool=False
    allow_visual_fallback:bool=True

@app.get('/api/assistant/models')
def assistant_model_list():return {'models':assistant_models(),'default':'auto','routing':'Local models only. Larger selections may require more memory.'}

@app.post('/api/copilot/chat')
def copilot_chat(body:CopilotRequest):
    return elias_chat(body.messages,body.use_evidence,6,body.model,body.app,body.context,body.source_ids)

@app.post('/api/assistant/document')
async def assistant_document(file:UploadFile=File(...)):
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/Path(file.filename or 'document.bin').name
        data=await file.read(20*1024*1024+1)
        if len(data)>20*1024*1024:raise HTTPException(413,'Document limit is 20 MB.')
        path.write_bytes(data);from .services.ingestion import extract
        extraction=extract(path)
        return {'name':path.name,**extraction,'text':extraction.get('text','')[:40000],'truncated':len(extraction.get('text',''))>40000}

@app.get('/api/media/status')
def media_status():return media_engine.status()

@app.get('/api/3d/status')
def blender_status():return blender_engine.status()

@app.post('/api/3d/render')
def blender_render(body:BlenderRenderRequest):
    return media_engine.submit(blender_engine.render,body.product,body.prompt,body.seconds,body.output_name)

@app.get('/api/media/checkpoints')
def media_checkpoints():
    try:return {'checkpoints':media_engine.checkpoints()}
    except Exception:raise HTTPException(503,'Start ComfyUI on 127.0.0.1:8188 to list installed checkpoints.')

@app.post('/api/media/checkpoint')
def media_checkpoint(body:CheckpointRequest):
    try:
        if body.checkpoint not in media_engine.checkpoints():raise ValueError('Checkpoint is not installed in ComfyUI.')
        return media_engine.save_workflow('image',media_engine.image_workflow(body.checkpoint))
    except Exception as e:raise HTTPException(400,str(e))

@app.post('/api/media/workflow')
def media_workflow(body:WorkflowRequest):
    try:return media_engine.save_workflow(body.kind,body.workflow)
    except Exception as e:raise HTTPException(400,str(e))

@app.post('/api/media/generate')
def media_generate(body:MediaRequest):return media_engine.submit(media_engine.generate,body.kind,body.prompt)

@app.get('/api/grimforge/preflight')
def grimforge_preflight(animation_style:str='2.5d'):
    from .services.episode import preflight
    return preflight(animation_style)

@app.post('/api/grimforge/render')
def grimforge_render(body:EpisodeRequest):
    return media_engine.submit(build_media_episode,body.premise,body.scene_count,body.animation_style,body.voice,body.model,body.allow_basic_fallback,body.allow_visual_fallback)

@app.get('/api/jobs/{job_id}')
def media_job(job_id:str):
    try:return media_engine.get_job(job_id)
    except (ValueError,FileNotFoundError):raise HTTPException(404,'Job not found')

@app.get('/api/vault/source/{item_id}')
def source_file(item_id:str):
    from .services.vault import _db
    with _db() as con:row=con.execute('SELECT * FROM items WHERE id=?',(item_id,)).fetchone()
    if not row:raise HTTPException(404,'Source not found')
    return FileResponse(row['stored_path'],filename=row['name'])
