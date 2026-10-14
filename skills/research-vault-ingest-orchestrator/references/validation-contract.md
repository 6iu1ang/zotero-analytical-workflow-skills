# Validation contract

## Required source and Note checks

- Zotero mode: unique parent Key and confirmed PDF attachment Key; PDF-only mode: actual supplied source without invented keys.
- PDF path resolves, PDF is readable, source identity matches; recorded SHA256 still matches.
- Note exists, uses the canonical template, has no placeholders, preserves source and note paths.
- Actual PDF/local or Zotero entry is usable; every finding has a real quotation and checked context.
- PDF pages are provided only after actual verification. Formula delimiters, definitions, units and figure/table details receive appropriate checks.
- Real related-note links resolve. No formal Fulltext file, image directory or reciprocal archive link is required.

Existing archive links are optional: if declared, check path/identity consistency rather than creating a replacement. An absent archive is NOT_REQUIRED, not a passed archival test or a deferred required stage.

## Knowledge checks

When applicable, check real source links, identity, claim/gap sidecars, statement drift, evidence counts, roles, template/schema, alias conflicts and relation conditions. `fulltext_verified` requires targeted original-PDF or existing-original-text verification for that particular claim; record the actual source locator in the existing evidence/log structure. A Note-only summary remains `note_supported`; interpretation remains labelled.

Use an available Knowledge validator and require exit code 0. If no official script is supplied, report local contract checks and the official-validator limitation honestly. Do not disable checks because MinerU was removed.

COMPLETE requires all applicable source, Note and Knowledge gates; missing MinerU Markdown never makes an otherwise complete PDF workflow partial.
