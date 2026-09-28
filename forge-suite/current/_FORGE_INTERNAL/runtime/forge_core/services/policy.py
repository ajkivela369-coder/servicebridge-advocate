from __future__ import annotations
from .detect import capabilities
from .hardware import current_hardware

def model_policy() -> dict:
    c=capabilities(); h=current_hardware(); pref=h['recommendation']['preferred']
    return {
      'ram_gb':c.get('platform',{}).get('ram_gb') or h.get('declared_profile',{}).get('memory',{}).get('installed_gb'),
      'hardware_tier':h['recommendation']['tier'],
      'preferred':{**pref,'embeddings':'nomic-embed-text','speech':'kokoro:bf_emma'},
      'optional':{'general':'qwen2.5:7b-instruct','coding':'qwen2.5-coder:7b','vision':'qwen2.5vl:7b'},
      'principle':'Use the smallest local model that satisfies the task; escalate only when needed and memory allows.'
    }
