from __future__ import annotations
from pathlib import Path
import json
import math
import shutil
import subprocess
import textwrap
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont

from .cache import stable_hash, cache_dir
from .tts import synthesize
from .detect import capabilities

ROOT = Path(__file__).resolve().parents[2]
OUTPUTS = ROOT / "data" / "outputs"
OUTPUTS.mkdir(parents=True, exist_ok=True)

W, H = 1920, 1080
BG = (7, 20, 35)
PANEL = (15, 35, 55)
CYAN = (76, 213, 229)
WHITE = (241, 247, 250)
MUTED = (164, 184, 196)
GREEN = (93, 214, 146)


def _font(size: int, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size=size)
    return ImageFont.load_default()


def _wrap(draw, text, font, max_width):
    words = text.split()
    lines, cur = [], ""
    for word in words:
        test = f"{cur} {word}".strip()
        if draw.textbbox((0,0), test, font=font)[2] <= max_width:
            cur = test
        else:
            if cur: lines.append(cur)
            cur = word
    if cur: lines.append(cur)
    return lines


def draw_slide(title: str, bullets: list[str], idx: int, total: int, path: Path):
    im = Image.new("RGB", (W,H), BG)
    d = ImageDraw.Draw(im)
    # header
    d.rounded_rectangle((90,70,1830,210), radius=28, fill=PANEL)
    d.text((135,105), "FORGE CORE  •  TEACH ME THIS", font=_font(30, True), fill=CYAN)
    d.text((1580,105), f"{idx:02d}/{total:02d}", font=_font(30, True), fill=MUTED)
    # title
    tf = _font(58, True)
    y = 275
    for line in _wrap(d, title, tf, 1610)[:3]:
        d.text((130,y), line, font=tf, fill=WHITE)
        y += 72
    # visual flow rail
    rail_y = 520
    stages = ["IDENTIFY","SCOPE","UPSTREAM","DOWNSTREAM","RESOLVE","COMMUNICATE"]
    box_w = 245
    x0 = 130
    for j,s in enumerate(stages):
        x = x0 + j*(box_w+28)
        active = j == min(len(stages)-1, math.floor((idx-1) / max(1,total-1) * len(stages)))
        fill = (20,54,72) if not active else (20,84,96)
        outline = CYAN if active else (50,80,95)
        d.rounded_rectangle((x,rail_y,x+box_w,rail_y+76), radius=18, fill=fill, outline=outline, width=3)
        sw = d.textbbox((0,0),s,font=_font(21,True))[2]
        d.text((x+(box_w-sw)/2,rail_y+25),s,font=_font(21,True),fill=WHITE if active else MUTED)
        if j < len(stages)-1:
            d.line((x+box_w+5,rail_y+38,x+box_w+23,rail_y+38), fill=CYAN, width=4)
    # bullets
    bf = _font(34)
    y = 665
    for bullet in bullets[:4]:
        lines = _wrap(d, bullet, bf, 1490)
        d.ellipse((132,y+13,150,y+31), fill=GREEN)
        for k,line in enumerate(lines[:2]):
            d.text((178,y+k*48), line, font=bf, fill=WHITE if k==0 else MUTED)
        y += max(76, len(lines[:2])*50+18)
    d.text((130,1010), "Local-first • cached • provenance-aware • no cloud required", font=_font(24), fill=MUTED)
    im.save(path, "PNG")


def _duration(path: Path) -> float:
    p = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(path)],capture_output=True,text=True,check=True)
    return float(p.stdout.strip())


def _srt_time(seconds: float) -> str:
    ms = int(round(seconds*1000)); h=ms//3600000; ms%=3600000; m=ms//60000; ms%=60000; s=ms//1000; ms%=1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def render_lesson(lesson: dict, output_name: str = "lesson") -> dict:
    caps = capabilities()
    if not caps["local_only_capable"]:
        raise RuntimeError("Local render prerequisites missing: FFmpeg, Pillow, and a local TTS engine are required.")
    key = stable_hash({"lesson":lesson,"renderer":"forge-core-v0.5.4-british"})
    work = cache_dir(key)
    final = OUTPUTS / f"{output_name}-{key[:8]}.mp4"
    manifest_path = OUTPUTS / f"{output_name}-{key[:8]}.manifest.json"
    srt_path = OUTPUTS / f"{output_name}-{key[:8]}.srt"
    if final.exists() and manifest_path.exists():
        return {"cached":True,"video":str(final),"manifest":str(manifest_path),"captions":str(srt_path) if srt_path.exists() else None,"cache_key":key}

    scenes = lesson.get("scenes") or []
    clips=[]; timeline=[]; engines=[]; cursor=0.0
    for i, scene in enumerate(scenes,1):
        slide = work / f"slide-{i:02d}.png"
        wav = work / f"voice-{i:02d}.wav"
        clip = work / f"clip-{i:02d}.mp4"
        if not slide.exists():
            draw_slide(scene.get("title",f"Step {i}"), scene.get("bullets") or [], i, len(scenes), slide)
        if not wav.exists():
            engine = synthesize(scene.get("narration") or scene.get("title", ""), wav)
        else:
            engine = capabilities()["voice"].get("preferred") or "local-tts"
        engines.append(engine)
        dur=max(2.0,_duration(wav)+0.4)
        if not clip.exists():
            subprocess.run([
                "ffmpeg","-y","-loglevel","error","-loop","1","-framerate","30","-i",str(slide),"-i",str(wav),
                "-t",f"{dur:.3f}","-vf",f"scale={W}:{H},format=yuv420p","-c:v","libx264","-preset","ultrafast","-tune","stillimage","-c:a","aac","-b:a","160k","-shortest",str(clip)
            ],check=True)
        clips.append(clip)
        timeline.append({"index":i,"start":cursor,"end":cursor+dur,"title":scene.get("title"),"narration":scene.get("narration"),"tts":engine})
        cursor += dur

    concat_file = work / "concat.txt"
    concat_file.write_text("\n".join([f"file '{c.as_posix()}'" for c in clips]), encoding="utf-8")
    temp = work / "joined.mp4"
    subprocess.run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",str(concat_file),"-c","copy",str(temp)],check=True)

    srt=[]
    for t in timeline:
        srt += [str(t["index"]), f"{_srt_time(t['start'])} --> {_srt_time(t['end']-0.08)}", t["narration"], ""]
    srt_path.write_text("\n".join(srt), encoding="utf-8")

    # Keep captions as a sidecar for maximum portability. MP4 remains editable and clean.
    shutil.copy2(temp, final)
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode":"LOCAL_ONLY",
        "cache_key":key,
        "lesson_builder":lesson.get("builder"),
        "duration_seconds":round(cursor,2),
        "tts_engines":sorted(set(engines)),
        "capabilities":caps,
        "timeline":timeline,
        "outputs":{"video":str(final),"captions":str(srt_path)},
        "network_services_used":[],
    }
    manifest_path.write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    return {"cached":False,"video":str(final),"manifest":str(manifest_path),"captions":str(srt_path),"cache_key":key,"duration_seconds":round(cursor,2)}
