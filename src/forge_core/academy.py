from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import time
from typing import Any, Sequence


@dataclass(frozen=True)
class AcademyQuestion:
    question_id: str
    lesson_id: str
    prompt: str
    options: tuple[str, ...]
    answer_index: int
    explanation: str

    def public_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("answer_index", None)
        return data


@dataclass(frozen=True)
class AcademyAttempt:
    lesson_id: str
    phase: str
    correct: bool
    selected_index: int
    answer_index: int
    created_at: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_question(
    lesson: dict[str, Any],
    lessons: Sequence[dict[str, Any]],
) -> AcademyQuestion:
    lesson_id = str(lesson["id"])
    correct = str(lesson["fix"])
    decoys = [
        str(item["fix"])
        for item in lessons
        if str(item.get("id")) != lesson_id and str(item.get("fix", "")).strip()
    ][:3]
    while len(decoys) < 3:
        decoys.append("Skip the failure and continue without changing the system.")

    options = [correct] + decoys
    digest = sha256(lesson_id.encode("utf-8")).digest()
    shift = digest[0] % len(options)
    options = options[shift:] + options[:shift]
    answer_index = options.index(correct)
    return AcademyQuestion(
        question_id=f"forge-{lesson_id}-repair",
        lesson_id=lesson_id,
        prompt=(
            "The system shows this failure:\n\n"
            + str(lesson["failure"])
            + "\n\nWhich response best matches the architecture?"
        ),
        options=tuple(options),
        answer_index=answer_index,
        explanation=str(lesson["fix"]),
    )


def score_question(question: AcademyQuestion, selected_index: int) -> bool:
    return int(selected_index) == int(question.answer_index)


def learning_gain(pre_correct: int, post_correct: int, total: int) -> dict[str, float]:
    total = max(1, int(total))
    raw = float(post_correct - pre_correct)
    possible = max(1, total - int(pre_correct))
    normalized = raw / possible
    return {
        "pre_percent": round(100.0 * int(pre_correct) / total, 1),
        "post_percent": round(100.0 * int(post_correct) / total, 1),
        "raw_gain": raw,
        "normalized_gain": round(normalized, 3),
    }


def remediation_plan(
    questions: Sequence[AcademyQuestion],
    selected_by_id: dict[str, int],
) -> list[dict[str, Any]]:
    out = []
    for question in questions:
        selected = selected_by_id.get(question.question_id)
        if selected is None or not score_question(question, selected):
            out.append(
                {
                    "lesson_id": question.lesson_id,
                    "question_id": question.question_id,
                    "repair": question.explanation,
                }
            )
    return out


class AcademyStore:
    """Local measurement store for pre-test → lesson/simulator → post-test."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS attempts (
                attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                lesson_id TEXT NOT NULL,
                phase TEXT NOT NULL,
                correct INTEGER NOT NULL,
                selected_index INTEGER NOT NULL,
                answer_index INTEGER NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_academy_session
            ON attempts(session_id, phase, lesson_id);
            """
        )

    def close(self) -> None:
        self.db.close()

    def record(
        self,
        session_id: str,
        *,
        lesson_id: str,
        phase: str,
        correct: bool,
        selected_index: int,
        answer_index: int,
    ) -> None:
        if phase not in {"pre", "post", "simulator"}:
            raise ValueError("phase must be pre, post, or simulator")
        with self.db:
            self.db.execute(
                """
                INSERT INTO attempts
                (session_id, lesson_id, phase, correct, selected_index,
                 answer_index, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    lesson_id,
                    phase,
                    1 if correct else 0,
                    int(selected_index),
                    int(answer_index),
                    time.time(),
                ),
            )

    def summary(self, session_id: str) -> dict[str, Any]:
        rows = self.db.execute(
            """
            SELECT phase, COUNT(*) AS total, SUM(correct) AS correct
            FROM attempts
            WHERE session_id=?
            GROUP BY phase
            """,
            (session_id,),
        ).fetchall()
        phases = {
            row["phase"]: {
                "total": int(row["total"]),
                "correct": int(row["correct"] or 0),
            }
            for row in rows
        }
        pre = phases.get("pre", {"total": 0, "correct": 0})
        post = phases.get("post", {"total": 0, "correct": 0})
        total = max(pre["total"], post["total"], 1)
        return {
            "session_id": session_id,
            "phases": phases,
            "learning_gain": learning_gain(pre["correct"], post["correct"], total),
        }
