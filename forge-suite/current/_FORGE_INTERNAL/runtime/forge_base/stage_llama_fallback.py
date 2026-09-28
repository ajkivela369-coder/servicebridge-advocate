from pathlib import Path
import os
root=Path(os.environ.get('FORGE_HOME') or (Path.home()/'Forge'))
target=root/'models'/'llama.cpp';target.mkdir(parents=True,exist_ok=True)
try:
    from huggingface_hub import hf_hub_download
    p=hf_hub_download(repo_id='Qwen/Qwen2.5-3B-Instruct-GGUF',filename='qwen2.5-3b-instruct-q4_k_m.gguf',local_dir=str(target))
    print(f'llama.cpp fallback model ready: {p}')
except Exception as e:
    raise SystemExit(f'Could not stage llama.cpp fallback model: {e}')
