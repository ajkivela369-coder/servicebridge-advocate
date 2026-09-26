export type RetrievalDoc = { id: string; text: string };
export type RetrievalScore = RetrievalDoc & { score: number };

function tokenize(text: string): string[] {
  return text.toLowerCase().match(/[a-z0-9]+/g)?.filter((token) => token.length > 2) ?? [];
}

function cosineSparse(a: Map<string, number>, b: Map<string, number>): number {
  let dot = 0;
  let aNorm = 0;
  let bNorm = 0;
  for (const value of a.values()) aNorm += value * value;
  for (const value of b.values()) bNorm += value * value;
  for (const [term, value] of a.entries()) dot += value * (b.get(term) ?? 0);
  if (!aNorm || !bNorm) return 0;
  return dot / (Math.sqrt(aNorm) * Math.sqrt(bNorm));
}

export function rankByTfidf(query: string, docs: RetrievalDoc[]): RetrievalScore[] {
  const tokenizedDocs = docs.map((doc) => tokenize(doc.text));
  const documentCount = docs.length;

  const df = new Map<string, number>();
  for (const tokens of tokenizedDocs) {
    for (const term of new Set(tokens)) {
      df.set(term, (df.get(term) ?? 0) + 1);
    }
  }

  const idf = new Map<string, number>();
  for (const [term, frequency] of df.entries()) {
    idf.set(term, Math.log((documentCount + 1) / (frequency + 1)) + 1);
  }

  const vectorize = (text: string) => {
    const tokens = tokenize(text);
    const counts = new Map<string, number>();
    for (const token of tokens) counts.set(token, (counts.get(token) ?? 0) + 1);
    const vector = new Map<string, number>();
    const total = Math.max(tokens.length, 1);
    for (const [term, count] of counts.entries()) {
      const termIdf = idf.get(term);
      if (termIdf !== undefined) vector.set(term, (count / total) * termIdf);
    }
    return vector;
  };

  const queryVector = vectorize(query);
  return docs
    .map((doc) => ({ ...doc, score: cosineSparse(queryVector, vectorize(doc.text)) }))
    .sort((a, b) => b.score - a.score);
}

type Extractor = (
  text: string,
  options: { pooling: "mean"; normalize: true },
) => Promise<{ data: Float32Array | number[] }>;

let extractorPromise: Promise<Extractor> | null = null;
const embeddingCache = new Map<string, number[]>();

async function getExtractor(): Promise<Extractor> {
  if (!extractorPromise) {
    extractorPromise = (async () => {
      const { pipeline } = await import("@huggingface/transformers");
      const extractor = await pipeline(
        "feature-extraction",
        "onnx-community/all-MiniLM-L6-v2-ONNX",
      );
      return extractor as unknown as Extractor;
    })();
  }
  return extractorPromise;
}

async function embed(text: string): Promise<number[]> {
  const cached = embeddingCache.get(text);
  if (cached) return cached;
  const extractor = await getExtractor();
  const output = await extractor(text, { pooling: "mean", normalize: true });
  const vector = Array.from(output.data);
  embeddingCache.set(text, vector);
  return vector;
}

function cosineDense(a: number[], b: number[]): number {
  const length = Math.min(a.length, b.length);
  let dot = 0;
  let aNorm = 0;
  let bNorm = 0;
  for (let i = 0; i < length; i += 1) {
    dot += a[i] * b[i];
    aNorm += a[i] * a[i];
    bNorm += b[i] * b[i];
  }
  if (!aNorm || !bNorm) return 0;
  return dot / (Math.sqrt(aNorm) * Math.sqrt(bNorm));
}

export async function rankByEmbedding(
  query: string,
  docs: RetrievalDoc[],
): Promise<RetrievalScore[]> {
  const queryVector = await embed(query);
  const results: RetrievalScore[] = [];

  for (const doc of docs) {
    const docVector = await embed(doc.text);
    results.push({ ...doc, score: cosineDense(queryVector, docVector) });
  }

  return results.sort((a, b) => b.score - a.score);
}
