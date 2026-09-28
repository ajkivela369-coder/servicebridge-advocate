from __future__ import annotations
import os, shutil
from .detect import capabilities

TASK_ROUTES={
 "general":["ollama:qwen2.5:3b","ollama:qwen2.5:7b-instruct","llama.cpp:qwen2.5-3b-instruct-q4_k_m","heuristic-local"],
 "coding":["ollama:qwen2.5-coder:3b","ollama:qwen2.5-coder:7b","ollama:qwen2.5:7b-instruct","llama.cpp:qwen2.5-3b-instruct-q4_k_m","template-local"],
 "embeddings":["ollama:nomic-embed-text","hashing-local"],
 "vision":["ollama:qwen2.5vl:3b","ollama:qwen2.5vl:7b","metadata-only-local"],
 "transcription":["whisper.cpp:small.en","whisper.cpp:base.en","faster-whisper:base.en"],
 "speech":["kokoro:af_heart","espeak-ng","windows-sapi"],
 "video":["ffmpeg-native","ffmpeg-portable","ffmpeg-wsl","ffmpeg-container"],
 "diagram":["pillow-svg-local","mermaid-cli","manim"]
}

def _ollama_models(caps):return set(caps.get('llm',{}).get('models') or [])
def _forge_home():
    from pathlib import Path
    return Path(os.environ.get('FORGE_HOME') or (Path.home()/'Forge'))

def choose(task:str,caps:dict|None=None)->dict:
    caps=caps or capabilities();routes=TASK_ROUTES.get(task,['unknown']);models=_ollama_models(caps);selected=None;reasons=[]
    for route in routes:
        if route.startswith('ollama:'):
            model=route.split('ollama:',1)[1]
            if model in models or model.replace(':7b-instruct',':7b') in models:selected=route;break
            reasons.append(f'{model} not loaded')
        elif route.startswith('llama.cpp:'):
            model=_forge_home()/'models'/'llama.cpp'/'qwen2.5-3b-instruct-q4_k_m.gguf'
            if caps.get('llama_cpp',{}).get('installed') and model.exists():selected=route;break
            reasons.append('llama.cpp binary/model not staged')
        elif route.startswith('whisper.cpp'):
            if caps.get('transcription',{}).get('path'):selected=route;break
            reasons.append('whisper.cpp not installed')
        elif route.startswith('faster-whisper'):
            if caps.get('transcription',{}).get('faster_whisper'):selected=route;break
        elif route.startswith('kokoro'):
            if caps.get('voice',{}).get('kokoro_python'):selected=route;break
        elif route=='espeak-ng':
            if caps.get('voice',{}).get('espeak'):selected=route;break
        elif route=='windows-sapi':
            if os.name=='nt' and (shutil.which('powershell') or shutil.which('pwsh')):selected=route;break
        elif route=='ffmpeg-native':
            if caps.get('video',{}).get('ready'):selected=route;break
        elif route=='ffmpeg-portable':
            if (_forge_home()/'bin'/'ffmpeg.exe').exists():selected=route;break
        elif route=='ffmpeg-wsl':
            if caps.get('linux_escape',{}).get('wsl'):selected=route;break
        elif route=='ffmpeg-container':
            if caps.get('containers',{}).get('podman') or caps.get('containers',{}).get('docker'):selected=route;break
        elif route.startswith('pillow'):
            if caps.get('diagram',{}).get('pillow'):selected=route;break
        elif route=='mermaid-cli' and caps.get('diagram',{}).get('mermaid_cli'):selected=route;break
        elif route=='manim' and caps.get('diagram',{}).get('manim'):selected=route;break
        elif route in {'heuristic-local','template-local','hashing-local','metadata-only-local'}:selected=route;break
    return {'task':task,'selected':selected,'routes':routes,'notes':reasons,'local':bool(selected)}

def routing_summary()->dict:
    caps=capabilities();return {task:choose(task,caps) for task in TASK_ROUTES}
