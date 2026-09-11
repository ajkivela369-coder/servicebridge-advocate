from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable

VOICE_TRIALS = [
    {
        "episode": 1,
        "voice": "Young Imperial Historian",
        "direction": "Low-mid register, early-30s character, measured authority, clean diction, restrained warmth.",
    },
    {
        "episode": 2,
        "voice": "Battle Chronicler",
        "direction": "Mid-low, disciplined momentum, stronger consonants, slightly more martial energy without shouting.",
    },
    {
        "episode": 3,
        "voice": "Old World Scholar",
        "direction": "Bookish, dry, faintly theatrical, deliberate pacing; humor lands as understated amusement.",
    },
    {
        "episode": 4,
        "voice": "Archive Commander",
        "direction": "Broadcast-clean baritone, concise phrasing, institutional confidence, cool neutrality on disputed lore.",
    },
    {
        "episode": 5,
        "voice": "Field Remembrancer",
        "direction": "War correspondent energy, human warmth, vivid pacing, reflective rather than bombastic.",
    },
    {
        "episode": 6,
        "voice": "Nocturne Curator",
        "direction": "Younger dark-academic voice, intimate resonance, precise pauses, excellent for mystery and horror.",
    },
]

VOICE_SCORE_FIELDS = [
    "clarity",
    "gravitas",
    "warmth",
    "pacing",
    "humor_delivery",
    "listener_fatigue",
    "intelligibility",
    "world_fit",
]

SERIES_DEFAULT = {
    "title": "The Imperium Cannot Win",
    "world": "Grimdark Galaxy",
    "premise": "A ten-part examination of how a civilization can survive for millennia while repeatedly reproducing the conditions of its own crises.",
    "parts": [
        ("The Machine That Survives", "Why survival and victory are not the same thing."),
        ("The Price of Emergency", "How emergency institutions become permanent structures."),
        ("The Bureaucracy of Apocalypse", "Why impossible scale creates absurd, dangerous administration."),
        ("Faith as Infrastructure", "How belief becomes governance, logistics, identity and weapon."),
        ("The Enemy Inside the System", "Why the system's defenses can deepen the conditions they fight."),
        ("War Without End", "How permanent conflict reshapes institutions, culture and incentives."),
        ("The Human Cost", "What the grand strategy looks like from one ordinary life."),
        ("Why Reform Fails", "Why even intelligent reformers collide with structure, scale and legitimacy."),
        ("Could It Be Different?", "The strongest counterargument: where adaptation and reform really do work."),
        ("Victory Is the Wrong Question", "Return to the opening thesis and redefine what survival means."),
    ],
}


@dataclass
class EpisodePlan:
    number: int
    title: str
    thesis: str
    duration_minutes: int
    voice: str
    hook: str
    payoff: str
    next_part_bridge: str
    visual_motif: str
    status: str = "planned"

    def to_dict(self) -> dict:
        return asdict(self)


def build_series_plan(
    series_title: str = SERIES_DEFAULT["title"],
    premise: str = SERIES_DEFAULT["premise"],
    world: str = SERIES_DEFAULT["world"],
    duration_minutes: int = 5,
) -> list[EpisodePlan]:
    episodes: list[EpisodePlan] = []
    parts = SERIES_DEFAULT["parts"]
    for index, (part_title, thesis) in enumerate(parts, 1):
        voice = next((v["voice"] for v in VOICE_TRIALS if v["episode"] == index), "Voice Tournament Winner")
        hook = (
            f"Open with one contradiction that makes {part_title.lower()} feel personally urgent, then state the episode question within 20 seconds."
        )
        payoff = f"Answer only this part's question: {thesis} Do not resolve the whole series early."
        bridge = (
            f"End by revealing the problem that Part {index + 1} must explain: {parts[index][1]}"
            if index < len(parts)
            else "Close the loop on Part 1 and leave one larger unresolved implication for a future series."
        )
        motifs = [
            "cathedral-scale machine / archive glyph",
            "red emergency seal becoming permanent architecture",
            "endless forms, ledgers and star-map routing lines",
            "candlelight becoming data-light / ritual becoming system",
            "mirror imagery and defensive walls closing inward",
            "campaign map with fronts that never disappear",
            "single human silhouette against impossible scale",
            "cracked blueprint / reform plan colliding with old masonry",
            "split-screen success and failure cases",
            "returning archive seal, now reinterpreted",
        ]
        episodes.append(
            EpisodePlan(
                number=index,
                title=f"Part {index}: {part_title}",
                thesis=thesis,
                duration_minutes=duration_minutes,
                voice=voice,
                hook=hook,
                payoff=payoff,
                next_part_bridge=bridge,
                visual_motif=motifs[index - 1],
            )
        )
    return episodes


def score_voice(scores: dict[str, float]) -> dict:
    normalized = {field: float(scores.get(field, 0)) for field in VOICE_SCORE_FIELDS}
    # Listener fatigue is scored as 'low fatigue quality': 10 = easy to listen to, 0 = tiring.
    weights = {
        "clarity": 0.16,
        "gravitas": 0.14,
        "warmth": 0.08,
        "pacing": 0.14,
        "humor_delivery": 0.10,
        "listener_fatigue": 0.14,
        "intelligibility": 0.16,
        "world_fit": 0.08,
    }
    weighted = sum(normalized[k] * weights[k] for k in weights)
    return {
        "scores": normalized,
        "weighted_score": round(weighted, 2),
        "max_score": 10.0,
    }


def rank_voice_trials(trials: Iterable[dict]) -> list[dict]:
    ranked = []
    for trial in trials:
        result = score_voice(trial.get("scores", {}))
        ranked.append({**trial, **result})
    return sorted(ranked, key=lambda row: row["weighted_score"], reverse=True)
