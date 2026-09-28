from __future__ import annotations
from pathlib import Path
from .vision import analyze_image
from .lesson import build_lesson

def inspect_image(path:Path,question:str='Teach me what is visibly present in this image.'):
    prompt='You are MedForge local teaching mode. Separate the response into OBSERVATIONS, POSSIBLE INTERPRETATIONS, LIMITATIONS, and WHAT TO VERIFY NEXT. Do not diagnose from an image alone. State only visible features as observations. Question: '+question
    result=analyze_image(path,prompt,model='qwen2.5vl:3b'); result['safety_contract']={'observation_not_diagnosis':True,'preserve_source':True,'human_verification_required':True}; return result

def make_lesson(title:str,source_text:str):
    l=build_lesson(title,source_text,prefer_ollama=True); l['mode']='MedForge Teach Me This'; l['disclaimer']='Educational synthesis only. Distinguish observed findings, source-recorded diagnoses, and hypotheses.'; return l
