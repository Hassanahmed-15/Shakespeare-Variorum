# NV Fidelity Projection — Post-927-Repair

**Sources:** `scripts/audit_nv_fidelity_all_plays.py`, `validation/nv_fidelity_all_plays.json` (post-Troilus 1953 witness), `validation/nv_truncation_audit.json`  
**Projection scenario:** All **927** `union_truncated` notes repaired to completion; King John witness stub fix deployed. This document projects tier/L1/L2 metrics **after** that repair — not current on-disk state.

---

## Legend

> **POST-927-repair projection.** Columns labeled *proj* assume 100% of the 927-note `union_truncated` backlog is fixed. Current-state columns reflect the baseline JSON audits as of this run.

### L1 — Structural / corpus integrity (no witness required)

Computed by `structural_metrics()` on **every note** in each play JSON:

| Signal | Meaning | Tier impact |
|--------|---------|-------------|
| **synth** | Notes with synthetic prefixes (`Editorial note:`, `Annotation:`, etc.) | Any > 0 → **Tier C** |
| **para** | Short paraphrase-style glosses (regex `PARAPHRASE_RE`) | Any > 0 → **Tier C** |
| **clip%** | `is_clipped()` heuristic (hyphen tail, unbalanced parens, stop-word endings on short notes) | > 4% → **Tier B** |

Also tracked: note count, avg/median length, % under 250 chars, % over 800 chars, `long_nv_style` count. All 22 plays: **synth=0, para=0**.

**Truncation %** in this chart comes from the separate exhaustive audit (`union_truncated` = hard truncation, mid-sentence cut, hyphen artifact, unbalanced parens, witness-prefix continuation, **or** `is_clipped`). This is the 927-note repair backlog.

**L1 clip% projection:** `is_clipped` is the first signal in `is_union_truncated()` — every clipped note is necessarily in the union set. Corpus-wide verification (22/22 plays): **122 clipped ⊆ 927 union; 0 clip-only notes.** After complete union repair, **L1 clip% projects to 0%** on all plays (not a separate backlog).

### L2 — IA witness traceability (35-note stratified sample)

From `score_note_sample()` in `scripts/nv_ia_witness.py`, matching each sampled note against that play's Internet Archive (or local) witness text:

| Metric | Definition |
|--------|------------|
| **exact%** | Score ≥ 0.95 (near-verbatim in witness) |
| **exact+high%** | exact + high (≥ 0.75); cross-refs auto-pass as exact; short glosses count as high |
| **fail%** | Score < 0.45 (not traceable in witness) |
| **partial%** | 0.45–0.75 (tracked but not in tier gate) |

Sample size: **n=35** per play (or all notes if fewer).

**L2 projection:** King John 97.1% → **100.0%** (stub fix clears the sole sample fail). All other plays retain current exact+high%. Troilus already at 100% on the 1953 local witness.

### Tier A / B / C (`assign_tier()`)

```148:159:scripts/audit_nv_fidelity_all_plays.py
def assign_tier(metrics: dict, l2: dict | None) -> str:
    if metrics["synthetic_prefix"] > 0 or metrics["paraphrase_style"] > 0:
        return "C"
    if metrics["clipped_pct"] > CLIP_MAX_PCT:
        return "B"
    if l2 is None:
        return "A" if metrics["synthetic_prefix"] == 0 else "B"
    if l2["exact_high_pct"] >= TIER_A_L2_MIN and l2["fail_pct"] == 0:
        return "A"
    if l2["exact_high_pct"] >= TIER_A_L2_MIN:
        return "A"
    return "B"
```

- **Tier A:** No synth/para; clip ≤ 4%; L2 exact+high ≥ **85%** (`TIER_A_L2_MIN`)
- **Tier B:** High clip%, or L2 exact+high < 85%, or witness fetch failed
- **Tier C:** Any synthetic or paraphrase-style notes

**"Faithful"** in tier terms = **Tier A**. L2 fail% > 0 does **not** block Tier A if exact+high ≥ 85%.

---

## Per-play chart (current → projected)

| Play | Yr | Notes | L1 (synth / para / clip%) | L2 exact% | L2 exact+high% | L2 fail% | Tier now | Trunc % (n) | Trunc % proj | L1 clip% proj | L2 exact+high% proj | Tier proj | Notes |
|------|-----|------:|---------------------------|----------:|-----------------:|---------:|:--------:|-------------:|-------------:|--------------:|--------------------:|:---------:|-------|
| Romeo and Juliet | 1871 | 720 | 0 / 0 / 0.14 | 85.7 | 100.0 | 0.0 | A | 0.56% (4) | 0% | 0% | 100.0 | A | — |
| Macbeth | 1873 | 1,252 | 0 / 0 / 0.24 | 97.1 | 100.0 | 0.0 | A | 1.28% (16) | 0% | 0% | 100.0 | A | — |
| Hamlet | 1877 | 1,948 | 0 / 0 / 0.15 | 85.7 | 100.0 | 0.0 | A | 2.10% (41) | 0% | 0% | 100.0 | A | — |
| King Lear | 1880 | 1,163 | 0 / 0 / 0.00 | 91.4 | 100.0 | 0.0 | A | 0.00% (0) | 0% | 0% | 100.0 | A | Clean baseline |
| Othello | 1886 | 921 | 0 / 0 / 0.43 | 80.0 | 100.0 | 0.0 | A | 0.98% (9) | 0% | 0% | 100.0 | A | — |
| The Merchant of Venice | 1888 | 1,027 | 0 / 0 / 0.19 | 82.9 | 100.0 | 0.0 | A | 1.46% (15) | 0% | 0% | 100.0 | A | — |
| As You Like It | 1890 | 940 | 0 / 0 / 0.00 | 88.6 | 100.0 | 0.0 | A | 0.00% (0) | 0% | 0% | 100.0 | A | Clean baseline |
| The Tempest | 1892 | 770 | 0 / 0 / 0.13 | 85.7 | 100.0 | 0.0 | A | 3.77% (29) | 0% | 0% | 100.0 | A | — |
| A Midsummer Night's Dream | 1895 | 745 | 0 / 0 / 0.00 | 94.3 | 100.0 | 0.0 | A | 0.00% (0) | 0% | 0% | 100.0 | A | Clean baseline |
| The Winter's Tale | 1898 | 1,109 | 0 / 0 / 0.99 | 85.7 | 100.0 | 0.0 | A | 4.24% (47) | 0% | 0% | 100.0 | A | — |
| Much Ado About Nothing | 1899 | 931 | 0 / 0 / 0.21 | 80.0 | 100.0 | 0.0 | A | 0.43% (4) | 0% | 0% | 100.0 | A | — |
| Twelfth Night | 1901 | 1,068 | 0 / 0 / 0.09 | 77.1 | 100.0 | 0.0 | A | 0.47% (5) | 0% | 0% | 100.0 | A | Lowest exact% (non-KJ) |
| Love's Labour's Lost | 1904 | 1,171 | 0 / 0 / 0.26 | 80.0 | 100.0 | 0.0 | A | 1.45% (17) | 0% | 0% | 100.0 | A | — |
| Antony and Cleopatra | 1907 | 1,053 | 0 / 0 / 0.95 | 88.6 | 100.0 | 0.0 | A | 5.51% (58) | 0% | 0% | 100.0 | A | — |
| Richard III | 1908 | 1,226 | 0 / 0 / 0.41 | 82.9 | 100.0 | 0.0 | A | 2.12% (26) | 0% | 0% | 100.0 | A | — |
| Julius Caesar | 1913 | 723 | 0 / 0 / 0.28 | 97.1 | 100.0 | 0.0 | A | 3.87% (28) | 0% | 0% | 100.0 | A | — |
| Cymbeline | 1913 | 1,035 | 0 / 0 / 0.48 | 94.3 | 100.0 | 0.0 | A | 8.60% (89) | 0% | 0% | 100.0 | A | — |
| King John | 1919 | 1,072 | 0 / 0 / 2.05 | 65.7 | 97.1 | **2.9** | A | **13.99% (150)** | 0% | 0% | 100.0 | A | Only L2 fail in corpus; stub fix assumed |
| Coriolanus | 1928 | 1,523 | 0 / 0 / 1.97 | 88.6 | 100.0 | 0.0 | A | **14.84% (226)** | 0% | 0% | 100.0 | A | Largest truncation backlog |
| Henry IV, Part 1 | 1936 | 738 | 0 / 0 / 0.68 | 77.1 | 100.0 | 0.0 | A | 3.66% (27) | 0% | 0% | 100.0 | A | — |
| Henry IV, Part 2 | 1940 | 1,982 | 0 / 0 / 0.61 | 85.7 | 100.0 | 0.0 | A | 2.37% (47) | 0% | 0% | 100.0 | A | — |
| Troilus and Cressida | 1953 | 621 | 0 / 0 / 0.00 | 85.7 | 100.0 | 0.0 | A | **14.33% (89)** | 0% | 0% | 100.0 | A | L2 already 100% on 1953 witness |
| **CORPUS (22 plays)** | — | **23,738** | **0 / 0 / 0.51** | **85.5** | **99.9** | **0.13** | **22×A** | **3.91% (927)** | **0%** | **0%** | **100.0** | **22×A** | — |

---

## Summary

### Tier changes after projected fixes

**None.** All 22 plays are **Tier A today** and remain **Tier A** after truncation repair and the King John stub fix. No play exceeded the 4% `clip%` ceiling before repair (highest: King John 2.05%); projected clip% is 0% corpus-wide.

### What the fixes actually clear

| Gap type | Before | After (projected) | Plays most affected |
|----------|--------|-------------------|---------------------|
| Union truncation | 927 notes (3.91%) | 0 | Coriolanus (226), King John (150), Cymbeline & Troilus (89 each) |
| L1 clip% (122 notes) | 0.51% corpus | 0% | Subset of union; no clip-only backlog |
| L2 witness fail (sample) | 1 note / 35 in King John (2.9%) | 0% corpus-wide | King John only |
| L2 exact+high (weighted) | 99.9% | 100.0% | King John 97.1% → 100% |

### Plays still not "faithful"?

**None at the Tier A/B/C level** — all 22 qualify as faithful after projection.

**Residual quality notes** (not tier failures):

1. **L2 exact% < 100% on most plays** — Many sampled notes land in the **high** bucket (fuzzy 0.75–0.95 match), not **exact**. Lowest current exact%: King John 65.7%, Twelfth Night & H4P1 77.1%. Tier A only requires exact+high ≥ 85%.
2. **L2 is a 35-note sample**, not exhaustive verification of all ~23.7k notes.
3. **Three plays had zero truncation** before repair (King Lear, As You Like It, Midsummer) — already structurally clean on the exhaustive audit.
4. **Troilus** already scores 100% L2 on the 1953 local witness (`data/troilus_nv_witness.txt`); the 89 truncated notes are an L1/content issue, not a witness-mapping issue.

### Highest truncation repair load

| Rank | Play | Notes to repair |
|------|------|----------------:|
| 1 | Coriolanus | 226 |
| 2 | King John | 150 |
| 3 | Cymbeline | 89 |
| 3 | Troilus and Cressida | 89 |
| 5 | Antony and Cleopatra | 58 |

---

## Bottom line

After completing the **927-note** truncation repair, deploying the King John witness stub fix, and with Troilus on the 1953 witness at 100% L2:

- **22 / 22 plays → Tier A**
- **0% corpus truncation** (`union_truncated`)
- **0% corpus L1 clip%** (122 clipped notes ⊆ union; no separate clip backlog)
- **100% weighted L2 exact+high, 0% fail**
- **0 synthetic / 0 paraphrase notes**

The corpus reaches full tier faithfulness. Remaining variance is in L2 **exact%** on small samples (fuzzy high-tier matches), which the tier system intentionally tolerates.
