param(
  [string]$ForgeHome = $(if($env:FORGE_HOME){$env:FORGE_HOME}else{"$env:USERPROFILE\Forge"}),
  [string]$Output = "$env:USERPROFILE\Desktop\Forge-Offline-Bundle.zip",
  [switch]$IncludeModels
)
$ErrorActionPreference = "Stop"
$stage = Join-Path $env:TEMP ("forge-offline-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $stage | Out-Null
$include = @("bin","downloads","manifests")
if ($IncludeModels) { $include += "models" }
foreach ($name in $include) {
  $src = Join-Path $ForgeHome $name
  if (Test-Path $src) { Copy-Item $src -Destination $stage -Recurse -Force }
}
if (Test-Path $Output) { Remove-Item $Output -Force }
Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $Output -CompressionLevel Optimal
Remove-Item $stage -Recurse -Force
Write-Host "Offline bundle created: $Output" -ForegroundColor Green
