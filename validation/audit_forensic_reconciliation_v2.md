# Audit forensic reconciliation (2026-07-11)

Resolves contradictions between Claude’s “screenshot run” (Othello 903/98.37%) and the `_v2` suite. All integers below are from repo files on disk after commit `64022fe`.

---

## 1. Provenance: what was actually audited

| File | Path | Size | SHA-256 (first 16) | Notes |
|------|------|-----:|--------------------|-------|
| Othello corpus | `Public/Data/othello_notes.json` | 820,913 | `9922dbef935a8ee0` | `_meta.textSource`: **MIT Shakespeare (Moby); public domain**; `quoteReanchored`: 292 |
| Deployed Othello (post-push) | `https://newvariorum.com/Public/Data/othello_notes.json` | — | `9922dbef935a8ee0` | **Matches repo** as of 2026-07-11 after push |
| Tail audit output | `validation/nv_tail_verify_all_plays_v2.json` | — | — | Built from current repo JSONs |
| Full-span | `validation/nv_fullspan_sample_v2/manifest.json` | — | — | seed 42, 14/play |
| Reader sample | `validation/nv_witness_sample/results.json` | — | — | 50/play act-stratified |

**Critical:** No file anywhere in the repo contains Othello tail **903 pass / 98.37%**. That figure does not appear in any `_v2` JSON, log, or prior validation artifact. The only Othello tail row on record is **862 / 56 / 93.90%**, identical in both the pre-rebuild 21-play slice and `_v2`.

---

## 2. Tail verification — determinism and v1 vs v2 diff

**Method:** `verify_all_notes.py` — last 90 chars, RapidFuzz `partial_ratio` ≥ 75 vs IA witness chunks.

**Back-to-back Othello run (same files):** (862, 56) → (862, 56) — **deterministic**.

**21-play comparison (exclude Troilus):**

| Source | Notes | Pass | Fail | Pass % |
|--------|------:|-----:|-----:|-------:|
| `nv_tail_verify_all_plays.json` (no Troilus rows) | 23,094 | 22,715 | 379 | 98.36% |
| `nv_tail_verify_all_plays_v2.json` | 23,094 | 22,715 | 379 | 98.36% |

**Plays with any count change between v1 and v2 (21-play set):** **0**.

The apparent “40 lost passes” came from comparing **22-play v1 totals** (23,715 notes, includes Troilus at 77.13%) to **21-play v2 totals** (23,094 notes). Not a corpus regression.

### Full per-play tail table (Table 2 source)

| Play | Notes | Pass | Fail | Pass % |
|------|------:|-----:|-----:|-------:|
| Othello | 918 | 862 | 56 | 93.90% ⚠ |
| As You Like It | 940 | 913 | 27 | 97.13% |
| A Midsummer Night's Dream | 745 | 724 | 21 | 97.18% |
| The Tempest | 770 | 749 | 21 | 97.27% |
| Love's Labour's Lost | 1,171 | 1,143 | 28 | 97.61% |
| Macbeth | 1,252 | 1,223 | 29 | 97.68% |
| Much Ado About Nothing | 931 | 910 | 21 | 97.74% |
| Romeo and Juliet | 720 | 704 | 16 | 97.78% |
| Twelfth Night | 1,068 | 1,045 | 23 | 97.85% |
| King John | 1,072 | 1,052 | 20 | 98.13% |
| Hamlet | 1,948 | 1,912 | 36 | 98.15% |
| Henry IV, Part 1 | 738 | 725 | 13 | 98.24% |
| King Lear | 1,163 | 1,148 | 15 | 98.71% |
| The Winter's Tale | 1,109 | 1,098 | 11 | 99.01% |
| The Merchant of Venice | 1,027 | 1,017 | 10 | 99.03% |
| Antony and Cleopatra | 1,053 | 1,044 | 9 | 99.15% |
| Cymbeline | 1,035 | 1,028 | 7 | 99.32% |
| Coriolanus | 1,503 | 1,495 | 8 | 99.47% |
| Richard III | 1,226 | 1,222 | 4 | 99.67% |
| Julius Caesar | 723 | 721 | 2 | 99.72% |
| Henry IV, Part 2 | 1,982 | 1,980 | 2 | 99.90% |

**Wilson 95% CI (corpus):** 98.19–98.51%

**Flagged (>2 pp below 98.36%):** Othello only.

**Why MIT rebuild did not move Othello tail %:** Tail verify matches **note text** against IA OCR, not line keys. The rebuild re-keyed 292 notes (line attachment) but did not rewrite note prose. Unchanged 862/56 is expected, not evidence of a stale file.

---

## 3. Full-span sample — arithmetic (exact)

Source: `validation/nv_fullspan_sample_v2/manifest.json` → `corpus_summary`

| Metric | n |
|--------|--:|
| Sampled | 294 |
| Exempt | 30 |
| Evaluable (scored) | 264 |
| Anchored | 194 |
| Unanchorable | 70 |
| **Check:** 194 + 70 | **= 264 ✓** |
| Automated pass (anchored) | 152 (78.4%) |
| Interior divergence | 40 |
| Span mismatch | 2 |

**Othello row (exact):** sampled 14; exempt 0; anchored **5**; unanchorable 9; auto-pass 4; interior 1; span-mismatch 0.

**Seed-42 reproduction vs prior `sample_manifest.json` (Troilus omitted):** **294 / 294** refs identical; 0 notes only in prior; 0 only in v2.

**Adjudication:** No new sample members. Othello’s 14 refs are the same seed-42 draw; line keys in refs updated where MIT rebuild moved notes, but membership unchanged. Interior cases remain the prior adjudicated set (40 total; Othello contributes 1, adjudicated 2026-07-08 as witness OCR degradation).

---

## 4. Reader sample — two scorers, not two runs

### A. Human-adjudicated (paper-citable)

Source: `validation/nv_witness_sample/reader_rate_table.md` — **22-play draw, 1,100 notes**, human review.

| Outcome | n | % |
|---------|--:|--:|
| Reader-OK | 1,089 | 99.0% |
| Truncated | 10 | 0.9% |
| Not in print | 1 | 0.1% |

Truncated includes 6 King John cases (play not rebuilt). This table is **human-adjudicated** and remains the paper’s authoritative reader figure until Jack re-reviews any new cases.

### B. Automated machine scorer (current script)

Source: `validation/nv_witness_sample/results.json` — **21-play, 1,050 notes**, `reason` field from `audit_nv_witness_sample.py`.

| Outcome | n | % |
|---------|--:|--:|
| Reader-OK (`reason` ≠ truncated/not_in_witness) | 1,048 | 99.8% |
| Truncated | 0 | 0.0% |
| Not located | 2 | 0.2% |

**This is not a corpus change.** The automated script uses different truncation detection than human adjudication. Example: King John `ACT 4 SCENE 1 / line 2 / note 0` — human: **truncated**; machine: `text_drift` / defective (not counted in reader-OK table above). Romeo `ACT 3 SCENE 3 / line 130` — human: truncated; machine: `anchor_only` / uncertain.

**Sample draw stability (21-play):** 1,050 notes per run; **950 unique refs** (100 intentional duplicates from act-stratified sampling); **0 reason-field changes** between current `results.json` and `_v2` copy.

**Paper guidance:** Keep **99.0% / 10 truncated / 1 not located (1,100)** for the human-adjudicated claim. Do **not** substitute 99.8% / 0 truncated without fresh human review.

---

## 5. Lineation (corpus-wide, Othello included)

Source: `validation/nv_lineation_alignment_v2.json`

| Metric | Value |
|--------|------:|
| Clickable annotated lines | 18,901 |
| Correct retrieval | 18,870 (99.84%) |
| Wrong key (different notes) | **31** (0.16%) |
| End-to-end pass | 18,862 (99.79%) |
| Othello clickable | 631 |
| Othello E2E | 99.05% |

Prior audit (Othello excluded): 18,854 clickable — difference = Othello’s 631 clickable minus overlap/empty-play recount (18,901 − 18,854 = +47 net; Othello adds 631 clickable lines not in prior denominator).

---

## 6. Truncation, repair cohorts, Johnson, stage direction

**Truncation:** 23,094 notes; **24** union flags (0.10%); **13** zero-flag plays.

**Repair cohorts:**

| Cohort | n | Pass % |
|--------|--:|-------:|
| Never in workbook | 22,276 | 98.36% |
| Workbook matched | 818 | 98.41% |
| Spliced (`complete`) | 730 | 98.90% |
| **Sum check** | 22,276 + 818 = **23,094** ✓ |

Workbook entries in cohort: **838**; matched in corpus: **818** (3.54% of corpus).

**Johnson:** **2,135** total; Othello **126**; unchanged vs prior.

**Stage direction:**

| Metric | Value |
|--------|------:|
| Total play lines | 67,502 |
| Bracket triggers | 2,139 |
| Misclassified | 52 (0.077% of lines) |
| Misclassified / bracket triggers | **2.43%** (was ~2.31% on prior 22-play run with different line inventory) |

---

## 7. Confirmations

| Check | Result |
|-------|--------|
| Deployed Othello = repo | **YES** (SHA `9922dbef…`, post-push) |
| `meliorandi` in `as_you_like_it.json` | present |
| Troilus in `PLAY_FILES` | absent |
| Othello play text MIT/Moby | confirmed via `_meta.textSource` and A1S1 `[Enter RODERIGO and IAGO]` |

---

## 8. Paper implications (corrected)

1. **Do not claim Othello tail at corpus average (98.37%).** That number was never produced by Cursor. Othello remains **93.90%** on tail verify — the only play >2 pp below mean.

2. **Do claim uniform MIT architecture** — one lineation regime, one attachment mechanism, Folger as future separate project.

3. **Do claim stable corpus totals** — 23,094 notes, 98.36% tail, 24 truncation flags, 2,135 Johnson unchanged vs pre-rebuild 21-play baseline.

4. **Reader sample:** retain human-adjudicated **99.0% (1,089/1,100)** until re-adjudication; do not cite machine 99.8% without human pass.

5. **Lineation:** cite **18,901 clickable / 99.79% E2E / 31 wrong-key** (corpus-wide including Othello).

6. **Limitations:** Othello tail-verify gap reflects IA OCR + Act 1 collation apparatus density, not Folger mixing (resolved) or display misalignment (fixed by quote re-anchoring).
