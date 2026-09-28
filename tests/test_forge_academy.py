from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from forge_core.academy import (
    AcademyStore,
    build_question,
    learning_gain,
    remediation_plan,
    score_question,
)


LESSONS = [
    {"id": "1", "failure": "cloud endpoint is used", "fix": "block non-local endpoints"},
    {"id": "2", "failure": "model runs out of VRAM", "fix": "choose a smaller admitted model"},
    {"id": "3", "failure": "duplicate evidence files", "fix": "reference one Vault source"},
    {"id": "4", "failure": "render service missing", "fix": "use deterministic FFmpeg fallback"},
]


class ForgeAcademyTests(unittest.TestCase):
    def test_question_has_one_correct_repair(self):
        q = build_question(LESSONS[0], LESSONS)
        self.assertEqual(len(q.options), 4)
        self.assertTrue(score_question(q, q.answer_index))
        wrong = (q.answer_index + 1) % 4
        self.assertFalse(score_question(q, wrong))

    def test_remediation_returns_only_wrong_or_missing_lessons(self):
        qs = [build_question(x, LESSONS) for x in LESSONS[:2]]
        selected = {
            qs[0].question_id: qs[0].answer_index,
            qs[1].question_id: (qs[1].answer_index + 1) % 4,
        }
        plan = remediation_plan(qs, selected)
        self.assertEqual([x["lesson_id"] for x in plan], ["2"])

    def test_learning_gain_is_measurable(self):
        gain = learning_gain(1, 3, 4)
        self.assertEqual(gain["pre_percent"], 25.0)
        self.assertEqual(gain["post_percent"], 75.0)
        self.assertGreater(gain["normalized_gain"], 0)

    def test_store_tracks_pre_and_post(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AcademyStore(Path(directory) / "academy.sqlite3")
            try:
                store.record("s1", lesson_id="1", phase="pre", correct=False, selected_index=0, answer_index=1)
                store.record("s1", lesson_id="1", phase="post", correct=True, selected_index=1, answer_index=1)
                summary = store.summary("s1")
                self.assertEqual(summary["phases"]["pre"]["correct"], 0)
                self.assertEqual(summary["phases"]["post"]["correct"], 1)
                self.assertGreater(summary["learning_gain"]["raw_gain"], 0)
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
