# True OCR-vs-Deployed Ablation — Revision-Round Recipe

**Status:** Not run for submission. Feasible in revision if a reviewer demands a genuine pre-LLM control.  
**Pinned sample:** `validation/nv_stage_ablation_manifest.json` (300 notes, seed 42).  
**Verification stack:** `scripts/verify_all_notes.py` (tail) + `scripts/audit_nv_fullspan_sample.py` (full-span).

---

## What the first ablation measured (and did not)

`scripts/audit_nv_stage_ablation.py` compared **earliest `*.pre_*_repair.backup`** vs **deployed JSON**. That is a **witness-repair / deployment** delta, not OCR-vs-Gemini:

- Only **19/300** notes differed (6.3%).
- Tail pass was **identical** (96.33% both arms).
- Gemini ran **before** those backups were taken.

This recipe is the **real experiment**: fresh page OCR (Stage 1) vs deployed note text (Stage 2 + later repairs).

---

## Why it is still possible

The methodology states that **20/23 NV volumes have 300–400 DPI page scans on Internet Archive** (plus local PDF for 1953 *Troilus*). Page images are not vendored in git, but they are **fetchable on demand** via Archive.org download/IIIF.

What is **not** in the repo:

- Pre-Gemini note JSON per line
- Note→page index
- hOCR bounding boxes (local `data/h4p2_*_hocr.txt.gz` files are plain text dumps, not hOCR XML)

What **is** in the repo:

- Pinned 300-note sample + dual verification code
- IA witness text cache (`data/ia_cache/*_djvu.txt`)
- Witness anchoring (`audit_nv_witness_sample.locate_note`, `find_start`)
- Page OCR precedent (`scripts/build_troilus_witness.py` — RapidOCR + PyMuPDF on PDF)

---

## Pipeline (seven steps)

### 1. Pin the sample

Use the existing manifest (do not redraw):

```bash
# 300 refs at validation/nv_stage_ablation_manifest.json
python3 scripts/audit_nv_true_ocr_ablation.py --dry-run
```

### 2. Resolve deployed note text

For each `{play, ref}` load the note string from the live play JSON (`audit_nv_fidelity_all_plays.PLAYS` paths).

### 3. Anchor in IA witness → estimate page

For each note:

1. Load play witness (`nv_witness_map.WITNESS_BY_PLAY` / local Troilus PDF text).
2. Find start offset with `find_start()` / `locate_note()` (same as witness sample audit).
3. Map character offset → **printed page** using one of:
   - **Preferred:** `{ia_id}_scandata.xml` leaf/page index (Archive download API).
   - **Fallback:** `{ia_id}_abbyy.gz` page boundaries (ABBYY page tags — use only for *page number*, not as Stage 1 text).
   - **Last resort:** linear interpolation `(offset / len(witness)) * leafCount` — document as ±2 pages uncertainty.

Output: `validation/nv_true_ocr_ablation_page_map.json` (ref, ia_id, leaf, witness_offset, anchor_confidence).

### 4. Fetch page image

For each unique `(ia_id, leaf)` in the sample (~150–250 pages, not 300):

```
https://archive.org/download/{ia_id}/{ia_id}_jp2/{ia_id}_{leaf:04d}.jp2
# or IIIF:
https://iiif.archive.org/iiif/{ia_id}%2F{ia_id}_jp2%2F{ia_id}_{leaf:04d}.jp2/full/full/0/default.jpg
```

Cache under `data/page_cache/{ia_id}/{leaf}.jpg`.

**Troilus:** use local `data/troilus_nv_1953.pdf` + PyMuPDF rasterize (already in `build_troilus_witness.py`).

### 5. Stage-1 OCR (pre-LLM)

**Engine:** Tesseract 5.x (paper) or RapidOCR (existing dep) for parity pilots.

```bash
# Full page, preserve layout
tesseract page.jpg stdout --oem 1 --psm 4 -l eng

# Optional apparatus crop (NV default layout: commentary below play text)
# Crop lower 55–65% of page height after manual QA on 5 pages/volume
```

Store raw page OCR: `data/page_cache/{ia_id}/{leaf}.tesseract.txt`

**Do not** use `*_djvu.txt` or `*_abbyy.gz` as Stage 1 — that is Internet Archive OCR, not your fresh Tesseract pass.

### 6. Segment note region (hard part)

No automatic NV apparatus parser exists. Use **witness-anchored fuzzy extraction**:

1. Take opening 6–12 words from deployed note body (`_note_body()` after lemma `]`).
2. Locate that phrase in the **fresh page OCR** (flexible whitespace, `rapidfuzz.partial_ratio` ≥ 85 on 40-char window).
3. Extend forward until a stop rule fires:
   - Next marginal line number (`^\s*\d+\s+[A-Z]` NV style)
   - Next critic opener (`^[A-Z][A-Z .'-]{2,30}:` or `NAME:]`)
   - 1.15× deployed note length (cap overrun)
4. If opening not found on estimated page, try **leaf±1** (page-map error buffer).
5. Flag `segmentation_confidence: low` for human QA; exclude from scored denominator or adjudicate.

Store: `validation/nv_true_ocr_ablation_segments.json`  
Fields: `ref`, `stage1_raw_page_ocr`, `stage1_segment`, `segment_method`, `confidence`.

**QA subsample:** manually check 15 segments (5 plays × 3) before trusting corpus rates.

### 7. Verify both arms

Reuse existing scorers on **segment text** (Stage 1) vs **deployed note** (Stage 2):

```python
# Tail: verify_all_notes.tail_verify_note(segment, chunks)
# Full-span: audit_nv_fullspan_sample.classify_note(segment, folded_ia, chunks)
```

Report:

| Metric | Stage 1 (Tesseract segment) | Stage 2 (deployed) |
|--------|----------------------------:|-------------------:|
| Tail pass % | | |
| Full-span pass % (anchored) | | |
| Unanchorable % | | |

Edit taxonomy (Stage 1 → Stage 2): character_repair, abbreviation_restoration, citation_rejoin, spelling_normalization, other — same rules as `audit_nv_stage_ablation.py`.

Write to `validation/nv_true_ocr_ablation_*` (suffix `_ablation` on all outputs).

---

## Commands (revision round)

```bash
# Prep: anchor + page URLs (no OCR)
python3 scripts/audit_nv_true_ocr_ablation.py --dry-run

# Pilot: 10 notes, RapidOCR/Tesseract on fetched pages
python3 scripts/audit_nv_true_ocr_ablation.py --pilot 10

# Full 300-note run (expect 4–8 hours; cache pages)
python3 scripts/audit_nv_true_ocr_ablation.py --run

# Re-score only after segment QA edits
python3 scripts/audit_nv_true_ocr_ablation.py --verify-only
```

**Dependencies to install once:**

```bash
brew install tesseract   # or apt install tesseract-ocr
pip install pymupdf rapidocr-onnxruntime pillow requests rapidfuzz
```

---

## Expected outcomes (honest)

| Aspect | Expectation |
|--------|-------------|
| Tail pass lift Stage 1 → Stage 2 | **+2–8 pp** on changed/long notes; **~0 pp** corpus-wide if Gemini mostly fixed abbreviations not tails |
| Full-span | Noisier; Stage 1 segments will score lower until segmentation QA |
| Segmentation failures | **5–15%** of sample without leaf±1 retry; budget human adjudication |
| Compute | ~200 page fetches + OCR; cache aggressively |

This is **stronger evidence** than the backup ablation for the claim “Gemini + witness repair improved print fidelity,” but it is **not** a CER benchmark against diplomatic gold (Levchenko/Boros framing).

---

## Paper language (if reviewer asks)

> We did not include fresh page-level Tesseract ablation in the initial submission. A pinned 300-note sample and verification stack are frozen (`nv_stage_ablation_manifest.json`). Revision work will re-OCR Archive.org page images for sample notes, segment apparatus regions via witness-anchored fuzzy match, and report tail and full-span witness pass rates for pre-LLM OCR vs deployed text.

---

## Relation to other artifacts

| Artifact | Role |
|----------|------|
| `nv_stage_ablation_*` | Backup-vs-deployed (done) |
| `nv_true_ocr_ablation_*` | Tesseract-vs-deployed (this recipe) |
| `nv_tail_verify_all_plays.json` | Corpus-wide tail census (97.8%) |
| `nv_fullspan_sample/*` | Full-span methodology v2 |

Regenerate backup ablation: `python3 scripts/audit_nv_stage_ablation.py`  
Prep true OCR ablation: `python3 scripts/audit_nv_true_ocr_ablation.py --dry-run`
