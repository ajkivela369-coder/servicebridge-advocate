from __future__ import annotations
import json, os, platform, shutil, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PROFILE=ROOT/'forge_base'/'hardware_profiles'/'AJ_HP_ELITEBOOK_840_G8.json'

def _powershell(script:str):
    exe=shutil.which('powershell') or shutil.which('pwsh')
    if not exe:return None
    try:
        r=subprocess.run([exe,'-NoProfile','-Command',script],capture_output=True,text=True,timeout=6)
        return r.stdout.strip() if r.returncode==0 else None
    except Exception:return None

def model_recommendation(live=None,base=None):
    live=live or {}; base=base or {}
    ram=live.get('ram_gb') or base.get('memory',{}).get('installed_gb') or 0
    gpu=(live.get('gpu') or '').lower()
    has_discrete=any(x in gpu for x in ['nvidia','radeon rx','arc a'])
    tier='cpu_16gb' if ram>=14 and not has_discrete else ('gpu_or_high_ram' if has_discrete or ram>=24 else 'constrained')
    if tier=='gpu_or_high_ram':
        pref={'general':'qwen2.5:7b-instruct','coding':'qwen2.5-coder:7b','vision':'qwen2.5vl:7b','transcription':'small.en'}
    elif tier=='cpu_16gb':
        pref={'general':'qwen2.5:3b','coding':'qwen2.5-coder:3b','vision':'qwen2.5vl:3b','transcription':'small.en'}
    else:
        pref={'general':'qwen2.5:1.5b','coding':'qwen2.5-coder:1.5b','vision':'metadata-only-local','transcription':'base.en'}
    return {'tier':tier,'preferred':pref,'note':'Forge escalates to larger models only when the task needs them and memory allows.'}

def current_hardware():
    base=json.loads(PROFILE.read_text()) if PROFILE.exists() else {}
    live={'platform':platform.system(),'machine':platform.machine()}
    if os.name=='nt':
        ram=_powershell('[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB,1)')
        cpu=_powershell('(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name)')
        gpu=_powershell('(Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name) -join "; "')
        disks=_powershell('Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {"$($_.DeviceID)|$([math]::Round($_.FreeSpace/1GB,1))|$([math]::Round($_.Size/1GB,1))"}')
        live.update({'ram_gb':float(ram) if ram else None,'cpu':cpu,'gpu':gpu,'disks':disks.splitlines() if disks else []})
    return {'declared_profile':base,'live':live,'recommendation':model_recommendation(live,base)}
