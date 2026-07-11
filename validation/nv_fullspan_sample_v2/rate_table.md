# NV Full-Span Witness Sample — 14 notes/play (seed 42)

**Date:** 2026-07-11
**Method (v2):** Start anchor + **tail-bounded right edge** (tail match position in witness);
`fuzz.ratio` ≥ **75** on normalized note vs bounded span.
If tail match fails: `span_estimated` using note length ±15%.

## Comparison to v1 (pre tail-bounded fix)

| Metric | v1 | v2 (this run) |
|--------|---:|--------------:|
| Anchored pass % | 53.1% | **78.4%** |
| Interior divergence | 85 | 40 |
| Unanchorable | 84 (30.2%) | 70 (26.5%) |

## Corpus summary

| Metric | Value |
|--------|------:|
| Notes sampled | 294 |
| Scored (excl. exempt) | 264 |
| **Anchored** | 194 |
| **Unanchorable** | 70 (26.5%) |
| **Full-span pass (scored)** | **57.6%** |
| **Full-span pass (anchored)** | **78.4%** |
| Interior divergence | 40 |
| Span mismatch | 2 |
| Span estimated (tail fail fallback) | 49 |
| Exempt | 30 |

## Post-adjudication fidelity summary

| Metric | Value |
|--------|------:|
| Anchored notes | 194 |
| Automated full-span pass | 152 (78.4%) |
| Adjudicated faithful after human review of automated failures | 192 (99.0% of anchored) |
| Unanchorable | 70 (26.5%), reported separately |
| Span mismatch (pending human adjudication) | 2 |

Interior-divergence cases (40) adjudicated 2026-07-08 as `witness_ocr_degradation` by author. Span-mismatch cases (2) await human review.

**Span extraction:** tail-bounded right edge when tail locates in witness;
otherwise `span_estimated` (note length ±15%). This run: 145 tail-bounded, 49 estimated among anchored notes.

## Score histogram (anchored notes only)

| Bucket | Count |
|--------|------:|
| 0-49 | 33 |
| 50-64 | 6 |
| 65-74 | 3 |
| 75-84 | 3 |
| 85-94 | 19 |
| 95-100 | 130 |

## Exempt notes (30) — rule and legitimacy

Exempt via `nv_ia_witness.is_cross_ref_note()` and `is_short_gloss()` (`scripts/nv_ia_witness.py`):

- **Cross-ref:** `See` / `cf.` pointers with &lt;80 chars after lemma — not apparatus prose.
- **Short gloss:** `That is,` / `i.e.` / critic `(YYYY):` one-liners under 120 chars.

These are auto-verifiable forms in the L2 fidelity audit; exempting them avoids false
full-span failures on notes that are pointers, not transcriptions. They remain reported
separately and are excluded from scored denominators (same as v1).

## Unanchorable rate hypothesis (31%)

- **Noisy-witness plays** (Troilus, Othello, Romeo, Richard III): 29/70 unanchorable notes.
- **Truncation repair workbook cohort:** 4/70 (repairs splice at note *ends*; openings should still anchor — low repair overlap argues against truncation as cause).
- **Opens with lemma bracket:** 58; **opens with critic name-colon:** 6; **neither:** 6.

Clustering is strongest in Antony (11), Othello (10), Winter's Tale (9), Romeo (7) — plays with Folger-style name-colon openings or poor IA witness alignment, not Troilus-first. High unanchorable rate reflects **start-anchor misses** on OCR-noisy witnesses and non-standard note openings, not truncation-repair corruption of note starts.

## Per-play results

| Play | Sampled | Anchored | Pass† | Interior | Unanch. |
|------|--------:|---------:|------:|---------:|--------:|
| A Midsummer Night's Dream | 14 | 14 | 64.3 | 4 | 0 |
| Antony and Cleopatra | 14 | 8 | 50.0 | 4 | 6 |
| As You Like It | 14 | 13 | 84.6 | 2 | 0 |
| Coriolanus | 14 | 12 | 83.3 | 2 | 1 |
| Cymbeline | 14 | 11 | 81.8 | 2 | 2 |
| Hamlet | 14 | 11 | 63.6 | 4 | 1 |
| Henry IV, Part 1 | 14 | 8 | 37.5 | 4 | 4 |
| Henry IV, Part 2 | 14 | 8 | 62.5 | 3 | 3 |
| Julius Caesar | 14 | 13 | 92.3 | 1 | 1 |
| King John | 14 | 10 | 90.0 | 1 | 1 |
| King Lear | 14 | 10 | 60.0 | 4 | 4 |
| Love's Labour's Lost | 14 | 12 | 75.0 | 3 | 1 |
| Macbeth | 14 | 6 | 83.3 | 1 | 8 |
| Much Ado About Nothing | 14 | 8 | 100.0 | 0 | 1 |
| Othello | 14 | 5 | 80.0 | 1 | 9 |
| Richard III | 14 | 2 | 100.0 | 0 | 11 |
| Romeo and Juliet | 14 | 5 | 100.0 | 0 | 9 |
| The Merchant of Venice | 14 | 10 | 90.0 | 1 | 0 |
| The Tempest | 14 | 9 | 77.8 | 2 | 4 |
| The Winter's Tale | 14 | 7 | 100.0 | 0 | 4 |
| Twelfth Night | 14 | 12 | 91.7 | 1 | 0 |

† Pass % among anchored notes.

Regenerate: `python3 scripts/audit_nv_fullspan_sample.py`
