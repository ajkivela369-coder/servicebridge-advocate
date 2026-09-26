import {
  rankByEmbedding,
  rankByTfidf,
  type RetrievalDoc,
  type RetrievalScore,
} from "./semantic";
import {
  RETRIEVAL_BENCHMARK,
  type RetrievalBenchmarkCase,
} from "./datasets";

export type BenchmarkCaseResult = {
  id: string;
  query: string;
  relevantIds: string[];
  note: string;
  ranked: RetrievalScore[];
  firstRelevantRank: number | null;
  top1Correct: boolean;
  top3Hit: boolean;
};

export type BenchmarkMetrics = {
  queryCount: number;
  hitAt1: number;
  recallAt3: number;
  mrr: number;
};

function scoreRank(
  ranked: RetrievalScore[],
  relevantIds: string[],
): Pick<BenchmarkCaseResult, "firstRelevantRank" | "top1Correct" | "top3Hit"> {
  const firstIndex = ranked.findIndex((row) => relevantIds.includes(row.id));
  const firstRelevantRank = firstIndex >= 0 ? firstIndex + 1 : null;
  return {
    firstRelevantRank,
    top1Correct: firstRelevantRank === 1,
    top3Hit: firstRelevantRank !== null && firstRelevantRank <= 3,
  };
}

export function summarizeBenchmark(rows: BenchmarkCaseResult[]): BenchmarkMetrics {
  if (!rows.length) {
    return { queryCount: 0, hitAt1: 0, recallAt3: 0, mrr: 0 };
  }

  const hitAt1 = rows.filter((row) => row.top1Correct).length / rows.length;
  const recallAt3 = rows.filter((row) => row.top3Hit).length / rows.length;
  const reciprocalRanks = rows.map((row) =>
    row.firstRelevantRank ? 1 / row.firstRelevantRank : 0,
  );

  return {
    queryCount: rows.length,
    hitAt1,
    recallAt3,
    mrr:
      reciprocalRanks.reduce((sum, value) => sum + value, 0) /
      reciprocalRanks.length,
  };
}

export function runTfidfBenchmark(
  docs: RetrievalDoc[],
  cases: RetrievalBenchmarkCase[] = RETRIEVAL_BENCHMARK,
): BenchmarkCaseResult[] {
  return cases.map((benchmarkCase) => {
    const ranked = rankByTfidf(benchmarkCase.query, docs);
    return {
      ...benchmarkCase,
      ranked,
      ...scoreRank(ranked, benchmarkCase.relevantIds),
    };
  });
}

export async function runEmbeddingBenchmark(
  docs: RetrievalDoc[],
  cases: RetrievalBenchmarkCase[] = RETRIEVAL_BENCHMARK,
): Promise<BenchmarkCaseResult[]> {
  const results: BenchmarkCaseResult[] = [];
  for (const benchmarkCase of cases) {
    const ranked = await rankByEmbedding(benchmarkCase.query, docs);
    results.push({
      ...benchmarkCase,
      ranked,
      ...scoreRank(ranked, benchmarkCase.relevantIds),
    });
  }
  return results;
}
