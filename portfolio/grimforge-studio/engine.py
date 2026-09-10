from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable


REFERENCE_DNA = {
    "Scholar-Voice Reference": {
        "narrator": 96,
        "humor": 28,
        "cinematic": 86,
        "depth": 98,
        "motion": 84,
        "pace": 54,
        "notes": "Thesis-led analysis, calm authority, intellectual cross-pollination, explicit canon-vs-interpretation labels, in-world terminal UI, diagrams, 2.5D depth and rare deadpan release beats.",
    },
    "Deadpan-Humor Reference": {
        "narrator": 76,
        "humor": 98,
        "cinematic": 76,
        "depth": 58,
        "motion": 74,
        "pace": 88,
        "notes": "Domesticated horror, bureaucratic framing of absurd stakes, triangular character dynamics, micro-interruptions, rhythm-of-three jokes, snap zooms, hard cuts to silence and kinetic captions.",
    },
    "Premium-Chronicler Reference": {
        "narrator": 92,
        "humor": 12,
        "cinematic": 99,
        "depth": 86,
        "motion": 98,
        "pace": 62,
        "notes": "Formal chronicler register, chaptered chronology, 4–6 plane parallax, continuous camera micro-moves, tactical maps, volumetric light, particles, selective 3D scale shots and layered broadcast-style audio.",
    },
}

VOICE_PROFILES = {
    "Young Imperial Historian": {
        "age_character": "early-to-mid 30s",
        "register": "low-mid",
        "tempo": "measured",
        "texture": "clean, resonant, educated",
        "direction": "Controlled authority with a slightly youthful brightness. Let dry humor register as a small smile, never as a comedy voice.",
    },
    "Battle Chronicler": {
        "age_character": "mid 30s",
        "register": "mid-low",
        "tempo": "measured with decisive accelerations",
        "texture": "commanding, cinematic, weathered but not old",
        "direction": "Treat battles like remembered history. Build weight before names, places, betrayals, and reversals.",
    },
    "Old World Scholar": {
        "age_character": "30s",
        "register": "low-mid",
        "tempo": "deliberate",
        "texture": "bookish, dry, faintly theatrical",
        "direction": "Sound like a dangerous manuscript is being explained by someone who finds the footnotes genuinely amusing.",
    },
}

ASSET_RIGHTS = [
    "Original AI artwork",
    "User-owned",
    "Licensed",
    "Public domain",
    "Third-party / reference only",
]

PRODUCTION_RECIPES = {
    "Archive Terminal": {
        "camera": "Locked archive frame with subtle scan drift, rack focus between foreground interface and central image.",
        "graphics": "Monospace citations, terminal typing, restrained glitch, waveform/data sidebars, source label in a fixed safe zone.",
        "edit": "Use as a bridge into sourced claims or methodology; exit on a clean degauss/static transition rather than constant glitching.",
    },
    "Layered Motion Painting": {
        "camera": "Separate 4–6 depth planes and maintain an ultra-slow push or pan; use foreground occlusion to sell depth.",
        "graphics": "Minimal text. Add dust, fog, embers, light shafts or subtle lens texture only where they reinforce environment.",
        "edit": "Hold longer than a normal B-roll cut. Let the narration reveal details as the virtual camera approaches them.",
    },
    "Strategic Map": {
        "camera": "Begin at system/kingdom scale, then travel to the decisive front, city or battlefield before the narration names the tactical problem.",
        "graphics": "Low-opacity terrain/grid, movement vectors, front lines, territory fills, date/source tag and only essential labels.",
        "edit": "Synchronize each vector or territory change to a narrated decision, not merely to time passing.",
    },
    "Comic Snap": {
        "camera": "Economical 2D posing with one-frame punch-ins, head snaps or scale contrast rather than full animation.",
        "graphics": "Kinetic word emphasis, color-coded speaker cues, occasional tiny/redacted text as a secondary gag.",
        "edit": "Use a rhythm of three: severe premise → elaborate justification → flat deflation; hard-cut to room tone when the joke peaks.",
    },
    "Premium 3D Establishing Shot": {
        "camera": "Wide volumetric reveal with slow dolly/crane movement; transition from planetary/city scale to a readable human-scale focal point.",
        "graphics": "Keep HUD minimal; favor environmental storytelling, silhouette, scale and selective heraldic color.",
        "edit": "Reserve for act openings, major reversals and payoff moments so 3D remains special rather than visual wallpaper.",
    },
    "Interpretation Diagram": {
        "camera": "Stable or gently floating composition so the viewer can actually think.",
        "graphics": "Radial diagram, duality map, timeline or causal chain with explicit INTERPRETATION badge and source anchors for the canon inputs.",
        "edit": "Reduce music density and let diagram elements enter in the same order as the argument.",
    },
}


@dataclass
class Scene:
    index: int
    start: str
    duration_seconds: int
    purpose: str
    narration_goal: str
    visual: str
    motion: str
    sound: str
    humor: str
    canon_label: str
    recipe: str
    camera: str
    graphics: str
    edit: str

    def to_dict(self) -> dict:
        return asdict(self)


def blend_reference_dna(weights: dict[str, int]) -> dict[str, int]:
    total = max(sum(max(v, 0) for v in weights.values()), 1)
    traits = ["narrator", "humor", "cinematic", "depth", "motion", "pace"]
    blended = {}
    for trait in traits:
        blended[trait] = round(
            sum(REFERENCE_DNA[name][trait] * max(weights.get(name, 0), 0) for name in REFERENCE_DNA) / total
        )
    return blended


def _clock(seconds: int) -> str:
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def _humor_line(level: int, index: int, world: str) -> str:
    if level < 20:
        return "None; preserve gravity."
    if level < 50:
        return "One dry pressure-release line after the dense idea; underplay it and return immediately to the argument."
    if level < 80:
        return "Deadpan tonal collision: treat one outrageous in-world consequence with painfully ordinary bureaucratic or domestic language."
    return "Escalating callback: plant a mundane misunderstanding here, intensify it through a second beat, then pay it off with a flat deflation or hard cut to silence."


def _recipe_for_scene(index: int, humor_level: int, motion_level: int) -> str:
    if humor_level >= 70 and index in {3, 5}:
        return "Comic Snap"
    mapping = {
        1: "Premium 3D Establishing Shot" if motion_level >= 70 else "Layered Motion Painting",
        2: "Strategic Map",
        3: "Layered Motion Painting",
        4: "Interpretation Diagram",
        5: "Archive Terminal",
        6: "Premium 3D Establishing Shot" if motion_level >= 65 else "Layered Motion Painting",
        7: "Layered Motion Painting",
        8: "Archive Terminal",
    }
    return mapping.get(index, "Layered Motion Painting")


def build_director_timeline(
    topic: str,
    angle: str,
    world: str,
    length_minutes: int,
    humor_level: int,
    motion_level: int,
    depth_level: int,
) -> list[Scene]:
    topic = topic.strip() or "the chosen subject"
    angle = angle.strip() or "what most summaries miss"
    total = max(4, min(length_minutes, 60)) * 60
    proportions = [0.06, 0.10, 0.16, 0.18, 0.18, 0.16, 0.10, 0.06]
    labels = [
        ("Cold open", f"State the unsettling question behind {topic}, not the encyclopedia definition."),
        ("Orientation", f"Give only the minimum lore needed to understand the thesis: {angle}."),
        ("First proof", "Move from broad claim to a concrete event, faction, text, artifact, or campaign."),
        ("Deep lens", "Bring in a useful outside lens—history, theology, myth, statecraft, warfare, economics, or psychology—then return immediately to the lore."),
        ("Complication", "Present the strongest counterexample, contradiction, retcon, or competing interpretation."),
        ("Reconstruction", "Show why the pieces still matter together. Label canon, inference, and fan interpretation separately."),
        ("Payoff", "Return to the opening question with a sharper answer and one memorable image."),
        ("Exit sting", "Close with a restrained final line that leaves one unresolved door open for the next episode."),
    ]
    visual_modes = [
        "Black screen into a dimensional reveal of an original relic, silhouette, ruined city or battlefield; establish scale before exposition.",
        "Animated star map or parchment campaign map with only the labels required to understand geography and stakes.",
        "Layered character/environment art with foreground, subject, midground and background separation; reveal the concrete evidence visually.",
        "Diagram, manuscript, iconography, timeline or causal model built to explain the outside intellectual lens without turning it into decoration.",
        "Abrupt contrast into a sourced archive frame, split-screen comparison or redacted dossier so the counterargument feels materially different.",
        "Premium dimensional establishing shot followed by annotated motion-art closeups that rebuild the thesis from individual pieces.",
        "Slow push through a symbolic environment while opening motifs return and the thesis becomes visually legible without extra text.",
        "Near-static final tableau or archive shutdown; let narration, ambience and one final visual detail carry the last beat.",
    ]
    sound_modes = [
        "Low drone, distant metal/choir texture and environmental room; hold percussion until the thesis lands.",
        "Subtle pulse and spatial ambience. Map movement receives soft tactical impacts rather than game-like beeps everywhere.",
        "Introduce restrained percussion or mechanical rhythm; keep narration centered and intelligible above the bed.",
        "Thin the score during complex explanation; use quiet UI/diagram sounds as punctuation, not constant activity.",
        "Narrow or briefly drop the score before the strongest counterexample; a short silence can do more than another impact.",
        "Build low brass, dark strings or percussion as the reconstruction gains confidence; duck automatically beneath narration.",
        "Widen the score and bring back the opening motif; sync a major visual reveal to a key word or narrator pause.",
        "Resolve to ambience and leave a pocket of silence before/after the final tonal hit.",
    ]
    scenes = []
    cursor = 0
    for idx, ((purpose, narration), prop) in enumerate(zip(labels, proportions), 1):
        duration = max(20, round(total * prop))
        if idx == len(labels):
            duration = max(20, total - cursor)
        motion = (
            "High motion: 4–6 plane depth where useful, constant micro-drift, selective particles/volumetrics, light interaction, tactical overlays and occasional 3D scale shots."
            if motion_level >= 70
            else "Moderate motion: parallax, map travel, light sweeps, restrained camera drift and occasional foreground occlusion."
            if motion_level >= 40
            else "Low motion: elegant stills, slow Ken Burns moves, deliberate cuts and a few carefully timed graphic reveals."
        )
        canon = "CANON / SOURCE" if idx in {2, 3, 5} else "INTERPRETATION" if idx in {4, 6, 7} else "EDITORIAL"
        recipe_name = _recipe_for_scene(idx, humor_level, motion_level)
        recipe = PRODUCTION_RECIPES[recipe_name]
        scenes.append(
            Scene(
                index=idx,
                start=_clock(cursor),
                duration_seconds=duration,
                purpose=purpose,
                narration_goal=narration,
                visual=visual_modes[idx - 1],
                motion=motion,
                sound=sound_modes[idx - 1],
                humor=_humor_line(humor_level, idx, world),
                canon_label=canon,
                recipe=recipe_name,
                camera=recipe["camera"],
                graphics=recipe["graphics"],
                edit=recipe["edit"],
            )
        )
        cursor += duration
    return scenes


def build_script_blueprint(topic: str, angle: str, world: str, depth: int, humor: int) -> list[dict]:
    topic = topic.strip() or "the chosen subject"
    angle = angle.strip() or "the hidden contradiction at its center"
    lens = (
        "Use at least two outside intellectual lenses, but every comparison must earn its place and return to the source material. Insert a micro-summary before changing intellectual frameworks."
        if depth >= 70
        else "Use one outside analogy only where it makes the lore clearer, then return to the source material."
    )
    joke = (
        "Use recurring deadpan callbacks, rhythm-of-three escalation, mundane-versus-apocalyptic contrast, and rare hard cuts to silence. Never make every line a joke."
        if humor >= 70
        else "Use occasional dry pressure-release lines after dense passages; underplay delivery and resume the serious argument immediately."
        if humor >= 30
        else "Keep humor nearly absent."
    )
    return [
        {"section": "Thesis Hook", "instruction": f"Open with a question or paradox about {topic}. Promise a specific new way to see it: {angle}."},
        {"section": "Minimum Necessary Lore", "instruction": "Orient newcomers without making veteran viewers sit through a wiki recital. Establish only the actors, rules and chronology needed for the thesis."},
        {"section": "Evidence Ladder", "instruction": "For each major claim: source fact → what it establishes → what remains uncertain → interpretation. Give sourced facts a visibly different production treatment from theory."},
        {"section": "Cross-Disciplinary Lens", "instruction": lens},
        {"section": "Counterweight", "instruction": "Give the strongest alternate reading, contradictory source, retcon, ambiguity or authorial complication before resolving the thesis."},
        {"section": "Humor Control", "instruction": joke},
        {"section": "Micro-Summary", "instruction": "Before the final act, spend 20–45 seconds restating the few conclusions the viewer must carry forward. Treat this as cognitive breathing room, not filler."},
        {"section": "Final Reframe", "instruction": f"Return to {topic}; answer the opening question more precisely than the hook did, then leave one consequential mystery open."},
    ]


def rights_gate(assets: Iterable[dict]) -> dict:
    blocked = []
    cleared = []
    for asset in assets:
        status = asset.get("rights") or "Third-party / reference only"
        entry = {"name": asset.get("name") or "Untitled asset", "rights": status}
        if status == "Third-party / reference only":
            blocked.append(entry)
        else:
            cleared.append(entry)
    return {
        "ready": not blocked,
        "blocked": blocked,
        "cleared": cleared,
        "note": "Rights labels are workflow metadata, not legal advice. Verify licenses and permitted use before publication.",
    }


def build_channel_concept(world: str, narrator: str, humor: int, depth: int) -> dict:
    if world == "Old World Dark Fantasy":
        promise = "Treat kingdoms, cults, monsters and wars like fragments from a dangerous medieval archive—serious enough to reward history nerds, strange enough to stay fun."
        visual = "charred parchment, candlelit maps, carved heraldry, fog, painted battle tableaux, ruined stone, practical manuscript graphics and selective volumetric depth"
    else:
        promise = "Treat impossible future history like a recovered imperial archive: grand, analytical, ominous, tactically legible and occasionally very dry."
        visual = "cathedral-scale silhouettes, star maps, archive-terminal overlays, dark metal, dust, embers, selective heraldic accents, parallax paintings and rare 3D scale reveals"
    return {
        "channel_promise": promise,
        "narrator": narrator,
        "visual_language": visual,
        "humor_rule": "Humor releases tension but never trivializes the central tragedy." if humor < 70 else "Deadpan absurdity is a recurring counter-rhythm to the epic stakes; use interruption, callbacks and silence as much as punchlines.",
        "depth_rule": "Every episode needs a thesis, a counterargument, micro-summaries and a clearly labeled interpretation layer." if depth >= 65 else "Every episode needs one clear thesis and a source-vs-interpretation distinction.",
    }
