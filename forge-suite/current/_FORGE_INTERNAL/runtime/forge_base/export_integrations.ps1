param(
 [string]$ForgeHome=$(if($env:FORGE_HOME){$env:FORGE_HOME}elseif(Test-Path 'D:\'){'D:\Forge'}else{"$env:USERPROFILE\Forge"}),
 [string]$SourceRoot=$(Split-Path $PSScriptRoot -Parent)
)
$ErrorActionPreference='Stop'
$stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
$outDir=Join-Path $ForgeHome "exports\Forge-App-Integration-Patches-$stamp"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
Copy-Item -Recurse -Force (Join-Path $SourceRoot 'integrations\*') $outDir
Copy-Item -Recurse -Force (Join-Path $SourceRoot 'sdk') (Join-Path $outDir 'sdk')
$zip="$outDir.zip"
Compress-Archive -Force -Path "$outDir\*" -DestinationPath $zip
Write-Host "Integration patch package exported:" -ForegroundColor Green
Write-Host $zip
