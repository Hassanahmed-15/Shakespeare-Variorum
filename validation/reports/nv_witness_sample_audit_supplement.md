# Supplement S2: Retired Strict Span-Match Audit (the “77%” Figure)

**Status:** Retired for headline reporting; retained here for transparency.  
**Script:** `scripts/audit_nv_witness_sample.py`  
**Artifacts:** `validation/nv_witness_sample/` (last run: 2026-07-08, 50 notes/play)

---

## 1. What this audit measured

Between July 2026 fidelity work and the adoption of corpus-wide **tail verification** (`scripts/verify_all_notes.py`), we ran a **stratified witness sample audit** asking: after locating a note in Internet Archive OCR, does the **full note text** overlap the witness window?

| Parameter | Value |
|-----------|-------|
| Sample design | 50 notes per play × 22 plays = **1,100 notes** (act-stratified) |
| Witness | Mapped IA `djvu.txt` per play (`scripts/nv_witness_map.py`); Troilus local OCR |
| Anchoring | Opening word chain (6–12 words) + fuzzy fallback (`locate_note`) |
| Span | Start anchor + end word chain when possible; else length window |
| Similarity | **Word-bag overlap** on normalized text (tokens ≥3 chars): \|note ∩ witness\| / \|note\| |
| Strict pass | Overlap ≥ **80%** → `faithful` |
| Lenient pass | Overlap 60–79% → `ocr_ok` |
| Defective | Overlap &lt;60%, truncation, apparatus splice, or `not_in_witness` |

This is **not** the same scorer as tail verification (`rapidfuzz.partial_ratio` on the last 90 characters).

---

## 2. Headline numbers (final run, Hamlet witness corrected)

| Bucket | *n* | % of 1,100 |
|--------|----:|-----------:|
| **Faithful (strict)** | 303 | 27.5% |
| OCR-tolerant | 22 | 2.0% |
| Defective | 66 | 6.0% |
| **Uncertain (unanchored)** | **592** | **53.8%** |
| Exempt (cross-ref / gloss) | 117 | 10.6% |

**Reported “77%”** = 303 / **391 verifiable** = **77.5%** strict among notes the matcher could anchor.  
**Only 35.5%** of scored notes (391 / 1,100) entered that denominator.

Lenient among verifiable: **83.1%**.

---

## 3. Why this audit understated fidelity

### 3.1 Silent exclusion of unanchored notes

When the matcher could not anchor a note opening in witness OCR, the verdict was **`uncertain`** and the note was **excluded from the pass-rate denominator**. On the final run, **592 / 1,100 (53.8%)** fell into this bucket—not because the notes were wrong, but because IA OCR is noisy and the anchor logic is brittle (hyphenation, long‑*s*, column breaks, Folger line keys in Othello, etc.).

**Romeo and Juliet** had **0 verifiable notes** in a 50-note sample (100% uncertain) despite **97.8%** tail-verify pass on the full play. Treating “could not anchor” as non-data made the audit **non-comparable** to corpus-wide tail checks.

### 3.2 “Defective” often meant bad anchor, not bad note

Of **66 defective** notes on the final run, manual taxonomy showed:

| Cause | Count | Interpretation |
|-------|------:|----------------|
| Word overlap &lt;35% after anchor | **47** | Matcher landed in **wrong witness window**; note lemmas often still present elsewhere in witness |
| Apparatus splice (extra line-N material appended) | **9** | Reader-acceptable extra content under project definition |
| Likely OCR (overlap 35–54%) | **6** | Genuine noise band |
| Near-miss (55–64%) | **2** | Threshold band |
| Not in witness | **2** | Short cross-refs |

**~71% of “defectives”** were measurement failures or acceptable extra material—not demonstrated paraphrase or fabrication.

### 3.3 Word-bag overlap is a weak full-span scorer

The metric ignores token order and punishes length mismatch harshly. A note that is a **correct prefix** of a longer witness span scores poorly if the window includes adjacent apparatus. Notes repaired by appending IA witness text can score as “extra content” (length ratio &gt;1.35 with overlap &lt;85%).

### 3.4 Witness mapping error (Hamlet)

An early run mapped Hamlet to `newvariorumediti11shak`—a volume of **critical essays**, not line apparatus—producing false uncertain/defective rates. The map was corrected to `anewvariorumedi07furngoog`. The Hamlet subsample was **unchanged** (13 faithful / 25 uncertain / 5 defective), showing most Hamlet failures were anchor/OCR limits, not wrong volume alone.

### 3.5 Ingest vs verify OCR lineage

Note text was ingested from **page-image OCR + Gemini**; witnesses are **IA `djvu.txt` OCR** (independent passes). Expecting high **character-level** span overlap across engines was optimistic; tail-verify (ends only, fuzzy) is better aligned with that split.

---

## 4. What replaced it

| Audit | Scope | Question | Corpus headline |
|-------|-------|----------|-----------------|
| **Tail verify** | All 23,715 notes | Does note **ending** appear in witness? | **97.8%** |
| **Truncation census** | All notes | Is note structurally cut off? | **0.10%** flags |
| **Reader sample** | 1,100 notes | Is line commentary present? | **99.0%** |
| **Full-span sample** (new) | ~308 notes | Does **entire** anchored note match witness span? | See `validation/nv_fullspan_sample/` |

The **77% figure should not appear** in the abstract or main fidelity claim. If cited at all, it must be labeled a **retired lower-bound sample** under a brittle metric, with unanchored notes excluded.

---

## 5. Reproduction

```bash
python3 scripts/audit_nv_witness_sample.py --sample-n 50
```

Outputs: `validation/nv_witness_sample/manifest.json`, `results.json`, `rate_table.md`.

---

## 6. Relation to new full-span sample (S3)

The replacement audit (`scripts/audit_nv_fullspan_sample.py`) addresses several failures of this retired audit:

1. **Reports unanchorable count explicitly** (does not drop silently from headline only).
2. Uses **`fuzz.ratio`** on fully normalized strings (same 75 cutoff philosophy as tail verify, stricter scorer).
3. Separates **interior divergence** (tail passes, full span fails)—cases tail-verify cannot see.
4. Smaller sample (~14/play, ~308 total) for referee-requested full-span check without reintroducing the 77% headline.

See `validation/nv_fullspan_sample/rate_table.md` for results.

---

## Adjudicated examples: automated failures attributable to witness OCR degradation

Three illustrative cases from the 60 interior-divergence notes adjudicated 2026-07-08 as `witness_ocr_degradation` (full packets: `validation/nv_fullspan_sample/interior_divergence_adjudication.{md,json}`).

### (i) Column-scrambling — Furness two-column apparatus interleaved

**Hamlet** — ACT 3 SCENE 1 / line 38 / note 0  
**Automated scores:** full_ratio 39.6, tail_ratio 100.0  
**Degradation type:** Two-column variant apparatus interleaved into a single OCR stream (Furness `anewvariorumedi07furngoog`).

**Note (electronic):**

> lawful espials] STEEVENS: Spies. CALDECOTT: Spies justifiably inquisitive. SINGER: 'An espiall in warres, a scoutwatch, a beholder, a viewer.'—Baret ELZE: These words are superfluous, injurious to the metre, and imply a justification unworthy of a king.

**Witness span (bounded):**

> lawful espials] Cm. Qq, Pope,  
> Theob. Han. Warb. Cap. Jen. Mai. El.  
> Ktly.  
>  
> 33. Will] nWleQ<\.  
> unseen] and un/een Q*76.  
>  
> 34. frankly] franckly Q^Qy franckely  
> Q^. frankcly F,F,. Oni. Q^e.  
>  
> 36. the affliction] Q'76. th' affUilion  
> QqFf, Rowe + , Jen. Coll. El. While,

The electronic note is continuous critical prose; the witness window captures collated variant readings from adjacent columns, not the note body.

### (ii) Long-s / ligature / character garble with play-text splice

**Macbeth** — ACT 2 SCENE 2 / line 6 / note 0  
**Automated scores:** full_ratio 62.4, tail_ratio 97.4  
**Degradation type:** Play-text column spliced into commentary span; long-s orthography and OCR ligature noise (`haue`, `Hue`, `Poffets`, `furfeted`).

**Note (electronic):**

> Bell-man] CLARENDON: The full significance of this passage may be best shown by comparing the following lines from Webster's Duchess of Malfi, IV, ii, where Bosola tells the Duchess: 'I am the common bellman, That usually is sent to condemn'd persons The night before they suffer.' Here, of course, Duncan is the condemned person. Compare also Spenser's Faerie Queene, V, c. vi, v. 27, where the cock is called 'the native belman of the night.' …

**Witness span (bounded, excerpt):**

> Bell-man] Clarendon : The full significance of this passage may be best  
> shown by comparing the following lines from Webster's Duchess of Malfi, IV, ii,  
> where Bosola tells the Duchess : ' I am the common bellman, That usually is sent  
> to condemn' d persons The night before they suffer.' Here, of course, Duncan is  
>  
>  
> 128 THE TRAGEDIE OF MACBETH [act ii, sc. ii.  
>  
> He is about it, the Doores are open : j  
> … I haue drugged their Poffets, … Whether they Hue, or dye.

The bounded span begins correctly but mid-note jumps into running play text and variant apparatus before resuming commentary.

### (iii) Lowest automated full-span score (0–49 band) — same passage still recognizable

**Hamlet** — ACT 2 SCENE 2 / line 613 / note 0  
**Automated scores:** full_ratio 49.2, tail_ratio 93.1 (score bucket 0–49)  
**Degradation type:** Truncated witness window and critic-attribution mismatch at note opening (OCR/span boundary), not paraphrase.

**Note (electronic):**

> peak] SINGER: To mope, to act foolishly and with irresolution.

**Witness span (bounded):**

> peak] Steevens has a long note to prove that this is the emphatic

Both strings open on the same lemma and discuss the same gloss; the automated scorer penalizes the short electronic note against a longer, differently attributed witness opening.
