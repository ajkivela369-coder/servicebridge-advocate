param(
  [string]$ForgeHome = $(if ($env:FORGE_HOME) {$env:FORGE_HOME} elseif (Test-Path 'D:\') {'D:\Forge'} else {"$env:USERPROFILE\Forge"}),
  [switch]$IncludeVision,
  [switch]$Force7B,
  [switch]$SkipWhisper,
  [switch]$SkipKokoro,
  [switch]$SkipOllama
)
$ErrorActionPreference='Stop'
$repo=Split-Path $PSScriptRoot -Parent
$env:FORGE_HOME=$ForgeHome
$env:HF_HOME=Join-Path $ForgeHome 'models\huggingface'
$env:OLLAMA_MODELS=Join-Path $ForgeHome 'models\ollama'
New-Item -ItemType Directory -Force -Path $env:HF_HOME,$env:OLLAMA_MODELS,(Join-Path $ForgeHome 'models\whisper') | Out-Null
$ram=0
try{$ram=[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB,1)}catch{}
$large=$Force7B -or $ram -ge 24

if(-not $SkipOllama){
 if(-not(Get-Command ollama -ErrorAction SilentlyContinue)){throw 'Ollama is not installed. Run bootstrap_windows.ps1 -InstallFoundation first.'}
 try{ollama list | Out-Null}catch{Start-Process -FilePath (Get-Command ollama).Source -ArgumentList 'serve' -WindowStyle Hidden;Start-Sleep -Seconds 3}
 if($large){$general='qwen2.5:7b-instruct';$coder='qwen2.5-coder:7b';$vision='qwen2.5vl:7b'}else{$general='qwen2.5:3b';$coder='qwen2.5-coder:3b';$vision='qwen2.5vl:3b'}
 Write-Host "RAM detected: $ram GB. Staging $general + $coder (3B defaults on 16 GB CPU-first systems; 7B only with -Force7B or >=24 GB RAM)" -ForegroundColor Cyan
 ollama pull $general
 ollama pull $coder
 ollama pull nomic-embed-text
 if($IncludeVision){ollama pull $vision}
}
if(-not $SkipWhisper){Write-Host 'Staging Whisper base.en + small.en with integrity checks' -ForegroundColor Cyan;python (Join-Path $PSScriptRoot 'model_manager.py') whisper base.en small.en}
if(-not $SkipKokoro){Write-Host 'Installing/warming Kokoro into retained cache' -ForegroundColor Cyan;python -m pip install "kokoro>=0.9.4" soundfile huggingface_hub;python (Join-Path $PSScriptRoot 'warm_kokoro.py')}
python (Join-Path $PSScriptRoot 'model_manager.py') status
