param(
    [Parameter(Mandatory=$true)][string]$ForgeRoot,
    [Parameter(Mandatory=$true)][string]$ForgeHome,
    [string]$OutputDir = ".\acceptance-results\windows",
    [ValidateSet("before","after")][string]$Phase = "before"
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

function Get-HashManifest {
    param([string]$Root)
    if (-not (Test-Path $Root)) { return @() }
    Get-ChildItem -LiteralPath $Root -File -Recurse -ErrorAction SilentlyContinue |
        Sort-Object FullName |
        ForEach-Object {
            $hash = $null
            try { $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash } catch {}
            [PSCustomObject]@{
                relative_path = $_.FullName.Substring($Root.Length).TrimStart('\')
                length = $_.Length
                last_write_utc = $_.LastWriteTimeUtc.ToString("o")
                sha256 = $hash
            }
        }
}

$machine = [PSCustomObject]@{
    phase = $Phase
    timestamp_utc = (Get-Date).ToUniversalTime().ToString("o")
    computer_name = $env:COMPUTERNAME
    windows = (Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber)
    cpu = (Get-CimInstance Win32_Processor | Select-Object -First 1 Name,NumberOfCores,NumberOfLogicalProcessors)
    memory_bytes = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory
    gpu = @(Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM,DriverVersion)
    powershell = $PSVersionTable.PSVersion.ToString()
    forge_root = (Resolve-Path $ForgeRoot).Path
    forge_home = if (Test-Path $ForgeHome) { (Resolve-Path $ForgeHome).Path } else { $ForgeHome }
    python = (Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)
    blender = (Get-Command blender -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)
    ffmpeg = (Get-Command ffmpeg -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)
}

$manifest = [PSCustomObject]@{
    machine = $machine
    forge_root_files = @(Get-HashManifest -Root $ForgeRoot)
    forge_home_files = @(Get-HashManifest -Root $ForgeHome)
}

$out = Join-Path $OutputDir ("windows-" + $Phase + "-manifest.json")
$manifest | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $out
Write-Host "Wrote $out"
Write-Host "This helper is read-only: it records machine facts and file hashes. Perform install/upgrade/reboot actions separately, then run again with -Phase after."
