param(
 [Parameter(Mandatory=$true)][string]$Bundle,
 [string]$ForgeHome = "$env:USERPROFILE\Forge",
 [switch]$Overwrite
)
$ErrorActionPreference="Stop"
$args=@((Join-Path $PSScriptRoot "bundle.py"),"restore",$Bundle,"--target",$ForgeHome)
if($Overwrite){$args += "--overwrite"}
python @args
[Environment]::SetEnvironmentVariable("FORGE_HOME",$ForgeHome,"User")
Write-Host "Forge restored to $ForgeHome. Run bootstrap_windows.ps1 and restore_selftest.py next." -ForegroundColor Green
