# NV Witness Sample — Reader-Focused Accuracy

**Same sample:** 50 notes/play × 22 plays = 1,100 notes (act-stratified)  
**Question:** Does the note contain the commentary the reader needs for **this line**?

## What counts as a problem

| Counts as **OK** | Counts as **FAIL** |
|---|---|
| Line commentary present in the print Variorum (witness locates) | **Truncated** — note cuts off before the edition continues |
| Extra material appended (reader can skip) | **Not in print** — cannot locate in any witness volume |
| OCR noise / wording drift | |
| Apparatus from another line appended at the end | |

## Results

| Metric | n | % |
|--------|--:|--:|
| **Has line material** | **1,089** | **99.0%** |
| Missing end (truncated) | 10 | 0.9% |
| Not found in print | 1 | 0.1% |
| Cross-ref / short gloss (exempt) | 117 | (included in OK) |

**Reader-critical error rate: 1.0%** (11 / 1,100)

Compare to strict span-match audit on the same sample: **17.2% defective** among verifiable notes.

## Truncated notes in sample (10)

| Play | Reference |
|------|-----------|
| Romeo and Juliet | ACT 3 SCENE 3 / line 130 / note 0 |
| Othello | ACT 1, SCENE 1 / line 1.1.53 / note 0 |
| The Tempest | ACT 4 SCENE 1 / line 79 / note 3 |
| King John | ACT 4 SCENE 1 / line 2 / note 0 |
| King John | ACT 4 SCENE 2 / line 287 / note 0 |
| King John | ACT 4 SCENE 3 / line 115 / note 0 |
| King John | ACT 5 SCENE 1 / line 76 / note 2 |
| King John | ACT 5 SCENE 2 / line 81 / note 1 |
| King John | ACT 5 SCENE 4 / line 63 / note 0 |
| King John | ACT 5 SCENE 6 / line 18 / note 1 |

## Not in print (1)

| Play | Reference |
|------|-----------|
| Richard III | ACT 2 SCENE 1 / line 105 / note 0 (short cross-ref) |

## Note on famous passages

Hamlet “To be or not to be” (ACT 3 SCENE 1 / line 70): **both notes pass** under this definition — Johnson/Hunter commentary is present; appended line-58 apparatus is extra, not missing material.

## Caveat

Sample estimate only. Truncation rate (~0.9%) aligns with the corpus truncation audit (~0.8% post-repair). King John is over-represented in the truncated bucket.
