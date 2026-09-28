param(
 [Parameter(Mandatory=$true)][string]$Archive,
 [Parameter(Mandatory=$true)][string]$Distribution,
 [string]$InstallLocation = $(Join-Path $(if($env:FORGE_HOME){$env:FORGE_HOME}else{"$env:USERPROFILE\Forge"}) "envs\wsl\$Distribution")
)
$ErrorActionPreference='Stop'
New-Item -ItemType Directory -Force -Path $InstallLocation | Out-Null
wsl --import $Distribution $InstallLocation $Archive --version 2
Write-Host "WSL distro restored as $Distribution at $InstallLocation" -ForegroundColor Green
