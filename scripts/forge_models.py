from __future__ import annotations

import argparse
import json

from forge_core.core import ForgePaths
from forge_core.model_profiles import register_present_profiles, staged_profile_status


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage/register Forge local model roles.")
    parser.add_argument("--profiles", default="config/forge_model_profiles.json")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()

    if args.status:
        print(json.dumps(staged_profile_status(args.profiles), indent=2))
        return

    paths = ForgePaths.default()
    registered = register_present_profiles(paths.model_catalog, args.profiles)
    if registered:
        print("Registered present model profiles: " + ", ".join(registered))
    else:
        print("No staged model files are present yet. Nothing was downloaded.")


if __name__ == "__main__":
    main()
