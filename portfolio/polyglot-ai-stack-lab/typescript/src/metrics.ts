import type { EvaluationCase, Label } from "./types";

export function accuracy(rows: EvaluationCase[]): number {
  const scored = rows.filter((row) => row.predicted !== undefined);
  if (scored.length === 0) return 0;

  const correct = scored.filter((row) => row.predicted === row.expected).length;
  return correct / scored.length;
}

export function countByLabel(rows: EvaluationCase[]): Record<Label, number> {
  const counts: Record<Label, number> = { PASS: 0, REVIEW: 0, FAIL: 0 };
  for (const row of rows) counts[row.expected] += 1;
  return counts;
}
