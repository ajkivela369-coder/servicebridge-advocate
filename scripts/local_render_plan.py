from __future__ import annotations

import argparse

from servicebridge.local_runtime.render import load_render_plan, render_plan


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a Forge plan completely locally with FFmpeg.")
    parser.add_argument("plan", help="Path to local-render-plan.json")
    args = parser.parse_args()

    plan = load_render_plan(args.plan)
    problems = plan.validate()
    if problems:
        for problem in problems:
            print("ERROR:", problem)
        raise SystemExit(2)

    output = render_plan(plan)
    print(f"Rendered: {output}")


if __name__ == "__main__":
    main()
