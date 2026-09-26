from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline


LABELS = ("FAIL", "PASS", "REVIEW")


@dataclass(frozen=True)
class LabeledCase:
    case_id: str
    answer: str
    label: str


@dataclass(frozen=True)
class CrossValidationResult:
    accuracy: float
    labels: tuple[str, ...]
    confusion: list[list[int]]
    report: dict


def load_cases(path: str | Path) -> list[LabeledCase]:
    cases: list[LabeledCase] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            label = str(row["expected"]).upper()
            if label not in LABELS:
                raise ValueError(f"line {line_number}: unsupported label {label!r}")
            cases.append(
                LabeledCase(
                    case_id=str(row["id"]),
                    answer=str(row["answer"]),
                    label=label,
                )
            )
    if not cases:
        raise ValueError("dataset is empty")
    return cases


def make_classifier() -> Pipeline:
    """Create a small, inspectable classical NLP classifier.

    TF-IDF converts text into numeric features. Logistic regression then learns
    weights that separate PASS / REVIEW / FAIL examples.
    """
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    ngram_range=(1, 2),
                    min_df=1,
                    sublinear_tf=True,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )


def cross_validate(cases: Iterable[LabeledCase], folds: int = 3) -> CrossValidationResult:
    rows = list(cases)
    texts = [case.answer for case in rows]
    labels = [case.label for case in rows]

    counts = {label: labels.count(label) for label in set(labels)}
    if len(counts) < 2:
        raise ValueError("at least two classes are required")
    if min(counts.values()) < folds:
        raise ValueError(
            f"each class needs at least {folds} examples for {folds}-fold stratified validation"
        )

    splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=42)
    predictions = cross_val_predict(make_classifier(), texts, labels, cv=splitter)

    ordered_labels = tuple(label for label in LABELS if label in counts)
    return CrossValidationResult(
        accuracy=float(accuracy_score(labels, predictions)),
        labels=ordered_labels,
        confusion=confusion_matrix(labels, predictions, labels=ordered_labels).tolist(),
        report=classification_report(
            labels,
            predictions,
            labels=ordered_labels,
            output_dict=True,
            zero_division=0,
        ),
    )


def fit_classifier(cases: Iterable[LabeledCase]) -> Pipeline:
    rows = list(cases)
    model = make_classifier()
    model.fit([case.answer for case in rows], [case.label for case in rows])
    return model


def predict(model: Pipeline, answers: Iterable[str]) -> list[str]:
    return [str(label) for label in model.predict(list(answers))]
