param(
  [string]$ForgeHome = $(if($env:FORGE_HOME){$env:FORGE_HOME}elseif(Test-Path 'D:\'){'D:\Forge'}else{"$env:USERPROFILE\Forge"}),
  [string]$SourceRoot = $(Split-Path $PSScriptRoot -Parent),
  [switch]$CreateDesktopShortcut,
  [switch]$CreateStartMenuShortcut
)
$ErrorActionPreference='Stop'
$target = Join-Path $ForgeHome 'runtime\ForgeCore'
$backupRoot = Join-Path $ForgeHome 'backups\runtime'
$manifestDir = Join-Path $ForgeHome 'manifests'
New-Item -ItemType Directory -Force -Path $ForgeHome,$backupRoot,$manifestDir | Out-Null

Write-Host "Deploying Forge Core runtime" -ForegroundColor Cyan
Write-Host "Source: $SourceRoot" -ForegroundColor DarkGray
Write-Host "Target: $target" -ForegroundColor DarkGray

$sourceFull=[System.IO.Path]::GetFullPath($SourceRoot).TrimEnd('\')
$targetFull=[System.IO.Path]::GetFullPath($target).TrimEnd('\')
$sameRuntime=$sourceFull.Equals($targetFull,[System.StringComparison]::OrdinalIgnoreCase)

if((-not $sameRuntime) -and (Test-Path $target)){
  $stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
  $backup=Join-Path $backupRoot "ForgeCore-$stamp"
  Write-Host "Preserving previous runtime -> $backup" -ForegroundColor Yellow
  Move-Item -Force $target $backup
}
New-Item -ItemType Directory -Force -Path $target | Out-Null

# Copy the release while excluding transient outputs/uploads and large user state.
if(-not $sameRuntime){
  $excludeDirs=@('.git','__pycache__','data\outputs','data\uploads')
  $roboArgs=@($SourceRoot,$target,'/E','/COPY:DAT','/R:2','/W:1','/NFL','/NDL','/NJH','/NJS','/NP')
  foreach($d in $excludeDirs){$roboArgs += @('/XD',(Join-Path $SourceRoot $d))}
  & robocopy @roboArgs | Out-Null
  if($LASTEXITCODE -ge 8){throw "robocopy failed with exit code $LASTEXITCODE"}
}else{
  Write-Host 'This GUI is already running from the permanent Forge runtime; refreshing shortcuts/manifest only.' -ForegroundColor Yellow
}

# Preserve user settings when a previous runtime exists.
$oldSettings=Get-ChildItem $backupRoot -Directory -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | ForEach-Object {Join-Path $_.FullName 'data\settings.json'}
$newSettings=Join-Path $target 'data\settings.json'
if($oldSettings -and (Test-Path $oldSettings)){
  New-Item -ItemType Directory -Force -Path (Split-Path $newSettings -Parent) | Out-Null
  Copy-Item -Force $oldSettings $newSettings
}

$env:FORGE_HOME=$ForgeHome
[Environment]::SetEnvironmentVariable('FORGE_HOME',$ForgeHome,'User')

$launcher=Join-Path $target 'Forge_Control_Center.cmd'
if(Test-Path $launcher){
  $ws=New-Object -ComObject WScript.Shell
  if($CreateDesktopShortcut){
    $shortcut=$ws.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'Forge Control Center.lnk'))
    $shortcut.TargetPath=$launcher
    $shortcut.WorkingDirectory=$target
    $shortcut.Description='Forge Control Center — local AI runtime, install, deploy and recovery'
    $shortcut.Save()
  }
  if($CreateStartMenuShortcut){
    $programs=[Environment]::GetFolderPath('Programs')
    $dir=Join-Path $programs 'Forge'
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $shortcut=$ws.CreateShortcut((Join-Path $dir 'Forge Control Center.lnk'))
    $shortcut.TargetPath=$launcher
    $shortcut.WorkingDirectory=$target
    $shortcut.Description='Forge Control Center'
    $shortcut.Save()
  }
}

$release='unknown'
try{$release=(Get-Content (Join-Path $target 'RELEASE_MANIFEST.json') -Raw | ConvertFrom-Json).version}catch{}
$record=[ordered]@{
  deployed_at=(Get-Date).ToString('o')
  source=$SourceRoot
  target=$target
  version=$release
  desktop_shortcut=[bool]$CreateDesktopShortcut
  start_menu_shortcut=[bool]$CreateStartMenuShortcut
}
$record | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 (Join-Path $manifestDir 'deployment.json')
Write-Host "Forge runtime deployed to $target" -ForegroundColor Green
Write-Host "Launch with: $launcher" -ForegroundColor Green
