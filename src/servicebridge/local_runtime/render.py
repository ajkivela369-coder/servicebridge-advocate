from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any

from .media import (
    burn_subtitles_command,
    concat_command,
    run_command,
    scene_video_command,
    video_clip_scene_command,
)


@dataclass(frozen=True)
class LocalSceneAsset:
    scene_id: str
    image_path: str
    duration: float
    audio_path: str = ""
    video_path: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LocalSceneAsset":
        return cls(
            scene_id=str(data["scene_id"]),
            image_path=str(data.get("image_path", "") or ""),
            duration=float(data["duration"]),
            audio_path=str(data.get("audio_path", "") or ""),
            video_path=str(data.get("video_path", "") or ""),
        )


@dataclass
class LocalRenderPlan:
    title: str
    output_path: str
    scenes: list[LocalSceneAsset] = field(default_factory=list)
    subtitles_path: str = ""
    width: int = 1920
    height: int = 1080
    fps: int = 30
    audio_lufs: int = -16

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LocalRenderPlan":
        return cls(
            title=str(data.get("title", "Local Forge Render")),
            output_path=str(data["output_path"]),
            scenes=[LocalSceneAsset.from_dict(x) for x in data.get("scenes", [])],
            subtitles_path=str(data.get("subtitles_path", "") or ""),
            width=int(data.get("width", 1920)),
            height=int(data.get("height", 1080)),
            fps=int(data.get("fps", 30)),
            audio_lufs=int(data.get("audio_lufs", -16)),
        )

    def validate(self) -> list[str]:
        problems = []
        if not self.scenes:
            problems.append("No scenes are configured.")
        if self.width <= 0 or self.height <= 0 or self.fps <= 0:
            problems.append("Width, height, and fps must be positive.")
        for scene in self.scenes:
            if scene.duration <= 0:
                problems.append(f"{scene.scene_id}: duration must be positive.")
            source_count = int(bool(scene.image_path)) + int(bool(scene.video_path))
            if source_count != 1:
                problems.append(
                    f"{scene.scene_id}: configure exactly one image_path or video_path."
                )
            if scene.image_path and not Path(scene.image_path).is_file():
                problems.append(f"{scene.scene_id}: image not found: {scene.image_path}")
            if scene.video_path and not Path(scene.video_path).is_file():
                problems.append(f"{scene.scene_id}: video not found: {scene.video_path}")
            if scene.audio_path and not Path(scene.audio_path).is_file():
                problems.append(f"{scene.scene_id}: audio not found: {scene.audio_path}")
        if self.subtitles_path and not Path(self.subtitles_path).is_file():
            problems.append(f"Subtitles not found: {self.subtitles_path}")
        return problems


def load_render_plan(path: str | Path) -> LocalRenderPlan:
    data = json.loads(Path(path).read_text())
    if not isinstance(data, dict):
        raise ValueError("Render plan must be a JSON object.")
    return LocalRenderPlan.from_dict(data)


def build_render_commands(
    plan: LocalRenderPlan,
    *,
    work_dir: str | Path,
) -> dict[str, Any]:
    problems = plan.validate()
    if problems:
        raise ValueError("Invalid local render plan: " + "; ".join(problems))

    work = Path(work_dir)
    work.mkdir(parents=True, exist_ok=True)
    segments = []
    commands = []

    for index, scene in enumerate(plan.scenes, start=1):
        segment = work / f"segment_{index:04d}.mp4"
        if scene.video_path:
            command = video_clip_scene_command(
                scene.video_path,
                segment,
                duration=scene.duration,
                audio_path=scene.audio_path or None,
                width=plan.width,
                height=plan.height,
                fps=plan.fps,
                audio_lufs=plan.audio_lufs,
            )
        else:
            command = scene_video_command(
                scene.image_path,
                segment,
                duration=scene.duration,
                audio_path=scene.audio_path or None,
                width=plan.width,
                height=plan.height,
                fps=plan.fps,
                audio_lufs=plan.audio_lufs,
            )
        commands.append(command)
        segments.append(segment)

    concat_file = work / "concat.txt"
    concat_file.write_text(
        "\n".join(f"file '{p.resolve().as_posix()}'" for p in segments),
        encoding="utf-8",
    )
    assembled = work / "assembled.mp4"
    commands.append(concat_command(concat_file, assembled))

    final_output = Path(plan.output_path)
    if plan.subtitles_path:
        commands.append(
            burn_subtitles_command(
                assembled,
                plan.subtitles_path,
                final_output,
            )
        )
    else:
        # Final copy remains a filesystem operation instead of an unnecessary
        # re-encode.
        final_output = Path(plan.output_path)

    return {
        "commands": commands,
        "segments": [str(x) for x in segments],
        "concat_file": str(concat_file),
        "assembled": str(assembled),
        "final_output": str(final_output),
        "copy_assembled_to_final": not bool(plan.subtitles_path),
    }


def render_plan(plan: LocalRenderPlan) -> Path:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("FFmpeg is required for local rendering.")

    output = Path(plan.output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="forge-local-render-") as tmp:
        built = build_render_commands(plan, work_dir=tmp)
        for command in built["commands"]:
            run_command(command)

        assembled = Path(built["assembled"])
        if built["copy_assembled_to_final"]:
            shutil.copy2(assembled, output)

    return output
