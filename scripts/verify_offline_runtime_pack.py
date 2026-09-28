from __future__ import annotations

import argparse
import json

from servicebridge.local_runtime.offline import verify_offline_pack


def main():
    parser = argparse.ArgumentParser(description="Verify a Creditless offline pack.")
    parser.add_argument("pack")
    args = parser.parse_args()
    result = verify_offline_pack(args.pack)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["ok"] else 2)


if __name__ == "__main__":
    main()
