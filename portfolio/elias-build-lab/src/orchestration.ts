export type ModelTier = "deterministic" | "local_model" | "frontier_llm";

export type ToolId =
  | "evidence.search_lexical"
  | "evidence.search_semantic"
  | "evidence.trace_claim"
  | "evidence.find_contradictions"
  | "evidence.build_timeline"
  | "evidence.verify_quote"
  | "authority.verify"
  | "reason.synthesize"
  | "packet.build"
  | "packet.qa";

export type ToolDefinition = {
  id: ToolId;
  label: string;
  purpose: string;
  model: ModelTier;
  preservesProvenance: boolean;
};

export type PlanStep = {
  order: number;
  tool: ToolDefinition;
  reason: string;
  requiresApproval: boolean;
};

export const TOOL_REGISTRY: ToolDefinition[] = [
  {
    id: "evidence.search_lexical",
    label: "Lexical evidence search",
    purpose: "Find exact terms, names, dates, and phrase overlap.",
    model: "deterministic",
    preservesProvenance: true,
  },
  {
    id: "evidence.search_semantic",
    label: "Semantic evidence search",
    purpose: "Find paraphrases and conceptually related passages.",
    model: "local_model",
    preservesProvenance: true,
  },
  {
    id: "evidence.trace_claim",
    label: "Claim → Source Trace",
    purpose: "Resolve a generated proposition back to source IDs and locators.",
    model: "deterministic",
    preservesProvenance: true,
  },
  {
    id: "evidence.find_contradictions",
    label: "Contradiction finder",
    purpose: "Surface potentially conflicting evidence for review.",
    model: "frontier_llm",
    preservesProvenance: true,
  },
  {
    id: "evidence.build_timeline",
    label: "Timeline builder",
    purpose: "Normalize dated evidence while preserving uncertainty.",
    model: "deterministic",
    preservesProvenance: true,
  },
  {
    id: "evidence.verify_quote",
    label: "Quote verifier",
    purpose: "Confirm literal support before preserving an exact quote.",
    model: "deterministic",
    preservesProvenance: true,
  },
  {
    id: "authority.verify",
    label: "Authority verifier",
    purpose: "Check configured official authority pages and metadata.",
    model: "deterministic",
    preservesProvenance: true,
  },
  {
    id: "reason.synthesize",
    label: "Reasoning / synthesis",
    purpose: "Compare retrieved evidence, explain significance, and draft grounded prose.",
    model: "frontier_llm",
    preservesProvenance: false,
  },
  {
    id: "packet.build",
    label: "Packet builder",
    purpose: "Assemble approved evidence and derived text into a structured packet.",
    model: "deterministic",
    preservesProvenance: true,
  },
  {
    id: "packet.qa",
    label: "Packet QA",
    purpose: "Check citation trace, missing sources, ordering, and export readiness.",
    model: "frontier_llm",
    preservesProvenance: true,
  },
];

const byId = (id: ToolId) => TOOL_REGISTRY.find((tool) => tool.id === id)!;

export function chooseModelForTask(task: string): ModelTier {
  const q = task.toLowerCase();

  if (
    q.includes("exact phrase") ||
    q.includes("page") ||
    q.includes("date") ||
    q.includes("quote") ||
    q.includes("timeline")
  ) {
    return "deterministic";
  }

  if (
    q.includes("similar meaning") ||
    q.includes("paraphrase") ||
    q.includes("semantic") ||
    q.includes("related evidence")
  ) {
    return "local_model";
  }

  return "frontier_llm";
}

function step(
  order: number,
  id: ToolId,
  reason: string,
  requiresApproval = false,
): PlanStep {
  return { order, tool: byId(id), reason, requiresApproval };
}

export function planEvidenceTask(task: string): PlanStep[] {
  const q = task.toLowerCase();
  const plan: PlanStep[] = [];
  let order = 1;

  const addHybridSearch = () => {
    plan.push(
      step(order++, "evidence.search_lexical", "Start with cheap, transparent exact-term retrieval."),
      step(order++, "evidence.search_semantic", "Add semantic candidates for paraphrases the lexical search may miss."),
    );
  };

  if (q.includes("packet") || q.includes("rebuttal") || q.includes("submission")) {
    addHybridSearch();
    plan.push(
      step(order++, "evidence.find_contradictions", "Stress-test the candidate evidence before drafting."),
      step(order++, "evidence.build_timeline", "Organize dated support and preserve uncertain dates."),
      step(order++, "reason.synthesize", "Draft only from the retrieved and reviewed evidence."),
      step(order++, "evidence.trace_claim", "Attach source and locator trace to important generated propositions."),
      step(order++, "packet.build", "Assemble approved content into a structured packet.", true),
      step(order++, "packet.qa", "Run final citation and completeness checks before export.", true),
    );
    return plan;
  }

  if (q.includes("contradiction") || q.includes("conflict")) {
    addHybridSearch();
    plan.push(
      step(order++, "evidence.find_contradictions", "Compare candidate passages for materially conflicting statements."),
      step(order++, "evidence.trace_claim", "Keep every flagged conflict tied to its source and locator."),
    );
    return plan;
  }

  if (q.includes("timeline") || q.includes("chronology")) {
    plan.push(
      step(order++, "evidence.search_lexical", "Find dates, encounters, and event language."),
      step(order++, "evidence.build_timeline", "Normalize event order without inventing missing dates."),
      step(order++, "evidence.trace_claim", "Tie each timeline event back to its evidence."),
    );
    return plan;
  }

  if (q.includes("verify") || q.includes("quote") || q.includes("citation")) {
    addHybridSearch();
    plan.push(
      step(order++, "evidence.verify_quote", "Confirm literal source support when exact wording matters."),
      step(order++, "evidence.trace_claim", "Record source and locator for the verified statement."),
    );
    return plan;
  }

  if (q.includes("law") || q.includes("regulation") || q.includes("authority")) {
    plan.push(
      step(order++, "authority.verify", "Check configured official authority sources first."),
      step(order++, "reason.synthesize", "Explain the verified authority in the context of the user request."),
    );
    return plan;
  }

  addHybridSearch();
  plan.push(
    step(order++, "reason.synthesize", "Use the frontier model for the part that genuinely requires higher-level reasoning."),
    step(order++, "evidence.trace_claim", "Reattach important conclusions to source evidence."),
  );
  return plan;
}

export function modelLabel(model: ModelTier): string {
  if (model === "deterministic") return "Deterministic code";
  if (model === "local_model") return "Local / specialized model";
  return "Frontier LLM";
}
