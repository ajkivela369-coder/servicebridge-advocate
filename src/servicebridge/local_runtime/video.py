from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any


def diffusers_video_available() -> bool:
    try:
        import diffusers  # noqa: F401
        import torch  # noqa: F401
        return True
    except Exception:
        return False


def _supported_call_kwargs(callable_obj, candidates: dict[str, Any]) -> dict[str, Any]:
    """
    Pass only parameters explicitly supported by the loaded pipeline unless its
    call signature accepts arbitrary keyword arguments.
    """
    signature = inspect.signature(callable_obj)
    parameters = signature.parameters
    accepts_var_kw = any(
        p.kind == inspect.Parameter.VAR_KEYWORD for p in parameters.values()
    )
    if accepts_var_kw:
        return {k: v for k, v in candidates.items() if v is not None}
    return {
        key: value
        for key, value in candidates.items()
        if key in parameters and value is not None
    }


def generate_video_local(
    prompt: str,
    *,
    model_path: str | Path,
    output_path: str | Path,
    negative_prompt: str = "",
    width: int = 768,
    height: int = 512,
    num_frames: int = 49,
    steps: int = 30,
    guidance_scale: float = 6.0,
    fps: int = 8,
    seed: int = 0,
    device: str | None = None,
    dtype_name: str | None = None,
    enable_cpu_offload: bool = False,
) -> dict[str, Any]:
    """
    Run a Diffusers-compatible text-to-video model entirely from local files.

    This is intentionally generic. Different video architectures have different
    preferred frame counts, resolutions, and dtypes, so callers should use a
    model-specific profile rather than assuming these defaults are optimal.

    No model download is allowed: from_pretrained receives local_files_only=True.
    """
    if not prompt.strip():
        raise ValueError("prompt is required.")

    try:
        import torch
        from diffusers import DiffusionPipeline
        from diffusers.utils import export_to_video
    except ImportError as exc:
        raise RuntimeError(
            "Direct local video generation requires torch + diffusers."
        ) from exc

    model_path = Path(model_path).expanduser().resolve()
    if not model_path.is_dir():
        raise FileNotFoundError(
            f"Expected an already-downloaded local Diffusers model directory: {model_path}"
        )

    if device is None:
        if torch.cuda.is_available():
            device = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"

    dtype_lookup = {
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
        "float32": torch.float32,
    }
    if dtype_name is None:
        dtype = torch.bfloat16 if device == "cuda" else torch.float32
        dtype_name = "bfloat16" if device == "cuda" else "float32"
    else:
        if dtype_name not in dtype_lookup:
            raise ValueError("dtype_name must be float16, bfloat16, or float32.")
        dtype = dtype_lookup[dtype_name]

    pipeline = DiffusionPipeline.from_pretrained(
        str(model_path),
        torch_dtype=dtype,
        local_files_only=True,
    )

    if enable_cpu_offload and device == "cuda" and hasattr(pipeline, "enable_model_cpu_offload"):
        pipeline.enable_model_cpu_offload()
    else:
        pipeline = pipeline.to(device)

    generator_device = "cpu" if device == "mps" else device
    generator = torch.Generator(device=generator_device).manual_seed(int(seed))

    candidates = {
        "prompt": prompt,
        "negative_prompt": negative_prompt or None,
        "width": int(width),
        "height": int(height),
        "num_frames": int(num_frames),
        "num_inference_steps": int(steps),
        "guidance_scale": float(guidance_scale),
        "generator": generator,
    }
    kwargs = _supported_call_kwargs(pipeline.__call__, candidates)
    if "prompt" not in kwargs:
        raise RuntimeError(
            "The loaded Diffusers pipeline does not expose a text prompt argument; "
            "use a compatible text-to-video profile or a model-specific worker."
        )

    result = pipeline(**kwargs)
    frames_batch = getattr(result, "frames", None)
    if frames_batch is None or len(frames_batch) == 0:
        raise RuntimeError("Local video pipeline returned no frames.")
    frames = frames_batch[0]

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    exported = export_to_video(
        frames,
        str(output),
        fps=int(fps),
    )

    return {
        "output_path": str(exported or output),
        "model_path": str(model_path),
        "provider": "local-diffusers-video",
        "network_downloads_allowed": False,
        "device": device,
        "dtype": dtype_name,
        "seed": int(seed),
        "fps": int(fps),
        "requested_frames": int(num_frames),
        "pipeline_class": type(pipeline).__name__,
        "call_parameters_used": sorted(kwargs.keys()),
    }
