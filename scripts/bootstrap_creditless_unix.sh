#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "ServiceBridge / Forge Creditless Bootstrap"
echo "Installs Python-side local runtime dependencies; model weights are not downloaded automatically."

python3 -m venv .venv-creditless
PY=".venv-creditless/bin/python"
"$PY" -m pip install --upgrade pip
"$PY" -m pip install -e .
"$PY" -m pip install -r apps/forge-systems-lab/requirements.txt
"$PY" -m pip install "pypdf>=5"

echo
echo "Local executable checks"
for exe in ffmpeg llama-server ollama piper nvidia-smi; do
  if command -v "$exe" >/dev/null 2>&1; then
    echo "  READY   $exe -> $(command -v "$exe")"
  else
    echo "  MISSING $exe"
  fi
done

echo
echo "Next:"
echo "1. Place model files under private_data/local_runtime/models (or another private folder)."
echo "2. Register them with scripts/local_model_catalog.py."
echo "3. Start only the local engines you need."
echo "4. Run: $PY scripts/local_runtime_doctor.py"
echo "5. Run: $PY -m streamlit run apps/forge-systems-lab/app.py"
echo
echo "For a truly offline machine, provision model weights before disconnecting the network."
