param([string]$ForgeHome = $(if($env:FORGE_HOME){$env:FORGE_HOME}else{"$env:USERPROFILE\Forge"}))
$ErrorActionPreference = "Continue"
$projects = Join-Path $ForgeHome "projects"
$out = Join-Path $ForgeHome "backups\git"
New-Item -ItemType Directory -Force -Path $out | Out-Null
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "Git is required." }
if (-not (Test-Path $projects)) { Write-Host "No projects directory yet: $projects"; exit 0 }
Get-ChildItem $projects -Directory | ForEach-Object {
  if (Test-Path (Join-Path $_.FullName ".git")) {
    $safe = $_.Name -replace '[^A-Za-z0-9._-]','_'
    $dest = Join-Path $out "$safe.bundle"
    Push-Location $_.FullName
    git bundle create $dest --all
    Pop-Location
    Write-Host "Backed up $($_.Name) -> $dest" -ForegroundColor Green
  }
}
