from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .advocate import Advocate
from .ingest import ingest_file
from .models import AdvocacyMode, AdvocacyRequest, BenefitLane, EvidenceClass
from .providers import OpenAIProvider, PromptOnlyProvider
from .store import EvidenceStore


def _db_path(value: str | None) -> Path:
    return Path(value or os.getenv("SERVICEBRIDGE_DB", "./private_data/servicebridge.sqlite3"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="servicebridge",
        description="Privacy-first, source-grounded medical and disability advocacy assistant.",
    )
    parser.add_argument("--db", help="Local SQLite evidence index (default: SERVICEBRIDGE_DB)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Create an empty local evidence index")

    ingest = sub.add_parser("ingest", help="Extract, redact, chunk, and index a source file")
    ingest.add_argument("path")
    ingest.add_argument(
        "--class",
        dest="evidence_class",
        choices=[item.value for item in EvidenceClass],
        default=EvidenceClass.UNKNOWN.value,
    )
    ingest.add_argument("--title")
    ingest.add_argument("--date", dest="document_date")
    ingest.add_argument("--author")
    ingest.add_argument(
        "--no-redact",
        action="store_true",
        help="Index unredacted text locally. Never use this for a shared/public database.",
    )

    sources = sub.add_parser("sources", help="List indexed sources")
    sources.add_argument("--json", action="store_true")

    search = sub.add_parser("search", help="Search the local evidence index")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=8)

    ask = sub.add_parser("ask", help="Build or run a record-grounded advocacy request")
    ask.add_argument("question")
    ask.add_argument("--lane", choices=[item.value for item in BenefitLane], default="general")
    ask.add_argument(
        "--mode",
        choices=[item.value for item in AdvocacyMode],
        default=AdvocacyMode.PRIVATE_ANALYSIS.value,
    )
    ask.add_argument("--audience", default="claimant")
    ask.add_argument("--output", dest="requested_output", default="analysis")
    ask.add_argument("--top-k", type=int, default=8)
    ask.add_argument(
        "--provider",
        choices=["prompt", "openai"],
        default="prompt",
        help="Prompt mode keeps all data local; OpenAI mode requires explicit selection.",
    )
    ask.add_argument("--model", help="Optional model override for OpenAI mode")
    ask.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    database = _db_path(args.db)

    if args.command == "init":
        with EvidenceStore(database):
            pass
        print(f"Created local evidence index: {database}")
        return 0

    with EvidenceStore(database) as store:
        if args.command == "ingest":
            source, chunks = ingest_file(
                args.path,
                EvidenceClass(args.evidence_class),
                redact=not args.no_redact,
                title=args.title,
                document_date=args.document_date,
                author=args.author,
            )
            store.add_document(source, chunks)
            counts = source.metadata.get("redaction_counts", {})
            print(
                json.dumps(
                    {
                        "source_id": source.source_id,
                        "title": source.title,
                        "chunks": len(chunks),
                        "redacted": source.redacted,
                        "redaction_counts": counts,
                    },
                    indent=2,
                )
            )
            return 0

        if args.command == "sources":
            items = [source.to_dict() for source in store.list_sources()]
            if args.json:
                print(json.dumps(items, indent=2))
            else:
                for item in items:
                    print(f"{item['source_id']}\t{item['evidence_class']}\t{item['title']}")
            return 0

        if args.command == "search":
            hits = store.search(args.query, limit=args.limit)
            for hit in hits:
                print(f"[{hit.chunk.source_id}; {hit.chunk.locator}] {hit.title}")
                print(hit.chunk.text)
                print()
            return 0

        if args.command == "ask":
            provider = (
                OpenAIProvider(model=args.model)
                if args.provider == "openai"
                else PromptOnlyProvider()
            )
            response = Advocate(store, provider).answer(
                AdvocacyRequest(
                    question=args.question,
                    lane=BenefitLane(args.lane),
                    mode=AdvocacyMode(args.mode),
                    audience=args.audience,
                    requested_output=args.requested_output,
                    top_k=args.top_k,
                )
            )
            print(json.dumps(response.to_dict(), indent=2) if args.json else response.answer)
            return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
