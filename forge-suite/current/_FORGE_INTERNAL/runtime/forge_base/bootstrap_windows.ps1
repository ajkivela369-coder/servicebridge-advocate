param(
  [string]$ForgeHome = '',
  [switch]$InstallFoundation,
  [switch]$InstallLocalAI,
  [switch]$StageModels,
  [switch]$IncludeVision,
  [switch]$EnableWSL,
  [switch]$InstallPodman,
  [switch]$PrepareOfflineCache
)
$ErrorActionPreference='Stop'
if(-not $ForgeHome){$ForgeHome=$(if(Test-Path 'D:\'){'D:\Forge'}else{"$env:USERPROFILE\Forge"})}
function Step($m){Write-Host "`n==> $m" -ForegroundColor Cyan}
function Note($m){Write-Host $m -ForegroundColor DarkGray}
function TryWinget([string]$Id){
  if(-not(Get-Command winget -ErrorAction SilentlyContinue)){Write-Warning "winget unavailable; skipped $Id";return}
  winget install -e --id $Id --accept-package-agreements --accept-source-agreements
}

Step "Create permanent Forge home: $ForgeHome"
$dirs=@('bin','downloads\installers','downloads\wheelhouse','downloads\npm-cache','downloads\npm-packages','downloads\containers','downloads\sources','models\ollama','models\whisper','models\huggingface','models\tts','tools\12ui','templates\design','cache\uv','cache\pip','envs','projects','exports','logs','manifests','backups','tmp')
foreach($d in $dirs){New-Item -ItemType Directory -Force -Path(Join-Path $ForgeHome $d)|Out-Null}

Step 'Persist model/cache locations for this Windows user'
$vars=@{FORGE_HOME=$ForgeHome;HF_HOME=(Join-Path $ForgeHome 'models\huggingface');OLLAMA_MODELS=(Join-Path $ForgeHome 'models\ollama');UV_CACHE_DIR=(Join-Path $ForgeHome 'cache\uv');PIP_CACHE_DIR=(Join-Path $ForgeHome 'cache\pip');npm_config_cache=(Join-Path $ForgeHome 'downloads\npm-cache')}
foreach($k in $vars.Keys){[Environment]::SetEnvironmentVariable($k,$vars[$k],'User');Set-Item -Path "env:$k" -Value $vars[$k]}
$env:PATH=(Join-Path $ForgeHome 'bin')+';'+$env:PATH

if($InstallFoundation){
  Step 'Install foundational native tools first'
  @('Python.Python.3.12','Git.Git','astral-sh.uv','Gyan.FFmpeg','OpenJS.NodeJS.LTS','Kitware.CMake','7zip.7zip','Ollama.Ollama') | ForEach-Object {TryWinget $_}
}

# Refresh PATH after winget installs so the rest of this same setup run can see new tools.
$env:PATH=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User')+';'+(Join-Path $ForgeHome 'bin')
if(-not (Get-Command python -ErrorAction SilentlyContinue)){
  $py=Get-Command py -ErrorAction SilentlyContinue
  if($py){
    $wrapper=Join-Path $ForgeHome 'bin\python.cmd'
    '@echo off' + "`r`n" + 'py -3 %*' | Set-Content -Encoding ASCII $wrapper
    $env:PATH=(Join-Path $ForgeHome 'bin')+';'+$env:PATH
  }
}
if(-not (Get-Command python -ErrorAction SilentlyContinue)){throw 'Python 3 is still unavailable after foundation setup. Reopen Forge Control Center or install Python 3.12, then press Repair / Verify.'}

if($InstallLocalAI){
  Step 'Install Forge runtime + local speech/transcription dependencies'
  $repo=Split-Path $PSScriptRoot -Parent
  python -m pip install -r (Join-Path $repo 'requirements.txt')
  python -m pip install -r (Join-Path $repo 'requirements-local-ai.txt')
  & (Join-Path $PSScriptRoot 'install_whisper_cpp.ps1') -ForgeHome $ForgeHome
  & (Join-Path $PSScriptRoot 'install_llama_cpp.ps1') -ForgeHome $ForgeHome
}

# Cache and models deliberately happen BEFORE WSL/Podman so a reboot requirement cannot
# prevent the core local runtime from being staged.
if($PrepareOfflineCache){
  Step 'Prepare retained installers + Python wheelhouse'
  & (Join-Path $PSScriptRoot 'cache_foundation.ps1') -ForgeHome $ForgeHome
  $repo=Split-Path $PSScriptRoot -Parent
  python -m pip download -r (Join-Path $repo 'requirements.txt') -d (Join-Path $ForgeHome 'downloads\wheelhouse')
  python -m pip download -r (Join-Path $repo 'requirements-local-ai.txt') -d (Join-Path $ForgeHome 'downloads\wheelhouse')
}

if($StageModels){
  Step 'Stage retained local models (adaptive to installed RAM)'
  $modelArgs=@('-ForgeHome',$ForgeHome)
  if($IncludeVision){$modelArgs+='-IncludeVision'}
  & (Join-Path $PSScriptRoot 'stage_models.ps1') @modelArgs
  python (Join-Path $PSScriptRoot 'stage_llama_fallback.py')
}

if($EnableWSL){
  Step 'Prepare WSL2 Linux escape hatch'
  try{
    if(-not([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){Write-Warning 'WSL setup can require Administrator privileges and reboot.'}
    wsl --update
    wsl --install --no-distribution
    Note 'If Windows requests a reboot, the native Forge setup above is already preserved. After reboot: wsl --install -d Ubuntu'
  }catch{Write-Warning "WSL setup did not complete: $($_.Exception.Message). Core Forge setup remains intact."}
}

if($InstallPodman){
  Step 'Prepare Podman container fallback'
  try{TryWinget 'RedHat.Podman-Desktop'}catch{Write-Warning "Podman install did not complete: $($_.Exception.Message). WSL/native routes remain available."}
}

Step 'Run Forge Doctor'
python (Join-Path $PSScriptRoot 'forge_base.py') doctor --home $ForgeHome
Write-Host "`nForge Base P1 initialized at $ForgeHome" -ForegroundColor Green
Write-Host 'Reopen terminals once so persistent environment variables are inherited.' -ForegroundColor Yellow
