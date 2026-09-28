from __future__ import annotations

import argparse

from servicebridge.local_runtime.image import generate_image_local


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an image with an already-installed local Diffusers model.")
    parser.add_argument("--model", required=True, help="Local model directory")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--negative", default="")
    parser.add_argument("--output", required=True)
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--steps", type=int, default=28)
    parser.add_argument("--guidance", type=float, default=5.0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--device", choices=["cpu", "cuda", "mps"], default=None)
    args = parser.parse_args()

    result = generate_image_local(
        args.prompt,
        model_path=args.model,
        output_path=args.output,
        negative_prompt=args.negative,
        width=args.width,
        height=args.height,
        steps=args.steps,
        guidance_scale=args.guidance,
        seed=args.seed,
        device=args.device,
    )
    print(result)


if __name__ == "__main__":
    main()
