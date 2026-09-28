param(
 [string]$ForgeHome = $(if($env:FORGE_HOME){$env:FORGE_HOME}elseif(Test-Path 'D:\'){'D:\Forge'}else{"$env:USERPROFILE\Forge"}),
 [switch]$OnlineOnly,
 [switch]$OfflineOnly
)
$ErrorActionPreference='Stop'
$pkgDir=Join-Path $ForgeHome 'downloads\npm-packages'
$npmCache=Join-Path $ForgeHome 'downloads\npm-cache'
$toolDir=Join-Path $ForgeHome 'tools\12ui'
$binDir=Join-Path $ForgeHome 'bin'
New-Item -ItemType Directory -Force -Path $pkgDir,$npmCache,$binDir | Out-Null

function Write-Wrapper {
  $local=Join-Path $toolDir 'node_modules\.bin\12ui.cmd'
  if(Test-Path $local){
    $wrapper=Join-Path $binDir '12ui.cmd'
    "@echo off`r`ncall `"$local`" %*`r`n" | Set-Content -Encoding ASCII $wrapper
    Write-Host "12ui wrapper installed: $wrapper" -ForegroundColor Green
    return $true
  }
  return $false
}

# 1) Already installed / previously restored.
if((Test-Path $toolDir) -and (Write-Wrapper)){ exit 0 }

# 2) Fully retained runtime ZIP: no registry/network needed.
$runtime=Get-ChildItem $pkgDir -Filter '12ui-runtime-*.zip' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if($runtime -and -not $OnlineOnly){
  Write-Host "Restoring cached 12ui runtime: $($runtime.Name)" -ForegroundColor Cyan
  if(Test-Path $toolDir){Remove-Item -Recurse -Force $toolDir}
  New-Item -ItemType Directory -Force -Path $toolDir | Out-Null
  Expand-Archive -Force $runtime.FullName $toolDir
  if(Write-Wrapper){ exit 0 }
  throw 'Cached 12ui runtime did not contain the expected executable.'
}
if($OfflineOnly){ throw 'No retained 12ui runtime is available yet. Run this once with internet access to seed the cache.' }

# 3) Online bootstrap. Cache npm content in ForgeHome so dependencies are retained.
if(-not(Get-Command npm -ErrorAction SilentlyContinue)){throw 'npm is unavailable. Install/stage Node.js first.'}
$env:npm_config_cache=$npmCache
Write-Host 'Testing access to npm registry…' -ForegroundColor Cyan
& npm ping --registry https://registry.npmjs.org/ --fetch-timeout=8000 --fetch-retries=0 | Out-Null
Write-Host 'Installing @12ui/design into the permanent Forge tool store…' -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $toolDir | Out-Null
& npm install --prefix $toolDir '@12ui/design' --no-audit --no-fund
if(-not(Write-Wrapper)){throw '12ui installed but its executable was not found.'}

# Run the vendor-recommended CLI install step when available. A failure here does not erase the retained package.
try{
  & (Join-Path $toolDir 'node_modules\.bin\12ui.cmd') cli install
}catch{
  Write-Warning "12ui vendor CLI install step did not complete: $($_.Exception.Message)"
}

# Archive the entire working runtime, not only the top-level npm tarball, so transitive dependencies restore offline.
$stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
$zip=Join-Path $pkgDir "12ui-runtime-$stamp.zip"
Compress-Archive -Force -Path (Join-Path $toolDir '*') -DestinationPath $zip
$hash=(Get-FileHash -Algorithm SHA256 $zip).Hash.ToLower()
@{file=(Split-Path $zip -Leaf);sha256=$hash;created=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $pkgDir '12ui-runtime-latest.json')
Write-Host "Retained offline 12ui runtime: $zip" -ForegroundColor Green
Write-Host 'Note: 12ui design generation is a hosted capability and can still require internet/service access. Forge local design remains the offline fallback.' -ForegroundColor Yellow
