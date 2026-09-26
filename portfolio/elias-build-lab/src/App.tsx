import { useMemo, useState } from "react";
import { rankByEmbedding, rankByTfidf, type RetrievalScore } from "./semantic";
import { runEmbeddingBenchmark, runTfidfBenchmark, summarizeBenchmark, type BenchmarkCaseResult } from "./benchmark";
import { RETRIEVAL_BENCHMARK, RETRIEVAL_DOCS, type Difficulty, type QueryType, type Topic } from "./datasets";
import { analyzeDataset, buildCandidateExpansion } from "./datasetQuality";

type Status = "Implemented" | "Lab" | "Candidate" | "Planned" | "Adopted";
type ViewId =
  | "overview"
  | "architecture"
  | "data"
  | "dataset"
  | "nlp"
  | "ml"
  | "evaluation"
  | "retrieval"
  | "embeddings"
  | "benchmark"
  | "timeline"
  | "ledger"
  | "portfolio";

type Lesson = {
  id: ViewId;
  label: string;
  short: string;
};

const LESSONS: Lesson[] = [
  { id: "overview", label: "Overview", short: "Two-app model" },
  { id: "architecture", label: "System Architecture", short: "Frontend, backend, API, DB" },
  { id: "data", label: "Evidence Cloud", short: "Data engineering + provenance" },
  { id: "dataset", label: "Dataset Lab", short: "Coverage, quality, expansion" },
  { id: "nlp", label: "NeuroEval: NLP", short: "Signals + TF-IDF" },
  { id: "ml", label: "NeuroEval: ML", short: "Labels + classifier" },
  { id: "evaluation", label: "Model Evaluation", short: "Metrics + errors" },
  { id: "retrieval", label: "Retrieval / RAG", short: "Find → ground → answer" },
  { id: "embeddings", label: "TF-IDF vs Embeddings", short: "Words vs meaning" },
  { id: "benchmark", label: "Retrieval Benchmark", short: "Measure which method wins" },
  { id: "timeline", label: "Build Timeline", short: "How Elias grows" },
  { id: "ledger", label: "Upgrade Ledger", short: "Lab → test → Elias" },
  { id: "portfolio", label: "Portfolio Skills", short: "What this proves" },
];

const syntheticAnswer =
  "Evidence suggests sodium channels drive depolarization, followed by potassium-mediated repolarization. The exact kinetics can vary across neuron types.";

const signalGroups = {
  concept: ["sodium channels", "potassium", "repolarization"],
  uncertainty: ["suggests", "can", "may", "might"],
  mechanism: ["followed by", "drive", "through", "because"],
  overconfidence: ["always", "never", "definitely", "proves"],
};

const tfidfTerms: Array<[string, number]> = [
  ["sodium channels", 0.82],
  ["repolarization", 0.73],
  ["potassium", 0.66],
  ["depolarization", 0.61],
  ["neuron types", 0.42],
];

const ledgerRows: Array<[string, Status, string, Status, string]> = [
  ["Evidence provenance trace", "Implemented", "Regression coverage exists", "Adopted", "Core Elias requirement"],
  ["TF-IDF retrieval", "Lab", "Classical baseline under test", "Candidate", "Useful lexical baseline"],
  ["Logistic regression", "Lab", "Cross-validation + metrics", "Lab", "Learning/evaluation tool"],
  ["Sentence embeddings", "Lab", "Real browser model wired; benchmark expanding", "Planned", "MiniLM comparison runs locally in Build Lab"],
  ["Semantic retrieval", "Lab", "Side-by-side TF-IDF comparison implemented", "Candidate", "Must beat fixed retrieval baseline before Elias adoption"],
  ["PyTorch classifier", "Planned", "Not implemented", "Planned", "Deep-learning learning track"],
  ["EvidencePipe quality checks", "Lab", "Unit tests in branch", "Candidate", "Promote only non-mutating checks"],
];


function overlapScore(query: string, text: string): number {
  const words = (value: string) =>
    new Set(value.toLowerCase().match(/[a-z]+/g)?.filter((x) => x.length > 3) ?? []);
  const q = words(query);
  const d = words(text);
  if (!q.size || !d.size) return 0;
  let common = 0;
  q.forEach((token) => {
    if (d.has(token)) common += 1;
  });
  return common / Math.sqrt(q.size * d.size);
}

function statusClass(status: Status) {
  return "status " + status.toLowerCase();
}

function CodePanel({ code, notes }: { code: string; notes: string[] }) {
  return (
    <div className="code-panel">
      <div className="panel-kicker">HOW IT IS BUILT</div>
      <pre><code>{code}</code></pre>
      <div className="line-notes">
        {notes.map((note) => <div key={note}>• {note}</div>)}
      </div>
    </div>
  );
}

function WhyBox({ why, skills }: { why: string; skills: string[] }) {
  return (
    <div className="why-grid">
      <div className="why-card">
        <div className="panel-kicker">WHY ELIAS CARES</div>
        <p>{why}</p>
      </div>
      <div className="why-card">
        <div className="panel-kicker">SKILLS DEMONSTRATED</div>
        <div className="chips">{skills.map((skill) => <span key={skill}>{skill}</span>)}</div>
      </div>
    </div>
  );
}

function App() {
  const [view, setView] = useState<ViewId>("overview");
  const [technical, setTechnical] = useState(false);
  const [query, setQuery] = useState("How do sodium and potassium channels affect an action potential?");
  const [studyChecks, setStudyChecks] = useState<Record<string, boolean>>(() => {
    try {
      return JSON.parse(localStorage.getItem("elias-build-lab-checks") || "{}");
    } catch {
      return {};
    }
  });

  const index = LESSONS.findIndex((lesson) => lesson.id === view);
  const progress = ((index + 1) / LESSONS.length) * 100;

  const toggleCheck = (key: string) => {
    const next = { ...studyChecks, [key]: !studyChecks[key] };
    setStudyChecks(next);
    localStorage.setItem("elias-build-lab-checks", JSON.stringify(next));
  };

  const retrieval = useMemo(
    () => rankByTfidf(query, RETRIEVAL_DOCS),
    [query],
  );

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">E</div>
          <div>
            <strong>Elias Build Lab</strong>
            <small>educational twin</small>
          </div>
        </div>
        <div className="mode-row">
          <span>{technical ? "Technical" : "Beginner"}</span>
          <button className="toggle" onClick={() => setTechnical((v) => !v)} aria-label="Toggle explanation depth">
            <span className={technical ? "toggle-dot on" : "toggle-dot"} />
          </button>
        </div>
        <nav>
          {LESSONS.map((lesson, i) => (
            <button
              key={lesson.id}
              className={view === lesson.id ? "nav-item active" : "nav-item"}
              onClick={() => setView(lesson.id)}
            >
              <span className="nav-number">{String(i + 1).padStart(2, "0")}</span>
              <span><strong>{lesson.label}</strong><small>{lesson.short}</small></span>
            </button>
          ))}
        </nav>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <span className="eyebrow">ELIAS BUILD LAB</span>
            <strong>{LESSONS[index].label}</strong>
          </div>
          <div className="progress-wrap">
            <span>{index + 1}/{LESSONS.length}</span>
            <div className="progress"><div style={{ width: progress + "%" }} /></div>
          </div>
        </header>

        <section className="content">
          {view === "overview" && <Overview technical={technical} />}
          {view === "architecture" && <Architecture technical={technical} />}
          {view === "data" && <DataLesson technical={technical} />}
          {view === "dataset" && <DatasetLab technical={technical} />}
          {view === "nlp" && <NlpLesson technical={technical} />}
          {view === "ml" && <MlLesson technical={technical} />}
          {view === "evaluation" && <EvaluationLesson technical={technical} />}
          {view === "retrieval" && (
            <RetrievalLesson query={query} setQuery={setQuery} results={retrieval} technical={technical} />
          )}
          {view === "embeddings" && <EmbeddingLesson technical={technical} />}
          {view === "benchmark" && <RetrievalBenchmarkLesson technical={technical} />}
          {view === "timeline" && <Timeline />}
          {view === "ledger" && <Ledger />}
          {view === "portfolio" && (
            <Portfolio checks={studyChecks} toggleCheck={toggleCheck} />
          )}
        </section>
      </main>
    </div>
  );
}

function Overview({ technical }: { technical: boolean }) {
  return (
    <>
      <div className="hero">
        <span className="eyebrow">TWO APPS. TWO JOBS.</span>
        <h1>Experiment freely here. Keep Elias fast, grounded, and production-focused.</h1>
        <p>
          Build Lab explains and tests the ideas behind Elias. A technique only moves into Elias
          after it survives a benchmark, failure review, and production safeguards.
        </p>
      </div>

      <div className="system-map">
        <div className="system-card production">
          <span className="badge adopted">PRODUCTION</span>
          <h3>Elias</h3>
          <p>Evidence-grounded workflows, retrieval, audit, Copilot, Packet Studio.</p>
        </div>
        <div className="arrow">← validated upgrades ←</div>
        <div className="system-card lab">
          <span className="badge lab">LAB</span>
          <h3>Elias Build Lab</h3>
          <p>NLP, ML, RAG, data engineering, evaluation, deep-learning experiments.</p>
        </div>
      </div>

      <div className="promotion">
        {["Learn", "Build", "Benchmark", "Inspect errors", "Compare", "Promote"].map((item, i) => (
          <div className="promotion-step" key={item}>
            <span>{i + 1}</span><strong>{item}</strong>
          </div>
        ))}
      </div>

      <WhyBox
        why="This prevents experimental complexity from making the production evidence app slower, harder to audit, or less reliable."
        skills={["AI systems design", "Experiment design", "Production judgment"]}
      />
      {technical && <p className="technical-note">Technical mode: the lab is a staging environment for candidate algorithms, not a second source of truth.</p>}
    </>
  );
}

function Architecture({ technical }: { technical: boolean }) {
  return (
    <>
      <div className="lesson-heading">
        <span className="eyebrow">SYSTEM ARCHITECTURE</span>
        <h1>Where the pieces of Elias live</h1>
        <p>Frontend, backend, APIs, and databases solve different parts of one product.</p>
      </div>
      <div className="two-col">
        <div className="visual-panel">
          <div className="panel-kicker">SEE IT</div>
          <div className="architecture-flow">
            <div><strong>Frontend</strong><small>what the user sees</small></div>
            <b>↕ API</b>
            <div><strong>Backend</strong><small>rules + AI orchestration</small></div>
            <b>↕</b>
            <div><strong>Evidence Cloud</strong><small>sources + metadata + provenance</small></div>
          </div>
          <div className="mini-grid">
            <div><b>TypeScript</b><span>UI and typed browser logic</span></div>
            <div><b>Python</b><span>ML, NLP, evaluation, data tools</span></div>
            <div><b>SQL</b><span>structured evidence queries</span></div>
            <div><b>JSON</b><span>data exchange and benchmark cases</span></div>
          </div>
        </div>
        <CodePanel
          code={'type Evidence = {\n  sourceId: string;\n  locator: string;\n  classification: "objective_test" | "claimant_report" | "ai_synthesis";\n};'}
          notes={[
            "A TypeScript type makes the expected data shape explicit.",
            "The classification union prevents arbitrary evidence labels.",
            technical ? "Static typing catches many interface mismatches before runtime." : "Think of it as a labeled form the app must follow.",
          ]}
        />
      </div>
      <WhyBox
        why="Elias depends on clean boundaries: the interface can change without rewriting the evidence layer, and model experiments can change without changing source identity."
        skills={["TypeScript", "APIs", "Databases", "Software architecture"]}
      />
    </>
  );
}

function DataLesson({ technical }: { technical: boolean }) {
  return (
    <>
      <div className="lesson-heading">
        <span className="eyebrow">DATA ENGINEERING / EVIDENCE CLOUD</span>
        <h1>Turn messy records into traceable evidence</h1>
        <p>Data engineering is the plumbing that makes later AI trustworthy.</p>
      </div>
      <div className="pipeline-row">
        {["PDF / text", "Extract", "Normalize", "Validate", "Deduplicate", "Store + trace"].map((x) => <div key={x}>{x}</div>)}
      </div>
      <div className="two-col">
        <div className="visual-panel">
          <div className="panel-kicker">SEE IT</div>
          <div className="trace">
            <div><small>Source</small><b>synthetic_ot_note.pdf</b></div>
            <span>→</span><div><small>Page</small><b>p. 2</b></div>
            <span>→</span><div><small>Class</small><b>clinician observation</b></div>
            <span>→</span><div><small>Statement</small><b>derived summary</b></div>
          </div>
          <div className="record-card">
            <span>Before</span><code>09/01/26 · "  Breaks were required.  "</code>
          </div>
          <div className="record-card good">
            <span>After</span><code>2026-09-01 · "Breaks were required."</code>
          </div>
        </div>
        <CodePanel
          code={"SELECT source_id, locator, evidence_class\nFROM evidence\nWHERE evidence_class = 'objective_test'\nORDER BY document_date;"}
          notes={[
            "SQL asks a structured question of the evidence store.",
            "The query keeps source identity and locator attached.",
            technical ? "Normalization and provenance are deterministic transformations, not generative interpretation." : "The system tidies the data without pretending to know facts that are missing.",
          ]}
        />
      </div>
      <WhyBox why="If provenance is lost during ingestion, a later AI answer can sound correct while becoming impossible to verify." skills={["Data engineering", "SQL", "Normalization", "Provenance"]} />
    </>
  );
}

function DatasetLab({ technical }: { technical: boolean }) {
  const report = useMemo(
    () => analyzeDataset(RETRIEVAL_DOCS, RETRIEVAL_BENCHMARK),
    [],
  );
  const [topic, setTopic] = useState<"all" | Topic>("all");
  const [difficulty, setDifficulty] = useState<"all" | Difficulty>("all");
  const [queryType, setQueryType] = useState<"all" | QueryType>("all");
  const [selectedId, setSelectedId] = useState(RETRIEVAL_BENCHMARK[0].id);

  const filtered = useMemo(
    () =>
      RETRIEVAL_BENCHMARK.filter(
        (item) =>
          (topic === "all" || item.topic === topic) &&
          (difficulty === "all" || item.difficulty === difficulty) &&
          (queryType === "all" || item.queryType === queryType),
      ),
    [topic, difficulty, queryType],
  );

  const selected =
    RETRIEVAL_BENCHMARK.find((item) => item.id === selectedId) ??
    RETRIEVAL_BENCHMARK[0];
  const expansion = buildCandidateExpansion(selected);
  const topics = Object.keys(report.topicCounts) as Topic[];

  return (
    <>
      <div className="lesson-heading">
        <span className="eyebrow">DATASET ENGINEERING</span>
        <h1>Bigger is useful only when the dataset becomes more representative.</h1>
        <p>
          The retrieval benchmark now has 25 synthetic passages and 50 labeled queries across ten
          neuroscience topics. Dataset Lab checks coverage, difficulty, query style, missing
          references, duplicate queries, and multi-passage relevance before we trust model scores.
        </p>
      </div>

      <div className="dataset-summary">
        <div><small>Passages</small><b>{report.documentCount}</b><span>5× larger corpus</span></div>
        <div><small>Queries</small><b>{report.queryCount}</b><span>5× benchmark growth</span></div>
        <div><small>Topics</small><b>{topics.length}</b><span>broader concept coverage</span></div>
        <div><small>Multi-source queries</small><b>{report.multiRelevantCount}</b><span>more realistic retrieval</span></div>
      </div>

      <div className="two-col">
        <div className="visual-panel">
          <div className="panel-kicker">COVERAGE BY QUERY STYLE</div>
          <div className="distribution-list">
            {Object.entries(report.queryTypeCounts).map(([label, count]) => (
              <div key={label}>
                <span>{label}</span>
                <div><i style={{ width: (count / report.queryCount) * 100 + "%" }} /></div>
                <b>{count}</b>
              </div>
            ))}
          </div>
          <div className="panel-kicker dataset-kicker">DIFFICULTY MIX</div>
          <div className="distribution-list">
            {Object.entries(report.difficultyCounts).map(([label, count]) => (
              <div key={label}>
                <span>{label}</span>
                <div><i style={{ width: (count / report.queryCount) * 100 + "%" }} /></div>
                <b>{count}</b>
              </div>
            ))}
          </div>
        </div>
        <div className="visual-panel">
          <div className="panel-kicker">VALIDATION CHECKS</div>
          <div className="quality-checks">
            <div className={report.missingRelevantDocumentIds.length ? "check-warn" : "check-pass"}>
              <b>{report.missingRelevantDocumentIds.length ? "Review" : "Pass"}</b>
              <span>Every gold relevance ID resolves to a real passage</span>
            </div>
            <div className={report.duplicateNormalizedQueries.length ? "check-warn" : "check-pass"}>
              <b>{report.duplicateNormalizedQueries.length ? "Review" : "Pass"}</b>
              <span>No exact normalized duplicate queries</span>
            </div>
            <div className="check-pass">
              <b>{report.averageQueryWords.toFixed(1)}</b>
              <span>average words per query</span>
            </div>
            <div className="check-pass">
              <b>{report.averageDocumentWords.toFixed(1)}</b>
              <span>average words per passage</span>
            </div>
            <div className={report.unusedDocumentIds.length > 5 ? "check-warn" : "check-pass"}>
              <b>{report.unusedDocumentIds.length}</b>
              <span>deliberate distractor / currently unused passages</span>
            </div>
          </div>
          <p className="caption">
            Unused passages are not automatically bad: distractors make retrieval harder. Missing
            relevance IDs and accidental duplicate queries are data-quality defects.
          </p>
        </div>
      </div>

      <div className="filter-bar">
        <label>Topic
          <select value={topic} onChange={(e) => setTopic(e.target.value as "all" | Topic)}>
            <option value="all">All topics</option>
            {topics.map((value) => <option key={value} value={value}>{value.replaceAll("_", " ")}</option>)}
          </select>
        </label>
        <label>Difficulty
          <select value={difficulty} onChange={(e) => setDifficulty(e.target.value as "all" | Difficulty)}>
            <option value="all">All</option>
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
        </label>
        <label>Query type
          <select value={queryType} onChange={(e) => setQueryType(e.target.value as "all" | QueryType)}>
            <option value="all">All</option>
            <option value="direct">Direct</option>
            <option value="paraphrase">Paraphrase</option>
            <option value="mechanism">Mechanism</option>
            <option value="indirect">Indirect</option>
            <option value="multi">Multi-source</option>
          </select>
        </label>
        <div className="filter-count">{filtered.length} / {report.queryCount} queries</div>
      </div>

      <div className="table-wrap dataset-table">
        <table>
          <thead>
            <tr><th>ID</th><th>Topic</th><th>Type</th><th>Difficulty</th><th>Query</th><th>Gold source(s)</th></tr>
          </thead>
          <tbody>
            {filtered.map((item) => (
              <tr key={item.id}>
                <td><button className="link-button" onClick={() => setSelectedId(item.id)}>{item.id}</button></td>
                <td>{item.topic.replaceAll("_", " ")}</td>
                <td>{item.queryType}</td>
                <td><span className={"difficulty " + item.difficulty}>{item.difficulty}</span></td>
                <td>{item.query}</td>
                <td>{item.relevantIds.join(", ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="two-col dataset-expansion">
        <div className="visual-panel">
          <div className="panel-kicker">REVIEW-FIRST EXPANSION QUEUE</div>
          <h3>{selected.id} · {selected.topic.replaceAll("_", " ")}</h3>
          <p className="selected-query">{selected.query}</p>
          <p className="caption">
            New variants are candidates, not automatic gold labels. A reviewer must verify wording,
            relevance IDs, difficulty, and whether a near-duplicate should stay in the same family.
          </p>
          <div className="candidate-list">
            {expansion.candidates.map((candidate) => (
              <div key={candidate.kind}>
                <span>{candidate.kind.replaceAll("_", " ")}</span>
                <p>{candidate.query}</p>
                <b>REVIEW REQUIRED</b>
              </div>
            ))}
          </div>
        </div>
        <CodePanel
          code={'candidate → duplicate check\n          → family check\n          → relevance review\n          → difficulty tag\n          → approve / reject\n          → benchmark'}
          notes={[
            "AI-assisted or templated expansion should create candidates, not silently create truth.",
            "Family IDs keep closely related variants grouped so later train/test splits do not leak paraphrases across the boundary.",
            technical
              ? "The next classifier dataset will use grouped splitting so paraphrase families remain entirely in train, validation, or test."
              : "Near-duplicate questions should not appear on both sides of a test, because that can make a model look smarter than it is.",
          ]}
        />
      </div>

      <WhyBox
        why="Model quality is capped by dataset quality. This lab makes coverage and labeling visible before we compare TF-IDF, embeddings, logistic regression, or neural networks."
        skills={["Dataset engineering", "Benchmark design", "Data validation", "Hard negatives", "Label quality", "Leakage prevention"]}
      />
    </>
  );
}

function NlpLesson({ technical }: { technical: boolean }) {
  const highlighted = highlightSynthetic(syntheticAnswer);
  return (
    <>
      <div className="lesson-heading">
        <span className="eyebrow">NEUROEVAL / NLP</span>
        <h1>Before a model can learn language, we need representations</h1>
        <p>Start with visible rules, then convert text into numeric features.</p>
      </div>
      <div className="two-col">
        <div className="visual-panel">
          <div className="panel-kicker">SEE IT</div>
          <div className="highlight-box" dangerouslySetInnerHTML={{ __html: highlighted }} />
          <div className="legend">
            <span className="concept">concept</span><span className="uncertainty">uncertainty</span><span className="mechanism">mechanism</span>
          </div>
          <h3>TF-IDF feature weights</h3>
          <div className="bars">
            {tfidfTerms.map(([term, weight]) => (
              <div className="bar-row" key={term}>
                <span>{term}</span>
                <div><i style={{ width: weight * 100 + "%" }} /></div>
                <b>{weight.toFixed(2)}</b>
              </div>
            ))}
          </div>
        </div>
        <CodePanel
          code={'vectorizer = TfidfVectorizer(\n    lowercase=True,\n    ngram_range=(1, 2),\n)\nX = vectorizer.fit_transform(texts)'}
          notes={[
            "lowercase=True removes capitalization differences.",
            "ngram_range=(1, 2) learns words and two-word phrases.",
            technical ? "TF-IDF is sparse lexical vectorization; it does not encode meaning the way neural embeddings do." : "TF-IDF gives important words and phrases useful numeric weights.",
          ]}
        />
      </div>
      <WhyBox why="TF-IDF gives NeuroEval a transparent baseline. Later, semantic embeddings must prove they improve retrieval rather than being adopted just because they are newer." skills={["NLP", "TF-IDF", "Feature engineering", "Python"]} />
    </>
  );
}

function MlLesson({ technical }: { technical: boolean }) {
  const [signal, setSignal] = useState(55);
  const pass = Math.min(92, 25 + signal * 0.65);
  const fail = Math.max(3, 48 - signal * 0.45);
  const review = Math.max(5, 100 - pass - fail);
  const total = pass + review + fail;
  const probs: Array<[string, number]> = [
    ["PASS", pass / total],
    ["REVIEW", review / total],
    ["FAIL", fail / total],
  ];
  return (
    <>
      <div className="lesson-heading">
        <span className="eyebrow">SUPERVISED MACHINE LEARNING</span>
        <h1>The model learns from examples with known labels</h1>
        <p>NeuroEval uses PASS / REVIEW / FAIL as a small teaching classification problem.</p>
      </div>
      <div className="two-col">
        <div className="visual-panel">
          <div className="panel-kicker">TRY IT</div>
          <label>Strength of evidence / calibrated language signal: <b>{signal}</b></label>
          <input type="range" min="0" max="100" value={signal} onChange={(e) => setSignal(Number(e.target.value))} />
          <div className="probability-grid">
            {probs.map(([label, p]) => (
              <div key={label}>
                <strong>{label}</strong><span>{(p * 100).toFixed(1)}%</span>
                <div className="prob"><i style={{ width: p * 100 + "%" }} /></div>
              </div>
            ))}
          </div>
          <p className="caption">Educational visualization only — these bars are not the production NeuroEval scikit-learn probabilities.</p>
        </div>
        <CodePanel
          code={'model = LogisticRegression(\n    class_weight="balanced",\n    random_state=42,\n)\nmodel.fit(X_train, y_train)'}
          notes={[
            "fit() learns weights from labeled examples.",
            "random_state makes the experiment reproducible.",
            technical ? "Logistic regression models class log-odds from weighted features and can expose class probabilities." : "The model learns which numeric language patterns tend to go with each label.",
          ]}
        />
      </div>
      <WhyBox why="A classical model gives us an interpretable benchmark before we experiment with neural networks." skills={["Machine learning", "Logistic regression", "Supervised learning", "Reproducibility"]} />
    </>
  );
}

function EvaluationLesson({ technical }: { technical: boolean }) {
  const matrix = [
    [3, 1, 0],
    [1, 2, 1],
    [0, 1, 3],
  ];
  return (
    <>
      <div className="lesson-heading">
        <span className="eyebrow">MODEL EVALUATION</span>
        <h1>Accuracy is only the beginning</h1>
        <p>We need to know what the model gets wrong, not just how often it is right.</p>
      </div>
      <div className="two-col">
        <div className="visual-panel">
          <div className="metric-grid">
            <div><small>Accuracy</small><b>66.7%</b></div>
            <div><small>Precision</small><b>0.68</b></div>
            <div><small>Recall</small><b>0.67</b></div>
            <div><small>F1</small><b>0.66</b></div>
          </div>
          <h3>Confusion matrix</h3>
          <div className="matrix">
            <span />
            {["PASS", "REVIEW", "FAIL"].map((x) => <b key={x}>{x}</b>)}
            {matrix.map((row, i) => [
              <b key={"r" + i}>{["PASS", "REVIEW", "FAIL"][i]}</b>,
              ...row.map((value, j) => <div className={i === j ? "diag" : ""} key={i + "-" + j}>{value}</div>),
            ])}
          </div>
          <p className="caption">Rows = true label. Columns = predicted label.</p>
        </div>
        <CodePanel
          code={'accuracy_score(y_true, y_pred)\nclassification_report(y_true, y_pred)\nconfusion_matrix(y_true, y_pred)'}
          notes={[
            "Precision asks how trustworthy a predicted class is.",
            "Recall asks how many real examples of a class were found.",
            technical ? "F1 is the harmonic mean of precision and recall; confusion matrices expose class-specific error structure." : "A confusion matrix shows exactly which kinds of examples the model mixes up.",
          ]}
        />
      </div>
      <WhyBox why="Error analysis prevents a good-looking average score from hiding a failure mode that matters to users." skills={["Model evaluation", "Precision/recall", "F1", "Error analysis"]} />
    </>
  );
}

function RetrievalLesson({
  query,
  setQuery,
  results,
  technical,
}: {
  query: string;
  setQuery: (value: string) => void;
  results: Array<{ id: string; text: string; score: number }>;
  technical: boolean;
}) {
  return (
    <>
      <div className="lesson-heading">
        <span className="eyebrow">RETRIEVAL / RAG</span>
        <h1>Find evidence first. Generate second.</h1>
        <p>A grounded assistant should retrieve relevant source chunks before drafting an answer.</p>
      </div>
      <div className="two-col">
        <div className="visual-panel">
          <div className="rag-flow">
            {["Question", "Retrieve", "Source chunks", "Grounded prompt", "Answer + trace"].map((x) => <div key={x}>{x}</div>)}
          </div>
          <label>Try a query</label>
          <input className="text-input" value={query} onChange={(e) => setQuery(e.target.value)} />
          <div className="retrieval-list">
            {results.map((item, i) => (
              <div key={item.id}>
                <b>#{i + 1} {item.id}</b><span>{item.score.toFixed(3)}</span><p>{item.text}</p>
              </div>
            ))}
          </div>
        </div>
        <CodePanel
          code={'query_vector = vectorizer.transform([query])\nscores = cosine_similarity(query_vector, matrix)[0]\nranked = scores.argsort()[::-1]'}
          notes={[
            "The query enters the same feature space as stored passages.",
            "Cosine similarity ranks related vectors.",
            technical ? "This is a lexical baseline. Sentence embeddings are a planned semantic comparison, not a completed production upgrade." : "Today we compare shared words; later we can test meaning-based embeddings.",
          ]}
        />
      </div>
      <WhyBox why="Elias needs retrieval that is not merely impressive—it must reliably find the right source while preserving traceability." skills={["Information retrieval", "RAG", "Cosine similarity", "Grounding"]} />
    </>
  );
}

function EmbeddingLesson({ technical }: { technical: boolean }) {
  const [query, setQuery] = useState("What material wraps axons so electrical signals can travel faster?");
  const [embeddingResults, setEmbeddingResults] = useState<RetrievalScore[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const tfidfResults = useMemo(() => rankByTfidf(query, RETRIEVAL_DOCS), [query]);

  const runEmbeddings = async () => {
    setLoading(true);
    setError("");
    try {
      const results = await rankByEmbedding(query, RETRIEVAL_DOCS);
      setEmbeddingResults(results);
    } catch (err) {
      setEmbeddingResults([]);
      setError(err instanceof Error ? err.message : "Embedding model could not run in this browser.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="lesson-heading">
        <span className="eyebrow">SEMANTIC RETRIEVAL LAB</span>
        <h1>TF-IDF compares words. Embeddings compare meaning.</h1>
        <p>
          We run both methods against the same synthetic neuroscience passages so the newer
          technique has to prove what it adds.
        </p>
      </div>

      <div className="compare-explainer">
        <div>
          <span className="badge lab">TF-IDF</span>
          <h3>Lexical representation</h3>
          <p>
            TF-IDF builds a sparse vector from words and phrases. Shared important terms create
            similarity; synonyms with no shared vocabulary can be missed.
          </p>
          <div className="mini-vector">myelin → 0.78<br />axons → 0.42<br />conduction → 0.64</div>
        </div>
        <div className="versus">VS</div>
        <div>
          <span className="badge lab">EMBEDDINGS</span>
          <h3>Semantic representation</h3>
          <p>
            A transformer converts the whole sentence into a dense 384-number vector. Texts can
            be close even when they use different words but express similar meaning.
          </p>
          <div className="mini-vector">[0.095, −0.025, 0.041, … 381 more]</div>
        </div>
      </div>

      <div className="try-box">
        <div className="panel-kicker">TRY THE SAME QUERY BOTH WAYS</div>
        <input className="text-input" value={query} onChange={(e) => setQuery(e.target.value)} />
        <button className="run-button" onClick={runEmbeddings} disabled={loading}>
          {loading ? "Loading model / computing embeddings…" : "Run real embedding comparison"}
        </button>
        <p className="caption">
          TF-IDF runs instantly. The embedding side loads the open MiniLM model in your browser on
          first use, then caches the model and document vectors for later comparisons.
        </p>
        {error && <div className="error-box">{error}</div>}
      </div>

      <div className="retrieval-compare-grid">
        <RetrievalColumn title="TF-IDF ranking" subtitle="important word/phrase overlap" rows={tfidfResults} />
        <RetrievalColumn
          title="Embedding ranking"
          subtitle="transformer-based semantic similarity"
          rows={embeddingResults}
          emptyText={loading ? "Computing…" : "Run the embedding comparison to populate this side."}
        />
      </div>

      <div className="two-col">
        <div className="visual-panel">
          <div className="panel-kicker">WHAT CHANGES?</div>
          <table className="concept-table">
            <tbody>
              <tr><th>Representation</th><td>TF-IDF: sparse word weights</td><td>Embeddings: dense learned vector</td></tr>
              <tr><th>Understands synonyms?</th><td>Usually only with word overlap</td><td>Often, through learned semantic patterns</td></tr>
              <tr><th>Interpretability</th><td>High: inspect weighted terms</td><td>Lower: dimensions are learned features</td></tr>
              <tr><th>Compute cost</th><td>Low</td><td>Higher; model inference required</td></tr>
              <tr><th>Elias decision</th><td>Current lab baseline</td><td>Candidate only if benchmark improves retrieval</td></tr>
            </tbody>
          </table>
        </div>
        <CodePanel
          code={'// TF-IDF\nrankByTfidf(query, documents)\n\n// Embeddings\nconst extractor = await pipeline(\n  "feature-extraction",\n  "onnx-community/all-MiniLM-L6-v2-ONNX"\n);\nconst vector = await extractor(text, {\n  pooling: "mean",\n  normalize: true,\n});'}
          notes={[
            "Both methods ultimately create vectors so we can compare texts numerically.",
            "TF-IDF learns weights from this document collection; the embedding model learned semantic patterns during pretraining.",
            technical
              ? "MiniLM produces normalized dense vectors; cosine similarity then compares vector direction in semantic feature space."
              : "Embeddings turn the overall meaning of a sentence into a numeric fingerprint.",
          ]}
        />
      </div>

      <WhyBox
        why="Elias should not adopt semantic retrieval merely because embeddings are fashionable. Build Lab now gives us a real comparison surface where we can define correct sources, run identical queries, inspect false matches, and decide from evidence."
        skills={["Sentence embeddings", "Transformers.js", "Semantic search", "TF-IDF", "Cosine similarity", "Retrieval evaluation"]}
      />
    </>
  );
}

function RetrievalColumn({
  title,
  subtitle,
  rows,
  emptyText = "No results",
}: {
  title: string;
  subtitle: string;
  rows: RetrievalScore[];
  emptyText?: string;
}) {
  return (
    <div className="visual-panel retrieval-column">
      <div className="panel-kicker">{title}</div>
      <p className="caption">{subtitle}</p>
      {rows.length === 0 ? (
        <div className="empty-state">{emptyText}</div>
      ) : (
        <div className="retrieval-list">
          {rows.map((item, index) => (
            <div key={item.id}>
              <b>#{index + 1} {item.id}</b>
              <span>{item.score.toFixed(3)}</span>
              <p>{item.text}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function RetrievalBenchmarkLesson({ technical }: { technical: boolean }) {
  const tfidfRows = useMemo(() => runTfidfBenchmark(RETRIEVAL_DOCS), []);
  const tfidfMetrics = useMemo(() => summarizeBenchmark(tfidfRows), [tfidfRows]);
  const [embeddingRows, setEmbeddingRows] = useState<BenchmarkCaseResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const embeddingMetrics = useMemo(
    () => summarizeBenchmark(embeddingRows),
    [embeddingRows],
  );

  const runBenchmark = async () => {
    setLoading(true);
    setError("");
    try {
      setEmbeddingRows(await runEmbeddingBenchmark(RETRIEVAL_DOCS));
    } catch (err) {
      setEmbeddingRows([]);
      setError(err instanceof Error ? err.message : "Embedding benchmark could not run.");
    } finally {
      setLoading(false);
    }
  };

  const formatMetric = (value: number) => (value * 100).toFixed(1) + "%";

  return (
    <>
      <div className="lesson-heading">
        <span className="eyebrow">RETRIEVAL BENCHMARK</span>
        <h1>Newer does not mean better. Measure it.</h1>
        <p>
          Fifty fixed neuroscience queries have human-defined relevant passages. Both retrieval
          methods must answer the same test so we can compare performance fairly.
        </p>
      </div>

      <div className="benchmark-rule">
        <strong>Fair comparison rule</strong>
        <span>same documents</span><b>+</b><span>same queries</span><b>+</b><span>same relevance labels</span><b>→</b><span>comparable metrics</span>
      </div>

      <div className="benchmark-metrics">
        <MetricSet title="TF-IDF baseline" metrics={tfidfMetrics} status="Implemented" />
        <MetricSet
          title="Sentence embeddings"
          metrics={embeddingMetrics}
          status={embeddingRows.length ? "Lab" : "Planned"}
          empty={!embeddingRows.length}
        />
      </div>

      <div className="try-box">
        <div className="panel-kicker">RUN THE REAL EMBEDDING BENCHMARK</div>
        <p>
          TF-IDF is already scored locally. This button runs the same fifty queries through MiniLM
          sentence embeddings and calculates Hit@1, Recall@3, and Mean Reciprocal Rank.
        </p>
        <button className="run-button" onClick={runBenchmark} disabled={loading}>
          {loading ? "Running 50-query semantic benchmark…" : "Run embedding benchmark"}
        </button>
        {error && <div className="error-box">{error}</div>}
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Query</th>
              <th>Expected</th>
              <th>TF-IDF top result</th>
              <th>TF-IDF rank</th>
              <th>Embedding top result</th>
              <th>Embedding rank</th>
            </tr>
          </thead>
          <tbody>
            {tfidfRows.map((row, index) => {
              const semantic = embeddingRows[index];
              return (
                <tr key={row.id}>
                  <td>
                    <strong>{row.id}</strong>
                    <div className="table-query">{row.query}</div>
                    <div className="caption">{row.note}</div>
                  </td>
                  <td>{row.relevantIds.join(", ")}</td>
                  <td>{row.ranked[0]?.id ?? "—"}</td>
                  <td className={row.top1Correct ? "metric-good" : "metric-review"}>
                    {row.firstRelevantRank ?? "miss"}
                  </td>
                  <td>{semantic?.ranked[0]?.id ?? "—"}</td>
                  <td className={
                    semantic
                      ? semantic.top1Correct
                        ? "metric-good"
                        : "metric-review"
                      : ""
                  }>
                    {semantic?.firstRelevantRank ?? "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="two-col">
        <div className="visual-panel">
          <div className="panel-kicker">WHAT THE METRICS MEAN</div>
          <div className="metric-explain">
            <div><b>Hit@1</b><span>How often the correct source is ranked first.</span></div>
            <div><b>Recall@3</b><span>How often a relevant source appears somewhere in the top three.</span></div>
            <div><b>MRR</b><span>Rewards putting the first relevant source as high in the ranking as possible.</span></div>
          </div>
          <p className="caption">
            With one relevant passage per query in this starter benchmark, Recall@3 is effectively
            the percentage of queries whose correct passage appears in the top three.
          </p>
        </div>
        <CodePanel
          code={'const ranked = retrieve(query, docs);\nconst rank = firstRelevantRank(ranked);\n\nhitAt1 = mean(rank === 1);\nrecallAt3 = mean(rank <= 3);\nmrr = mean(1 / rank);'}
          notes={[
            "The benchmark defines relevance before either method runs.",
            "Every method gets the same queries and document collection.",
            technical
              ? "MRR emphasizes ranking quality; later we can add multi-relevance metrics such as nDCG and precision@k when the benchmark contains several valid passages per query."
              : "We are scoring the methods by where they place the correct evidence, not by which output looks more impressive.",
          ]}
        />
      </div>

      <WhyBox
        why="If semantic retrieval actually improves relevant-source ranking, we have evidence for an Elias candidate upgrade. If it does not, TF-IDF remains the safer, cheaper baseline."
        skills={["Benchmark design", "Retrieval evaluation", "Hit@1", "Recall@K", "MRR", "Error analysis"]}
      />
    </>
  );
}

function MetricSet({
  title,
  metrics,
  status,
  empty = false,
}: {
  title: string;
  metrics: { queryCount: number; hitAt1: number; recallAt3: number; mrr: number };
  status: Status;
  empty?: boolean;
}) {
  return (
    <div className="visual-panel benchmark-set">
      <div className="benchmark-set-head">
        <strong>{title}</strong>
        <span className={statusClass(status)}>{status}</span>
      </div>
      <div className="metric-grid">
        <div><small>Queries</small><b>{empty ? "—" : metrics.queryCount}</b></div>
        <div><small>Hit@1</small><b>{empty ? "—" : (metrics.hitAt1 * 100).toFixed(1) + "%"}</b></div>
        <div><small>Recall@3</small><b>{empty ? "—" : (metrics.recallAt3 * 100).toFixed(1) + "%"}</b></div>
        <div><small>MRR</small><b>{empty ? "—" : metrics.mrr.toFixed(3)}</b></div>
      </div>
    </div>
  );
}

function Timeline() {
  const items: Array<[string, string, Status, string]> = [
    ["1", "Deterministic evidence rules", "Implemented", "Keep source categories distinct."],
    ["2", "Lexical retrieval", "Implemented", "Search and source-grounded prompting."],
    ["3", "NeuroEval NLP / ML baselines", "Lab", "TF-IDF, logistic regression, cross-validation."],
    ["4", "Embedding comparison", "Lab", "Real MiniLM browser embeddings vs TF-IDF baseline."],
    ["5", "Deep-learning comparison", "Planned", "PyTorch classifier vs classical ML."],
    ["6", "Production promotion gate", "Candidate", "Only validated gains move into Elias."],
  ];
  return (
    <>
      <div className="lesson-heading"><span className="eyebrow">BUILD TIMELINE</span><h1>How Elias grows without turning production into an experiment</h1></div>
      <div className="timeline">
        {items.map(([n, title, status, note]) => (
          <div key={n}><span>{n}</span><div><h3>{title}</h3><p>{note}</p></div><span className={statusClass(status)}>{status}</span></div>
        ))}
      </div>
    </>
  );
}

function Ledger() {
  return (
    <>
      <div className="lesson-heading"><span className="eyebrow">UPGRADE LEDGER</span><h1>What stays in the lab, and what earns a place in Elias</h1></div>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Experiment</th><th>Build Lab</th><th>Test status</th><th>Elias</th><th>Evidence / notes</th></tr></thead>
          <tbody>
            {ledgerRows.map(([name, lab, test, elias, note]) => (
              <tr key={name}>
                <td><strong>{name}</strong></td>
                <td><span className={statusClass(lab)}>{lab}</span></td>
                <td>{test}</td>
                <td><span className={statusClass(elias)}>{elias}</span></td>
                <td>{note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

function Portfolio({ checks, toggleCheck }: { checks: Record<string, boolean>; toggleCheck: (key: string) => void }) {
  const skills = [
    "Explain frontend vs backend vs API vs database",
    "Explain provenance and why source identity survives transformation",
    "Explain TF-IDF and why text becomes numeric features",
    "Explain supervised learning and logistic regression",
    "Explain train/test separation and cross-validation",
    "Interpret precision, recall, F1, and a confusion matrix",
    "Explain lexical retrieval, cosine similarity, and RAG",
    "Explain the difference between TF-IDF and sentence embeddings",
    "Describe why PyTorch is still a planned experiment",
  ];
  return (
    <>
      <div className="lesson-heading"><span className="eyebrow">PORTFOLIO + STUDY CHECKLIST</span><h1>What I can explain now</h1><p>Checking a box is for your own study progress, not an automatic expertise claim.</p></div>
      <div className="checklist">
        {skills.map((skill) => (
          <label key={skill}>
            <input type="checkbox" checked={Boolean(checks[skill])} onChange={() => toggleCheck(skill)} />
            <span>{skill}</span>
          </label>
        ))}
      </div>
      <div className="skill-map">
        {["Python", "SQL", "TypeScript", "NLP", "Machine Learning", "AI Evaluation", "Retrieval / RAG", "Data Engineering", "Testing / CI", "Technical Writing", "Health Informatics"].map((x) => <span key={x}>{x}</span>)}
      </div>
      <div className="portfolio-note">
        <strong>Portfolio standard</strong>
        <p>A technology moves from exposure to hands-on project experience after you can explain it, run it, make a small change, interpret the output, and describe an important limitation.</p>
      </div>
    </>
  );
}

function highlightSynthetic(text: string): string {
  let output = text;
  const replacements: Array<[string, string]> = [];
  Object.entries(signalGroups).forEach(([group, terms]) => {
    terms.forEach((term) => replacements.push([term, group]));
  });
  replacements.sort((a, b) => b[0].length - a[0].length);
  replacements.forEach(([term, group]) => {
    const escaped = term.replace(/[.*+?^$()|[\]\\{}]/g, "\\$&");
    const re = new RegExp("(" + escaped + ")", "gi");
    output = output.replace(re, '<mark class="' + group + '">$1</mark>');
  });
  return output;
}

export default App;
