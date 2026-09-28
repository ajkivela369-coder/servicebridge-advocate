from __future__ import annotations

import argparse

from servicebridge.local_runtime.offline import build_offline_pack


def main():
    parser = argparse.ArgumentParser(description="Build a portable Creditless runtime pack.")
    parser.add_argument("--output", default="./forge-creditless-offline-pack.zip")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--model-catalog", default="./private_data/local_runtime/models.json")
    parser.add_argument("--workflow-catalog", default="./private_data/local_runtime/workflows.json")
    parser.add_argument("--wheelhouse", default=None)
    parser.add_argument("--include-models", action="store_true")
    args = parser.parse_args()

    result = build_offline_pack(
        args.output,
        repo_root=args.repo_root,
        model_catalog=args.model_catalog,
        workflow_catalog=args.workflow_catalog,
        wheelhouse=args.wheelhouse,
        include_models=args.include_models,
    )
    print(result)


if __name__ == "__main__":
    main()
