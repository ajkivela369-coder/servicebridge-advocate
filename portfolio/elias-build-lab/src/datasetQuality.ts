import type {
  DatasetDocument,
  RetrievalBenchmarkCase,
  Difficulty,
  QueryType,
  Topic,
} from "./datasets";

export type DatasetQualityReport = {
  documentCount: number;
  queryCount: number;
  topicCounts: Record<string, number>;
  difficultyCounts: Record<Difficulty, number>;
  queryTypeCounts: Record<QueryType, number>;
  multiRelevantCount: number;
  missingRelevantDocumentIds: string[];
  unusedDocumentIds: string[];
  duplicateNormalizedQueries: string[][];
  averageQueryWords: number;
  averageDocumentWords: number;
};

function words(text: string): string[] {
  return text.toLowerCase().match(/[a-z0-9]+/g) ?? [];
}

function normalizeQuery(text: string): string {
  return words(text).join(" ");
}

function average(values: number[]): number {
  if (!values.length) return 0;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

export function analyzeDataset(
  docs: DatasetDocument[],
  cases: RetrievalBenchmarkCase[],
): DatasetQualityReport {
  const docIds = new Set(docs.map((doc) => doc.id));
  const usedIds = new Set<string>();
  const missingRelevant = new Set<string>();

  const topicCounts: Record<string, number> = {};
  const difficultyCounts: Record<Difficulty, number> = {
    easy: 0,
    medium: 0,
    hard: 0,
  };
  const queryTypeCounts: Record<QueryType, number> = {
    direct: 0,
    paraphrase: 0,
    mechanism: 0,
    indirect: 0,
    multi: 0,
  };

  const normalizedGroups = new Map<string, string[]>();

  for (const item of cases) {
    topicCounts[item.topic] = (topicCounts[item.topic] ?? 0) + 1;
    difficultyCounts[item.difficulty] += 1;
    queryTypeCounts[item.queryType] += 1;

    for (const id of item.relevantIds) {
      usedIds.add(id);
      if (!docIds.has(id)) missingRelevant.add(id);
    }

    const key = normalizeQuery(item.query);
    const ids = normalizedGroups.get(key) ?? [];
    ids.push(item.id);
    normalizedGroups.set(key, ids);
  }

  return {
    documentCount: docs.length,
    queryCount: cases.length,
    topicCounts,
    difficultyCounts,
    queryTypeCounts,
    multiRelevantCount: cases.filter((item) => item.relevantIds.length > 1).length,
    missingRelevantDocumentIds: [...missingRelevant].sort(),
    unusedDocumentIds: docs
      .map((doc) => doc.id)
      .filter((id) => !usedIds.has(id))
      .sort(),
    duplicateNormalizedQueries: [...normalizedGroups.values()].filter(
      (ids) => ids.length > 1,
    ),
    averageQueryWords: average(cases.map((item) => words(item.query).length)),
    averageDocumentWords: average(docs.map((doc) => words(doc.text).length)),
  };
}

export type CandidateExpansion = {
  familyId: string;
  topic: Topic;
  baseQuery: string;
  candidates: Array<{
    kind: "shorter" | "plain_language" | "contrast";
    query: string;
    reviewRequired: true;
  }>;
};

export function buildCandidateExpansion(
  item: RetrievalBenchmarkCase,
): CandidateExpansion {
  const directTopic = item.topic.replaceAll("_", " ");
  return {
    familyId: item.familyId,
    topic: item.topic,
    baseQuery: item.query,
    candidates: [
      {
        kind: "shorter",
        query: `In ${directTopic}, what is the key mechanism being tested here?`,
        reviewRequired: true,
      },
      {
        kind: "plain_language",
        query: `Explain the same ${directTopic} idea in plain language and identify the most relevant source passage.`,
        reviewRequired: true,
      },
      {
        kind: "contrast",
        query: `Which source best distinguishes this ${directTopic} concept from a closely related but different mechanism?`,
        reviewRequired: true,
      },
    ],
  };
}
