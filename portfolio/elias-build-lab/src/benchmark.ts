import {
  rankByEmbedding,
  rankByTfidf,
  type RetrievalDoc,
  type RetrievalScore,
} from "./semantic";

export type BenchmarkCase = {
  id: string;
  query: string;
  relevantIds: string[];
  note: string;
};

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

export const RETRIEVAL_BENCHMARK: BenchmarkCase[] = [
  {
    id: "Q01",
    query: "Which ion channels are responsible for the rising and falling phases of an action potential?",
    relevantIds: ["N001"],
    note: "Direct vocabulary overlap with sodium, potassium, and action-potential physiology.",
  },
  {
    id: "Q02",
    query: "What membrane proteins make a neuron spike and then return toward resting voltage?",
    relevantIds: ["N001"],
    note: "Semantic paraphrase with less exact vocabulary overlap.",
  },
  {
    id: "Q03",
    query: "How does NMDA receptor activity participate in long-term changes at synapses?",
    relevantIds: ["N003"],
    note: "Direct receptor/plasticity query.",
  },
  {
    id: "Q04",
    query: "What mechanism links glutamate, depolarization, calcium entry, and synaptic strengthening?",
    relevantIds: ["N003"],
    note: "Mechanistic paraphrase that should still retrieve the NMDA passage.",
  },
  {
    id: "Q05",
    query: "Which brain-resident immune cells respond to inflammatory signals?",
    relevantIds: ["N005"],
    note: "Paraphrase of microglial immune function.",
  },
  {
    id: "Q06",
    query: "What cells act like the nervous system's local immune sentinels?",
    relevantIds: ["N005"],
    note: "Low lexical overlap; intended to probe semantic retrieval.",
  },
  {
    id: "Q07",
    query: "What structure enables saltatory conduction between nodes of Ranvier?",
    relevantIds: ["N007"],
    note: "Direct vocabulary overlap with myelin physiology.",
  },
  {
    id: "Q08",
    query: "What insulation around axons helps electrical signals travel faster?",
    relevantIds: ["N007"],
    note: "Semantic paraphrase of myelin and conduction speed.",
  },
  {
    id: "Q09",
    query: "Which glial cells help regulate extracellular ions and support synaptic metabolism?",
    relevantIds: ["N009"],
    note: "Direct astrocyte/homeostasis query.",
  },
  {
    id: "Q10",
    query: "What support cells help neurons keep the chemical environment around synapses stable?",
    relevantIds: ["N009"],
    note: "Semantic paraphrase with reduced exact-term overlap.",
  },
];

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
  cases: BenchmarkCase[] = RETRIEVAL_BENCHMARK,
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
  cases: BenchmarkCase[] = RETRIEVAL_BENCHMARK,
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
