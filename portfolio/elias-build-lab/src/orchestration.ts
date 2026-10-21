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
  | "veteran.issue_matrix"
  | "veteran.decision_audit"
  | "veteran.rebuttal_map"
  | "packet.build"
  | "packet.qa"
  | "packet.export";

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
    id: "veteran.issue_matrix",
    label: "Veteran issue matrix",
    purpose: "Map each contested issue to favorable evidence, adverse evidence, missing evidence, and verified authority.",
    model: "frontier_llm",
    preservesProvenance: true,
  },
  {
    id: "veteran.decision_audit",
    label: "VBA decision audit",
    purpose: "Compare an agency decision with the cited record and flag unsupported, incomplete, or internally inconsistent reasoning for review.",
    model: "frontier_llm",
    preservesProvenance: true,
  },
  {
    id: "veteran.rebuttal_map",
    label: "Rebuttal map",
    purpose: "Build a source-backed response to adverse findings without hiding contradictory evidence.",
    model: "frontier_llm",
    preservesProvenance: true,
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
    purpose: "Check citation trace, missing sources, adverse-evidence treatment, ordering, and export readiness.",
    model: "frontier_llm",
    preservesProvenance: true,
  },
  {
    id: "packet.export",
    label: "Packet export / filing handoff",
    purpose: "Create the final export artifact or filing handoff after the veteran reviews the packet.",
    model: "deterministic",
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

  const asksToFabricateOrHideEvidence =
    q.includes("invent reasonable support") ||
    q.includes("invent evidence") ||
    q.includes("delete the contradictory evidence") ||
    q.includes("delete the unfavorable") ||
    q.includes("hide unfavorable") ||
    q.includes("ignore adverse evidence") ||
    q.includes("stronger medical conclusion than the evidence supports") ||
    q.includes("guessing the dates") ||
    q.includes("guess the dates") ||
    q.includes("even if you cannot verify it") ||
    q.includes("exact page and quote anyway");

  const explicitlyMissingSource =
    q.includes("no records loaded") ||
    q.includes("have not provided the document") ||
    q.includes("without the source");

  if (asksToFabricateOrHideEvidence || explicitlyMissingSource) {
    return [];
  }

  const addHybridSearch = () => {
    plan.push(
      step(order++, "evidence.search_lexical", "Start with cheap, transparent exact-term retrieval."),
      step(order++, "evidence.search_semantic", "Add semantic candidates for paraphrases the lexical search may miss."),
    );
  };

  if (
    q.includes("veteran") ||
    q.includes("vba") ||
    q.includes("va claim") ||
    q.includes("hlr") ||
    q.includes("supplemental claim") ||
    q.includes("board appeal") ||
    q.includes("c&p") ||
    q.includes("rating decision")
  ) {
    addHybridSearch();
    plan.push(
      step(order++, "veteran.issue_matrix", "Map each contested issue to favorable evidence, adverse evidence, gaps, and verified authority."),
      step(order++, "veteran.decision_audit", "Audit the agency reasoning against the cited record rather than accepting conclusions at face value."),
      step(order++, "evidence.find_contradictions", "Surface conflicts and adverse evidence so the packet can address them directly."),
      step(order++, "evidence.build_timeline", "Build a chronology that preserves uncertain dates and links events to sources."),
      step(order++, "authority.verify", "Verify configured official authority before relying on it in advocacy."),
      step(order++, "veteran.rebuttal_map", "Develop the strongest source-backed response to adverse findings while preserving contrary evidence."),
      step(order++, "reason.synthesize", "Draft veteran-focused advocacy from verified evidence and authority."),
      step(order++, "evidence.trace_claim", "Attach source and locator trace to important factual propositions."),
      step(order++, "packet.build", "Build the complete veteran advocacy packet without requiring approval for each internal draft iteration."),
      step(order++, "packet.qa", "Iterate QA for citations, gaps, adverse evidence, and reviewer readiness before presenting the final draft."),
      step(order++, "packet.export", "Export or hand off the final packet only after the veteran approves it.", true),
    );
    return plan;
  }

  if (q.includes("packet") || q.includes("rebuttal") || q.includes("submission")) {
    addHybridSearch();
    plan.push(
      step(order++, "evidence.find_contradictions", "Stress-test the candidate evidence before drafting."),
      step(order++, "evidence.build_timeline", "Organize dated support and preserve uncertain dates."),
      step(order++, "reason.synthesize", "Draft only from the retrieved and reviewed evidence."),
      step(order++, "evidence.trace_claim", "Attach source and locator trace to important generated propositions."),
      step(order++, "packet.build", "Assemble the structured packet and permit iterative internal revisions."),
      step(order++, "packet.qa", "Run citation, adverse-evidence, completeness, and export-readiness checks."),
      step(order++, "packet.export", "Export or hand off the final packet only after user approval.", true),
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
