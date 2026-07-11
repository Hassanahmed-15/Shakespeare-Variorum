# Tail-verify repair cohort split

**Date:** 2026-07-11

nv_tail_verify_all_plays.json stores per-play aggregates only; workbook cohort scored per-note; untouched cohort derived by subtraction from corpus census totals.

**Excluded plays (1):** Troilus and Cressida

Repair manifest: `contractor_truncation_workbook.json` (927 entries, 89 excluded, 818 matched in current corpus)

## Two-group split

| Cohort | Notes | Pass | Fail | Pass % |
|--------|------:|-----:|-----:|-------:|
| Never in workbook | 22,276 | 21,910 | 366 | **98.36%** |
| Workbook-flagged (repair cohort) | 818 | 805 | 13 | **98.41%** |
| Full corpus (census) | 23,094 | 22,715 | 379 | **98.36%** |

## By workbook status

| Status | n | Pass % |
|--------|--:|-------:|
| complete | 730 | 98.9% |
| gap_marked | 9 | 44.44% |
| no_change_needed | 79 | 100.0% |

## Spliced only (`complete` + text changed)

| n | Pass | Fail | Pass % |
|--:|-----:|-----:|-------:|
| 730 | 722 | 8 | **98.9%** |

Auditable per-note cross-ref: `nv_tail_verify_repair_split_v2.json` → `workbook_crossref`
