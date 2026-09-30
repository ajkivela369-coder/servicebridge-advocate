from __future__ import annotations
import json, os, shutil, subprocess, uuid
from pathlib import Path
from .render import OUTPUTS


def _candidates():
    env = os.environ.get("FORGE_BLENDER", "").strip()
    if env:
        yield Path(env)
    found = shutil.which("blender")
    if found:
        yield Path(found)
    if os.name == "nt":
        base = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Blender Foundation"
        if base.exists():
            for p in sorted(base.glob("Blender */blender.exe"), reverse=True):
                yield p
        local = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Blender Foundation/Blender/blender.exe"
        if str(local) and local.exists():
            yield local


def find_blender():
    seen = set()
    for p in _candidates():
        try:
            p = p.resolve()
        except Exception:
            pass
        key = str(p).lower()
        if key in seen:
            continue
        seen.add(key)
        if p.exists() and p.is_file():
            return p
    return None


def status():
    p = find_blender()
    version = None
    if p:
        try:
            out = subprocess.check_output([str(p), "--version"], text=True, errors="replace", timeout=8)
            version = (out.splitlines() or ["Blender"])[0].strip()
        except Exception:
            version = "Blender detected"
    return {
        "engine": "Blender",
        "installed": bool(p),
        "path": str(p) if p else None,
        "version": version,
        "ffmpeg": bool(shutil.which("ffmpeg")),
        "uses": ["MedForge 3D mechanism teaching", "GrimForge 3D previs/blockout"],
        "note": "Blender renders are genuine 3D scenes. MedForge geometry is educational, not patient-specific anatomy; GrimForge Blender output is previs unless a production scene is authored.",
    }


def _script_text():
    return r'''import bpy, json, math, sys
from pathlib import Path
from mathutils import Vector

args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if len(args) < 2 or args[0] != '--spec':
    raise SystemExit('Expected --spec <json>')
spec = json.loads(Path(args[1]).read_text(encoding='utf-8'))
kind = spec.get('kind', 'grimforge')
prompt = str(spec.get('prompt', '')).lower()
out_mp4 = Path(spec['output_mp4'])
out_png = Path(spec['output_png'])
out_blend = Path(spec['output_blend'])
frames_dir = Path(spec['frames_dir'])
seconds = max(2.0, min(float(spec.get('seconds', 6)), 30.0))
fps = 24
frames = max(48, int(seconds * fps))

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
try:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
except Exception:
    try:
        scene.render.engine = 'BLENDER_EEVEE'
    except Exception:
        scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.fps = fps
scene.frame_start = 1
scene.frame_end = frames
if scene.world is None:
    scene.world = bpy.data.worlds.new('Forge World')
scene.world.color = (0.008, 0.012, 0.022)

def mat(name, color, metal=0.0, rough=.45, emit=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bs = m.node_tree.nodes.get('Principled BSDF')
    if bs:
        if 'Base Color' in bs.inputs: bs.inputs['Base Color'].default_value = (*color, 1)
        if 'Metallic' in bs.inputs: bs.inputs['Metallic'].default_value = metal
        if 'Roughness' in bs.inputs: bs.inputs['Roughness'].default_value = rough
        for key in ('Emission Color', 'Emission'):
            if emit and key in bs.inputs: bs.inputs[key].default_value = (*color, 1)
        if emit and 'Emission Strength' in bs.inputs: bs.inputs['Emission Strength'].default_value = emit
    return m

def add_cube(name, loc, scale, material, bevel=.08):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale
    if material: o.data.materials.append(material)
    if bevel:
        mod = o.modifiers.new('Soft edges', 'BEVEL'); mod.width = bevel; mod.segments = 3
    return o

def add_sphere(name, loc, scale, material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale
    if material: o.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return o

def add_cyl(name, loc, radius, depth, material):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=radius, depth=depth, location=loc)
    o = bpy.context.object; o.name = name
    if material: o.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return o

def add_text(txt, loc, size, material, extrude=.02):
    bpy.ops.object.text_add(location=loc, rotation=(math.radians(72), 0, 0))
    o = bpy.context.object; o.data.body = txt; o.data.align_x = 'CENTER'; o.data.size = size; o.data.extrude = extrude
    if material: o.data.materials.append(material)
    return o

def point_camera(cam, target=(0,0,1)):
    direction = Vector(target) - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

def add_area(loc, energy, size, color=(1,1,1)):
    bpy.ops.object.light_add(type='AREA', location=loc)
    l = bpy.context.object; l.data.energy = energy; l.data.shape = 'DISK'; l.data.size = size; l.data.color = color
    point_camera(l, (0,0,1))
    return l

floor = mat('Floor', (0.018,0.035,0.055), metal=.1, rough=.55)
add_cube('Stage', (0,0,-.3), (8,8,.25), floor, .12)
add_area((5,-5,8), 1500, 5, (0.7,0.85,1))
add_area((-5,2,5), 900, 4, (1,.3,.25))
add_area((0,5,3), 650, 3, (.25,.45,1))

if kind == 'medforge':
    bone = mat('Bone', (0.82,0.86,0.88), rough=.65)
    cart = mat('Cartilage', (.25,.62,.72), rough=.35)
    accent = mat('Mechanism cue', (1,.06,.08), rough=.3, emit=1.2)
    label = mat('Label', (1,.35,.42), rough=.3, emit=.4)
    add_cyl('Superior bone', (0,0,2.4), 1.05, 3.7, bone)
    add_sphere('Superior head', (0,0,.65), (1.3,1.3,.8), bone)
    add_sphere('Inferior head', (0,0,-.05), (1.25,1.25,.62), bone)
    add_cyl('Inferior bone', (0,0,-2.0), .92, 3.2, bone)
    add_cyl('Joint space', (0,0,.28), 1.32, .22, cart)
    add_sphere('Mechanism focus', (1.1,-.45,.35), (.34,.34,.34), accent)
    shaft = add_cyl('Vector shaft', (2.2,-.55,.45), .10, 2.4, accent); shaft.rotation_euler[1] = math.radians(76)
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=.35, radius2=0, depth=.65, location=(3.35,-.55,.75), rotation=(0,math.radians(76),0))
    bpy.context.object.data.materials.append(accent)
    add_text('MEDFORGE 3D TEACHING MODEL', (0,2.9,3.4), .42, label)
    add_text('NOT PATIENT-SPECIFIC GEOMETRY', (0,2.9,2.85), .25, label)
    cam_start=(8,-10,5.6); cam_end=(5.2,-11,4.2); target=(0,0,.2)
else:
    if any(k in prompt for k in ('forest','wood','jungle')):
        base=(.035,.13,.055); ruin=(.11,.22,.07); accent=(.35,1,.22)
    elif any(k in prompt for k in ('desert','sand','dune')):
        base=(.24,.16,.07); ruin=(.42,.22,.06); accent=(1,.58,.10)
    elif any(k in prompt for k in ('medieval','castle','fortress','gate')):
        base=(.11,.10,.095); ruin=(.25,.17,.09); accent=(1,.35,.04)
    else:
        base=(.10,.14,.18); ruin=(.35,.11,.035); accent=(1,.18,.02)
    steel=mat('Environment',base,metal=.55,rough=.34)
    rust=mat('Structures',ruin,metal=.25,rough=.55)
    glow=mat('Story focus',accent,metal=.1,rough=.22,emit=3.5)
    amber=mat('Character marker',(1,.48,.03),rough=.35,emit=.7)
    add_cube('Station core',(0,0,1.2),(2.4,2.1,1.5),steel,.15)
    add_sphere('Failing reactor',(0,-2.1,1.3),(1.0,1.0,1.0),glow)
    for i,x in enumerate((-5,-3.6,3.6,5)):
        add_cube('Ruin '+str(i),(x,1.4,1.2),(0.65,2.1,1.5+i*.18),rust,.08)
    add_cube('Bridge',(0,3.3,.35),(4.5,.55,.25),steel,.06)
    add_sphere('Medic marker',(-1.7,-.5,.35),(.28,.28,.55),amber)
    add_text('GRIMFORGE 3D PREVIS',(0,4.6,3.1),.48,amber)
    cam_start=(10,-13,7.0); cam_end=(-7,-11,5.2); target=(0,0,1.2)

bpy.ops.object.camera_add(location=cam_start)
cam=bpy.context.object; scene.camera=cam; point_camera(cam,target); cam.data.lens=42
cam.keyframe_insert(data_path='location',frame=1); cam.keyframe_insert(data_path='rotation_euler',frame=1)
cam.location=cam_end; point_camera(cam,target); cam.keyframe_insert(data_path='location',frame=frames); cam.keyframe_insert(data_path='rotation_euler',frame=frames)
if cam.animation_data and cam.animation_data.action:
    action = cam.animation_data.action
    # Blender 5.x changed Action internals; older releases expose fcurves directly.
    # Default keyframe interpolation is already Bezier, so skip this optional polish
    # when the compatibility attribute is unavailable.
    for fc in getattr(action, 'fcurves', []):
        for kp in fc.keyframe_points: kp.interpolation='BEZIER'

out_blend.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out_blend))
scene.frame_set(1)
scene.render.image_settings.file_format='PNG'; scene.render.filepath=str(out_png); bpy.ops.render.render(write_still=True)
frames_dir.mkdir(parents=True, exist_ok=True)
scene.render.image_settings.file_format='PNG'; scene.render.use_file_extension=True; scene.render.filepath=str(frames_dir / 'frame-')
bpy.ops.render.render(animation=True)
print('FORGE_BLENDER_FRAMES='+str(frames_dir))
'''


def render(kind: str, prompt: str = "", seconds: float = 6.0, output_name: str = "forge-3d", progress=lambda x: None):
    if kind not in ("medforge", "grimforge"):
        raise ValueError("3D render kind must be medforge or grimforge.")
    blender = find_blender()
    if not blender:
        raise RuntimeError("Blender is not installed. Open Forge Setup & Repair → Install Media / 3D Tools.")
    safe = "".join(c if c.isalnum() or c in "._-" else "-" for c in output_name).strip("-")[:80] or ("medforge-3d" if kind == "medforge" else "grimforge-previz")
    run_id = uuid.uuid4().hex[:10]
    work = OUTPUTS / f"blender-{kind}-{run_id}"
    work.mkdir(parents=True, exist_ok=True)
    mp4 = OUTPUTS / f"{safe}-{run_id}.mp4"
    png = OUTPUTS / f"{safe}-{run_id}.png"
    blend = OUTPUTS / f"{safe}-{run_id}.blend"
    frames_dir = work / "frames"
    spec = {"kind": kind, "prompt": prompt[:16000], "seconds": max(2, min(float(seconds), 30)), "output_mp4": str(mp4), "output_png": str(png), "output_blend": str(blend), "frames_dir": str(frames_dir)}
    spec_path = work / "spec.json"
    spec_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    script = work / "forge_blender_render.py"
    script.write_text(_script_text(), encoding="utf-8")
    progress("Launching Blender headless 3D renderer")
    log = work / "blender.log"
    with log.open("w", encoding="utf-8", errors="replace") as fh:
        p = subprocess.run([str(blender), "--background", "--python", str(script), "--", "--spec", str(spec_path)], stdout=fh, stderr=subprocess.STDOUT, text=True, timeout=3600)
    if p.returncode != 0:
        tail = log.read_text(encoding="utf-8", errors="replace")[-4000:]
        raise RuntimeError("Blender render failed. " + tail)
    frame_files = sorted(frames_dir.glob("frame-*.png"))
    if not frame_files:
        raise RuntimeError("Blender finished but produced no animation frames.")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("Blender rendered frames, but external FFmpeg is unavailable for MP4 assembly.")
    progress("Encoding Blender frames to MP4 with external FFmpeg")
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-framerate", "24", "-i", str(frames_dir / "frame-%04d.png"), "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(mp4)], check=True, timeout=1200)
    shutil.rmtree(frames_dir, ignore_errors=True)
    missing = [str(x) for x in (mp4, png, blend) if not x.exists() or x.stat().st_size == 0]
    if missing:
        raise RuntimeError("Blender finished but expected outputs are missing: " + ", ".join(missing))
    progress("Blender 3D render completed")
    full_scene = kind == "grimforge" and str(output_name).startswith("grimforge-3d-scene")
    render_type = "3D mechanism teaching clip" if kind == "medforge" else ("Procedural 3D animated scene" if full_scene else "3D cinematic previs")
    boundary = "Educational non-patient-specific geometry" if kind == "medforge" else ("Genuine Blender 3D animation. Visual fidelity depends on available authored/generated assets; this procedural scene is not automatically photorealistic." if full_scene else "Previsualization/blockout; not a final cinematic render")
    return {"engine": "Blender", "kind": kind, "render_type": render_type, "video": str(mp4), "image": str(png), "blend": str(blend), "log": str(log), "seconds": seconds, "prompt": prompt, "boundary": boundary}