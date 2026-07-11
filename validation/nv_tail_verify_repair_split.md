# Tail-verify repair cohort split

**Date:** 2026-07-08

> **Note:** `nv_tail_verify_all_plays.json` contains per-play totals only, not per-note
> pass/fail. This split re-scores each note with identical `verify_all_notes.py` logic.

Repair manifest: `contractor_truncation_workbook.json` (927 entries)

## Two-group split

| Cohort | Notes | Pass | Fail | Pass % |
|--------|------:|-----:|-----:|-------:|
| Never in workbook | 22,802 | 22,303 | 499 | **97.81%** |
| Workbook-flagged (repair cohort) | 913 | 891 | 22 | **97.59%** |
| **Full corpus** | 23,715 | 23,194 | 521 | **97.8%** |

## Workbook status (matched entries)

| Status | n | Pass % |
|--------|--:|-------:|
| complete | 817 | 98.65% |
| gap_marked | 15 | 33.33% |
| no_change_needed | 81 | 98.77% |

## Spliced notes only (`complete` + text changed in workbook)

| n | Pass | Fail | Pass % |
|--:|-----:|-----:|-------:|
| 817 | 806 | 11 | **98.65%** |

Workbook entries not matched in current corpus: 14

Full auditable cross-ref: `nv_tail_verify_repair_split.json` → `workbook_crossref`
