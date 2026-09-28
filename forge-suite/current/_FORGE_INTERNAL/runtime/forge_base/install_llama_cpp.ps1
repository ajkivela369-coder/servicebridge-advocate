param(
  [string]$ForgeHome = $(if ($env:FORGE_HOME) {$env:FORGE_HOME} elseif (Test-Path 'D:\') {'D:\Forge'} else {"$env:USERPROFILE\Forge"})
)
$ErrorActionPreference='Stop'
$bin=Join-Path $ForgeHome 'bin';$cache=Join-Path $ForgeHome 'downloads\installers\llama.cpp'
New-Item -ItemType Directory -Force -Path $bin,$cache | Out-Null
Write-Host 'Finding latest official llama.cpp Windows CPU x64 release…' -ForegroundColor Cyan
$release=Invoke-RestMethod -Headers @{'User-Agent'='Forge-Core'} -Uri 'https://api.github.com/repos/ggml-org/llama.cpp/releases/latest'
$asset=$release.assets | Where-Object { $_.name -match '^llama-.*-bin-win-cpu-x64\.zip$' } | Select-Object -First 1
if(-not $asset){throw 'Could not find the official Windows x64 CPU llama.cpp release asset.'}
$zip=Join-Path $cache $asset.name
if(-not(Test-Path $zip)){Invoke-WebRequest -UseBasicParsing -Uri $asset.browser_download_url -OutFile $zip}
$tmp=Join-Path $env:TEMP ('forge-llama-'+[guid]::NewGuid().ToString('N'));New-Item -ItemType Directory -Path $tmp|Out-Null
Expand-Archive -Force -Path $zip -DestinationPath $tmp
$server=Get-ChildItem -Path $tmp -Recurse -Filter 'llama-server.exe'|Select-Object -First 1
if(-not $server){throw 'llama-server.exe not found in release.'}
Get-ChildItem -Path $server.Directory.FullName -File | Where-Object { $_.Extension -in '.exe','.dll' } | ForEach-Object {Copy-Item -Force $_.FullName (Join-Path $bin $_.Name)}
Remove-Item -Recurse -Force $tmp
Write-Host "llama.cpp ready: $(Join-Path $bin 'llama-server.exe')" -ForegroundColor Green
