export type VeteranPacketSection = {
  id: string;
  title: string;
  purpose: string;
  required: boolean;
  pageTarget?: string;
};

export type VeteranPacketStyle = {
  id: "aj_visual_defense" | "aj_concise_filing";
  name: string;
  description: string;
  sections: VeteranPacketSection[];
};

export const AJ_PACKET_STYLES: VeteranPacketStyle[] = [
  {
    id: "aj_visual_defense",
    name: "AJ Visual Defense Packet",
    description:
      "Full visual advocacy packet modeled on the established AJ evidence/rebuttal format: source-first, issue-by-issue, screenshot-rich, visually polished, and built for reviewer navigation.",
    sections: [
      {
        id: "cover",
        title: "Cover / Case Identity",
        purpose: "Veteran, matter, issue set, packet title, date/version, and read-first instruction.",
        required: true,
        pageTarget: "1",
      },
      {
        id: "index",
        title: "Evidence Roadmap + Direct-Links Index",
        purpose: "Page-ranged roadmap to controlling sections and the underlying source repository.",
        required: true,
        pageTarget: "1–2",
      },
      {
        id: "executive",
        title: "Executive Advocacy Summary",
        purpose: "Concise statement of the veteran's requested outcome, strongest evidence, and the central evidentiary problem.",
        required: true,
        pageTarget: "1–2",
      },
      {
        id: "issue_matrix",
        title: "Contested-Issue Matrix",
        purpose: "Issue → favorable evidence → adverse evidence → missing evidence → verified authority → requested resolution.",
        required: true,
      },
      {
        id: "core_contradiction",
        title: "Core Contradiction / Why the Decision Does Not Fit the Record",
        purpose: "Lead with the clearest mismatch between the agency reasoning and the individualized record.",
        required: true,
      },
      {
        id: "timeline",
        title: "Service / Medical / Functional Chronology",
        purpose: "Visual chronology preserving uncertain dates and linking each event to its source.",
        required: true,
      },
      {
        id: "point_by_point",
        title: "Point-by-Point Rebuttal",
        purpose: "For each adverse finding: agency finding → omitted evidence → contrary/supporting evidence → analysis → reviewer question.",
        required: true,
      },
      {
        id: "favorable",
        title: "Strongest Favorable Evidence",
        purpose: "Ranked evidence cards with provider/date/source/page, exact quote when verified, and relevance explanation.",
        required: true,
      },
      {
        id: "adverse_reconciliation",
        title: "Adverse-Evidence Reconciliation",
        purpose: "Address material unfavorable evidence directly; contextualize or rebut it only when the record supports doing so.",
        required: true,
      },
      {
        id: "functional",
        title: "Functional Capacity / Reliability",
        purpose: "Focus on duration, recovery, off-task time, attendance, pace, safety, endurance, and predictable access to work-like function.",
        required: true,
      },
      {
        id: "visuals",
        title: "Visual Evidence + Mechanism Walkthrough",
        purpose: "Source screenshots, diagrams, body maps, injury/aggravation pathways, and clearly labeled educational reconstructions.",
        required: false,
      },
      {
        id: "questions",
        title: "Reviewer Questions",
        purpose: "Short, concrete questions that force reconciliation of the strongest record evidence with the adverse finding.",
        required: false,
      },
      {
        id: "requested_action",
        title: "Requested Action",
        purpose: "Primary requested relief plus a narrower alternative when appropriate.",
        required: true,
      },
      {
        id: "source_index",
        title: "Source Index + Filing Notes",
        purpose: "Neutral filenames, provider/date, key pages, purpose, and notice that complete originals remain controlling.",
        required: true,
      },
      {
        id: "appendix",
        title: "Selected Primary-Source Exhibits",
        purpose: "Only the most useful pages are embedded; complete originals remain in the evidence repository.",
        required: true,
      },
    ],
  },
  {
    id: "aj_concise_filing",
    name: "AJ Concise Filing Packet",
    description:
      "Shorter reviewer-first packet that keeps the established AJ logic but minimizes duplicated exhibits for portals with tight size or page limits.",
    sections: [
      {
        id: "cover",
        title: "Cover + Read-First Note",
        purpose: "Identify the veteran, matter, controlling submission, and superseded drafts.",
        required: true,
      },
      {
        id: "executive",
        title: "Executive Evidence Roadmap",
        purpose: "Requested outcome, strongest 3–5 evidence points, central contradiction, and source links.",
        required: true,
      },
      {
        id: "issue_matrix",
        title: "Issue-by-Issue Matrix",
        purpose: "Agency finding → omitted/contrary evidence → why it matters → requested resolution.",
        required: true,
      },
      {
        id: "timeline",
        title: "Focused Chronology",
        purpose: "Only dates needed to understand the contested issue.",
        required: true,
      },
      {
        id: "point_by_point",
        title: "Focused Rebuttal",
        purpose: "Compact source-backed response to the material adverse findings.",
        required: true,
      },
      {
        id: "requested_action",
        title: "Requested Action",
        purpose: "Clear primary and alternative disposition.",
        required: true,
      },
      {
        id: "source_index",
        title: "Source Index / Repository Links",
        purpose: "Key pages plus direct paths to complete originals.",
        required: true,
      },
    ],
  },
];

export const AJ_PACKET_PRESENTATION_RULES = [
  "Use a polished reviewer-facing PDF, not raw AI prose.",
  "Lead with a cover/read-first page, roadmap, and executive advocacy summary.",
  "Use the pattern: agency finding → omitted evidence → contrary/supporting evidence → analysis → reviewer question.",
  "Keep source filename, provider/date, page/locator, and evidence class visible on important evidence cards.",
  "Use exact quotations only after literal source verification.",
  "Separate records-prove facts, claimant/witness reports, evidence-suggests interpretations, and unknown/missing items.",
  "Use screenshots and visual exhibits selectively so each disputed point can be independently verified.",
  "Repeat a source screenshot when necessary for independent verification of a separate issue, but do not dump full records into the packet.",
  "Keep complete originals in the evidence repository; packet excerpts are convenience copies and the originals control.",
  "Use visual chronology, evidence-convergence tables, diagrams/body maps, and educational reconstructions when they clarify the record.",
  "Label derived visuals as illustrations/reconstructions, never as original medical imaging.",
  "Address adverse evidence directly; do not hide it or give it gratuitous prominence.",
  "Preserve claimant voice for firsthand history while separating it from clinician findings and AI interpretation.",
  "Prioritize functional reliability: duration, recovery, off-task time, attendance, pace, safety, endurance, and variability.",
  "Use descriptive filenames with date/version labels and create portal-safe compressed variants when needed.",
  "Validate the exact final PDF size; target an UNDER5MB variant when a filing portal requires it.",
];

export const AJ_EVIDENCE_CARD_TEMPLATE = {
  fields: [
    "Issue / proposition",
    "Source file",
    "Provider / author",
    "Date",
    "Page / locator",
    "Evidence classification",
    "Verified quote or faithful paraphrase",
    "Why it matters",
    "Agency finding addressed",
    "Reviewer question",
  ],
};

export const AJ_REBUTTAL_BLOCK_TEMPLATE = {
  order: [
    "Agency finding",
    "What the finding leaves out",
    "Contrary or qualifying evidence",
    "Source trace",
    "Why the omission matters",
    "Reviewer question",
    "Requested resolution",
  ],
};
