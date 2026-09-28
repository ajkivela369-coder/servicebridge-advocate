param(
 [string]$ForgeHome = $(if($env:FORGE_HOME){$env:FORGE_HOME}elseif(Test-Path 'D:\'){'D:\Forge'}else{"$env:USERPROFILE\Forge"}),
 [switch]$LocalAI
)
$ErrorActionPreference='Stop'
$repo=Split-Path $PSScriptRoot -Parent
$wheelhouse=Join-Path $ForgeHome 'downloads\wheelhouse'
if(-not(Test-Path $wheelhouse)){throw "Wheelhouse not found: $wheelhouse"}
if(-not(Test-Path (Join-Path $repo '.venv'))){python -m venv (Join-Path $repo '.venv')}
$py=Join-Path $repo '.venv\Scripts\python.exe'
& $py -m pip install --no-index --find-links $wheelhouse -r (Join-Path $repo 'requirements.txt')
if($LocalAI){& $py -m pip install --no-index --find-links $wheelhouse -r (Join-Path $repo 'requirements-local-ai.txt')}
Write-Host 'Forge Python runtime restored from the offline wheelhouse.' -ForegroundColor Green
