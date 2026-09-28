# Forge Base P1 completion checklist

## Foundation
- [x] Permanent Forge home and cache/model folders
- [x] Doctor + storage/RAM/tool detection
- [x] Native Windows-first strategy
- [x] WSL2 escape hatch scripts
- [x] Podman install path
- [x] Offline installer cache path
- [x] Python wheelhouse

## Local engines
- [x] FFmpeg render route + portable/cache fallback strategy
- [x] Ollama model staging
- [x] Hardware-adaptive Qwen general/coding models
- [x] Nomic local embeddings
- [x] Optional Qwen2.5-VL local vision
- [x] whisper.cpp installer + base.en/small.en integrity-checked model cache
- [x] faster-whisper fallback
- [x] Kokoro cache/warm-up
- [x] eSpeak + Windows SAPI voice fallbacks

## Shared app services
- [x] Teach Me This video pipeline
- [x] Deterministic animated flowchart engine
- [x] Persistent local vector search
- [x] Vision API
- [x] Transcription API
- [x] Model/task router
- [x] Hardware-aware policy

## Recovery
- [x] SHA-256 offline bundle create/verify/restore
- [x] Optional models in offline bundle
- [x] Git project backup/restore
- [x] WSL export/restore
- [x] Manifests and provenance
- [x] End-to-end self-test

## Standing release gate
A capability is not considered complete until its local route, fallback route and offline restore route are documented and testable.

## UI/design resilience addendum
- [x] 12ui is optional, not a hard runtime dependency.
- [x] One successful online install can be retained as a complete offline-restorable Node runtime.
- [x] npm cache is centralized under Forge Home.
- [x] Forge local design fallback works without network or npm.
- [x] Doctor records DNS reachability for key package/model hosts.
- [x] UI-design feature is covered by the local/fallback/offline release gate.
