param(
 [string]$ForgeHome = $(if ($env:FORGE_HOME) {$env:FORGE_HOME} elseif (Test-Path 'D:\') {'D:\Forge'} else {"$env:USERPROFILE\Forge"})
)
$ErrorActionPreference='Continue'
$dest=Join-Path $ForgeHome 'downloads\installers'; New-Item -ItemType Directory -Force -Path $dest | Out-Null
$ids=@('Git.Git','astral-sh.uv','Gyan.FFmpeg','OpenJS.NodeJS.LTS','Kitware.CMake','7zip.7zip','Ollama.Ollama','RedHat.Podman-Desktop')
if(Get-Command winget -ErrorAction SilentlyContinue){
 foreach($id in $ids){
   Write-Host "Caching installer metadata/package for $id" -ForegroundColor Cyan
   winget download -e --id $id --download-directory $dest --accept-package-agreements --accept-source-agreements 2>$null
 }
 winget export -o (Join-Path $ForgeHome 'manifests\winget-packages.json') --accept-source-agreements | Out-Null
}else{ Write-Warning 'winget unavailable; installer cache step skipped.' }
Write-Host 'Caching whisper.cpp portable Windows release…' -ForegroundColor Cyan
& (Join-Path $PSScriptRoot 'install_whisper_cpp.ps1') -ForgeHome $ForgeHome
Write-Host 'Caching llama.cpp portable Windows release…' -ForegroundColor Cyan
& (Join-Path $PSScriptRoot 'install_llama_cpp.ps1') -ForgeHome $ForgeHome

Write-Host 'Caching/restoring optional 12ui design accelerator…' -ForegroundColor Cyan
try{& (Join-Path $PSScriptRoot 'cache_12ui.ps1') -ForgeHome $ForgeHome}catch{Write-Warning "12ui unavailable: $($_.Exception.Message). Forge local design fallback remains ready."}
