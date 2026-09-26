from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from .evaluator import (
    CERTAINTY_WORDS,
    EVIDENCE_WORDS,
    HEDGE_WORDS,
    MECHANISM_WORDS,
    _tokens,
)
from .ml import LabeledCase, make_classifier


@dataclass(frozen=True)
class TextSignals:
    tokens: tuple[str, ...]
    concepts_found: tuple[str, ...]
    concepts_missing: tuple[str, ...]
    uncertainty_words: tuple[str, ...]
    certainty_words: tuple[str, ...]
    mechanism_words: tuple[str, ...]
    evidence_words: tuple[str, ...]


def text_signals(text: str, required_concepts: Iterable[str] = ()) -> TextSignals:
    tokens = _tokens(text)
    concepts = [concept.strip() for concept in required_concepts if concept.strip()]
    lowered = text.lower()

    found = tuple(concept for concept in concepts if concept.lower() in lowered)
    missing = tuple(concept for concept in concepts if concept.lower() not in lowered)

    return TextSignals(
        tokens=tuple(sorted(tokens)),
        concepts_found=found,
        concepts_missing=missing,
        uncertainty_words=tuple(sorted(tokens & HEDGE_WORDS)),
        certainty_words=tuple(sorted(tokens & CERTAINTY_WORDS)),
        mechanism_words=tuple(sorted(tokens & MECHANISM_WORDS)),
        evidence_words=tuple(sorted(tokens & EVIDENCE_WORDS)),
    )


def tfidf_features(
    cases: Iterable[LabeledCase],
    case_id: str,
    *,
    limit: int = 12,
) -> list[tuple[str, float]]:
    rows = list(cases)
    if not rows:
        raise ValueError("at least one case is required")

    try:
        index = next(i for i, case in enumerate(rows) if case.case_id == case_id)
    except StopIteration as exc:
        raise ValueError(f"unknown case_id: {case_id}") from exc

    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=1,
        sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform([case.answer for case in rows])
    feature_names = vectorizer.get_feature_names_out()
    vector = matrix[index].toarray()[0]

    ranked = sorted(
        ((feature_names[i], float(weight)) for i, weight in enumerate(vector) if weight > 0),
        key=lambda pair: pair[1],
        reverse=True,
    )
    return ranked[: max(0, limit)]


def prediction_probabilities(
    cases: Iterable[LabeledCase],
    answer: str,
) -> list[tuple[str, float]]:
    rows = list(cases)
    if not rows:
        raise ValueError("at least one case is required")
    model = make_classifier()
    model.fit([case.answer for case in rows], [case.label for case in rows])

    classifier = model.named_steps["classifier"]
    probabilities = model.predict_proba([answer])[0]
    return sorted(
        (
            (str(label), float(probability))
            for label, probability in zip(classifier.classes_, probabilities)
        ),
        key=lambda pair: pair[1],
        reverse=True,
    )


def cross_validation_rows(
    cases: Iterable[LabeledCase],
    *,
    folds: int = 3,
) -> list[dict[str, str | bool]]:
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

    return [
        {
            "id": case.case_id,
            "expected": case.label,
            "predicted": str(prediction),
            "correct": bool(case.label == prediction),
            "answer": case.answer,
        }
        for case, prediction in zip(rows, predictions)
    ]
