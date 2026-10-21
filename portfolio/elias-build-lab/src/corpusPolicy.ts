export type CorpusTier =
  | "private_reference"
  | "reviewed_gold"
  | "synthetic_public"
  | "production_case";

export type CorpusSourceClass =
  | "prior_packets"
  | "prior_chats"
  | "connected_drive"
  | "user_uploads"
  | "synthetic_examples";

export type CorpusUse =
  | "packet_structure"
  | "layout_patterns"
  | "retrieval_benchmark"
  | "planner_benchmark"
  | "rebuttal_patterns"
  | "source_control_patterns"
  | "visual_design"
  | "error_analysis";

export type CorpusPolicy = {
  tier: CorpusTier;
  mayContainPrivateData: boolean;
  mayEnterPublicRepo: boolean;
  mayBeUsedForExamples: boolean;
  requiresDeidentification: boolean;
  notes: string;
};

export const CORPUS_POLICIES: CorpusPolicy[] = [
  {
    tier: "private_reference",
    mayContainPrivateData: true,
    mayEnterPublicRepo: false,
    mayBeUsedForExamples: true,
    requiresDeidentification: true,
    notes:
      "User-authorized prior packets, chats, connected-drive files, and uploads may inform private pattern extraction, benchmarks, layouts, and failure analysis. Raw private content stays out of the public repository.",
  },
  {
    tier: "reviewed_gold",
    mayContainPrivateData: false,
    mayEnterPublicRepo: true,
    mayBeUsedForExamples: true,
    requiresDeidentification: true,
    notes:
      "Human-reviewed de-identified cases derived from private reference material. Suitable for fixed evaluation once every label/source relationship is checked.",
  },
  {
    tier: "synthetic_public",
    mayContainPrivateData: false,
    mayEnterPublicRepo: true,
    mayBeUsedForExamples: true,
    requiresDeidentification: false,
    notes:
      "Fully synthetic examples used to teach, test, and demonstrate public Build Lab behavior.",
  },
  {
    tier: "production_case",
    mayContainPrivateData: true,
    mayEnterPublicRepo: false,
    mayBeUsedForExamples: false,
    requiresDeidentification: false,
    notes:
      "Live user case data used only for the user's active case workflow. It is not automatically converted into a public example or shared benchmark.",
  },
];

export const PRIVATE_REFERENCE_SOURCES: Array<{
  sourceClass: CorpusSourceClass;
  uses: CorpusUse[];
  rule: string;
}> = [
  {
    sourceClass: "prior_packets",
    uses: [
      "packet_structure",
      "layout_patterns",
      "rebuttal_patterns",
      "source_control_patterns",
      "visual_design",
      "error_analysis",
    ],
    rule:
      "Learn recurring packet architecture, visual hierarchy, evidence-card structure, filing constraints, and reviewer-navigation patterns without copying identifiers into public fixtures.",
  },
  {
    sourceClass: "prior_chats",
    uses: [
      "planner_benchmark",
      "rebuttal_patterns",
      "source_control_patterns",
      "error_analysis",
    ],
    rule:
      "Use prior decisions, corrections, preferences, and failure cases to create de-identified planner/evaluation cases.",
  },
  {
    sourceClass: "connected_drive",
    uses: [
      "packet_structure",
      "layout_patterns",
      "retrieval_benchmark",
      "rebuttal_patterns",
      "source_control_patterns",
      "visual_design",
      "error_analysis",
    ],
    rule:
      "Use relevant connected-drive case materials as private reference data; do not crawl or publish unrelated files, raw identifiers, or source content.",
  },
  {
    sourceClass: "user_uploads",
    uses: [
      "packet_structure",
      "layout_patterns",
      "retrieval_benchmark",
      "rebuttal_patterns",
      "source_control_patterns",
      "visual_design",
      "error_analysis",
    ],
    rule:
      "Use explicitly supplied files as the factual basis for the user's work and as private reference patterns for de-identified evaluation design.",
  },
  {
    sourceClass: "synthetic_examples",
    uses: [
      "retrieval_benchmark",
      "planner_benchmark",
      "layout_patterns",
      "error_analysis",
    ],
    rule:
      "Use synthetic data for public demos, CI, examples, and regression tests whenever private source detail is unnecessary.",
  },
];

export const CORPUS_PIPELINE = [
  "private source",
  "extract reusable pattern",
  "remove identifiers / private facts",
  "separate record fact from advocacy pattern",
  "human review",
  "create synthetic or de-identified case",
  "assign benchmark expectation",
  "public regression test",
];
