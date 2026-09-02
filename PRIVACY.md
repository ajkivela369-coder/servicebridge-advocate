# Privacy and record-handling policy

ServiceBridge is designed for highly sensitive medical, military, employment, education, and
benefit records. A Git repository is not a medical-record system.

## Never commit

- source medical records or benefit files;
- Social Security, VA, DoD, insurance, claim, student, or patient identifiers;
- dates of birth, home addresses, private phone numbers, or personal email addresses;
- API keys, access tokens, passwords, cookies, or signed download URLs;
- extracted text, OCR, local search databases, model transcripts, or generated drafts containing
  protected information;
- third-party records without authorization.

The `.gitignore` covers common locations and extensions, and `scripts/check_public_repo.py` blocks
several common secret patterns and private-data directories. Neither can recognize every sensitive
file. Before every commit, inspect `git status` and the staged diff.

## Data flow

Prompt-only mode performs extraction, redaction, indexing, retrieval, and prompt construction on
the local computer. It does not call an AI provider.

OpenAI mode is opt-in. It transmits the constructed request and retrieved excerpts to the API and
sets `store=False`. That setting alone does not establish HIPAA, Privacy Act, agency, legal,
contractual, or organizational compliance. The operator must make that determination and use an
appropriately configured service.

## Redaction limits

The built-in redactor targets common structured identifiers. It does not reliably remove names,
facilities, unit information, exact dates, rare events, faces, handwriting, images, metadata, or
identifying combinations of facts. A human must review any document before it leaves the local
environment.

## Public examples

Only fictional or properly licensed synthetic records belong in this repository. Never “anonymize”
a real case merely by changing the person's name.

## Incident response

If sensitive information is committed, stop sharing the repository, rotate exposed credentials,
and remove the data from Git history. Deleting the latest copy is not enough because prior commits
retain content. Notify affected people and organizations when law, policy, or ethics requires it.