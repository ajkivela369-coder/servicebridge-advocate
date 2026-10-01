# SearchSignal v2 synchronization status
Checked September 30, 2026 (America/New_York).

## Completed
Local WordPress acceptance code, machine-readable results, browser evidence,
and Playground launch results are now collected in wordpress-lab/.
See wordpress-lab/ACCEPTANCE.md for exact scope and remaining boundaries.

## Live source comparison blocked
Floot project: beaa0fb7-7532-4b8f-a5e6-9dbf049757d4.
The source-list request was refused because the account reached its daily
100 build-action limit. The reported reset is 2026-10-01 18:00 UTC
(October 1 at 2 p.m. Eastern).
No alternate access was used to bypass that limit.

The existing source/ directory has six snapshot files. It is not an
authoritative v2 export. Live-to-repository parity has NOT been verified.
Do not replace it with the older local Express demo or call v2 sync complete.

## Resume after source access is available
1. Export the current Floot file tree and version; read all app-owned source.
2. Compare and mirror crawler, document audit, redirect validation,
   context-aware GEO, schema, analytics, and UI files, including new endpoints.
3. Preserve runtime/dependency metadata and record hashes and source version.
4. Run Portfolio QC and relevant live smoke checks; inspect CI on the new commit.
5. Update README and build history only for behavior actually observed.

## Existing CI
At base commit abcace87fa0b7760593c1467a0e4e5f7e192e124,
Portfolio Quality Control, CI, and AI Evaluation Portfolio CI all succeeded.
