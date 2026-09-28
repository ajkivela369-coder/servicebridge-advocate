param([string]$ForgeHome = $(if($env:FORGE_HOME){$env:FORGE_HOME}elseif(Test-Path 'D:\'){'D:\Forge'}else{"$env:USERPROFILE\Forge"}))
$ErrorActionPreference='Stop'
& (Join-Path $PSScriptRoot 'install_12ui.ps1') -ForgeHome $ForgeHome
# The installer archives the complete runtime and uses FORGE_HOME/downloads/npm-cache for dependencies.
Write-Host '12ui package/runtime cache is seeded.' -ForegroundColor Green
