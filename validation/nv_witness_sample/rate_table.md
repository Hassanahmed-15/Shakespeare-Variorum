# NV Witness Sample Audit — 50 notes/play (act-stratified)

**Date:** 2026-07-08
**Method:** Span-anchored comparison vs Internet Archive OCR witness(es) per play.
**Sample:** Up to 50 notes per play, spread across acts.

## Corpus summary (sample estimate)

| Metric | Value |
|--------|------:|
| Plays | 22 |
| Notes sampled | 1100 |
| Scored (excl. cross-ref/gloss) | 983 |
| Located in witness (verifiable) | 391 (39.8%) |
| **Accuracy (verifiable notes, strict)** | **77.5%** |
| Accuracy (verifiable, + OCR tolerance) | 83.1% |
| Defective (verifiable only) | 16.9% |
| Unverifiable (witness locate failed) | 60.2% |
| Exempt (cross-ref / short gloss) | 117 |

Approx. 95% CI on strict accuracy among verifiable notes: ±4.1 percentage points.

## Verdict definitions

- **faithful** — start and end anchored in witness; ≥82% word overlap; no continuation past end
- **ocr_ok** — anchored; 65–82% overlap (likely OCR noise)
- **defective** — truncated, apparatus splice, extra content, text drift, or not in witness
- **uncertain** — opening matches witness but span not confirmed
- **exempt** — cross-reference or short gloss (auto-verifiable form)

## Per-play results

| Play | Sampled | Acts | Verifiable | Strict† | Lenient† | Defect† | Unverif. |
|------|--------:|-----:|-----------:|--------:|---------:|--------:|---------:|
| A Midsummer Night's Dream | 50 | 5 | 23 | 87.0 | 87.0 | 13.0 | 48.9 |
| Antony and Cleopatra | 50 | 5 | 5 | 100.0 | 100.0 | 0.0 | 88.9 |
| As You Like It | 50 | 5 | 40 | 97.5 | 100.0 | 0.0 | 13.0 |
| Coriolanus | 50 | 5 | 23 | 87.0 | 87.0 | 13.0 | 53.1 |
| Cymbeline | 50 | 5 | 25 | 84.0 | 84.0 | 16.0 | 45.7 |
| Hamlet | 50 | 5 | 18 | 72.2 | 72.2 | 27.8 | 58.1 |
| Henry IV, Part 1 | 50 | 5 | 7 | 57.1 | 71.4 | 28.6 | 82.5 |
| Henry IV, Part 2 | 50 | 5 | 7 | 85.7 | 85.7 | 14.3 | 81.6 |
| Julius Caesar | 50 | 5 | 24 | 87.5 | 95.8 | 4.2 | 51.0 |
| King John | 50 | 5 | 18 | 88.9 | 88.9 | 11.1 | 61.7 |
| King Lear | 50 | 5 | 28 | 78.6 | 85.7 | 14.3 | 33.3 |
| Love's Labour's Lost | 50 | 5 | 22 | 72.7 | 77.3 | 22.7 | 45.0 |
| Macbeth | 50 | 5 | 7 | 85.7 | 100.0 | 0.0 | 85.1 |
| Much Ado About Nothing | 50 | 5 | 22 | 77.3 | 86.4 | 13.6 | 47.6 |
| Othello | 50 | 5 | 9 | 88.9 | 100.0 | 0.0 | 80.9 |
| Richard III | 50 | 5 | 5 | 20.0 | 20.0 | 80.0 | 89.4 |
| Romeo and Juliet | 50 | 5 | 0 | None | None | None | 100.0 |
| The Merchant of Venice | 50 | 5 | 23 | 78.3 | 82.6 | 17.4 | 46.5 |
| The Tempest | 50 | 5 | 12 | 66.7 | 91.7 | 8.3 | 73.3 |
| The Winter's Tale | 50 | 5 | 8 | 87.5 | 87.5 | 12.5 | 80.5 |
| Troilus and Cressida | 50 | 5 | 29 | 17.2 | 24.1 | 75.9 | 39.6 |
| Twelfth Night | 50 | 5 | 36 | 83.3 | 97.2 | 2.8 | 18.2 |

† Strict / Lenient / Defect percentages are among **verifiable** notes only.

## Caveats

- Rates are **sample estimates**, not a census of all ~23,738 notes.
- Witness text is OCR from Internet Archive scans; lenient bucket absorbs typical OCR variance.
- Multi-volume plays search several cached witnesses; some defects may still hide between volumes.

Regenerate: `python3 scripts/audit_nv_witness_sample.py`
