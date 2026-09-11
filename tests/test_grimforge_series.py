from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
GRIMFORGE = ROOT / "portfolio" / "grimforge-studio"
sys.path.insert(0, str(GRIMFORGE))

from series_engine import VOICE_TRIALS, build_series_plan, rank_voice_trials


class GrimForgeSeriesTests(unittest.TestCase):
    def test_default_series_has_ten_five_minute_parts(self):
        plan = build_series_plan(duration_minutes=5)
        self.assertEqual(len(plan), 10)
        self.assertTrue(all(ep.duration_minutes == 5 for ep in plan))
        self.assertEqual(plan[0].number, 1)
        self.assertEqual(plan[-1].number, 10)

    def test_first_six_episodes_use_distinct_voice_trials(self):
        plan = build_series_plan(duration_minutes=5)
        voices = [ep.voice for ep in plan[:6]]
        self.assertEqual(len(set(voices)), 6)
        self.assertEqual(voices, [row["voice"] for row in VOICE_TRIALS])

    def test_voice_ranking_orders_by_weighted_score(self):
        trials = [
            {"episode": 1, "voice": "A", "scores": {"clarity": 10, "gravitas": 10, "warmth": 10, "pacing": 10, "humor_delivery": 10, "listener_fatigue": 10, "intelligibility": 10, "world_fit": 10}},
            {"episode": 2, "voice": "B", "scores": {"clarity": 5, "gravitas": 5, "warmth": 5, "pacing": 5, "humor_delivery": 5, "listener_fatigue": 5, "intelligibility": 5, "world_fit": 5}},
        ]
        ranked = rank_voice_trials(trials)
        self.assertEqual(ranked[0]["voice"], "A")
        self.assertGreater(ranked[0]["weighted_score"], ranked[1]["weighted_score"])


if __name__ == "__main__":
    unittest.main()
