from __future__ import annotations
import argparse, json
from .auditor import audit

def main() -> None:
    parser = argparse.ArgumentParser(description="Safety-first health-science AI output auditor")
    parser.add_argument("text")
    args = parser.parse_args()
    print(json.dumps(audit(args.text).to_dict(), indent=2))

if __name__ == "__main__":
    main()
