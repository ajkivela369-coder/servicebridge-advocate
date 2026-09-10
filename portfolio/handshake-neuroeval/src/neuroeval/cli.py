from __future__ import annotations
import argparse, json
from .evaluator import evaluate

def main() -> None:
    parser = argparse.ArgumentParser(description="Transparent biology/neuroscience AI-response evaluator")
    parser.add_argument("answer")
    parser.add_argument("--concept", action="append", default=[])
    args = parser.parse_args()
    print(json.dumps(evaluate(args.answer, args.concept).to_dict(), indent=2))

if __name__ == "__main__":
    main()
