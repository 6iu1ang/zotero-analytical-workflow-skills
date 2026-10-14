# Production ingest pipeline

Accept only a user-specified paper; do not discover or download unrelated papers.

1. Inspect actual Note, original PDF, prior logs and Knowledge coverage by stable identity.
2. Resolve Zotero parent/attachment identity with `zotero-data-fetcher`, or use the supplied PDF without invented Zotero identity.
3. Read the original PDF; verify quotations, context, pages, formulas and relevant figures.
4. Reuse or create/repair the same Analytical Note with `zotero-analytical-writer` and the canonical template.
5. Validate Note → original PDF path/URI, identity, source hash and source evidence. Existing Fulltext links are optional and checked only if declared.
6. Use `research-vault-knowledge-maintainer` for a justified Knowledge decision and necessary update.
7. Validate applicable contracts and append the result to the process log.

Formal MinerU conversion/archive is outside normal ingest. Do not install MinerU or call a conversion API during reading. Existing archives remain usable. A separately explicit archival request should use a user-selected archival tool; this bundle does not ship one.
