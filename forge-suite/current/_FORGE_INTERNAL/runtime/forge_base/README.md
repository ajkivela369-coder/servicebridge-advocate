# Forge Base P1 — anti-roadblock layer

Forge Base makes Forge Core reproducible, recoverable, and local-first. It creates one durable workspace for tools, models, installers, caches, environments, logs, backups and exported artifacts.

## Windows default

Forge prefers `D:\Forge` when a D: drive exists; otherwise it uses `%USERPROFILE%\Forge`.

## Durable layout

- `bin/` portable executables
- `downloads/installers/` retained installers and release archives
- `downloads/wheelhouse/` offline Python packages
- `downloads/npm-cache/` npm cache
- `downloads/containers/` exported container images
- `downloads/sources/` retained source archives
- `models/ollama/`, `models/llama.cpp/`, `models/whisper/`, `models/huggingface/`
- `cache/` generated assets and local vector database
- `envs/` isolated environments / WSL import locations
- `projects/` checked-out Forge apps
- `exports/` finished artifacts
- `manifests/` Doctor, hashes, inventories and test results
- `backups/` offline bundles, WSL exports and project bundles

## Resilience order

1. Healthy native tool.
2. Cached portable binary/model in `FORGE_HOME`.
3. Second local engine (for example Ollama -> llama.cpp).
4. WSL2.
5. Podman/container.
6. Cached-source build when necessary.
7. Optional cloud only when explicitly approved.

## P1 rule

A capability is not considered complete unless `feature_gate.py` confirms it has:
- a local route,
- a fallback route,
- and an offline asset/restore strategy.

This layer does not bypass authentication, licensing, access controls, safety restrictions, or vendor service limits.
