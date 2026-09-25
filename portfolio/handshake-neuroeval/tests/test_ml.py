import json
import tempfile
import unittest
from pathlib import Path

from neuroeval.ml import cross_validate, fit_classifier, load_cases, predict
from neuroeval.retrieval import RetrievalItem, TfidfRetrievalIndex


class NeuroEvalMLTests(unittest.TestCase):
    def _cases_file(self) -> Path:
        rows = [
            ("P1", "Evidence suggests sodium and potassium channels support repolarization.", "PASS"),
            ("P2", "Research indicates calcium can modulate synaptic signaling.", "PASS"),
            ("P3", "Myelination can support saltatory conduction between nodes.", "PASS"),
            ("R1", "Dopamine is involved in reward.", "REVIEW"),
            ("R2", "Myelin makes signaling faster.", "REVIEW"),
            ("R3", "NMDA receptors matter for plasticity.", "REVIEW"),
            ("F1", "Dopamine definitely guarantees pleasure in every circuit.", "FAIL"),
            ("F2", "Astrocytes alone make a barrier that never changes.", "FAIL"),
            ("F3", "Microglia always destroy every neuron.", "FAIL"),
        ]
        handle = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False)
        for case_id, answer, expected in rows:
            handle.write(json.dumps({"id": case_id, "answer": answer, "expected": expected}) + "\n")
        handle.close()
        return Path(handle.name)

    def test_classifier_cross_validation_returns_metrics(self):
        cases = load_cases(self._cases_file())
        result = cross_validate(cases, folds=3)
        self.assertGreaterEqual(result.accuracy, 0.0)
        self.assertLessEqual(result.accuracy, 1.0)
        self.assertEqual(set(result.labels), {"PASS", "REVIEW", "FAIL"})

    def test_fit_and_predict(self):
        cases = load_cases(self._cases_file())
        model = fit_classifier(cases)
        predictions = predict(model, ["Evidence suggests sodium channels contribute to signaling."])
        self.assertEqual(len(predictions), 1)
        self.assertIn(predictions[0], {"PASS", "REVIEW", "FAIL"})

    def test_retrieval_returns_relevant_item(self):
        index = TfidfRetrievalIndex(
            [
                RetrievalItem("a", "sodium channels depolarize neuronal membranes"),
                RetrievalItem("b", "microglia participate in immune signaling"),
                RetrievalItem("c", "myelin supports saltatory conduction"),
            ]
        )
        hits = index.search("sodium channel depolarization", limit=1)
        self.assertEqual(hits[0].item_id, "a")


if __name__ == "__main__":
    unittest.main()
