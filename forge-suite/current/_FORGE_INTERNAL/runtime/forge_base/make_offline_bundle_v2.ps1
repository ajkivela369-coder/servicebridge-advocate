param(
 [string]$Output = $(Join-Path $(if ($env:FORGE_HOME){$env:FORGE_HOME}else{"$env:USERPROFILE\Forge"}) "backups\Forge-Offline-Bundle.zip"),
 [switch]$IncludeModels
)
$repo=Split-Path $PSScriptRoot -Parent
python (Join-Path $PSScriptRoot "forge_base.py") inventory
$args=@((Join-Path $PSScriptRoot "bundle.py"),"create",$Output)
if($IncludeModels){$args += "--include-models"}
python @args
python (Join-Path $PSScriptRoot "bundle.py") verify $Output
Write-Host "Offline bundle ready: $Output" -ForegroundColor Green
