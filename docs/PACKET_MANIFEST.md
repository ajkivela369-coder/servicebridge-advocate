# Submission PDF assembly

The `servicebridge packet` CLI preserves selected PDF pages, including image diagrams, screenshots, and URL annotations. It does not turn an AI draft into medical or legal evidence. Use the original record pages and review each selection.

Install the document extra (`pip install -e '.[documents]'`). Write a local manifest beside the PDFs:

```json
{
  "jurisdiction": "VA and New Hampshire APTD - separate legal sections",
  "items": [
    {"path": "cover.pdf", "pages": [1], "kind": "record", "label": "Cover and evidence index"},
    {"path": "clinical.pdf", "pages": [2, 5], "kind": "record", "label": "Clinical findings"},
    {"path": "injury-diagram.pdf", "pages": [1], "kind": "diagram", "label": "Illustration - interpretation, not imaging"},
    {"path": "history-screenshots.pdf", "pages": [1], "kind": "screenshot", "label": "Dated medical history"},
    {"path": "law.pdf", "pages": [1], "kind": "law", "label": "Applicable law", "citation": "Verified citation, jurisdiction and access date"}
  ]
}
```

Run `servicebridge packet build manifest.json submission.pdf --max-mb 5 --report packet-qa.json` and retain the JSON output as the page provenance map. Exit status 2 means the output exceeds the size limit or contains a non-HTTP URL annotation. `servicebridge packet check submission.pdf` reports image pages, textless pages, and preserved clickable links. A textless scan needs visual review and possibly OCR; it is not automatically defective. Assemble VA and state disability legal sections deliberately and verify the current text and applicability before sending. Keep private records outside the public repository.
