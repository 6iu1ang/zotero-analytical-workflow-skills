# ResearchVault architecture

```text
Original Zotero/user PDF (primary evidence)
              ↑ source_file / actual PDF URI / verified pages
Analytical Note (single-paper structured understanding)
              ↑ real source_notes
Knowledge (derived cross-paper navigation and synthesis)
```

Vault root: `config.vault_root` 所指定的实际 Vault. Use existing folders and indexes; do not assume `02vault` or initialize architecture during inspection. Parent `zotero_key` and PDF `pdf_key` are stable identities when confirmed.

Normal evidence trace is Knowledge → Analytical Note → original PDF. Existing `03fulltext` archives are optional aids, kept separate from Notes and excluded from ordinary paper indexes. A file hit is not a new paper. No formal MinerU archive is produced or required by ingestion.
