param([string]$ForgeHome = $(if($env:FORGE_HOME){$env:FORGE_HOME}else{"$env:USERPROFILE\Forge"}))
$ErrorActionPreference = "Continue"
New-Item -ItemType Directory -Force -Path (Join-Path $ForgeHome "manifests") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $ForgeHome "backups") | Out-Null
if (Get-Command winget -ErrorAction SilentlyContinue) {
  winget export -o (Join-Path $ForgeHome "manifests\winget-packages.json") --accept-source-agreements | Out-Null
}
if (Get-Command python -ErrorAction SilentlyContinue) {
  python "$PSScriptRoot\forge_base.py" doctor --home $ForgeHome | Out-File -Encoding utf8 (Join-Path $ForgeHome "logs\doctor.txt")
  python "$PSScriptRoot\forge_base.py" inventory --home $ForgeHome | Out-Null
}
if (Get-Command ollama -ErrorAction SilentlyContinue) {
  ollama list | Out-File -Encoding utf8 (Join-Path $ForgeHome "manifests\ollama-models.txt")
}
if (Get-Command wsl -ErrorAction SilentlyContinue) {
  wsl -l -v | Out-File -Encoding utf8 (Join-Path $ForgeHome "manifests\wsl-distros.txt")
}
Write-Host "Snapshot written under $ForgeHome\manifests and logs." -ForegroundColor Green
