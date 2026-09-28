from __future__ import annotations

import argparse

from servicebridge.local_runtime.video import generate_video_local


def main():
    parser = argparse.ArgumentParser(
        description="Generate video with an already-downloaded local Diffusers pipeline."
    )
    parser.add_argument("--model", required=True, help="Local Diffusers model directory")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--negative", default="")
    parser.add_argument("--output", required=True)
    parser.add_argument("--width", type=int, default=768)
    parser.add_argument("--height", type=int, default=512)
    parser.add_argument("--frames", type=int, default=49)
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--guidance", type=float, default=6.0)
    parser.add_argument("--fps", type=int, default=8)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--device", choices=["cpu", "cuda", "mps"], default=None)
    parser.add_argument("--dtype", choices=["float16", "bfloat16", "float32"], default=None)
    parser.add_argument("--cpu-offload", action="store_true")
    args = parser.parse_args()

    result = generate_video_local(
        args.prompt,
        model_path=args.model,
        output_path=args.output,
        negative_prompt=args.negative,
        width=args.width,
        height=args.height,
        num_frames=args.frames,
        steps=args.steps,
        guidance_scale=args.guidance,
        fps=args.fps,
        seed=args.seed,
        device=args.device,
        dtype_name=args.dtype,
        enable_cpu_offload=args.cpu_offload,
    )
    print(result)


if __name__ == "__main__":
    main()
