# Validation & Paper Materials

This directory holds the methods paper, reproducibility artifacts, and audit scripts referenced in *Full Fathom Five: Transforming the New Variorum Shakespeare Through Computational Access*.

## Paper

| File | Description |
|------|-------------|
| [`humanize_workspace/draft.md`](humanize_workspace/draft.md) | Current paper draft (Markdown) |
| [`paper_extract.txt`](paper_extract.txt) | Plain-text export of the paper PDF for search/audit |

## Key audits (results)

| Directory / file | What it verifies |
|------------------|------------------|
| [`nv_lineation_alignment.json`](nv_lineation_alignment.json) / [`.md`](nv_lineation_alignment.md) | MIT reading text ↔ Variorum key alignment (click simulation) |
| [`nv_fidelity_all_plays_no_troilus.json`](nv_fidelity_all_plays_no_troilus.json) | Corpus-wide NV fidelity rates |
| [`nv_fullspan_sample/`](nv_fullspan_sample/) | Stratified full-span witness sample |
| [`nv_tail_verify_repair_split.md`](nv_tail_verify_repair_split.md) | Tail-boundary verification by repair class |
| [`fff_citation_audit/`](fff_citation_audit/) | Onions / Schmidt / LEME citation accuracy sample |
| [`paper_bib_audit/`](paper_bib_audit/) | Bibliography citation map |
| [`othello_folger_alignment_stats.json`](othello_folger_alignment_stats.json) | Folger TEI alignment metrics (Othello) |
| [`reports/`](reports/) | Supplementary audit write-ups |

## Scripts (repo root `scripts/`)

Run from repository root:

```bash
python3 scripts/audit_lineation_alignment.py
python3 scripts/audit_nv_fidelity_all_plays.py
python3 scripts/audit_nv_truncation.py
python3 scripts/audit_fff_citation_accuracy.py
python3 scripts/audit_othello_folger_alignment.py
```

See individual script headers for inputs, outputs, and CLI flags.

## Live platform

- **Site:** [newvariorum.com](https://newvariorum.com)
- **Archival deposit:** [Zenodo 10.5281/zenodo.21126208](https://doi.org/10.5281/zenodo.21126208)
