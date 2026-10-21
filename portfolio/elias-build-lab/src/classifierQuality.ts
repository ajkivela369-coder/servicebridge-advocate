import type {
  ClassifierExample,
  ClassLabel,
  DataSplit,
} from "./classifierDataset";

export type ClassifierQualityReport = {
  exampleCount: number;
  familyCount: number;
  topicCount: number;
  labelCounts: Record<ClassLabel, number>;
  splitCounts: Record<DataSplit, number>;
  splitLabelCounts: Record<DataSplit, Record<ClassLabel, number>>;
  failureModeCounts: Record<string, number>;
  duplicateTexts: string[][];
  leakingFamilies: string[];
  missingRationales: string[];
  familyLabelProblems: string[];
  templateGeneratedCount: number;
  humanReviewedCount: number;
};

function emptyLabelCounts(): Record<ClassLabel, number> {
  return { PASS: 0, REVIEW: 0, FAIL: 0 };
}

function normalize(text: string): string {
  return text.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

export function analyzeClassifierDataset(
  rows: ClassifierExample[],
): ClassifierQualityReport {
  const labelCounts = emptyLabelCounts();
  const splitCounts: Record<DataSplit, number> = {
    train: 0,
    validation: 0,
    test: 0,
  };
  const splitLabelCounts: Record<DataSplit, Record<ClassLabel, number>> = {
    train: emptyLabelCounts(),
    validation: emptyLabelCounts(),
    test: emptyLabelCounts(),
  };
  const failureModeCounts: Record<string, number> = {};
  const familySplits = new Map<string, Set<DataSplit>>();
  const familyLabels = new Map<string, Set<ClassLabel>>();
  const normalizedTexts = new Map<string, string[]>();
  const topics = new Set<string>();
  const families = new Set<string>();
  const missingRationales: string[] = [];

  let templateGeneratedCount = 0;
  let humanReviewedCount = 0;

  for (const row of rows) {
    labelCounts[row.label] += 1;
    splitCounts[row.split] += 1;
    splitLabelCounts[row.split][row.label] += 1;
    failureModeCounts[row.failureMode] =
      (failureModeCounts[row.failureMode] ?? 0) + 1;
    topics.add(row.topic);
    families.add(row.familyId);

    if (!row.rationale.trim()) missingRationales.push(row.id);
    if (row.reviewStatus === "template_generated") templateGeneratedCount += 1;
    if (row.reviewStatus === "human_reviewed") humanReviewedCount += 1;

    const splitSet = familySplits.get(row.familyId) ?? new Set<DataSplit>();
    splitSet.add(row.split);
    familySplits.set(row.familyId, splitSet);

    const labelSet = familyLabels.get(row.familyId) ?? new Set<ClassLabel>();
    labelSet.add(row.label);
    familyLabels.set(row.familyId, labelSet);

    const key = normalize(row.text);
    const ids = normalizedTexts.get(key) ?? [];
    ids.push(row.id);
    normalizedTexts.set(key, ids);
  }

  const leakingFamilies = [...familySplits.entries()]
    .filter(([, splits]) => splits.size > 1)
    .map(([familyId]) => familyId)
    .sort();

  const familyLabelProblems = [...familyLabels.entries()]
    .filter(([, labels]) => labels.size !== 3)
    .map(([familyId]) => familyId)
    .sort();

  const duplicateTexts = [...normalizedTexts.values()]
    .filter((ids) => ids.length > 1)
    .sort((a, b) => a[0].localeCompare(b[0]));

  return {
    exampleCount: rows.length,
    familyCount: families.size,
    topicCount: topics.size,
    labelCounts,
    splitCounts,
    splitLabelCounts,
    failureModeCounts,
    duplicateTexts,
    leakingFamilies,
    missingRationales,
    familyLabelProblems,
    templateGeneratedCount,
    humanReviewedCount,
  };
}

export function classifierDatasetAssertions(
  report: ClassifierQualityReport,
): string[] {
  const problems: string[] = [];

  if (report.exampleCount !== 300) {
    problems.push(`Expected 300 examples, found ${report.exampleCount}.`);
  }
  if (
    report.labelCounts.PASS !== 100 ||
    report.labelCounts.REVIEW !== 100 ||
    report.labelCounts.FAIL !== 100
  ) {
    problems.push("Expected balanced 100 / 100 / 100 label counts.");
  }
  if (report.leakingFamilies.length) {
    problems.push(
      `Family leakage across splits: ${report.leakingFamilies.join(", ")}.`,
    );
  }
  if (report.familyLabelProblems.length) {
    problems.push(
      `Families missing one or more labels: ${report.familyLabelProblems.join(", ")}.`,
    );
  }
  if (report.missingRationales.length) {
    problems.push(
      `Examples missing rationale: ${report.missingRationales.join(", ")}.`,
    );
  }

  return problems;
}
