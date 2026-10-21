export type Label = "PASS" | "REVIEW" | "FAIL";

export interface EvaluationCase {
  id: string;
  answer: string;
  expected: Label;
  predicted?: Label;
  confidence?: number;
}

export function isErrorCase(item: EvaluationCase): boolean {
  return item.predicted !== undefined && item.predicted !== item.expected;
}
