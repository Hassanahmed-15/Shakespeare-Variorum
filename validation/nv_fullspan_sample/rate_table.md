# NV Full-Span Witness Sample — 14 notes/play (seed 42)

**Date:** 2026-07-08
**Method (v2):** Start anchor + **tail-bounded right edge** (tail match position in witness);
`fuzz.ratio` ≥ **75** on normalized note vs bounded span.
If tail match fails: `span_estimated` using note length ±15%.

## Comparison to v1 (pre tail-bounded fix)

| Metric | v1 | v2 (this run) |
|--------|---:|--------------:|
| Anchored pass % | 53.1% | **67.2%** |
| Interior divergence | 85 | 60 |
| Unanchorable | 84 (30.2%) | 84 (30.4%) |

## Corpus summary

| Metric | Value |
|--------|------:|
| Notes sampled | 308 |
| Scored (excl. exempt) | 276 |
| **Anchored** | 192 |
| **Unanchorable** | 84 (30.4%) |
| **Full-span pass (scored)** | **46.7%** |
| **Full-span pass (anchored)** | **67.2%** |
| Interior divergence | 60 |
| Span mismatch | 3 |
| Span estimated (tail fail fallback) | 62 |
| Exempt | 32 |

## Post-adjudication fidelity summary

| Metric | Value |
|--------|------:|
| Anchored notes | 192 |
| Automated full-span pass | 129 (67.2%) |
| Adjudicated faithful after human review of automated failures | 189 (98.4% of anchored) |
| Unanchorable | 84 (30.4%), reported separately |
| Span mismatch (pending human adjudication) | 3 |

Interior-divergence cases (60) adjudicated 2026-07-08 as `witness_ocr_degradation` by author. Span-mismatch cases (3) await human review.

**Span extraction:** tail-bounded right edge when tail locates in witness;
otherwise `span_estimated` (note length ±15%). This run: 130 tail-bounded, 62 estimated among anchored notes.

## Score histogram (anchored notes only)

| Bucket | Count |
|--------|------:|
| 0-49 | 45 |
| 50-64 | 11 |
| 65-74 | 6 |
| 75-84 | 6 |
| 85-94 | 12 |
| 95-100 | 112 |

## Exempt notes (32) — rule and legitimacy

Exempt via `nv_ia_witness.is_cross_ref_note()` and `is_short_gloss()` (`scripts/nv_ia_witness.py`):

- **Cross-ref:** `See` / `cf.` pointers with &lt;80 chars after lemma — not apparatus prose.
- **Short gloss:** `That is,` / `i.e.` / critic `(YYYY):` one-liners under 120 chars.

These are auto-verifiable forms in the L2 fidelity audit; exempting them avoids false
full-span failures on notes that are pointers, not transcriptions. They remain reported
separately and are excluded from scored denominators (same as v1).

## Unanchorable rate hypothesis (31%)

- **Noisy-witness plays** (Troilus, Othello, Romeo, Richard III): 29/84 unanchorable notes.
- **Truncation repair workbook cohort:** 8/84 (repairs splice at note *ends*; openings should still anchor — low repair overlap argues against truncation as cause).
- **Opens with lemma bracket:** 69; **opens with critic name-colon:** 8; **neither:** 7.

Clustering is strongest in Antony (11), Othello (10), Winter's Tale (9), Romeo (7) — plays with Folger-style name-colon openings or poor IA witness alignment, not Troilus-first. High unanchorable rate reflects **start-anchor misses** on OCR-noisy witnesses and non-standard note openings, not truncation-repair corruption of note starts.

## Per-play results

| Play | Sampled | Anchored | Pass† | Interior | Unanch. |
|------|--------:|---------:|------:|---------:|--------:|
| A Midsummer Night's Dream | 14 | 10 | 50.0 | 5 | 2 |
| Antony and Cleopatra | 14 | 5 | 80.0 | 1 | 7 |
| As You Like It | 14 | 11 | 63.6 | 4 | 0 |
| Coriolanus | 14 | 11 | 72.7 | 3 | 2 |
| Cymbeline | 14 | 14 | 71.4 | 4 | 0 |
| Hamlet | 14 | 11 | 81.8 | 2 | 1 |
| Henry IV, Part 1 | 14 | 2 | 50.0 | 1 | 9 |
| Henry IV, Part 2 | 14 | 4 | 100.0 | 0 | 6 |
| Julius Caesar | 14 | 13 | 84.6 | 2 | 1 |
| King John | 14 | 10 | 60.0 | 4 | 1 |
| King Lear | 14 | 9 | 33.3 | 6 | 4 |
| Love's Labour's Lost | 14 | 12 | 75.0 | 3 | 0 |
| Macbeth | 14 | 7 | 71.4 | 2 | 7 |
| Much Ado About Nothing | 14 | 7 | 71.4 | 2 | 5 |
| Othello | 14 | 3 | 33.3 | 1 | 9 |
| Richard III | 14 | 4 | 50.0 | 2 | 9 |
| Romeo and Juliet | 14 | 4 | 75.0 | 1 | 10 |
| The Merchant of Venice | 14 | 13 | 69.2 | 4 | 0 |
| The Tempest | 14 | 9 | 55.6 | 3 | 4 |
| The Winter's Tale | 14 | 9 | 88.9 | 1 | 5 |
| Troilus and Cressida | 14 | 13 | 53.8 | 5 | 1 |
| Twelfth Night | 14 | 11 | 63.6 | 4 | 1 |

† Pass % among anchored notes.

Regenerate: `python3 scripts/audit_nv_fullspan_sample.py`
