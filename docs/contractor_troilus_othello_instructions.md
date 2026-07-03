# Contractor Package: Troilus and Cressida + Othello

**Copy-paste email intro (for contractor outreach):**

---

Subject: Shakespeare New Variorum — Troilus (89 notes) + Othello (12 items)

Hello,

We need help repairing **two plays** in our digital Shakespeare Variorum dataset:

1. **Troilus and Cressida** — 89 truncated scholarly notes (automated extraction clipped them mid-sentence).
2. **Othello** — 9 truncated notes plus 3 editorial cleanup tasks (duplicate fragments and witness mis-alignments).

Each note is an apparatus entry from the 19th/early-20th-century *New Variorum* editions. Your job is to restore text to match the **printed NV edition** using the linked Internet Archive volume (or an agreed alternate witness for Troilus — see below).

You will receive:

- This instruction document
- `validation/contractor_troilus_workbook.csv` — 89 truncation rows
- `validation/contractor_othello_workbook.csv` — 9 truncation rows + 3 editorial rows

Ground truth is always the Internet Archive scan of the correct NV volume. Do not paraphrase, summarize, or invent text. Transcribe exactly, preserving original spelling, punctuation, and citation style.

When finished, return the completed workbooks with `status` set to `complete` (or `no_change_needed` / `DELETE_NOTE` as described per row). Payment is released after our automated verification passes.

Please confirm receipt and estimated turnaround.

Thank you,

---

## 1. What this job is

The Shakespeare Variorum project digitizes the **New Variorum (NV)** critical apparatus: long scholarly notes keyed to individual lines. During OCR and ingestion, many notes were cut off before their natural ending.

**You are NOT editing play dialogue** — only the `notes` strings attached to line entries in the play JSON files.

| Play | JSON file | Truncation rows | Extra editorial rows |
|------|-----------|-----------------|----------------------|
| Troilus and Cressida | `Public/Data/troilus_and_cressida.json` | 89 | — |
| Othello | `Public/Data/othello_notes_folger.json` | 9 | 3 |

Othello uses **Folger-style line keys** (e.g. `1.1.18`, `1.3.285`) rather than bare scene line numbers. Troilus uses numeric line keys within each scene (e.g. `29`, `53` under `ACT 1, SCENE 1`).

---

## 2. Ground-truth witnesses (Internet Archive)

### Othello

| Field | Value |
|-------|-------|
| Edition | NV Othello (Furness, 1886) |
| `witness_ia_id` | `newvariorumediti13shak` |
| Witness URL | https://archive.org/details/newvariorumediti13shak |
| DjVu text | https://archive.org/download/newvariorumediti13shak/newvariorumediti13shak_djvu.txt |

IA access is generally open. Use IA search on the text layer or read scanned pages.

### Troilus and Cressida

| Field | Value |
|-------|-------|
| Edition | NV Troilus Vol. XXV (Hillebrand/Baldwin, **1953**) — this is what our JSON reflects |
| Canonical `witness_ia_id` | `newvariorumediti0000unse` |
| Canonical URL | https://archive.org/details/newvariorumediti0000unse |
| **Problem** | IA returns **401** (lending-restricted) for automated download |

**Fallback witness (workbook default):**

| Field | Value |
|-------|-------|
| `witness_ia_id` | `newvariorumediti22shak` |
| URL | https://archive.org/details/newvariorumediti22shak |
| Edition | Vol. XXII (1917 Furness lineage) |
| Match quality | ~85–91% note alignment vs 1953 text |

Workbook rows list `newvariorumediti22shak` because it is the witness we can verify automatically. **If you can access the 1953 volume** (borrow on IA, HathiTrust, or a library scan), prefer that for Troilus transcription. Note any edition used in `contractor_notes`.

**Optional local PDF:** Project owner may provide `/tmp/troilus_nv.pdf` (image-only; requires OCR or manual reading). Contact us if you need this file or help obtaining the 1953 witness.

---

## 3. Workbook columns

Standard columns (both workbooks):

| Column | Description |
|--------|-------------|
| `play_name` | Full play title |
| `play_file` | JSON filename stem (`troilus_and_cressida` or `othello_notes_folger`) |
| `act_scene` | Scene key, e.g. `ACT 1, SCENE 1` or `ACT 1 SCENE 1` |
| `line_key` | Line identifier (Folger key for Othello; scene line number for Troilus) |
| `note_index` | 0-based index when multiple notes exist on one line |
| `current_note_text` | Full note as it exists now — your starting point |
| `truncation_signals` | Why the audit flagged truncation (truncation rows only) |
| `witness_ia_id` | IA identifier for verification |
| `witness_url` | Full archive.org link |
| `status` | `pending` → change to `complete`, `no_change_needed`, or per editorial instructions |
| `completed_note_text` | **You fill this** with the full corrected note (truncation + editorial_cleanup rows) |
| `contractor_notes` | Required for `no_change_needed`, `DELETE_NOTE`, or `ALSO_DELETE_NOTE_INDEX_0` |
| `char_count_before` | Length of original (auto) |
| `char_count_after` | Length of your completed text |
| `task_type` | `truncation` \| `editorial_cleanup` \| `dedupe` |
| `task_description` | Row-specific instructions |

### Deliverable format

Return **either**:

- Completed `.csv` workbooks (Excel-friendly), **or**
- Equivalent `.json` with the same structure as the CSV

**Required on every row:**

- `status`: `complete` or `no_change_needed`
- Truncation / `editorial_cleanup`: non-empty `completed_note_text` with the **entire** corrected note
- `dedupe` (delete fragment): `status=complete`, `contractor_notes=DELETE_NOTE`, leave `completed_note_text` empty
- `no_change_needed`: explain in `contractor_notes`

---

## 4. Troilus and Cressida — step-by-step

**Scope:** 89 union-truncated notes (14.3% of play notes).

1. Open `validation/contractor_troilus_workbook.csv`.
2. For each row (`task_type` = `truncation`):
   1. Read `current_note_text` and `truncation_signals`.
   2. Open `witness_url` (fallback Vol. XXII, or 1953 if you have access).
   3. Navigate to the act/scene; search for the note opening (critic name in caps, lemma in brackets).
   4. Transcribe the **complete** note from print into `completed_note_text`.
   5. Set `status` = `complete` and update `char_count_after`.
3. Preserve original spelling, citation brackets, em-dashes, Latin, and NV-style closers (`—Ed.]`, `.]`, etc.).
4. Return `contractor_troilus_workbook.csv`.

**Tips:**

- Notes often follow play lines in NV page layout; use embedded line-number cues (e.g. `29.`, `57.`).
- If the 1917 witness differs from 1953 wording, transcribe the **1953** text if you have it; otherwise use 1917 and flag in `contractor_notes`.
- Multiple notes on one line are distinguished by `note_index`.

---

## 5. Othello — step-by-step

**Scope:** 9 truncation repairs + 3 editorial tasks in `validation/contractor_othello_workbook.csv`.

**Data file:** `Public/Data/othello_notes_folger.json`  
**Witness:** https://archive.org/details/newvariorumediti13shak

### 5a. Truncation rows (9 items)

Same workflow as §4, using Folger line keys. Flagged locations include:

| act_scene | line_key | note_index | Issue (summary) |
|-----------|----------|------------|-----------------|
| ACT 1, SCENE 1 | 1.1.18 | 0 | Clipped mid-gloss |
| ACT 1, SCENE 1 | 1.1.44 | 0 | Clipped collation tail |
| ACT 1, SCENE 1 | 1.1.47 | 0 | Mid-sentence cut |
| ACT 1, SCENE 1 | 1.1.53 | 0 | Hard truncation |
| ACT 1, SCENE 3 | 1.3.285 | 0 | Long note cut mid-parenthesis |
| ACT 1, SCENE 3 | 1.3.291 | 16 | Long collation note cut |
| ACT 2, SCENE 1 | 2.1.66 | 1 | Mid-sentence cut |
| ACT 3, SCENE 1 | 3.1.21 | 2 | Hyphen artifact / clip |
| ACT 3, SCENE 2 | 3.2.4 | 0 | Hyphen artifact / clip |

### 5b. Editorial task 1 — Walker dedupe (`task_type`: `dedupe`)

| Field | Value |
|-------|-------|
| line_key | `1.1.36` |
| note_index | `0` |

**Problem:** A **fragment** note starts mid-sentence (`f as disproportion in Qq...`) — it is the tail of the Walker collation on interpolated *s* in Folio spellings.

**Complete note location:** `1.1.42` / `note_index` `1` — begins `others] Walker (Crit. i, 233)...`

**Action:**

1. On row `1.1.36` / note `0`: set `status=complete`, `contractor_notes=DELETE_NOTE`, leave `completed_note_text` empty.
2. Optionally verify `1.1.42` note `1` against witness **§31 others]** (no change needed if already correct).

### 5c. Editorial task 2 — brace duplicate + witness alignment (`task_type`: `editorial_cleanup`)

| Field | Value |
|-------|-------|
| line_key | `1.3.22` |
| note_index | `1` |

**Problem:** Two notes on this line — note `0` lacks the `brace]` lemma; note `1` is the keeper but has `—ED.]` instead of witness `— Ed.]`.

**Witness (§32 brace]):** ends with `...when a knight had braced on his armour he was ready. — Ed.]`

**Action:**

1. Put the verbatim witness text in `completed_note_text` for note_index `1`.
2. Set `contractor_notes=ALSO_DELETE_NOTE_INDEX_0` (we will remove the duplicate note `0` on apply).
3. Set `status=complete`.

### 5d. Editorial task 3 — Pope Sighs bracket (`task_type`: `editorial_cleanup`)

| Field | Value |
|-------|-------|
| line_key | `1.3.175` |
| note_index | `0` |

**Problem:** `kisses] POPE: Sighs is evidently the true reading...` — digital text may include a synthesized `—ED.]` closer; IA DjVu text layer **breaks mid-bracket** at “kissing in Eliza”.

**Action:**

1. Open witness **§182 kisses]** in the **scanned pages** (not only the broken text layer).
2. Transcribe the full Pope note including the complete Furness editor bracket through its proper closer.
3. Put full text in `completed_note_text`; set `status=complete`.

---

## 6. Truncation signals (reference)

| Signal | Meaning |
|--------|---------|
| `is_clipped` | Ends on stop-word, comma/semicolon, or short unclosed parenthesis |
| `hard_truncation` | Missing terminal punctuation or ends with word fragment |
| `mid_sentence_cut` | Ends with lowercase letter (prose continues) |
| `hyphen_artifact` | Ends with `-` from column/page line break |
| `unbalanced_parens` | More `(` than `)` without scholarly closer |
| `witness_prefix` | IA witness continues after where the note ends |

False positive? Use `no_change_needed` and document why.

---

## 7. What NOT to do

| Do not | Why |
|--------|-----|
| Paraphrase or summarize | Verbatim NV text required |
| Invent missing words | Transcribe print only |
| Modernize spelling | Match the edition |
| Edit play dialogue | Notes only |
| Return only the missing tail | `completed_note_text` must be the **full** note |
| Substitute a different NV edition without noting it | Breaks verification |

---

## 8. Quality criteria (acceptance)

A row is acceptable when:

1. **Complete** — note ends with NV-style terminal punctuation.
2. **Longer or equal** — completed text ≥ original (unless `DELETE_NOTE` or `no_change_needed`).
3. **Prefix preserved** — opening matches the clipped original (truncation rows).
4. **Witness-aligned** — substantial prefix appears in IA witness text.
5. **Verbatim** — spot-checks match scanned pages.

For `dedupe` rows: fragment removed, surviving note witness-aligned.

---

## 9. How to return completed work

Email or shared folder with:

1. `contractor_troilus_workbook.csv` (all 89 rows addressed)
2. `contractor_othello_workbook.csv` (all 12 rows addressed)

Use UTF-8 encoding. Keep all original columns; only edit `status`, `completed_note_text`, `contractor_notes`, and `char_count_after`.

---

## 10. Payment verification (how we check)

After you return workbooks, we run (from repo root):

```bash
# Troilus — apply truncation completions (dry-run first)
python3 scripts/apply_contractor_completions.py \
  --workbook validation/contractor_troilus_workbook.csv --dry-run

python3 scripts/apply_contractor_completions.py \
  --workbook validation/contractor_troilus_workbook.csv

# Othello — truncation rows apply via same script; DELETE_NOTE / ALSO_DELETE rows applied manually
python3 scripts/apply_contractor_completions.py \
  --workbook validation/contractor_othello_workbook.csv --dry-run

# Per-play truncation re-audit
python3 scripts/audit_nv_truncation.py  # expect 0 union-truncated for each play

# Payment gate (workbook completeness + post-apply audit)
python3 scripts/verify_contractor_completions.py \
  --workbook validation/contractor_troilus_workbook.csv \
  --allow-remaining 0

python3 scripts/verify_contractor_completions.py \
  --workbook validation/contractor_othello_workbook.csv \
  --allow-remaining 0
```

**Payment is released when:**

- Every workbook row has `status` ∈ {`complete`, `no_change_needed`}
- `complete` rows have required fields per task type
- Re-audit shows **0 union-truncated notes** for Troilus and Othello
- Othello editorial tasks resolved (fragment deleted, brace deduped, Pope note witness-complete)
- Witness spot-checks pass (`verify_contractor_completions.py` samples completed notes against IA text)

You do not need repo access — we run verification on our side.

**Note:** `apply_contractor_completions.py` handles text replacement for `truncation` and `editorial_cleanup` rows. Rows with `contractor_notes=DELETE_NOTE` or `ALSO_DELETE_NOTE_INDEX_0` are applied manually by the project owner after your workbook is verified.

---

## 11. File reference

| Path | Purpose |
|------|---------|
| `Public/Data/troilus_and_cressida.json` | Troilus play + notes |
| `Public/Data/othello_notes_folger.json` | Othello play + notes (Folger line keys) |
| `validation/contractor_troilus_workbook.csv` | 89 truncation tasks |
| `validation/contractor_othello_workbook.csv` | 9 truncation + 3 editorial tasks |
| `scripts/nv_witness_map.py` | Canonical IA witness IDs |
| `docs/contractor_truncation_repair_instructions.md` | Full 22-play package (reference) |

---

## 12. Questions

Contact the project owner for:

- Troilus 1953 witness access (IA borrow, PDF, HathiTrust)
- Ambiguous note boundaries
- Rows where fallback and canonical witnesses disagree

---

*Package generated from live play JSON and `validation/contractor_truncation_workbook.csv`. Troilus: 89 union-truncated notes. Othello: 9 union-truncated + 3 editorial items.*
