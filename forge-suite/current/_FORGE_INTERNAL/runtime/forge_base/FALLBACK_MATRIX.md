# Forge fallback matrix

| Need | Primary | Fallback 1 | Fallback 2 | Offline preparation |
|---|---|---|---|---|
| Local reasoning | Ollama + Qwen | llama.cpp + retained Qwen GGUF | deterministic heuristic/template path | cache Ollama models, llama.cpp binaries + GGUF |
| Coding | Qwen Coder via Ollama | llama.cpp Qwen | local templates/manual code path | retain both model routes |
| Embeddings/search | nomic-embed-text | deterministic feature hashing | SQLite lexical/vector cache | retain Ollama model + SQLite database |
| Vision | Qwen2.5-VL | metadata-only local path | manual/source inspection | retain VLM model; provenance preserved |
| Narration | Kokoro | eSpeak | Windows SAPI | cache HF model + Python wheelhouse |
| Transcription | whisper.cpp | faster-whisper | WSL whisper.cpp | cache executable + base.en/small.en + wheels |
| Final render | native FFmpeg | cached portable FFmpeg | WSL/container FFmpeg | retain installer/portable binary |
| Diagrams | Pillow/SVG deterministic | Mermaid | Manim | wheelhouse/npm cache/templates |
| Linux-only dependency | WSL2 | Podman | explicit full VM only when needed | WSL export + container images |
| Python environment | uv | venv + pip | offline wheelhouse | retained wheels + lock/requirements |
| Project recovery | Git bundle | project ZIP | source archive | verified backups |
| Cloud credits/service unavailable | local engine | alternate local engine | ask before optional cloud | cloud is never the sole route |

## UI / design

| Need | Primary | Local fallback | Offline recovery |
|---|---|---|---|
| High-end UI design exploration | 12ui when service reachable | Forge local HTML/CSS/SVG design | Restore cached 12ui runtime; otherwise use retained templates/local renderer |
| npm unavailable | Retained 12ui runtime | Forge local design | `downloads/npm-packages` + `downloads/npm-cache` |
| Hosted design service unavailable | — | Forge local design | `templates/design` + local renderer |
