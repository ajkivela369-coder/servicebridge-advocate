# Forge Base P1 — upstream sources

Forge deliberately keeps a manifest of where its retained local tools/models come from.

- Ollama model library: https://ollama.com/library
  - `qwen2.5:7b-instruct`
  - `qwen2.5-coder:7b`
  - `nomic-embed-text`
  - optional `qwen2.5vl:7b`
- whisper.cpp official repository/releases: https://github.com/ggml-org/whisper.cpp
- whisper.cpp model cache: https://huggingface.co/ggerganov/whisper.cpp
- Kokoro inference library: https://github.com/hexgrad/kokoro
- Kokoro model: https://huggingface.co/hexgrad/Kokoro-82M
- FFmpeg: https://ffmpeg.org/
- uv: https://docs.astral.sh/uv/
- WSL: https://learn.microsoft.com/windows/wsl/
- Podman Desktop: https://podman-desktop.io/

## Retention rule

After first successful staging, Forge keeps installers/binaries/models inside `FORGE_HOME`, inventories them, and can place them into a verified offline bundle. Upstream services are then needed only for updates or tools/models not yet cached.
- llama.cpp: https://github.com/ggml-org/llama.cpp
- Qwen GGUF fallback model: https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF
