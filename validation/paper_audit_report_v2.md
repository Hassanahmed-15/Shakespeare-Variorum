# Paper audit report (v2) — deployed corpus, 21-play denominator

**Date:** 2026-07-11  
**Scope:** All audits exclude *Troilus and Cressida* (21 plays). Othello notes mapped to MIT/Moby spine (`Public/Data/othello_notes.json`).  
**Artifacts:** `validation/*_v2.*`, `validation/nv_fullspan_sample_v2/`, `validation/nv_witness_sample_v2/`.

---

## 1. Full-corpus tail verification

Method: `verify_all_notes.py` — last 90 characters, RapidFuzz `partial_ratio` ≥ 75 against IA witness chunks.

| Metric | Value |
|--------|------:|
| Notes | 23,094 |
| Pass | 22,715 |
| Fail | 379 |
| Pass rate | **98.36%** |
| 95% Wilson CI | **98.19–98.51%** |

**Prior baseline (no Troilus):** 23,094 notes @ 98.36% — **unchanged** at corpus level.

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

**Flagged (>2 pp below corpus 98.36%):** Othello only (93.90%, 56 fails; concentrated in ACT 1 SCENE 1 early lines).

---

## 2. Truncation census

Source: `audit_nv_truncation.py` → `validation/nv_truncation_audit_v2.json`.

| Metric | Value |
|--------|------:|
| Notes audited | 23,094 |
| Union truncation flags | 24 |
| Flag rate | **0.10%** |
| Plays with zero union flags | 13 |

Zero-flag plays: *Romeo and Juliet*, *King Lear*, *Othello*, *The Merchant of Venice*, *As You Like It*, *A Midsummer Night's Dream*, *Much Ado About Nothing*, *Love's Labour's Lost*, *Richard III*, *Julius Caesar*, *King John*, *Henry IV, Part 1*, *Henry IV, Part 2*.

---

## 3. Repair-cohort controls

Source: `slice_tail_verify_by_repair.py --exclude "Troilus and Cressida" --suffix _v2` (census: `nv_tail_verify_all_plays_v2.json`).

| Cohort | n | Pass | Fail | Pass % |
|--------|--:|-----:|-----:|-------:|
| Never in repair workbook | 22,276 | 21,910 | 366 | 98.36% |
| Full repair workbook cohort | 818 | 805 | 13 | 98.41% |
| Spliced completions (`complete`) | 730 | 722 | 8 | 98.90% |
| **Full corpus (check)** | **23,094** | **22,715** | **379** | **98.36%** |

**Cohort sum check:** untouched + workbook = 22,276 + 818 = **23,094** (matches corpus 23,094).

| Workbook metric | v2 | Prior paper |
|-----------------|---:|------------:|
| Workbook entries in cohort | 838 | 927 (22-play workbook) |
| Matched in corpus (scored) | **818** | 824 / 838 cited |
| Share of corpus | **3.54%** | 3.6% (838) |

---

## 4. Stratified full-span sample

Method: `audit_nv_fullspan_sample.py`, seed **42**, **14 notes/play** (21 plays → 294 notes). Tail-bounded v2 spans.

| Metric | n | % of evaluable |
|--------|--:|---------------:|
| Sampled | 294 | — |
| Exempt (cross-ref / gloss) | 30 | — |
| Evaluable (scored) | 264 | 100% |
| Anchored | 194 | 73.5% |
| Unanchorable | 70 | **26.5%** |
| Automated pass (`full_span_match`) | 152 | **78.4%** of anchored |
| Interior-divergence flags | 40 | — |
| Span-mismatch flags | 2 | — |

**Prior baseline:** 294 sampled; 179 anchored; 83 unanchorable (28.2% of evaluable); 122 automated pass.

### Seed-42 reproduction vs `validation/nv_fullspan_sample/sample_manifest.json`

- Overlap (21-play, Troilus omitted from prior): **294 / 294** refs identical.
- Notes only in prior draw: **0**.
- Notes only in v2 draw: **0**.

**Conclusion:** Seed-42 draw **fully reproduces** the prior full-span sample for all non-Troilus plays. **No new Othello notes** require author adjudication for sample membership.

**Othello in sample:** 14 sampled; 0 anchored; 9 unanchorable; 4 automated pass.

---

## 5. Reader-focused sample

Method: `audit_nv_witness_sample.py`, **50 notes/play**, act-stratified (deterministic). 21 × 50 = **1,050** notes.

| Outcome | n | % |
|---------|--:|--:|
| Reader-OK | 1048 | **99.8%** |
| Truncated | 0 | 0.0% |
| Not located in witness | 2 | 0.2% |
| 95% Wilson CI (reader-OK) | — | **99.31–99.95%** |

**Prior baseline (22-play / 1,100):** 99.0% reader-OK; 10 truncated (1.0%).

### Sample reproduction vs prior `validation/nv_witness_sample/results.json` (Troilus omitted)

- Shared refs: **1050 / 1,050**.
- Refs only in prior: **0**.
- Refs only in v2: **0**.

**Conclusion:** Act-stratified draw is **unchanged** for all 21 plays after Othello MIT rebuild.

**Not located in witness:**

- `Love's Labour's Lost` — `ACT 1 SCENE 1 / line 246 / note 1`
- `Richard III` — `ACT 2 SCENE 1 / line 105 / note 0`

---

## 6. Lineation retrieval audit

Method: `audit_lineation_alignment.py` — **Othello included**, Troilus excluded.

| Metric | Value |
|--------|------:|
| Clickable annotated lines | 18,901 |
| Correct retrieval | 18,870 (**99.84%**) |
| Wrong key (different notes) | 31 (**0.16%**) |
| End-to-end pass | 18,862 (**99.79%**) |

**Othello:** 631 clickable; retrieval 99.37%; E2E 99.05%.

---

## 7. Johnson search count

| Total Johnson hits (21 plays) | **2,135** |
| Prior baseline | 2,135 |
| Change | **None** |
| Othello contribution | **126** |

---

## 8. Stage-direction misclassification

| Metric | Value |
|--------|------:|
| Total play lines | 67,502 |
| Bracket triggers | 2,139 |
| Misclassified | 52 (0.077% of lines) |

---

## 9. Deployment consistency checks

| Check | Result |
|-------|--------|
| Repo `othello_notes.json` SHA-256 | `9922dbef935a8ee0997bf7f125d15831c4ac0ff61177e90ec6026a5f46759a64` |
| Deployed `othello_notes.json` | `1a30245811f41b94d404a069db3fa898650b50659a514906cc07bdcf3eac6719` |
| Othello deploy match | **NO — repo ahead of production** |
| `as_you_like_it.json` repo vs deploy | match |
| `meliorandi` patch (repo) | present |
| Troilus in `PLAY_FILES` | **absent** |

---

## Executive summary

- Corpus tail pass **98.36%** (Wilson 98.19–98.51%) unchanged vs prior; **Othello** alone >2 pp below mean (**93.90%**).
- Truncation union **0.10%**; repair workbook **818** notes (3.54%); Johnson **2,135** unchanged.
- Full-span seed 42: **294/294** refs match prior no-Troilus manifest — **no adjudication** needed for sample membership.
- Reader sample: **99.8%** OK (0 truncated); **1,050/1,050** refs unchanged vs prior no-Troilus draw.
- **Blocker:** Live `othello_notes.json` ≠ repo — redeploy before claiming production parity.
