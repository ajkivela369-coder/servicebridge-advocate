param(
  [string]$ForgeHome = $(if ($env:FORGE_HOME) {$env:FORGE_HOME} elseif (Test-Path 'D:\') {'D:\Forge'} else {"$env:USERPROFILE\Forge"})
)
$ErrorActionPreference='Stop'
$bin=Join-Path $ForgeHome 'bin'; $cache=Join-Path $ForgeHome 'downloads\installers\whisper.cpp'
New-Item -ItemType Directory -Force -Path $bin,$cache | Out-Null
Write-Host 'Finding latest official whisper.cpp Windows x64 release…' -ForegroundColor Cyan
$release=Invoke-RestMethod -Headers @{ 'User-Agent'='Forge-Core' } -Uri 'https://api.github.com/repos/ggml-org/whisper.cpp/releases/latest'
$asset=$release.assets | Where-Object { $_.name -eq 'whisper-bin-x64.zip' } | Select-Object -First 1
if(-not $asset){ $asset=$release.assets | Where-Object { $_.name -match 'whisper.*bin.*x64.*\.zip$' -and $_.name -notmatch 'cuda|blas|arm' } | Select-Object -First 1 }
if(-not $asset){ throw 'Could not find a CPU x64 Windows release asset. Use the WSL/source-build fallback documented in FALLBACK_MATRIX.md.' }
$zip=Join-Path $cache $asset.name
if(-not (Test-Path $zip)){ Invoke-WebRequest -UseBasicParsing -Uri $asset.browser_download_url -OutFile $zip }
$tmp=Join-Path $env:TEMP ('forge-whisper-'+[guid]::NewGuid().ToString('N')); New-Item -ItemType Directory -Path $tmp | Out-Null
Expand-Archive -Force -Path $zip -DestinationPath $tmp
$exe=Get-ChildItem -Path $tmp -Recurse -Filter 'whisper-cli.exe' | Select-Object -First 1
if(-not $exe){ throw 'Release downloaded but whisper-cli.exe was not found.' }
# Copy the executable and sibling DLLs so dynamic builds stay usable offline.
Copy-Item -Force $exe.FullName (Join-Path $bin 'whisper-cli.exe')
Get-ChildItem -Path $exe.Directory.FullName -Filter '*.dll' | ForEach-Object { Copy-Item -Force $_.FullName (Join-Path $bin $_.Name) }
Remove-Item -Recurse -Force $tmp
Write-Host "whisper.cpp ready: $(Join-Path $bin 'whisper-cli.exe')" -ForegroundColor Green
