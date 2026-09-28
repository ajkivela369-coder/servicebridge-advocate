from __future__ import annotations

import argparse
import json

from forge_core.recovery import run_recovery_drill


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Restore Forge from an offline pack and run the strict recovery acceptance test."
    )
    parser.add_argument("pack")
    parser.add_argument(
        "--report",
        default="./private_data/forge/recovery/latest.json",
    )
    parser.add_argument(
        "--network-isolated-confirmed",
        action="store_true",
        help="Set only when this drill is actually being run with external network access disabled.",
    )
    parser.add_argument("--primary-executable", default="ollama")
    args = parser.parse_args()

    report = run_recovery_drill(
        args.pack,
        report_path=args.report,
        primary_executable=args.primary_executable,
        network_isolation_confirmed=args.network_isolated_confirmed,
    )
    print(json.dumps(report.to_dict(), indent=2))
    raise SystemExit(0 if report.status == "PASS" else 3)


if __name__ == "__main__":
    main()
