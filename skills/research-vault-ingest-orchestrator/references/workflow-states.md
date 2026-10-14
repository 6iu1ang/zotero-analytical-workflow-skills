# Workflow states

Process states are separate from Knowledge evidence roles and verification states.

| State | Meaning / next action |
| --- | --- |
| COMPLETE | Readable source PDF, validated Note/source links and applicable Knowledge decision/checks pass |
| ALREADY_COMPLETE | Same complete conditions already hold; no rewrite |
| NOTE_CREATED / NOTE_TEMPLATE_REPAIRED | Continue source and Knowledge checks |
| KNOWLEDGE_UPDATED / NO_KNOWLEDGE_CHANGE | Knowledge decision succeeded; final checks/log |
| NOTE_DEFERRED / PARTIAL_NOTE_MISSING | Source or Note work remains |
| PDF_NOT_FOUND / PDF_UNREADABLE | Resolve actual source problem; retry |
| SOURCE_VERIFICATION_FAILED / VALIDATION_FAILED | Fix the failing contract; do not declare success |
| KEY_CONFLICT / MANUAL_REVIEW_REQUIRED | Resolve ambiguous identity |
| SCHEMA_REVIEW_REQUIRED | Evidence needs an explicit schema migration |

`FULLTEXT_DEFERRED`, `PARTIAL_FULLTEXT_MISSING`, `FULLTEXT_FAILED` and `MINERU_FAILED` are historical states. Preserve old logs; inspect and revalidate each affected paper before appending a current result. No conversion is needed solely to retire a historical Fulltext state.

PDF-only precision reading can be complete within that mode without claiming Zotero ingestion.
