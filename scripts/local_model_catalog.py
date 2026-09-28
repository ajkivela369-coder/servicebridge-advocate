from __future__ import annotations

import argparse
from pathlib import Path

from servicebridge.local_runtime.models import (
    LocalModel,
    LocalModelCatalog,
    artifact_sha256,
)
from servicebridge.local_runtime import detect_hardware


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage locally installed model files.")
    parser.add_argument(
        "--catalog",
        default="./private_data/local_runtime/models.json",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add")
    add.add_argument("--id", required=True)
    add.add_argument("--kind", required=True, choices=["text", "vision", "embedding", "reranker", "image", "video", "tts"])
    add.add_argument("--path", required=True)
    add.add_argument("--format", default="unknown")
    add.add_argument("--quality-rank", type=int, default=0)
    add.add_argument("--min-ram-gb", type=float, default=0)
    add.add_argument("--min-vram-gb", type=float, default=0)
    add.add_argument("--hash", action="store_true")
    add.add_argument("--license", default="")
    add.add_argument("--source", default="")
    add.add_argument("--replace", action="store_true")

    sub.add_parser("list")
    verify = sub.add_parser("verify")
    verify.add_argument("--id", required=True)
    sub.add_parser("best")

    args = parser.parse_args()
    catalog = LocalModelCatalog(args.catalog)

    if args.command == "add":
        path = Path(args.path).expanduser().resolve()
        if not path.exists() or not (path.is_file() or path.is_dir()):
            raise SystemExit(f"Model file/directory not found: {path}")
        digest = artifact_sha256(path) if args.hash else ""
        catalog.add(
            LocalModel(
                model_id=args.id,
                kind=args.kind,
                path=str(path),
                format=args.format,
                quality_rank=args.quality_rank,
                min_ram_gb=args.min_ram_gb,
                min_vram_gb=args.min_vram_gb,
                sha256=digest,
                license=args.license,
                source=args.source,
            ),
            replace=args.replace,
        )
        print(f"Registered {args.id}")
        return

    if args.command == "list":
        for model in catalog.list():
            print(f"{model.kind:10} {model.model_id:28} {model.path}")
        return

    if args.command == "verify":
        print(catalog.verify(args.id))
        return

    hardware = detect_hardware()
    for kind in ["text", "vision", "embedding", "reranker", "image", "video", "tts"]:
        model = catalog.best(kind, hardware)
        print(f"{kind:10} {model.model_id if model else 'none'}")


if __name__ == "__main__":
    main()
