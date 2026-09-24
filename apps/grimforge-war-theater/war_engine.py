from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import random
from typing import Dict, List

REFERENCE_URL = "https://youtu.be/XQ1jlW7hQrA?si=uSU_l2gwdhQopib4"
REFERENCE_EMBED = "https://www.youtube.com/embed/XQ1jlW7hQrA"

PRESETS: Dict[str, List[str]] = {
    "War Fantasy Flavor": [
        "Grim Siege", "Last Stand", "Imperial Conquest", "Savage Horde",
        "Holy Crusade", "Dark Sorcery War", "Monster Invasion",
        "Rebellion", "Frozen Campaign", "Desert War", "Custom",
    ],
    "Battle Type": [
        "Fortress Siege", "Open Field Battle", "Bridge Defense", "Ambush",
        "Naval Assault", "City Sack", "Mountain Pass", "Forest War",
        "Cavalry Charge", "Final Boss / Titan Battle", "Custom",
    ],
    "Story Structure": [
        "Heroic Last Stand", "Pyrrhic Victory", "Desperate Defense",
        "Betrayal Mid-Battle", "Reinforcements Arrive", "Catastrophic Defeat",
        "Commander Sacrifice", "Tactical Masterstroke", "Three-Act Epic",
        "Episodic Cliffhanger", "Custom",
    ],
    "Visual Scale": [
        "Intimate Warband", "Company / Battalion", "Army Scale",
        "Massive Continental War", "Mythic / Colossal", "Custom",
    ],
    "Cinematic Camera": [
        "Gritty Ground-Level", "Epic Wides + Hero Closeups",
        "Tactical / Readable Geography", "Handheld Chaos",
        "Slow Operatic", "Fast Trailer Energy", "Custom",
    ],
    "Narration": [
        "No Narrator", "Sparse Epic Narrator", "Battlefield Historian",
        "Soldier POV", "Commander Journal", "Dark Chronicle", "Custom",
    ],
    "Sound": [
        "Ambience-First", "Percussion War Score", "Dark Orchestral",
        "Sparse / Tense", "Choir + Brass", "Brutal Foley / Impacts", "Custom",
    ],
    "Runtime": [
        "60–90 sec teaser", "3 min short", "5 min episode",
        "8 min episode", "12 min episode", "15 min episode", "Custom",
    ],
    "Violence": [
        "Cinematic / restrained", "Intense but non-gory",
        "Battlefield aftermath emphasis",
    ],
}

FACTIONS = {
    "Ashen Crown": {
        "motif": "black iron crowns split by ember-red seams",
        "army": "oathbound infantry, smoke cavalry, siege saints",
        "rule": "heat drawn from buried battlefield relics",
        "commander": "stoic siege marshal",
        "palette": "charcoal, ember red, old gold",
    },
    "Ivory March": {
        "motif": "bone-white pennants marked with cobalt knots",
        "army": "pike walls, river knights, bell-bearing engineers",
        "rule": "warding geometry hammered into shields",
        "commander": "disciplined field architect",
        "palette": "ivory, cobalt, steel",
    },
    "Thorn Host": {
        "motif": "green-black antler sigils and copper thorns",
        "army": "forest levies, beast outriders, sapper covens",
        "rule": "living roots remember old roads",
        "commander": "vengeful pathfinder queen",
        "palette": "pine black, copper, moss",
    },
    "Storm Reliquary": {
        "motif": "silver shrine plates and violet storm glass",
        "army": "relic bearers, cliff archers, thunder wagons",
        "rule": "captured lightning stored in sainted metal",
        "commander": "reckless relic admiral",
        "palette": "silver, violet, storm blue",
    },
    "Cinder Republic": {
        "motif": "burnt-orange sun disks stamped into scavenged armor",
        "army": "citizen spears, demolition guilds, ash dragoons",
        "rule": "powder weapons fed by volcanic salts",
        "commander": "elected veteran tribune",
        "palette": "rust, soot, orange",
    },
    "Glass Covenant": {
        "motif": "translucent banners threaded with black wire",
        "army": "mirror lancers, shard priests, silent artillery",
        "rule": "refraction magic bends sight but not sound",
        "commander": "cold ceremonial tactician",
        "palette": "smoke glass, pearl, black",
    },
    "Iron Orchard": {
        "motif": "red fruit sigils hanging from chainwork standards",
        "army": "armored farmers, ox artillery, hedge knights",
        "rule": "war engines grown around living timber cores",
        "commander": "patient harvest general",
        "palette": "iron, bark brown, dark crimson",
    },
    "Moonless Choir": {
        "motif": "matte banners with concentric silver cuts",
        "army": "night infantry, echo riders, bell assassins",
        "rule": "sound can be stored, redirected, or erased",
        "commander": "whispering cantor-general",
        "palette": "ink black, silver, muted blue",
    },
}

REFERENCE_LENSES = {
    "Slow Siege Epic": {
        "scale": "Army-scale spectacle anchored by readable human stakes",
        "shot_rhythm": "Slow setup → compressed clash → long aftermath",
        "camera": "Disciplined geography; movement reserved for reversals",
        "narration": "Sparse, weighty narration at act turns only",
        "lighting": "Directional low light, smoke depth, warm fire accents",
        "sound": "Ambience and impacts carry scale; score enters selectively",
        "story": "Preparation → attrition → breach → sacrifice → aftermath",
    },
    "Ground-Level Chaos": {
        "scale": "Human-scale immediacy with glimpses of a larger war",
        "shot_rhythm": "Short reactive coverage broken by sudden wide holds",
        "camera": "Shoulder-height handheld, late reframes, short lenses",
        "narration": "Minimal narration; rely on dialogue and physical action",
        "lighting": "Dirty naturalism, fire flicker, obscured horizons",
        "sound": "Breath, armor, boots, nearby impacts; music sparse",
        "story": "Contact → confusion → local objective → escape or cost",
    },
    "Tactical War Chronicle": {
        "scale": "Readable formations, fronts, reserves, and objectives",
        "shot_rhythm": "Geography master → tactical insert → human reaction",
        "camera": "High masters, locked screen direction, deliberate lenses",
        "narration": "Historian voice clarifies why each move matters",
        "lighting": "Clear terrain separation and readable silhouettes",
        "sound": "Command calls, horns, formation noise, restrained score",
        "story": "Plan → contact → counter-plan → reversal → resolution",
    },
    "Operatic Mythic Battle": {
        "scale": "Mythic scale with colossal environmental stakes",
        "shot_rhythm": "Long tableaux punctuated by abrupt intimate closeups",
        "camera": "Crane-like moves, extreme wides, ceremonial symmetry",
        "narration": "Poetic but sparse",
        "lighting": "High contrast, volumetric shafts, supernatural accents",
        "sound": "Choir, low brass, vast reverberation, selective silence",
        "story": "Omen → gathering → revelation → impossible clash → legend",
    },
    "Fast Trailer Combat": {
        "scale": "Rapid alternation between army spectacle and hero beats",
        "shot_rhythm": "Fast escalation, short shots, repeated visual motifs",
        "camera": "Pushes, whip transitions, low tracking, aerial punctuation",
        "narration": "Short hook lines only",
        "lighting": "Bold separation and high-impact silhouettes",
        "sound": "Percussive hits, risers, hard mutes before reveals",
        "story": "Hook → escalation → reveal → bigger reveal → cliffhanger",
    },
    "Custom": {
        "scale": "", "shot_rhythm": "", "camera": "", "narration": "",
        "lighting": "", "sound": "", "story": "",
    },
}

RUNTIME_SECONDS = {
    "60–90 sec teaser": 80,
    "3 min short": 180,
    "5 min episode": 300,
    "8 min episode": 480,
    "12 min episode": 720,
    "15 min episode": 900,
}

# Original performance profiles only. These describe broad narration qualities
# and are not intended to clone or impersonate any identifiable narrator.
TTS_ENGINES = {
    "Kokoro": {
        "status": "planned",
        "role": "HQ local/default",
        "runtime": "Browser-local or local Python worker",
        "license": "Apache-2.0",
        "notes": "Preferred high-quality local narrator engine; no voice cloning required.",
    },
    "KittenTTS": {
        "status": "planned",
        "role": "Lightweight CPU fallback",
        "runtime": "Local Python worker",
        "license": "Apache-2.0",
        "notes": "Small CPU-friendly fallback for low-resource machines.",
    },
    "MeloTTS": {
        "status": "planned",
        "role": "Multilingual narrator",
        "runtime": "Local Python worker",
        "license": "MIT",
        "notes": "Useful for multilingual narration and accent coverage.",
    },
    "Piper": {
        "status": "planned",
        "role": "Offline reliability fallback",
        "runtime": "Local Python/ONNX worker",
        "license": "GPL-3.0-or-later engine; voice licenses vary",
        "notes": "Fast offline fallback; each selected voice model needs its own license check.",
    },
    "Browser Speech": {
        "status": "connected",
        "role": "Instant preview fallback",
        "runtime": "Browser SpeechSynthesis",
        "license": "Browser/platform provided",
        "notes": "Current working preview path; voice availability varies by device.",
    },
}

NARRATOR_VOICE_PROFILES = {
    "Grim Chronicle": {
        "description": "Deep, mature, resonant war-story narration with deliberate pacing, restrained intensity, and weighty pauses.",
        "rate": 0.86,
        "pitch": 0.76,
        "volume": 1.0,
        "preferred_names": ["Daniel", "Brian", "George", "Bill", "David", "James", "Arthur", "Mark"],
        "preferred_langs": ["en-GB", "en-US", "en-AU"],
    },
    "Battlefield Historian": {
        "description": "Steady, authoritative chronicle delivery: clear geography, measured cadence, controlled emotion.",
        "rate": 0.91,
        "pitch": 0.84,
        "volume": 1.0,
        "preferred_names": ["Daniel", "George", "Brian", "Arthur", "David"],
        "preferred_langs": ["en-GB", "en-US"],
    },
    "War-Weary Commander": {
        "description": "Low, tired authority with shorter phrases, heavier pauses, and restrained urgency.",
        "rate": 0.82,
        "pitch": 0.70,
        "volume": 1.0,
        "preferred_names": ["Brian", "Bill", "David", "Mark", "Daniel"],
        "preferred_langs": ["en-US", "en-GB", "en-AU"],
    },
    "Ancient Chronicler": {
        "description": "Slow, grave storyteller delivery for mythic battles, omens, sacrifice, and aftermath.",
        "rate": 0.78,
        "pitch": 0.68,
        "volume": 0.98,
        "preferred_names": ["George", "Bill", "Arthur", "Daniel", "David"],
        "preferred_langs": ["en-GB", "en-US"],
    },
    "Neutral Storyteller": {
        "description": "Natural, warm narrative delivery for longer episodes with less theatrical weight.",
        "rate": 0.96,
        "pitch": 0.90,
        "volume": 1.0,
        "preferred_names": ["George", "Brian", "Daniel", "Alex", "David"],
        "preferred_langs": ["en-US", "en-GB", "en-AU"],
    },
}


@dataclass
class Scene:
    id: str
    act: str
    title: str
    duration: int
    intensity: int
    narration: str
    dialogue: str
    visual: str
    camera: str
    sound: str
    continuity: str
    palette: str


@dataclass
class Episode:
    title: str
    logline: str
    synopsis: str
    runtime_seconds: int
    presets: Dict[str, str]
    faction: str
    enemy: str
    commander: str
    objective: str
    scenes: List[Scene]

    def to_dict(self) -> dict:
        return asdict(self)


def stable_rng(*parts: str) -> random.Random:
    digest = sha256("|".join(parts).encode("utf-8")).hexdigest()
    return random.Random(int(digest[:16], 16))


def runtime_seconds(runtime_label: str, custom_minutes: int = 12) -> int:
    return RUNTIME_SECONDS.get(runtime_label, max(60, custom_minutes * 60))


def random_presets(seed_text: str = "") -> Dict[str, str]:
    rng = stable_rng(seed_text or "grimforge-surprise")
    result = {}
    for group, options in PRESETS.items():
        eligible = [x for x in options if x != "Custom"]
        result[group] = rng.choice(eligible)
    return result


def make_episode(
    title: str,
    presets: Dict[str, str],
    faction: str,
    enemy: str,
    commander: str,
    objective: str,
    custom_minutes: int = 12,
    scene_count: int = 8,
) -> Episode:
    rng = stable_rng(title, faction, enemy, commander, objective, *presets.values())
    total = runtime_seconds(presets.get("Runtime", "12 min episode"), custom_minutes)
    scene_count = max(5, min(14, int(scene_count)))
    faction_data = FACTIONS[faction]
    structure = presets.get("Story Structure", "Three-Act Epic")
    battle = presets.get("Battle Type", "Fortress Siege")
    camera = presets.get("Cinematic Camera", "Epic Wides + Hero Closeups")
    sound = presets.get("Sound", "Dark Orchestral")
    narration_mode = presets.get("Narration", "Sparse Epic Narrator")
    scale = presets.get("Visual Scale", "Army Scale")
    flavor = presets.get("War Fantasy Flavor", "Grim Siege")

    beats = [
        ("Act I", "The Oath", 24, "The battlefield is established and the cost of failure becomes personal."),
        ("Act I", "The Enemy Horizon", 38, "The opposing force arrives in a way that makes the scale legible."),
        ("Act I", "First Contact", 58, "The first tactical test reveals what each side can really do."),
        ("Act II", "The Plan Works", 66, "The defenders gain a temporary advantage and confidence rises."),
        ("Act II", "The Reversal", 84, "A hidden threat, failed assumption, or betrayal changes the map."),
        ("Act II", "The Cost", 88, "A hero unit, district, or formation pays for the reversal."),
        ("Act III", "The Final Push", 96, "The commander commits the last reserve to a decisive action."),
        ("Act III", "Aftermath", 32, "The result is visible in terrain, survivors, and the next threat."),
    ]
    while len(beats) < scene_count:
        insert_at = max(2, len(beats) - 2)
        beats.insert(insert_at, ("Act II", f"Escalation {len(beats)-6}", rng.randint(65, 90), "A new battlefield complication raises pressure without resetting continuity."))
    beats = beats[:scene_count]

    weights = [1.0 + (0.25 if "Reversal" in b[1] or "Final" in b[1] else 0) for b in beats]
    weight_sum = sum(weights)
    durations = [max(8, round(total * w / weight_sum)) for w in weights]
    drift = total - sum(durations)
    durations[-1] += drift

    scenes: List[Scene] = []
    for i, ((act, beat_title, intensity, purpose), duration) in enumerate(zip(beats, durations), start=1):
        direction = "left-to-right" if i % 2 else "right-to-left"
        if beat_title == "The Reversal":
            direction = "axis deliberately broken, then re-established"
        narration = ""
        if narration_mode != "No Narrator":
            narration = (
                f"{beat_title}. {commander} learns that {objective.lower()} "
                f"will demand more than the {faction} expected."
            )
        dialogue = ""
        if i in {1, 5, 7}:
            dialogue = rng.choice([
                "Hold until the signal. Then make them pay for every step.",
                "The map is wrong. They are already inside the lower ward.",
                "No reserve remains. Good. Then no one is waiting behind us.",
                "If the gate falls, the city becomes the battlefield.",
            ])
        visual = (
            f"{flavor}; {battle}; {scale}. {purpose} "
            f"Original {faction} forces face {enemy}. Motif: {faction_data['motif']}."
        )
        cam = (
            f"{camera}; scene {i}; {direction}; "
            + ("extreme wide geography anchor" if i in {1, 5, scene_count} else "medium battlefield coverage with reaction closeups")
        )
        snd = (
            f"{sound}; foreground armor/boots/impacts; "
            + ("brief pre-impact silence before the turn" if intensity >= 80 else "ambience under restrained score")
        )
        continuity = (
            f"Maintain {faction_data['palette']} palette, heraldry, commander wardrobe, "
            f"terrain damage, army positions, injury state, and accumulated wall damage from prior scenes."
        )
        scenes.append(
            Scene(
                id=f"S{i:02d}",
                act=act,
                title=beat_title,
                duration=duration,
                intensity=intensity,
                narration=narration,
                dialogue=dialogue,
                visual=visual,
                camera=cam,
                sound=snd,
                continuity=continuity,
                palette=faction_data["palette"],
            )
        )

    ending = {
        "Heroic Last Stand": "The field is lost, but the objective survives because someone stayed.",
        "Pyrrhic Victory": "The objective is achieved at a cost that makes victory feel like another form of defeat.",
        "Catastrophic Defeat": "The defenders fail, but the collapse reveals the shape of the wider war.",
        "Episodic Cliffhanger": "The immediate battle resolves just as a larger threat enters the campaign.",
    }.get(structure, "The battle resolves tactically while leaving a larger campaign consequence behind.")

    return Episode(
        title=title,
        logline=f"{commander} leads the {faction} against {enemy}: {objective}",
        synopsis=(
            f"An original {presets.get('War Fantasy Flavor','war fantasy').lower()} story built around "
            f"{presets.get('Battle Type','battle').lower()} and {structure.lower()}. {ending}"
        ),
        runtime_seconds=total,
        presets=dict(presets),
        faction=faction,
        enemy=enemy,
        commander=commander,
        objective=objective,
        scenes=scenes,
    )


def veyr_advice(action: str, episode: Episode | None, pro: bool = False) -> str:
    if not episode:
        return "Forge or load an episode first so I can read the current battle structure."
    scenes = episode.scenes
    weakest = min(scenes, key=lambda s: s.intensity)
    peak = max(scenes, key=lambda s: s.intensity)
    if action == "Improve battle pacing":
        return (
            f"{'Technical pass: ' if pro else ''}Trim **{weakest.title}** and give **{peak.title}** more room. "
            "Avoid two high-intensity scenes back-to-back without a reaction or geography reset."
        )
    if action == "Strengthen the opening hook":
        return (
            f"Open on a 5–8 second fragment of **{peak.title}**, then cut back to **{scenes[0].title}**. "
            "That gives the episode a promise before the setup."
        )
    if action == "Make this feel larger scale":
        return (
            "Add an extreme-wide geography anchor at every act change, with a tiny foreground human reference. "
            "Scale reads best when the audience can compare army size to something familiar."
        )
    if action == "Clarify battlefield geography":
        return (
            "Lock one screen direction for the faction, re-establish the map after every reversal, "
            "and never cut across the axis without a visible reason."
        )
    if action == "Fix continuity":
        return (
            "Check heraldry, palette, commander wardrobe, wall damage, injuries, time of day, "
            "and army positions. Damage should accumulate; nothing resets between scenes."
        )
    if action == "Improve commander arc":
        return (
            "Give the commander one decision in Act I, one mistaken assumption in Act II, "
            "and one costly choice in Act III. Keep those moments visually distinct from general battle coverage."
        )
    if action == "Strengthen sound design":
        return (
            "Reserve full score for turns. Let boots, armor, wind, distant horns, and impact Foley carry the scale. "
            "Use a short near-silence before the largest hit."
        )
    if action == "Add a tactical reversal":
        return (
            "Introduce a second threat on the opposite axis at the midpoint, then immediately restore geography "
            "with a high master shot so the audience understands why the plan failed."
        )
    if action == "Diagnose weak scene":
        return f"**{weakest.title}** is the softest beat. Give it a visible complication, irreversible cost, or merge it into the next scene."
    if action == "Prepare final QC":
        return (
            "QC: rights basis, readable geography, continuity locks, final take per scene, caption fit, "
            "audio clipping, black frames, loudness, and clear distinction between animatic and final render."
        )
    if action == "What is missing for final episode":
        return (
            "The Streamlit build can create the episode structure and playable animatic now. "
            "A true full-motion MP4 still needs connected video/TTS/audio/render providers or a local render worker."
        )
    return "I can help with pacing, scale, geography, continuity, commander arc, sound, tactical reversals, weak-scene diagnosis, or final QC."
