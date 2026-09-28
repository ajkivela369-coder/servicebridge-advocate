param(
  [Parameter(Mandatory=$true)][string]$Distribution,
  [string]$ForgeHome = $(if($env:FORGE_HOME){$env:FORGE_HOME}else{"$env:USERPROFILE\Forge"})
)
$ErrorActionPreference = "Stop"
$dir = Join-Path $ForgeHome "backups\wsl"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$out = Join-Path $dir ("$Distribution-$stamp.tar")
wsl --export $Distribution $out
Write-Host "WSL distro exported to $out" -ForegroundColor Green
