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

PROJECT_SCHEMA_VERSION = 1

FULL_EPISODE_PROFILES = {
    "Economy": {
        "shots_per_scene": 2,
        "clip_seconds": 5,
        "description": "Lean full-episode pass for free/limited GPU quotas. One geography/master shot plus one story/character shot per scene.",
    },
    "Cinematic": {
        "shots_per_scene": 3,
        "clip_seconds": 6,
        "description": "Balanced default: master geography, action/coverage, and character/detail coverage for every scene.",
    },
    "Epic": {
        "shots_per_scene": 4,
        "clip_seconds": 7,
        "description": "Dense coverage for larger battles: geography, action, character, and detail/reaction shots per scene.",
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
GPU_BACKENDS = {
    "Hugging Face ZeroGPU": {
        "status": "available_external",
        "connection": "Gradio API / Space endpoint",
        "cost": "Free daily quota",
        "hardware": "Dynamic RTX Pro 6000 Blackwell, 48 GB or 96 GB VRAM",
        "best_for": "Short test renders, API-callable GrimForge worker, demos",
        "notes": "Best free backend for direct app integration. Free account quota is limited and resets daily.",
    },
    "Kaggle T4x2": {
        "status": "available_external",
        "connection": "Notebook worker / exported render job",
        "cost": "Free weekly GPU quota",
        "hardware": "2× NVIDIA T4, 16 GB VRAM each",
        "best_for": "CogVideoX, optimized Wan/LTX tests, longer free batch jobs",
        "notes": "Useful free compute, but not reliable as a permanent web API. Treat it as a manual or semi-automated render worker.",
    },
    "Google Colab Free": {
        "status": "available_external",
        "connection": "Notebook worker / exported render job",
        "cost": "Free, dynamically limited",
        "hardware": "GPU type varies by availability",
        "best_for": "Testing notebooks and one-off renders",
        "notes": "Free GPU access is not guaranteed and limits vary. Do not treat this as an always-on production backend.",
    },
    "Lightning AI Free": {
        "status": "available_external",
        "connection": "Studio/job worker",
        "cost": "Free starter credits; then paid",
        "hardware": "T4/L4/L40S/A100 and others depending credits",
        "best_for": "More stable GPU experiments and temporary workers",
        "notes": "Free plan can include promotional GPU credits. Treat free GPU time as finite starter capacity, not unlimited hosting.",
    },
}

VIDEO_ENGINES = {
    "LTX-2": {
        "status": "planned",
        "role": "Flagship cinematic / audio-video",
        "modes": "Text-to-video, image-to-video, multi-keyframe, extension, audio+video",
        "runtime": "GPU worker / ComfyUI",
        "license": "LTX Community License",
        "notes": "Primary high-end option; strongest fit for cinematic sequence work and synchronized audio/video experiments.",
    },
    "Wan 2.2": {
        "status": "planned",
        "role": "Reference-driven battle shots",
        "modes": "T2V, I2V, TI2V, speech-to-video, animation",
        "runtime": "GPU worker / ComfyUI / Diffusers",
        "license": "Apache-2.0",
        "notes": "Strong choice for image-conditioned shots, character animation, and 720p battle generation.",
    },
    "Mochi 1": {
        "status": "planned",
        "role": "Open cinematic fallback",
        "modes": "Text-to-video",
        "runtime": "GPU worker / ComfyUI",
        "license": "Apache-2.0",
        "notes": "Permissive open option with strong motion and prompt adherence; useful as a dependable alternate renderer.",
    },
    "CogVideoX-2B": {
        "status": "planned",
        "role": "Lighter open fallback",
        "modes": "Text-to-video",
        "runtime": "GPU worker / Diffusers",
        "license": "Apache-2.0",
        "notes": "Smaller fallback model for lower-cost experimentation and simpler deployment than the largest generators.",
    },
}

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


def episode_from_dict(data: dict) -> Episode:
    """Rehydrate an Episode exported by GrimForge."""
    scenes = [Scene(**scene) for scene in data.get("scenes", [])]
    return Episode(
        title=data["title"],
        logline=data.get("logline", ""),
        synopsis=data.get("synopsis", ""),
        runtime_seconds=int(data.get("runtime_seconds", sum(s.duration for s in scenes))),
        presets=dict(data.get("presets", {})),
        faction=data.get("faction", "Ashen Crown"),
        enemy=data.get("enemy", ""),
        commander=data.get("commander", ""),
        objective=data.get("objective", ""),
        scenes=scenes,
    )


def render_route_advice(video_engine: str, gpu_backend: str) -> dict:
    """Heuristic routing guidance only; this is not live hardware detection."""
    matrix = {
        "LTX-2": {
            "Hugging Face ZeroGPU": ("preferred", "High-VRAM burst compute is the cleanest free-app integration target."),
            "Lightning AI Free": ("good", "Flexible GPU workers are a strong fit when credits are available."),
            "Google Colab Free": ("experimental", "Can work for optimized notebook runs, but GPU type and session lifetime vary."),
            "Kaggle T4x2": ("experimental", "Useful for experiments, but dual T4 memory is less convenient for heavier LTX workflows."),
        },
        "Wan 2.2": {
            "Hugging Face ZeroGPU": ("preferred", "Good target for short API-style test renders with dynamic high-VRAM allocation."),
            "Lightning AI Free": ("good", "Flexible worker hardware makes this a practical cloud route."),
            "Kaggle T4x2": ("experimental", "Good for optimized notebook tests; treat as batch compute rather than a permanent API."),
            "Google Colab Free": ("experimental", "Useful for one-off optimized runs when a suitable GPU is assigned."),
        },
        "Mochi 1": {
            "Hugging Face ZeroGPU": ("preferred", "The high-VRAM pool is the safest free target for this heavier model."),
            "Lightning AI Free": ("good", "A larger temporary GPU can work when credits and hardware are available."),
            "Kaggle T4x2": ("not_recommended", "Native Mochi workloads are heavy for this backend; use only with aggressive optimization."),
            "Google Colab Free": ("not_recommended", "Free Colab hardware is too variable for a dependable Mochi route."),
        },
        "CogVideoX-2B": {
            "Kaggle T4x2": ("preferred", "The lighter model is a strong match for free T4-class experimentation."),
            "Google Colab Free": ("good", "A useful economy route when a GPU is available."),
            "Hugging Face ZeroGPU": ("good", "Works as a burst API-style option, though the GPU is more capable than this model needs."),
            "Lightning AI Free": ("good", "Straightforward worker target when starter credits are available."),
        },
    }
    rating, reason = matrix.get(video_engine, {}).get(
        gpu_backend, ("experimental", "No GrimForge routing rule exists for this combination yet.")
    )
    labels = {
        "preferred": "Preferred route",
        "good": "Good route",
        "experimental": "Experimental route",
        "not_recommended": "Not recommended",
    }
    return {"rating": rating, "label": labels[rating], "reason": reason}


def build_render_manifest(
    episode: Episode,
    *,
    video_engine: str,
    gpu_backend: str,
    tts_engine: str,
    narrator_voice: str,
    reference_url: str = "",
) -> dict:
    """Create a portable planned render job without claiming that rendering occurred."""
    route = render_route_advice(video_engine, gpu_backend)
    scenes = []
    for scene in episode.scenes:
        target_clip_seconds = 8 if scene.intensity >= 80 else 6
        prompt = (
            f"{scene.visual} Camera: {scene.camera}. "
            f"Sound intent: {scene.sound}. Continuity: {scene.continuity}"
        )
        scenes.append({
            "scene_id": scene.id,
            "act": scene.act,
            "title": scene.title,
            "story_duration_seconds": scene.duration,
            "target_clip_seconds": target_clip_seconds,
            "intensity": scene.intensity,
            "prompt": prompt,
            "narration": scene.narration,
            "dialogue": scene.dialogue,
            "status": "planned",
            "take_status": "unrendered",
        })

    digest = sha256(
        f"{episode.title}|{video_engine}|{gpu_backend}|{tts_engine}|{narrator_voice}".encode("utf-8")
    ).hexdigest()[:12]
    return {
        "schema_version": PROJECT_SCHEMA_VERSION,
        "job_id": f"gf-{digest}",
        "app": "GrimForge War Theater",
        "title": episode.title,
        "stage": "planned",
        "honesty": "This manifest is a render plan. It does not mean video, audio, or a final MP4 has been rendered.",
        "providers": {
            "video_engine": video_engine,
            "gpu_backend": gpu_backend,
            "tts_engine": tts_engine,
            "narrator_voice": narrator_voice,
        },
        "route_guidance": route,
        "reference_url": reference_url,
        "episode": episode.to_dict(),
        "scenes": scenes,
    }


def build_full_episode_manifest(
    episode: Episode,
    *,
    profile_name: str,
    video_engine: str,
    gpu_backend: str,
    tts_engine: str,
    narrator_voice: str,
    reference_url: str = "",
) -> dict:
    """Create a multi-shot whole-episode production manifest."""
    profile = FULL_EPISODE_PROFILES.get(profile_name, FULL_EPISODE_PROFILES["Cinematic"])
    shot_roles = [
        ("MASTER", "establish readable geography and faction positions"),
        ("ACTION", "show the scene's tactical action with clear screen direction"),
        ("CHARACTER", "show commander/hero reaction or decision with identity continuity"),
        ("DETAIL", "show a prop, damage state, weapon, terrain consequence, or atmospheric insert"),
    ]
    scenes = []
    all_shots = []
    for scene in episode.scenes:
        scene_shots = []
        for idx in range(profile["shots_per_scene"]):
            code, purpose = shot_roles[idx]
            seconds = profile["clip_seconds"]
            if code == "MASTER":
                camera = "extreme wide or wide master; readable geography; stable axis"
            elif code == "ACTION":
                camera = "medium/wide kinetic coverage; preserve screen direction and battlefield logic"
            elif code == "CHARACTER":
                camera = "medium close-up or close-up; preserve face, wardrobe, heraldry, injury state"
            else:
                camera = "detail insert; continuity-bearing object or environmental consequence"
            prompt = (
                f"{scene.visual} Shot role: {code}. Purpose: {purpose}. "
                f"Camera: {camera}. Scene camera intent: {scene.camera}. "
                f"Continuity locks: {scene.continuity}. Palette: {scene.palette}. "
                "Create an original war-fantasy shot; do not reproduce characters, logos, dialogue, or protected visual assets from a reference."
            )
            shot = {
                "shot_id": f"{scene.id}-{code}-{idx+1:02d}",
                "scene_id": scene.id,
                "role": code,
                "purpose": purpose,
                "target_seconds": seconds,
                "prompt": prompt,
                "continuity": scene.continuity,
                "status": "planned",
                "take_status": "unrendered",
            }
            scene_shots.append(shot)
            all_shots.append(shot)
        scenes.append({
            "scene_id": scene.id,
            "title": scene.title,
            "act": scene.act,
            "story_duration_seconds": scene.duration,
            "narration": scene.narration,
            "dialogue": scene.dialogue,
            "sound": scene.sound,
            "shots": scene_shots,
        })

    base = build_render_manifest(
        episode,
        video_engine=video_engine,
        gpu_backend=gpu_backend,
        tts_engine=tts_engine,
        narrator_voice=narrator_voice,
        reference_url=reference_url,
    )
    base["production_mode"] = "full_episode"
    base["profile"] = profile_name
    base["profile_description"] = profile["description"]
    base["scene_manifests"] = scenes
    base["shots"] = all_shots
    base["shot_count"] = len(all_shots)
    base["planned_generated_footage_seconds"] = sum(s["target_seconds"] for s in all_shots)
    base["assembly"] = {
        "video": "Select/trim best takes; preserve scene order and continuity; assemble with FFmpeg or equivalent.",
        "narration": "Generate narration per scene, align to picture, and duck music beneath speech.",
        "sound": "Layer dialogue/narration, Foley, impacts, ambience, room tone, and music.",
        "captions": "Generate after picture lock; validate fit and safe margins.",
        "qc": [
            "rights basis known",
            "no missing/black shots",
            "identity and wardrobe continuity",
            "battlefield geography readable",
            "screen direction intentional",
            "audio not clipped",
            "target loudness met",
            "caption overflow clear",
        ],
    }
    return base


def benchmark_scorecard(episode: Episode | None, profile_name: str = "Cinematic") -> dict:
    """Transparent planning scorecard, not an aesthetic quality judgment."""
    if not episode:
        return {
            "overall": 0,
            "narrative_coverage": 0,
            "continuity_planning": 0,
            "geography_planning": 0,
            "audio_planning": 0,
            "shot_variety": 0,
            "notes": ["Forge or load an episode first."],
        }
    profile = FULL_EPISODE_PROFILES.get(profile_name, FULL_EPISODE_PROFILES["Cinematic"])
    narrative = min(100, 55 + len(episode.scenes) * 4)
    continuity = 95 if all(s.continuity for s in episode.scenes) else 60
    geography = 92 if all("direction" in s.camera or "geography" in s.camera for s in episode.scenes) else 75
    audio = 90 if all(s.sound for s in episode.scenes) else 65
    variety = {2: 72, 3: 90, 4: 96}.get(profile["shots_per_scene"], 80)
    overall = round((narrative + continuity + geography + audio + variety) / 5)
    notes = [
        "This score measures production-plan completeness, not whether generated footage will look better than a reference.",
        "Actual visual quality still depends on the connected video model, reference conditioning, take selection, and final edit.",
    ]
    return {
        "overall": overall,
        "narrative_coverage": narrative,
        "continuity_planning": continuity,
        "geography_planning": geography,
        "audio_planning": audio,
        "shot_variety": variety,
        "notes": notes,
    }
