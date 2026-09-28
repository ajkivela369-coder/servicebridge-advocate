from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector


def parse_args():
    args = sys.argv
    if "--" in args:
        args = args[args.index("--") + 1 :]
    else:
        args = []
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", required=True)
    parser.add_argument("--render", action="store_true")
    return parser.parse_args(args)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        # Remove unused data blocks so repeated background runs stay clean.
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def import_obj(path: Path):
    before = set(bpy.context.scene.objects)
    try:
        bpy.ops.wm.obj_import(filepath=str(path))
    except Exception:
        bpy.ops.import_scene.obj(filepath=str(path))
    imported = [obj for obj in bpy.context.scene.objects if obj not in before]
    if not imported:
        raise RuntimeError(f"No Blender object was imported from {path}")
    return imported


def make_material(name: str, role: str, index: int):
    material = bpy.data.materials.new(name=f"MAT_{name}")
    palette = [
        (0.22, 0.62, 0.72, 1.0),
        (0.72, 0.48, 0.18, 1.0),
        (0.38, 0.72, 0.42, 1.0),
        (0.62, 0.42, 0.72, 1.0),
        (0.72, 0.30, 0.30, 1.0),
    ]
    material.diffuse_color = palette[index % len(palette)]
    material["medforge_role"] = role
    return material


def set_origin_to_geometry(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    finally:
        obj.select_set(False)


def bounds_world(objects):
    points = []
    for obj in objects:
        for corner in obj.bound_box:
            points.append(obj.matrix_world @ Vector(corner))
    if not points:
        return Vector((-50, -50, -50)), Vector((50, 50, 50))
    mn = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    mx = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return mn, mx


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def add_camera_and_lights(objects):
    scene = bpy.context.scene
    mn, mx = bounds_world(objects)
    center = (mn + mx) * 0.5
    extent = max((mx - mn).length, 50.0)

    camera_data = bpy.data.cameras.new("MedForgeCamera")
    camera = bpy.data.objects.new("MedForgeCamera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = Vector((center.x, center.y - extent * 1.6, center.z + extent * 0.65))
    camera_data.lens = 52
    camera_data.clip_start = max(0.01, extent / 10000.0)
    camera_data.clip_end = max(10000.0, extent * 20.0)
    look_at(camera, center)
    scene.camera = camera

    key_data = bpy.data.lights.new("Key", type="AREA")
    key_data.energy = 1100
    key_data.shape = "DISK"
    key_data.size = extent
    key = bpy.data.objects.new("Key", key_data)
    scene.collection.objects.link(key)
    key.location = Vector((center.x - extent * 0.8, center.y - extent, center.z + extent))
    look_at(key, center)

    fill_data = bpy.data.lights.new("Fill", type="AREA")
    fill_data.energy = 650
    fill_data.size = extent * 0.8
    fill = bpy.data.objects.new("Fill", fill_data)
    scene.collection.objects.link(fill)
    fill.location = Vector((center.x + extent, center.y - extent * 0.2, center.z + extent * 0.3))
    look_at(fill, center)

    rim_data = bpy.data.lights.new("Rim", type="AREA")
    rim_data.energy = 900
    rim_data.size = extent * 0.6
    rim = bpy.data.objects.new("Rim", rim_data)
    scene.collection.objects.link(rim)
    rim.location = Vector((center.x, center.y + extent, center.z + extent * 0.8))
    look_at(rim, center)


def configure_scene(scene_spec):
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 0.001
    scene.frame_start = int(scene_spec.get("frame_start", 1))
    scene.frame_end = int(scene_spec.get("frame_end", 90))
    scene.render.fps = int(scene_spec.get("fps", 30))
    scene.render.resolution_x = int(scene_spec.get("width", 1280))
    scene.render.resolution_y = int(scene_spec.get("height", 720))
    scene.render.resolution_percentage = 100

    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except Exception:
        try:
            scene.render.engine = "BLENDER_EEVEE"
        except Exception:
            pass

    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"

    # Burn the evidence class into rendered frames so an exported MP4 cannot
    # lose the reconstruction boundary when separated from its manifest.
    scene.render.use_stamp = True
    scene.render.use_stamp_note = True
    scene.render.stamp_note_text = (
        "ILLUSTRATIVE / DERIVED · segmentation geometry + explicit motion · "
        "not proof of diagnosis or causation"
    )
    scene.render.use_stamp_date = False
    scene.render.use_stamp_time = False
    scene.render.use_stamp_render_time = False
    scene.render.use_stamp_frame = True
    scene.render.use_stamp_frame_range = False
    scene.render.use_stamp_camera = False
    scene.render.use_stamp_scene = False
    scene.render.use_stamp_filename = False
    scene.render.use_stamp_marker = False
    scene.render.use_stamp_sequencer_strip = False
    scene.render.stamp_font_size = 14

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.025, 0.03, 0.035)

    scene["medforge_scene_class"] = "ILLUSTRATIVE / DERIVED"
    scene["medforge_rule"] = (
        "Meshes derive from imported segmentations; motion is user/record-specified. "
        "Animation is not proof of diagnosis or causation."
    )


def main():
    args = parse_args()
    scene_path = Path(args.scene).resolve()
    spec = json.loads(scene_path.read_text())
    base = scene_path.parent

    clear_scene()
    configure_scene(spec)

    imported_by_id = {}
    all_objects = []

    for index, item in enumerate(spec.get("objects", [])):
        obj_path = (base / item["obj_path"]).resolve()
        imported = import_obj(obj_path)
        # OBJ can theoretically contain multiple object groups; apply the same
        # provenance to every imported piece.
        material = make_material(item["object_id"], item.get("evidence_class", "DERIVED"), index)
        for obj in imported:
            obj.name = item["object_id"] if len(imported) == 1 else f'{item["object_id"]}_{obj.name}'
            obj.data.materials.clear()
            obj.data.materials.append(material)
            obj["medforge_source_mask"] = item.get("source_mask", "")
            obj["medforge_provenance"] = item.get("provenance", "")
            obj["medforge_evidence_class"] = item.get("evidence_class", "DERIVED / UNREVIEWED")
            try:
                for poly in obj.data.polygons:
                    poly.use_smooth = True
            except Exception:
                pass
            set_origin_to_geometry(obj)
            all_objects.append(obj)

        # Keep derived geometry separate from illustrative motion. The controller
        # carries keyframes; meshes remain children with their provenance intact.
        center = Vector((0.0, 0.0, 0.0))
        for obj in imported:
            center += obj.location
        center /= max(1, len(imported))

        controller = bpy.data.objects.new(f'RIG_{item["object_id"]}', None)
        controller.empty_display_type = "PLAIN_AXES"
        controller.empty_display_size = 8.0
        controller.location = center
        controller["medforge_control_role"] = "ILLUSTRATIVE / HYPOTHESIZED MOTION RIG"
        controller["medforge_structure_id"] = item["object_id"]
        bpy.context.scene.collection.objects.link(controller)

        for obj in imported:
            world = obj.matrix_world.copy()
            obj.parent = controller
            obj.matrix_world = world

        imported_by_id[item["object_id"]] = [controller]

    bpy.context.view_layer.update()
    add_camera_and_lights(all_objects)

    for motion in spec.get("motions", []):
        targets = imported_by_id.get(motion["structure_id"], [])
        for obj in targets:
            base_location = obj.location.copy()
            base_rotation = obj.rotation_euler.copy()

            start = int(motion["start_frame"])
            end = int(motion["end_frame"])
            obj.location = base_location
            obj.rotation_euler = base_rotation
            obj.keyframe_insert(data_path="location", frame=start)
            obj.keyframe_insert(data_path="rotation_euler", frame=start)

            tx, ty, tz = [float(x) for x in motion["translation_mm_xyz"]]
            rx, ry, rz = [math.radians(float(x)) for x in motion["rotation_deg_xyz"]]
            obj.location = base_location + Vector((tx, ty, tz))
            obj.rotation_euler = (
                base_rotation.x + rx,
                base_rotation.y + ry,
                base_rotation.z + rz,
            )
            obj.keyframe_insert(data_path="location", frame=end)
            obj.keyframe_insert(data_path="rotation_euler", frame=end)
            obj["medforge_motion_evidence_lane"] = motion.get(
                "evidence_lane", "ILLUSTRATIVE / HYPOTHESIZED"
            )
            obj["medforge_motion_note"] = motion.get("note", "")

    output_blend = (base / spec.get("output_blend", "medforge_scene.blend")).resolve()
    output_blend.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output_blend))

    if args.render or bool(spec.get("render_video", False)):
        output_video = (base / spec.get("output_video", "medforge_scene.mp4")).resolve()
        output_video.parent.mkdir(parents=True, exist_ok=True)
        bpy.context.scene.render.filepath = str(output_video)
        bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
