# NV Stage-1 vs Stage-2 Witness Ablation (300-note sample)

**Date:** 2026-07-10

## Sample

- Notes: **300** stratified across **22** plays
- Seed: **42**

## Text sources

- **Stage 1:** Earliest *.pre_*_repair.backup per deployed JSON (ingest OCR layer on disk)
- **Stage 2:** Deployed Public/Data JSON (current corrected corpus)

**Limitation:** True Tesseract/ABBYY-only stage-1 JSON is not archived separately.
Stage 1 here is the **earliest `*.pre_*_repair.backup`** per play—the least post-processed
note text on disk (typically pre-phase-2 or pre-clip witness repair). Gemini correction
occurred upstream of these snapshots; this ablation measures **automated witness-repair
and deployment edits**, not OCR-vs-Gemini in isolation.

Backup kinds used:

- `pre_phase2_repair`: 107 notes
- `pre_phase2_skipped_repair`: 70 notes
- `pre_trunc_repair`: 55 notes
- `pre_clip_repair`: 42 notes
- `pre_repair`: 13 notes
- `pre_troilus_repair`: 13 notes

## Tail verification (last 90 chars, partial_ratio ≥ 75)

| Stage | Pass n | Pass % |
|-------|-------:|-------:|
| Stage 1 (raw OCR proxy) | 289 | **96.33%** |
| Stage 2 (deployed) | 289 | **96.33%** |
| Δ (stage2 − stage1) | +0 | **+0.00 pp** |

## Full-span verification (tail-bounded span, fuzz.ratio ≥ 75)

| Stage | Scored | Anchored | Full-span pass | Pass % (scored) | Pass % (anchored) |
|-------|-------:|---------:|---------------:|----------------:|------------------:|
| Stage 1 | 270 | 200 | 154 | 57.04% | 77.0% |
| Stage 2 | 270 | 200 | 151 | 55.93% | 75.5% |

Δ full-span pass (anchored): **-1.50 pp** (-3 notes)

## Stage-1 → stage-2 edits on sample

- Changed notes: **19** / 300 (6.33%)
- Unchanged: 281

| Category | Count | % of changed |
|----------|------:|-------------:|
| other | 16 | 84.2% |
| character_repair | 2 | 10.5% |
| spelling_normalization | 1 | 5.3% |

Of **other**, 15 are large tail extensions (stage-2 longer by >80 chars, shared prefix)—witness truncation completion.

## Verification lift on changed notes only

- Tail pass: stage1 94.74% → stage2 94.74% (+0.00 pp)
- Full-span pass (anchored): stage1 85.71% → stage2 64.29% (-21.43 pp)

Regenerate: `python3 scripts/audit_nv_stage_ablation.py`
