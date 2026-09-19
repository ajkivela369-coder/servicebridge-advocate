from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


EVIDENCE_KINDS = (
    "exact_quote",
    "paraphrase",
    "claimant_report",
    "clinician_observation",
    "objective_test",
    "medical_opinion",
    "agency_finding",
    "analyst_synthesis",
)


PROGRAM_SECTIONS = {
    "VA / VBA": (
        "requested_action",
        "issues_presented",
        "duty_status_chronology",
        "favorable_evidence_map",
        "objective_findings",
        "direct_secondary_aggravation_analysis",
        "functional_reliability",
        "governing_authorities",
        "focused_development_questions",
        "cited_source_appendix",
        "requested_disposition",
    ),
    "Social Security (SSDI / SSI)": (
        "requested_action",
        "alleged_onset_and_duration",
        "five_step_framework",
        "medically_determinable_impairments",
        "severity_and_listings_when_raised",
        "objective_and_symptom_evidence",
        "medical_opinions",
        "rfc_by_function",
        "past_relevant_work",
        "other_work_analysis",
        "sustained_work_reliability",
        "governing_authorities",
        "cited_source_appendix",
        "requested_disposition",
    ),
    "New Hampshire": (
        "requested_action",
        "state_program_standard",
        "incorporated_federal_standard_only_if_applicable",
        "medical_and_functional_evidence",
        "state_specific_eligibility_elements",
        "governing_authorities",
        "cited_source_appendix",
        "requested_disposition",
    ),
}


@dataclass(frozen=True)
class PreflightResult:
    status: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


def agency_sections(program: str) -> tuple[str, ...]:
    return PROGRAM_SECTIONS.get(program, PROGRAM_SECTIONS["New Hampshire"])


def missing_record_interpretation(record_name: str, has_actual_adverse_finding: bool = False) -> str:
    name = record_name.strip() or "record"
    if has_actual_adverse_finding:
        return f"Review the actual adverse finding concerning the missing {name}; do not infer beyond its stated scope."
    return f"Missing {name} is a development gap, not affirmative negative evidence."


def classify_quote(proposed: str, source_text: str) -> str:
    proposed_clean = " ".join(proposed.split()).strip()
    source_clean = " ".join(source_text.split()).strip()
    if proposed_clean and proposed_clean in source_clean:
        return "exact_quote"
    return "paraphrase"


def dedupe_cited_sources(
    sources: Iterable[dict],
    cited_source_ids: Iterable[str],
) -> list[dict]:
    cited = {str(value) for value in cited_source_ids}
    seen: set[str] = set()
    output: list[dict] = []
    for source in sources:
        source_id = str(source.get("source_id") or source.get("name") or "")
        if not source_id or source_id not in cited or source_id in seen:
            continue
        seen.add(source_id)
        output.append(dict(source))
    return output


def submission_preflight(payload: dict) -> PreflightResult:
    blockers: list[str] = []
    warnings: list[str] = []

    authorities = payload.get("legal_authorities") or []
    issues = [str(issue).strip() for issue in payload.get("issues") or [] if str(issue).strip()]
    arguments = payload.get("arguments") or []
    appendix = payload.get("source_appendix") or []
    literature = payload.get("literature") or []

    if not authorities:
        blockers.append("No governing legal or program authorities were verified.")

    argument_issues = {str(item.get("issue") or "").strip() for item in arguments if isinstance(item, dict)}
    for issue in issues:
        if issue not in argument_issues:
            blockers.append(f"Requested issue lacks its own supported argument: {issue}")

    for index, argument in enumerate(arguments, start=1):
        if not isinstance(argument, dict):
            blockers.append(f"Argument {index} is malformed.")
            continue
        citations = [str(value).strip() for value in argument.get("source_citations") or [] if str(value).strip()]
        if not citations:
            blockers.append(f"Argument {index} has no claimant-record citation.")
        if argument.get("requires_pinpoint") and not argument.get("has_pinpoint"):
            warnings.append(f"Argument {index} needs a more precise source locator.")

    source_ids = [str(item.get("source_id") or item.get("name") or "") for item in appendix if isinstance(item, dict)]
    nonempty_ids = [value for value in source_ids if value]
    if len(nonempty_ids) != len(set(nonempty_ids)):
        warnings.append("Source appendix contains duplicate source identities.")

    if appendix:
        cited_count = sum(1 for item in appendix if isinstance(item, dict) and item.get("cited"))
        if cited_count / len(appendix) < 0.5:
            warnings.append("Most appendix entries are not cited in the filing; trim to the cited high-yield source set.")

    weak_literature = [
        item for item in literature
        if isinstance(item, dict) and float(item.get("relevance_score") or 0.0) < 0.65
    ]
    if weak_literature:
        warnings.append("One or more literature items are weakly matched and should be excluded rather than used as padding.")

    status = "Draft" if blockers else "Needs Review" if warnings else "Ready to Submit"
    return PreflightResult(status=status, blockers=tuple(blockers), warnings=tuple(warnings))
