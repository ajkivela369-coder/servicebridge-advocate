"""Shared local ComfyUI adapter and persistent media jobs. No cloud submission."""
import copy, json, time, uuid, threading, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from .vault import forge_home
from .render import OUTPUTS

BASE='http://127.0.0.1:8188'
POOL=ThreadPoolExecutor(max_workers=1)
LOCK=threading.Lock()
ACTIVE=set()

def request(path,body=None,timeout=15):
    req=urllib.request.Request(BASE+path,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=timeout) as r:return json.load(r)

def workflow_dir():
    d=forge_home()/'config'/'media-workflows';d.mkdir(parents=True,exist_ok=True);return d

def save_workflow(kind,workflow):
    if kind not in ('image','video'):raise ValueError('Choose image or video.')
    if not isinstance(workflow,dict) or not workflow or len(workflow)>500:raise ValueError('Upload a ComfyUI API-format workflow, not the visual editor JSON.')
    if '{{prompt}}' not in json.dumps(workflow):raise ValueError('Put {{prompt}} in the positive prompt text before exporting the API workflow.')
    for node in workflow.values():
        if not isinstance(node,dict) or not isinstance(node.get('inputs'),dict) or not node.get('class_type'):raise ValueError('Every node must have class_type and inputs; export using API format.')
    (workflow_dir()/(kind+'.json')).write_text(json.dumps(workflow,indent=2))
    return {'ok':True,'kind':kind}

def status():
    try:
        request('/system_stats',timeout=2);online=True
    except Exception:online=False
    return {'engine':'ComfyUI local','online':online,'image_configured':(workflow_dir()/'image.json').exists(),'video_configured':(workflow_dir()/'video.json').exists(),'endpoint':BASE,'note':'Configured does not mean validated. Generation requires installed models and workflow nodes.'}


def ensure_image_workflow():
    """Configure the standard local image workflow from the first installed checkpoint when possible."""
    st=status()
    if st.get("image_configured"):
        return {"ok":True,"configured":True,"changed":False}
    if not st.get("online"):
        return {"ok":False,"configured":False,"changed":False,"reason":"ComfyUI offline"}
    try:
        cps=checkpoints()
        if not cps:return {"ok":False,"configured":False,"changed":False,"reason":"No installed checkpoints found"}
        save_workflow("image",image_workflow(cps[0]))
        return {"ok":True,"configured":True,"changed":True,"checkpoint":cps[0]}
    except Exception as e:
        return {"ok":False,"configured":False,"changed":False,"reason":str(e)}

def image_workflow(checkpoint):
    return {'1':{'class_type':'CheckpointLoaderSimple','inputs':{'ckpt_name':checkpoint}},
      '2':{'class_type':'CLIPTextEncode','inputs':{'text':'{{prompt}}','clip':['1',1]}},
      '3':{'class_type':'CLIPTextEncode','inputs':{'text':'blurry, watermark, illegible text','clip':['1',1]}},
      '4':{'class_type':'EmptyLatentImage','inputs':{'width':1024,'height':576,'batch_size':1}},
      '5':{'class_type':'KSampler','inputs':{'model':['1',0],'positive':['2',0],'negative':['3',0],'latent_image':['4',0],'seed':1,'steps':25,'cfg':7.0,'sampler_name':'euler','scheduler':'normal','denoise':1.0}},
      '6':{'class_type':'VAEDecode','inputs':{'samples':['5',0],'vae':['1',2]}},
      '7':{'class_type':'SaveImage','inputs':{'filename_prefix':'Forge','images':['6',0]}}}

def checkpoints():
    info=request('/object_info/CheckpointLoaderSimple',timeout=4)
    return info['CheckpointLoaderSimple']['input']['required']['ckpt_name'][0]

def generate(kind,prompt,progress=lambda x:None):
    config=workflow_dir()/(kind+'.json')
    if not config.exists():raise RuntimeError(f'No {kind} workflow configured. Open Media Engine setup and select a checkpoint or import an API workflow.')
    workflow=json.loads(config.read_text())
    def substitute(v):
        if isinstance(v,str):return v.replace('{{prompt}}',prompt)
        if isinstance(v,list):return [substitute(x) for x in v]
        if isinstance(v,dict):return {k:substitute(x) for k,x in v.items()}
        return v
    workflow=substitute(workflow)
    # The local-only route rejects registered paid/cloud API nodes.
    info=request('/object_info',timeout=15)
    for node in workflow.values():
        meta=info.get(node['class_type'])
        if not meta:raise RuntimeError('Missing ComfyUI node: '+node['class_type'])
        if meta.get('api_node'):raise RuntimeError('Cloud API nodes are not enabled in this local workflow route.')
        for key in ('seed','noise_seed'):
            if isinstance(node['inputs'].get(key),int):node['inputs'][key]=uuid.uuid4().int%(2**48)
    queued=request('/prompt',{'prompt':workflow,'client_id':'forge-'+uuid.uuid4().hex})
    if queued.get('node_errors'):raise RuntimeError('ComfyUI rejected workflow inputs: '+json.dumps(queued['node_errors'])[:1500])
    prompt_id=queued.get('prompt_id')
    if not prompt_id:raise RuntimeError('ComfyUI did not return a job ID.')
    progress('Generating '+kind+' in ComfyUI; job '+prompt_id)
    deadline=time.monotonic()+1800
    while time.monotonic()<deadline:
        record=request('/history/'+urllib.parse.quote(prompt_id),timeout=15).get(prompt_id)
        if record:
            state=record.get('status',{})
            if state.get('status_str')=='error':raise RuntimeError('ComfyUI generation failed: '+json.dumps(state.get('messages',[]))[:1500])
            if state.get('completed') or record.get('outputs'):
                results=[]
                for node in record.get('outputs',{}).values():
                    for family in ('images','gifs','videos'):
                        for item in node.get(family,[]):
                            ext=Path(item.get('filename','')).suffix.lower()
                            allowed=('.png','.jpg','.jpeg','.webp') if kind=='image' else ('.mp4','.webm','.mov')
                            if ext not in allowed:continue
                            params={k:item.get(k,'') for k in ('filename','subfolder','type')};params['type']=params['type'] or 'output'
                            dest=OUTPUTS/('forge-'+uuid.uuid4().hex+ext)
                            with urllib.request.urlopen(BASE+'/view?'+urllib.parse.urlencode(params),timeout=120) as response, dest.open('wb') as out:
                                total=0
                                while chunk:=response.read(1024*1024):
                                    total+=len(chunk)
                                    if total>512*1024*1024:raise RuntimeError('Media output exceeded 512 MB limit.')
                                    out.write(chunk)
                            if not dest.stat().st_size:raise RuntimeError('Renderer returned an empty file.')
                            results.append(str(dest))
                if not results:raise RuntimeError('Workflow finished without a saved '+kind+' output. Add the appropriate save/output node.')
                return {'files':results,'engine':'ComfyUI local','prompt_id':prompt_id,'kind':kind}
        time.sleep(2)
    raise RuntimeError('Timed out after 30 minutes. Check the ComfyUI queue before resubmitting; the renderer may still be running.')

def job_dir():
    d=forge_home()/'jobs';d.mkdir(parents=True,exist_ok=True);return d

def submit(fn,*args):
    jid=uuid.uuid4().hex; path=job_dir()/(jid+'.json')
    def persist(data):
        tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2));tmp.replace(path)
    record={'id':jid,'status':'queued','stage':'Waiting for render worker','created':time.time()}
    persist(record)
    with LOCK:ACTIVE.add(jid)
    def run():
        def progress(stage):record.update(stage=stage);persist(record)
        try:
            record.update(status='running');progress('Starting')
            result=fn(*args,progress=progress)
            record.update(status='completed',stage='Completed',result=result)
        except Exception as e:record.update(status='failed',stage='Failed',error=str(e))
        finally:
            persist(record)
            with LOCK:ACTIVE.discard(jid)
    POOL.submit(run)
    return record

def get_job(jid):
    if len(jid)!=32 or any(c not in '0123456789abcdef' for c in jid):raise ValueError('Invalid job ID')
    record=json.loads((job_dir()/(jid+'.json')).read_text())
    with LOCK:active=jid in ACTIVE
    if record['status'] in ('queued','running') and not active:record.update(status='interrupted',stage='Core restarted; check ComfyUI before retrying.')
    return record
