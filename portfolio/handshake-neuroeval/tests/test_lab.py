import unittest

from neuroeval.lab import (
    cross_validation_rows,
    prediction_probabilities,
    text_signals,
    tfidf_features,
)
from neuroeval.ml import LabeledCase


CASES = [
    LabeledCase("P1", "Evidence suggests sodium and potassium channels support repolarization.", "PASS"),
    LabeledCase("P2", "Research indicates calcium can modulate synaptic signaling.", "PASS"),
    LabeledCase("P3", "Myelination can support saltatory conduction between nodes.", "PASS"),
    LabeledCase("R1", "Dopamine is involved in reward.", "REVIEW"),
    LabeledCase("R2", "Myelin makes signaling faster.", "REVIEW"),
    LabeledCase("R3", "NMDA receptors matter for plasticity.", "REVIEW"),
    LabeledCase("F1", "Dopamine definitely guarantees pleasure in every circuit.", "FAIL"),
    LabeledCase("F2", "Astrocytes alone make a barrier that never changes.", "FAIL"),
    LabeledCase("F3", "Microglia always destroy every neuron.", "FAIL"),
]


class VisualLabHelpersTests(unittest.TestCase):
    def test_text_signals_explain_rule_based_features(self):
        signals = text_signals(
            "Evidence suggests sodium channels matter because signaling can vary.",
            ["sodium channels", "potassium"],
        )
        self.assertEqual(signals.concepts_found, ("sodium channels",))
        self.assertEqual(signals.concepts_missing, ("potassium",))
        self.assertIn("suggests", signals.uncertainty_words)
        self.assertIn("because", signals.mechanism_words)
        self.assertIn("evidence", signals.evidence_words)

    def test_tfidf_features_return_weighted_terms(self):
        features = tfidf_features(CASES, "P1")
        self.assertTrue(features)
        self.assertTrue(all(weight > 0 for _, weight in features))

    def test_prediction_probabilities_sum_to_one(self):
        probs = prediction_probabilities(CASES, "Evidence suggests sodium channels contribute.")
        self.assertAlmostEqual(sum(value for _, value in probs), 1.0, places=6)

    def test_cross_validation_rows_include_errors_and_labels(self):
        rows = cross_validation_rows(CASES, folds=3)
        self.assertEqual(len(rows), len(CASES))
        self.assertTrue(all("expected" in row and "predicted" in row for row in rows))


if __name__ == "__main__":
    unittest.main()
