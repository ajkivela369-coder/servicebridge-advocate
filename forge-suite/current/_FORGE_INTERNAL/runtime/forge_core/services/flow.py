from __future__ import annotations
from pathlib import Path
import math, shutil, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont

W,H=1920,1080
BG=(7,20,35); PANEL=(15,35,55); CYAN=(76,213,229); WHITE=(241,247,250); MUTED=(164,184,196); GREEN=(93,214,146)

def _font(size,b=False):
    for p in (["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf","C:/Windows/Fonts/arialbd.ttf"] if b else ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf","C:/Windows/Fonts/arial.ttf"]):
        if Path(p).exists(): return ImageFont.truetype(p,size)
    return ImageFont.load_default()

def _frame(nodes, active, title):
    im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im)
    d.text((90,70),title,font=_font(54,True),fill=WHITE)
    n=len(nodes); margin=100; gap=22; bw=(W-2*margin-gap*(n-1))/n; y=420
    centers=[]
    for i,node in enumerate(nodes):
        x=margin+i*(bw+gap); centers.append((x+bw/2,y+95))
        on=i<=active; fill=(20,84,96) if i==active else (20,54,72)
        d.rounded_rectangle((x,y,x+bw,y+190),radius=28,fill=fill,outline=CYAN if on else (50,80,95),width=5 if i==active else 2)
        label=str(node)[:28]
        box=d.textbbox((0,0),label,font=_font(26,True)); d.text((x+(bw-(box[2]-box[0]))/2,y+72),label,font=_font(26,True),fill=WHITE if on else MUTED)
        if i<n-1:
            ax=x+bw+5; bx=x+bw+gap-5; ay=y+95
            d.line((ax,ay,bx,ay),fill=CYAN if i<active else (50,80,95),width=6)
            d.polygon([(bx,ay),(bx-18,ay-12),(bx-18,ay+12)],fill=CYAN if i<active else (50,80,95))
    d.text((90,930),"Forge Core • deterministic local animation • no generative video credits",font=_font(28),fill=MUTED)
    return im

def animate_flow(nodes:list[str], output:Path, title="Find where the chain broke", seconds_per_step=1.4):
    if len(nodes)<2: raise ValueError("Need at least two nodes")
    ffmpeg=shutil.which("ffmpeg")
    if not ffmpeg: raise RuntimeError("FFmpeg required")
    output=Path(output); output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="forge-flow-") as td:
        td=Path(td); clips=[]
        for i in range(len(nodes)):
            png=td/f"f{i:02d}.png"; mp4=td/f"c{i:02d}.mp4"; _frame(nodes,i,title).save(png)
            subprocess.run([ffmpeg,"-y","-loglevel","error","-loop","1","-i",str(png),"-t",str(seconds_per_step),"-vf",f"scale={W}:{H},format=yuv420p","-r","30","-c:v","libx264","-preset","ultrafast",str(mp4)],check=True); clips.append(mp4)
        lst=td/"concat.txt"; lst.write_text("\n".join(f"file '{p.as_posix()}'" for p in clips))
        subprocess.run([ffmpeg,"-y","-loglevel","error","-f","concat","-safe","0","-i",str(lst),"-c","copy",str(output)],check=True)
    return {"video":str(output),"nodes":nodes,"duration_seconds":round(len(nodes)*seconds_per_step,2)}
