from __future__ import annotations

import argparse

from servicebridge.local_runtime import RuntimeMode, RuntimePolicy
from servicebridge.local_runtime.evidence import LocalSemanticEvidenceStore
from servicebridge.local_runtime.memory import LocalEmbeddingClient, LocalVectorStore
from servicebridge.store import EvidenceStore


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build/update the local semantic evidence index with a localhost embedding model."
    )
    parser.add_argument(
        "--database",
        default="./private_data/servicebridge.sqlite3",
    )
    parser.add_argument(
        "--vectors",
        default="./private_data/local_runtime/evidence_vectors.sqlite3",
    )
    parser.add_argument(
        "--endpoint",
        default="http://127.0.0.1:8080/v1/embeddings",
    )
    parser.add_argument("--model", default="local-embedding-model")
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    policy = RuntimePolicy(mode=RuntimeMode.CREDITLESS)
    embedder = LocalEmbeddingClient(
        endpoint=args.endpoint,
        model=args.model,
        policy=policy,
    )

    with EvidenceStore(args.database) as base, LocalVectorStore(args.vectors) as vectors:
        hybrid = LocalSemanticEvidenceStore(base, vectors, embedder)
        count = hybrid.index(batch_size=args.batch_size)

    print(f"Indexed {count} evidence chunks locally.")


if __name__ == "__main__":
    main()
