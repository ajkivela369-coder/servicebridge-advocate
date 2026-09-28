from __future__ import annotations

import argparse
import json
from pathlib import Path

from servicebridge.local_runtime import RuntimeMode, runtime_snapshot
from servicebridge.local_runtime.workers import worker_capabilities


INSTALL_HINTS = {
    "llama_cpp": "Install llama.cpp and place llama-server on PATH.",
    "piper": "Install Piper locally and download at least one voice model.",
    "ffmpeg": "Install FFmpeg and place ffmpeg on PATH.",
    "comfyui": "Run ComfyUI locally with API access on 127.0.0.1:8188.",
    "ollama": "Optional: install Ollama if you prefer it over llama.cpp.",
    "faster_whisper": "Install faster-whisper and pre-download a model for fully offline use.",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect the ServiceBridge/Forge local runtime.")
    parser.add_argument(
        "--mode",
        choices=[x.value for x in RuntimeMode],
        default=RuntimeMode.CREDITLESS.value,
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    snapshot = runtime_snapshot(RuntimeMode(args.mode))
    snapshot["workers"] = [x.to_dict() for x in worker_capabilities()]
    snapshot["install_hints"] = INSTALL_HINTS

    if args.json:
        print(json.dumps(snapshot, indent=2))
        return

    hw = snapshot["hardware"]
    print("ServiceBridge Local Runtime")
    print("=" * 32)
    print(f"Mode: {snapshot['mode']}")
    print(
        f"Hardware: {hw['os']} {hw['machine']} · {hw['cpu_count']} CPU threads · "
        f"{hw['ram_gb'] or '?'} GB RAM · tier={hw['tier']}"
    )
    if hw.get("gpu_name"):
        print(f"GPU: {hw['gpu_name']} · {hw.get('gpu_vram_gb') or '?'} GB VRAM")
    else:
        print("GPU: no NVIDIA GPU reported by nvidia-smi")

    print("\nLocal services")
    for service in snapshot["services"]:
        state = "READY" if service["healthy"] else ("INSTALLED" if service["installed"] else "MISSING")
        print(f"- {service['service_id']}: {state}")
        if state != "READY":
            print(f"  {INSTALL_HINTS.get(service['service_id'], service['notes'])}")

    print("\nLocal workers")
    for worker in snapshot["workers"]:
        state = "READY" if worker["available"] else "MISSING"
        print(f"- {worker['worker_id']}: {state} · {worker['notes']}")

    print("\nCreditless invariant")
    if args.mode == RuntimeMode.CREDITLESS.value:
        print("- Non-local model endpoints are blocked by policy.")
        print("- Cloud fallback is disabled.")
        print("- Missing capabilities must degrade locally instead of buying credits.")


if __name__ == "__main__":
    main()
