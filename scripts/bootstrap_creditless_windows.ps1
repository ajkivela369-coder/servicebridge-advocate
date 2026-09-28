param(
  [switch]$WithOCR,
  [switch]$WithWhisper
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

Write-Host "ServiceBridge / Forge Creditless Bootstrap" -ForegroundColor Cyan
Write-Host "This installs Python-side local runtime dependencies. It does not buy credits or configure cloud APIs."
Write-Host "Model weights are NOT downloaded automatically."

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  throw "Python 3.11+ is required and was not found on PATH."
}

$PythonVersion = python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
Write-Host "Python: $PythonVersion"

$Venv = Join-Path $RepoRoot ".venv-creditless"
if (-not (Test-Path $Venv)) {
  python -m venv $Venv
}

$Py = Join-Path $Venv "Scripts\python.exe"
& $Py -m pip install --upgrade pip
& $Py -m pip install -e .
& $Py -m pip install -r apps/forge-systems-lab/requirements.txt
& $Py -m pip install "pypdf>=5"

if ($WithWhisper) {
  & $Py -m pip install faster-whisper
}

if ($WithOCR) {
  Write-Host "Installing PaddleOCR Python package. Backend/model provisioning may require additional setup."
  & $Py -m pip install paddleocr
}

Write-Host ""
Write-Host "Local executable checks" -ForegroundColor Cyan
foreach ($Exe in @("ffmpeg", "llama-server", "ollama", "piper", "blender", "nvidia-smi")) {
  $Found = Get-Command $Exe -ErrorAction SilentlyContinue
  if ($Found) {
    Write-Host ("  READY   {0} -> {1}" -f $Exe, $Found.Source) -ForegroundColor Green
  } else {
    Write-Host ("  MISSING {0}" -f $Exe) -ForegroundColor Yellow
  }
}

Write-Host ""
Write-Host "Next:" -ForegroundColor Cyan
Write-Host "1. Place local model files under private_data\local_runtime\models (or another private folder)."
Write-Host "2. Register them with scripts\local_model_catalog.py."
Write-Host "3. Start your local llama.cpp server / Piper / ComfyUI only for capabilities you want."
Write-Host "4. Run: $Py scripts\local_runtime_doctor.py"
Write-Host "5. Run Systems Lab: $Py -m streamlit run apps\forge-systems-lab\app.py"
Write-Host ""
Write-Host "For a truly offline machine, download model weights before disconnecting the network."
