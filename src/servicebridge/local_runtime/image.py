from __future__ import annotations

from pathlib import Path
from typing import Any


def diffusers_available() -> bool:
    try:
        import diffusers  # noqa: F401
        import torch  # noqa: F401
        return True
    except Exception:
        return False


def generate_image_local(
    prompt: str,
    *,
    model_path: str | Path,
    output_path: str | Path,
    negative_prompt: str = "",
    width: int = 1024,
    height: int = 1024,
    steps: int = 28,
    guidance_scale: float = 5.0,
    seed: int = 0,
    device: str | None = None,
) -> dict[str, Any]:
    """
    Generate a still image directly with a local Diffusers model directory.

    local_files_only=True is mandatory here: Creditless workflows must fail
    clearly when weights are missing instead of downloading them.
    """
    try:
        import torch
        from diffusers import AutoPipelineForText2Image
    except ImportError as exc:
        raise RuntimeError(
            "Direct local image generation requires torch + diffusers."
        ) from exc

    model_path = Path(model_path).expanduser().resolve()
    if not model_path.exists():
        raise FileNotFoundError(model_path)

    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    dtype = torch.float16 if device == "cuda" else torch.float32
    pipeline = AutoPipelineForText2Image.from_pretrained(
        str(model_path),
        torch_dtype=dtype,
        local_files_only=True,
    )
    pipeline = pipeline.to(device)

    generator_device = device if device != "mps" else "cpu"
    generator = torch.Generator(device=generator_device).manual_seed(int(seed))
    result = pipeline(
        prompt=prompt,
        negative_prompt=negative_prompt or None,
        width=int(width),
        height=int(height),
        num_inference_steps=int(steps),
        guidance_scale=float(guidance_scale),
        generator=generator,
    )
    if not getattr(result, "images", None):
        raise RuntimeError("Local image pipeline returned no image.")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.images[0].save(output)
    return {
        "output_path": str(output),
        "model_path": str(model_path),
        "device": device,
        "seed": int(seed),
        "width": int(width),
        "height": int(height),
        "steps": int(steps),
        "provider": "local-diffusers",
        "network_downloads_allowed": False,
    }
