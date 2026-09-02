from __future__ import annotations

from .models import AdvocacyRequest, AdvocacyResponse, RetrievalHit
from .policies import instructions_for
from .providers import PromptOnlyProvider, TextProvider
from .store import EvidenceStore


class Advocate:
    def __init__(self, store: EvidenceStore, provider: TextProvider | None = None):
        self.store = store
        self.provider = provider or PromptOnlyProvider()

    def answer(self, request: AdvocacyRequest) -> AdvocacyResponse:
        hits = self.store.search(request.question, limit=request.top_k)
        warnings: list[str] = []
        if not hits:
            warnings.append("No matching source excerpts were retrieved; do not treat the output as record-grounded.")

        instructions = instructions_for(request.lane, request.mode)
        input_text = self._build_input(request, hits)
        answer = self.provider.generate(instructions=instructions, input_text=input_text)
        return AdvocacyResponse(
            answer=answer,
            citations=[hit.citation for hit in hits],
            retrieved_chunks=len(hits),
            model=self.provider.model,
            warnings=warnings,
        )

    @staticmethod
    def _build_input(request: AdvocacyRequest, hits: list[RetrievalHit]) -> str:
        evidence = "\n\n".join(
            f"[{hit.chunk.source_id}; {hit.chunk.locator}; {hit.chunk.evidence_class.value}]\n"
            f"Title: {hit.title}\n{hit.chunk.text}"
            for hit in hits
        ) or "[No source excerpts retrieved]"
        return f"""TASK
Question: {request.question}
Benefit lane: {request.lane.value}
Audience: {request.audience}
Requested output: {request.requested_output}

REQUIRED OUTPUT DISCIPLINE
- Lead with the answer or requested draft.
- Mark record-supported facts with [source_id; locator].
- Separately identify: records prove; claimant/witnesses report; evidence suggests; gaps.
- If drafting for an external audience, omit private strategy and speculative adverse arguments.
- End with concrete next steps only when useful.

RETRIEVED EVIDENCE
{evidence}
"""
