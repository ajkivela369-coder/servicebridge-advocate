-- SQL demonstrates the structured-data layer around an ML experiment.

CREATE TABLE IF NOT EXISTS evaluations (
    case_id TEXT PRIMARY KEY,
    answer TEXT NOT NULL,
    expected_label TEXT NOT NULL CHECK (expected_label IN ('PASS','REVIEW','FAIL')),
    predicted_label TEXT,
    confidence REAL CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1))
);

-- Class balance matters before training/evaluation.
SELECT
    expected_label,
    COUNT(*) AS example_count
FROM evaluations
GROUP BY expected_label
ORDER BY expected_label;

-- Error analysis: rows where model prediction disagrees with the benchmark.
SELECT
    case_id,
    expected_label,
    predicted_label,
    confidence
FROM evaluations
WHERE predicted_label IS NOT NULL
  AND predicted_label <> expected_label
ORDER BY confidence DESC;
