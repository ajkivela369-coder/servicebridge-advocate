from __future__ import annotations

import argparse
import json
from pathlib import Path

from neuroeval.ml import cross_validate, load_cases
from neuroeval.retrieval import RetrievalItem, TfidfRetrievalIndex


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run NeuroEval's classical NLP/ML learning experiment."
    )
    parser.add_argument(
        "--data",
        default=str(Path(__file__).parent / "data" / "benchmark_extended.jsonl"),
    )
    parser.add_argument(
        "--query",
        default="How do sodium and potassium channels contribute to an action potential?",
    )
    args = parser.parse_args()

    cases = load_cases(args.data)
    result = cross_validate(cases)

    index = TfidfRetrievalIndex(
        RetrievalItem(item_id=case.case_id, text=case.answer)
        for case in cases
    )
    retrieval_hits = index.search(args.query, limit=3)

    payload = {
        "warning": (
            "Learning demonstration only. The benchmark is small, so metrics are unstable "
            "and must not be presented as production model performance."
        ),
        "classification": {
            "method": "TF-IDF bigrams + logistic regression",
            "folds": 3,
            "accuracy": round(result.accuracy, 4),
            "labels": list(result.labels),
            "confusion_matrix": result.confusion,
            "per_class": {
                label: {
                    "precision": round(result.report[label]["precision"], 4),
                    "recall": round(result.report[label]["recall"], 4),
                    "f1": round(result.report[label]["f1-score"], 4),
                    "support": int(result.report[label]["support"]),
                }
                for label in result.labels
            },
        },
        "retrieval_baseline": {
            "method": "TF-IDF cosine similarity",
            "query": args.query,
            "hits": [
                {"id": hit.item_id, "score": round(hit.score, 4), "text": hit.text}
                for hit in retrieval_hits
            ],
        },
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
