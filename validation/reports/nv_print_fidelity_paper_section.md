# Verifying Fidelity to the Print New Variorum

*Draft paper section — July 2026. Intended for insertion into the project paper after the description of the electronic corpus. Tables may be renumbered to match the journal template.*

---

A central claim of this project is that the electronic New Variorum corpus does not invent or paraphrase Furness’s line commentary, but rather makes the printed apparatus available in machine-readable form for the twenty-two plays treated here. That claim is not self-evident: the notes were digitized over time, sometimes truncated mid-sentence, and are checked against Internet Archive OCR that itself contains long‑*s*, ligature, and column-scrambled artifacts. We therefore treat fidelity as an empirical question and answer it with two complementary measurements.

**Completeness** asks whether line commentary is present and structurally whole—whether a note cuts off before the printed edition continues. **Textual fidelity** asks whether the electronic wording matches the corresponding print witness, modulo ordinary OCR noise. Completeness matters for the reader who opens a line and needs the full apparatus; fidelity matters for the claim that what appears on screen is Furness (or Hillebrand/Baldwin for *Troilus and Cressida*, 1953), not a modern rewrite. We do not claim character-perfect identity with print. We claim that the corpus is *substantially complete* and *largely faithful* under explicit, reproducible checks against the print OCR witnesses.

Ground truth for every check is the digitized text of the relevant New Variorum volume (“the witness”), ordinarily the Internet Archive *djvu.txt* stream mapped play-by-play in our witness registry. *Troilus and Cressida* uses a local OCR of the 1953 volume because the matching IA item is lending-restricted. Witnesses run to roughly $10^5$–$10^6$ characters and carry the usual scanning defects; those defects bound how high any automated match rate can rise and must be kept in view when interpreting residual non-matches.

## Completeness: Truncation Detection and Repair

An automated truncation audit over the full corpus (23,715 notes) combines surface signals—missing terminals, mid-sentence grammatical cues, hyphenation cutoffs, unbalanced brackets—with witness-prefix continuity (whether the note’s ending is a literal prefix of unused witness text). That audit originally flagged **927** notes as likely truncated. Those entries were repaired under a strict rule: **append only continuation located verbatim in the witness**; where a genuine gap remained (corrupted OCR region or unlocatable passage), close with an honest ellipsis (`...`) rather than fabricate bridge text. Completions concentrated in *Troilus* used that honest-gap convention more often than other plays, consistent with known corruption in that volume’s OCR.

After repair and merge into the live play JSON, the same truncation heuristic returns **24** union flags on the full corpus (**0.10%**; Table 1). Residual flags cluster on short citations and dictionary-style endings that close on source-faithful unmatched brackets—forms the detector does not always recognize as terminal. Contractor review of an earlier residual set likewise treated remaining detector hits as false positives after line-by-line witness comparison. Independently, a stratified reader-focused sample of 1,100 notes (50 per play, spread across acts) asked only whether the electronic note still supplies the commentary needed for that line—counting truncated or wholly unlocated notes as failures, but treating OCR wording drift and harmless appended apparatus as acceptable. Under that definition, **99.0%** of sampled notes retain usable line material (Table 2).

Together, the census and the sample support a strong completeness claim: structural truncation is now a vanishingly small residue, and readers of randomly selected notes almost always find the line’s apparatus present.

**Table 1.** Exhaustive truncation census after repair (22 plays, 23,715 notes).

| Metric | Value |
|--------|------:|
| Notes audited | 23,715 |
| Union truncation flags | 24 |
| Flag rate | **0.10%** |
| Plays with zero flags | 14 of 22 |

*Union flags = notes matching any truncation signal in `audit_nv_truncation.py` (hard truncation, mid-sentence cut, hyphenation, unbalanced delimiters, and/or witness-prefix continuation). Post-repair audit date aligned with live corpus used for Table 3.*

**Table 2.** Reader-focused stratified sample (50 notes × 22 plays = 1,100).

| Outcome | *n* | % of sample |
|---------|----:|------------:|
| Line commentary present (reader OK) | 1,089 | **99.0** |
| Truncated (missing ending relative to print) | 10 | 0.9 |
| Not located in witness | 1 | 0.1 |
| Cross-reference / short gloss (counted OK) | 117 | — |

*Criterion: fail only if material needed for the line is missing; extra appended apparatus and OCR drift do not count as failure. Approximate 95% Wilson interval on reader-OK rate: about 98.2–99.4%.*

## Textual Fidelity: Full-Corpus Tail Verification

Completeness does not by itself prove that wording tracks print. For fidelity we verified **every** note against its mapped witness by fuzzy-matching the note’s final ~90 characters (normalized for whitespace, apostrophes, long‑*s*, and ligatures) to overlapping chunks of the witness, accepting a partial-ratio score of ≥75. This *tail verification* is deliberately OCR-tolerant and end-sensitive: it catches notes whose endings are absent or badly wrong in the witness, while allowing character-level OCR garble. It does not certify mid-note identity, nor does it punish harmless lengthening.

On the full set of 23,715 notes, **23,194** pass (**97.8%**; Table 3). Of the **521** non-matches (2.2%), score taxonomy shows that **nearly all** are partial mismatches—about **89%** score in the 50–69 band and about **11%** in the near-miss 70–74 band—rather than catastrophic absences (a single note scored below 50). The residual is heavily concentrated in two known hard cases: *Troilus and Cressida* (142 fails; local 1953 OCR is especially noisy) and *Othello* (56 fails; the play file mixes classic Furness lemma apparatus with Folger-indexed / modern gloss forms that cannot be expected to match Furness page OCR). Excluding *Troilus* alone, the corpus pass rate is **98.4%**; the other twenty plays fail at roughly **1.5%**. Pure truncation, measured independently, accounts for only **0.10%** of the corpus. The honest reading of the 2.2% gap is therefore: mostly witness OCR and a play-specific source mismatch, plus a thin genuine residue—not wholesale fabrication or paraphrasing.

We deliberately do **not** headline an earlier full-span sample audit that reported about **77%** strict word-overlap among only those notes the matcher could anchor in OCR. That procedure left most sampled notes *unscored* (unverifiable under brittle anchoring) and classified many bad-window matches as “defective.” It understates fidelity for methodological reasons and is unsuitable as a corpus claim.

**Table 3.** Full-corpus tail verification against mapped print witnesses.

| Play | Notes | Pass | Fail | Pass % |
|------|------:|-----:|-----:|-------:|
| Romeo and Juliet | 720 | 704 | 16 | 97.8 |
| Macbeth | 1,252 | 1,223 | 29 | 97.7 |
| Hamlet | 1,948 | 1,912 | 36 | 98.2 |
| King Lear | 1,163 | 1,148 | 15 | 98.7 |
| Othello | 918 | 862 | 56 | 93.9 |
| The Merchant of Venice | 1,027 | 1,017 | 10 | 99.0 |
| As You Like It | 940 | 913 | 27 | 97.1 |
| The Tempest | 770 | 749 | 21 | 97.3 |
| A Midsummer Night’s Dream | 745 | 724 | 21 | 97.2 |
| The Winter’s Tale | 1,109 | 1,098 | 11 | 99.0 |
| Much Ado About Nothing | 931 | 910 | 21 | 97.7 |
| Twelfth Night | 1,068 | 1,045 | 23 | 97.9 |
| Love’s Labour’s Lost | 1,171 | 1,143 | 28 | 97.6 |
| Antony and Cleopatra | 1,053 | 1,044 | 9 | 99.2 |
| Richard III | 1,226 | 1,222 | 4 | 99.7 |
| Julius Caesar | 723 | 721 | 2 | 99.7 |
| Cymbeline | 1,035 | 1,028 | 7 | 99.3 |
| King John | 1,072 | 1,052 | 20 | 98.1 |
| Coriolanus | 1,503 | 1,495 | 8 | 99.5 |
| Henry IV, Part 1 | 738 | 725 | 13 | 98.2 |
| Henry IV, Part 2 | 1,982 | 1,980 | 2 | 99.9 |
| Troilus and Cressida | 621 | 479 | 142 | 77.1 |
| **Corpus** | **23,715** | **23,194** | **521** | **97.8** |

*Method: last 90 characters of each note; rapidfuzz `partial_ratio` ≥ 75 against overlapping witness chunks. Witnesses: Internet Archive *djvu* text per play registry, except *Troilus and Cressida* (local 1953 OCR). Corpus excluding *Troilus*: 98.4% (22,715 / 23,094).*

## What We Claim—and What We Do Not

On the evidence above, we answer the fidelity question as follows. The electronic corpus **faithfully replicates the printed New Variorum line apparatus for practical scholarly use**: commentary for a given line is almost always present and whole (**0.10%** truncation-flag rate; **99%** reader-sample success), and wording tracks the print witness under OCR-tolerant verification for **97.8%** of all notes. Corpus-wide scans find **no** systematic synthetic preface fabrications or wholesale paraphrase replacements of the kind that would indicate machine-rewritten notes. Residual non-matches are best explained by noisy witnesses (especially *Troilus*), a minority of non-Furness gloss forms in *Othello*, and ordinary threshold/OCR effects—not by missing print apparatus at the order of several percent.

We do **not** claim (1) that every electronic character equals print, (2) that we have counted every printed note against every electronic note in a full coverage census, or (3) that *Troilus* and *Othello* match the cleanest Furness volumes under the same automated bar. Those limits belong in methods caveats; they do not overturn the headline result.

In short: relative to the print New Variorum as witnessed by digitized page text, the electronic corpus is **substantially complete** and **largely faithful**. That is the standard we set for “replication” here—and the empirical record supports it.

---

### Suggested one-sentence methods abstract (optional)

*We verified 23,715 electronic New Variorum notes against mapped print OCR witnesses: after verbatim completion of 927 truncated entries, residual truncation flags fell to 0.10%, a stratified 1,100-note reader sample retained line commentary in 99.0% of cases, and fuzzy tail-matching against witnesses passed for 97.8% of the full corpus.*
