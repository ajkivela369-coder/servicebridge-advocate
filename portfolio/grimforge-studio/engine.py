from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable


REFERENCE_DNA = {
    "Scholar-Voice Reference": {
        "narrator": 96,
        "humor": 28,
        "cinematic": 82,
        "depth": 98,
        "motion": 78,
        "pace": 54,
        "notes": "Thesis-led analysis, intellectual cross-pollination, calm authority, clear separation of lore and interpretation.",
    },
    "Deadpan-Humor Reference": {
        "narrator": 76,
        "humor": 98,
        "cinematic": 72,
        "depth": 58,
        "motion": 70,
        "pace": 84,
        "notes": "Deadpan escalation, callbacks, mundane framing of absurd stakes, character-driven comic rhythm.",
    },
    "Premium-Chronicler Reference": {
        "narrator": 92,
        "humor": 12,
        "cinematic": 97,
        "depth": 86,
        "motion": 94,
        "pace": 62,
        "notes": "Formal chronicler register, long-form chronology, premium documentary flow, ceremonial transitions.",
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
        return "One dry pressure-release line after the dense idea; no meme insert."
    if level < 80:
        return "Deadpan contrast: describe one outrageous in-world fact with painfully ordinary administrative language."
    return "Escalating callback: plant a bureaucratic absurdity here and pay it off one scene later without breaking the world tone."


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
        "Black screen to slow reveal of an original illustrated relic / battlefield silhouette",
        "Animated star map or parchment map with only essential labels",
        "Layered character/environment artwork with foreground-middle-background parallax",
        "Diagram, manuscript, iconography, timeline, or campaign overlay built as an explanatory visual",
        "Abrupt visual contrast: clean evidence card, split-screen comparison, or redacted archive frame",
        "3D-feel establishing shot followed by annotated motion-art closeups",
        "Slow push through a symbolic environment while earlier visual motifs return",
        "Near-static final tableau; let sound and narration carry the last beat",
    ]
    sound_modes = [
        "Low atmospheric drone, distant metal/choir texture; hold percussion until the thesis lands",
        "Subtle pulse; use spatial ambience to create scale",
        "Introduce restrained percussion or mechanical rhythm with the first concrete evidence",
        "Thin the music under complex explanation; punctuate diagrams with soft impacts",
        "Drop or narrow the score before the counterargument, then reintroduce texture",
        "Build low brass/percussion or dark strings as the reconstruction gains certainty",
        "Widen the score and bring back the opening motif",
        "Resolve to ambience; one final tonal hit after the last sentence",
    ]
    scenes = []
    cursor = 0
    for idx, ((purpose, narration), prop) in enumerate(zip(labels, proportions), 1):
        duration = max(20, round(total * prop))
        if idx == len(labels):
            duration = max(20, total - cursor)
        motion = (
            "High motion: layered depth, camera drift, particles, selective 3D, animated masks and light."
            if motion_level >= 70
            else "Moderate motion: parallax, map moves, light sweeps, restrained camera drift."
            if motion_level >= 40
            else "Low motion: elegant stills, slow Ken Burns moves, deliberate cuts."
        )
        canon = "CANON / SOURCE" if idx in {2, 3, 5} else "INTERPRETATION" if idx in {4, 6, 7} else "EDITORIAL"
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
            )
        )
        cursor += duration
    return scenes


def build_script_blueprint(topic: str, angle: str, world: str, depth: int, humor: int) -> list[dict]:
    topic = topic.strip() or "the chosen subject"
    angle = angle.strip() or "the hidden contradiction at its center"
    lens = (
        "Use at least two outside intellectual lenses, but every comparison must earn its place and return to the source material."
        if depth >= 70
        else "Use one outside analogy only where it makes the lore clearer."
    )
    joke = (
        "Use recurring deadpan callbacks and one mundane-versus-apocalyptic contrast per major section."
        if humor >= 70
        else "Use occasional dry pressure-release lines after dense passages."
        if humor >= 30
        else "Keep humor nearly absent."
    )
    return [
        {"section": "Thesis Hook", "instruction": f"Open with a question or paradox about {topic}. Promise a specific new way to see it: {angle}."},
        {"section": "Minimum Necessary Lore", "instruction": "Orient newcomers without making veteran viewers sit through a wiki recital."},
        {"section": "Evidence Ladder", "instruction": "For each major claim: source fact → what it establishes → what remains uncertain → interpretation."},
        {"section": "Cross-Disciplinary Lens", "instruction": lens},
        {"section": "Counterweight", "instruction": "Give the strongest alternate reading, contradictory source, retcon, or ambiguity before resolving the thesis."},
        {"section": "Humor Control", "instruction": joke},
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
        promise = "Treat kingdoms, cults, monsters and wars like fragments from a dangerous medieval archive."
        visual = "charred parchment, candlelit maps, carved heraldry, mist, painted battle tableaux, ruined stone"
    else:
        promise = "Treat impossible future history like a recovered imperial archive: grand, analytical, ominous, occasionally very dry."
        visual = "cathedral-scale silhouettes, star maps, archive overlays, dark metal, dust, embers, restrained heraldic accents"
    return {
        "channel_promise": promise,
        "narrator": narrator,
        "visual_language": visual,
        "humor_rule": "Humor releases tension but never trivializes the central tragedy." if humor < 70 else "Deadpan absurdity is a recurring counter-rhythm to the epic stakes.",
        "depth_rule": "Every episode needs a thesis, a counterargument, and a clearly labeled interpretation layer." if depth >= 65 else "Every episode needs one clear thesis and a source-vs-interpretation distinction.",
    }
