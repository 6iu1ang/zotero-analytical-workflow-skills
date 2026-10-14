# Ingest gates

| Gate | Pass condition | Failure |
| --- | --- | --- |
| State inspection | Actual artifacts, history and coverage classified by stable identity | VALIDATION_FAILED / MANUAL_REVIEW_REQUIRED |
| Identity/source | Confirmed parent and attachment for Zotero mode; actual supplied PDF for PDF-only mode | PDF_NOT_FOUND / PDF_UNREADABLE / KEY_CONFLICT |
| Original evidence | Readable PDF, verified source identity and actual quotations/context/pages | SOURCE_VERIFICATION_FAILED |
| Analytical Note | Correct template, source links, metadata and finding/quote pairs | NOTE_FAILED / NOTE_DEFERRED / NOTE_TEMPLATE_REPAIR_REQUIRED |
| Source validation | Note source resolves, identifiers/hash agree; declared optional archive links resolve | VALIDATION_FAILED |
| Knowledge | Justified update or NO_KNOWLEDGE_CHANGE, coverage and source checks where applicable | SCHEMA_REVIEW_REQUIRED / VALIDATION_FAILED |
| Final | All applicable checks pass, then append result | VALIDATION_FAILED |

No MinerU/Fulltext creation gate exists. Empty `fulltext_path` is valid. `fulltext_verified` requires actual original-source verification (PDF or an existing archive), never a summary alone. Stop downstream writes on a failed required gate.
