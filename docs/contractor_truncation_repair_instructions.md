# Contractor Package: NV Truncation Ground-Truth Repair

**Copy-paste email intro (for contractor outreach):**

---

Subject: Shakespeare New Variorum — manual repair of truncated scholarly notes (~927 items)

Hello,

We need help completing **927 truncated editorial notes** in our digital Shakespeare Variorum dataset. Each note is a scholarly apparatus entry from the 19th/early-20th-century *New Variorum* editions (Furness and successors). Our automated extraction clipped many notes mid-sentence; your job is to restore each note to match the **printed edition** using the linked Internet Archive volume.

You will receive:
- This instruction document
- `contractor_truncation_workbook.csv` (Excel-friendly) or `.json` — one row per note

Ground truth is always the **Internet Archive scan** of the correct NV volume for that play (witness URL provided per row). Do not paraphrase, summarize, or invent text. Transcribe the missing continuation exactly, preserving original spelling, punctuation, and citation style.

When finished, return the completed workbook with `status` set to `complete` (or `no_change_needed` with an explanation in `contractor_notes`). Payment is released after our automated verification passes (zero truncated notes remaining, spot-checks against IA witnesses).

Please confirm receipt and estimated turnaround.

Thank you,

---

## 1. What this job is

The Shakespeare Variorum project digitizes the **New Variorum (NV)** critical apparatus: long scholarly notes keyed to individual lines of each play. During OCR and automated ingestion, **~927 notes** (as of the latest audit) were cut off before their natural ending — mid-word, mid-sentence, or before a closing citation bracket.

Your task: **for each workbook row, produce the full note text as it appears in the printed NV edition**, so the digital note ends with proper scholarly punctuation (period, `]`, `—Ed.]`, etc.) and contains no missing prose.

**Scope:** 22 plays, **927 union-truncated notes** (current count from `validation/nv_truncation_audit.json`). The workbook includes every note flagged by any truncation signal, not only a subset from earlier repair phases.

**You are NOT editing the play dialogue** — only the `notes` strings attached to line entries.

---

## 2. Ground-truth source: Internet Archive NV volumes

Each row includes:

| Field | Meaning |
|-------|---------|
| `witness_ia_id` | Internet Archive identifier for the correct NV volume |
| `witness_url` | Direct link: `https://archive.org/details/{witness_ia_id}` |

Witness mapping is canonical per play (see `scripts/nv_witness_map.py` in the repo). **Do not substitute a different edition** unless the row's witness is unavailable; contact us first.

### How to use the witness

1. Open `witness_url` in a browser.
2. Use IA's **search** (Ctrl/Cmd+F) on the DjVu/text layer, or read the scanned pages.
3. Locate the note by its **opening words** — the `current_note_text` column gives the full clipped text; the note almost always begins with a critic's name in caps and a bracket, e.g. `JOHNSON:]` or `STEEVENS (ed. 1793):]`.
4. Also search for **line-number cues** embedded in notes (e.g. `117.`, `64.`) and the **lemma** (the word or phrase being glossed).
5. Transcribe from the first character of the note through its **complete ending** in print.

**Troilus and Cressida** may use a fallback witness (Vol. XXII) when the canonical 1953 volume is restricted on IA; the workbook row still lists the IA id used for verification.

---

## 3. Workbook columns

| Column | Description |
|--------|-------------|
| `play_name` | Full play title |
| `play_file` | JSON filename stem (informational) |
| `act_scene` | Scene key, e.g. `ACT 3 SCENE 1` |
| `line_key` | Line number within scene |
| `note_index` | 0-based index when multiple notes exist on one line |
| `current_note_text` | **Full** truncated note as it exists now — your starting point |
| `truncation_signals` | Why the audit flagged it (see §5) |
| `witness_ia_id` | IA identifier |
| `witness_url` | Full archive.org link |
| `status` | Set to `pending` → change to `complete` or `no_change_needed` |
| `completed_note_text` | **You fill this** with the full corrected note |
| `contractor_notes` | Optional notes to reviewer (required if `no_change_needed`) |
| `char_count_before` | Length of original (auto) |
| `char_count_after` | Length of your completed text (you may fill, or we compute on import) |

### Deliverable format

Return **either**:

- `contractor_truncation_workbook.json` — same structure as provided, with your edits, **or**
- `contractor_truncation_workbook.csv` — same columns, Excel-friendly

**Required on every row:**

- `status`: `complete` **or** `no_change_needed`
- If `complete`: `completed_note_text` must contain the **entire** note (not a diff/patch — paste the full string)
- If `no_change_needed`: explain in `contractor_notes` (e.g. false positive, cross-reference only, note intentionally ends at citation)

---

## 4. Step-by-step workflow (per note)

1. **Read** `current_note_text` and `truncation_signals`.
2. **Open** `witness_url`.
3. **Find** the matching note in the printed apparatus (search opening phrase + line number).
4. **Compare** print ending to digital ending — identify exactly where truncation occurred.
5. **Transcribe** the complete note from print into `completed_note_text`.
   - Preserve original spelling (`lov'd`, `ne'er`, `&c.`).
   - Preserve citation brackets, em-dashes, and Latin.
   - Join hyphenated line-break fragments (`Ca-` + `lamity` → `Calamity` only if print has no hyphen).
6. **Set** `status` to `complete` and update `char_count_after`.
7. **Move** to the next row.

**Tips for hard lookups:**

- Notes often follow the play line in the NV page layout; navigate to the act/scene in the witness.
- If a note quotes another play, the witness may continue across column breaks — keep reading until the note's closing `]` or `—Ed.]`.
- Multiple notes on one line are distinguished by `note_index` (0, 1, 2…).

---

## 5. Truncation signals (reference)

The audit flags a note if **any** of these apply:

| Signal | Meaning |
|--------|---------|
| `is_clipped` | Ends on a stop-word, comma/semicolon, or short unclosed parenthesis |
| `hard_truncation` | Missing terminal punctuation or ends with a short word fragment |
| `mid_sentence_cut` | Ends with a lowercase letter (prose clearly continues) |
| `hyphen_artifact` | Ends with `-` from column/page line break |
| `unbalanced_parens` | More `(` than `)` without a scholarly closer |
| `witness_prefix` | IA witness text continues after where the note ends |

If you believe a flag is a **false positive** and the note is complete in print, use `no_change_needed` and document why.

---

## 6. What NOT to do

| Do not | Why |
|--------|-----|
| Paraphrase or summarize | We need verbatim NV text |
| Invent missing words | Only transcribe what is in print |
| Modernize spelling or punctuation | Match the edition |
| Edit play dialogue (`play` field) | Notes only |
| Return only the "missing tail" | `completed_note_text` must be the **full** note |
| Change critic attribution or line numbers | Must match print |
| Use a different NV edition than the witness | Breaks verification |

---

## 7. Quality criteria (acceptance)

A completed row is acceptable when:

1. **Complete** — note ends with NV-style terminal punctuation (`."`, `.]`, `—Ed.]`, `ff.]`, etc.).
2. **Longer** — `completed_note_text` is at least as long as `current_note_text` (strictly longer unless `no_change_needed`).
3. **Prefix preserved** — opening of completed text matches the original clipped note.
4. **Witness-aligned** — a substantial prefix of the note body appears in the IA witness text.
5. **Verbatim** — spot-checks by our team match the scanned page.

---

## 8. How verification works (payment gate)

After you return the workbook, we run:

```bash
# Apply your completions into the dataset (dry-run first)
python3 scripts/apply_contractor_completions.py --workbook validation/contractor_truncation_workbook.json --dry-run

# Apply for real
python3 scripts/apply_contractor_completions.py --workbook validation/contractor_truncation_workbook.json

# Payment gate — must pass
python3 scripts/verify_contractor_completions.py --workbook validation/contractor_truncation_workbook.json
```

**Payment is released when:**

- Every workbook row has `status` ∈ {`complete`, `no_change_needed`}
- `complete` rows have non-empty `completed_note_text`
- `no_change_needed` rows have non-empty `contractor_notes`
- Re-audit shows **0 union-truncated notes** across all 22 plays (or documented exceptions we approve)
- Spot-checks against IA witnesses pass

You do not need repo access for verification — we run these scripts on our side.

---

## 9. Play-level truncation counts (audit snapshot)

| Play | Union-truncated |
|------|-----------------|
| Romeo and Juliet | 4 |
| Macbeth | 16 |
| Hamlet | 41 |
| King Lear | 0 |
| Othello | 9 |
| The Merchant of Venice | 15 |
| As You Like It | 0 |
| The Tempest | 29 |
| A Midsummer Night's Dream | 0 |
| The Winter's Tale | 47 |
| Much Ado About Nothing | 4 |
| Twelfth Night | 5 |
| Love's Labour's Lost | 17 |
| Antony and Cleopatra | 58 |
| Richard III | 26 |
| Julius Caesar | 28 |
| Cymbeline | 89 |
| King John | 150 |
| Coriolanus | 226 |
| Henry IV, Part 1 | 27 |
| Henry IV, Part 2 | 47 |
| Troilus and Cressida | 89 |
| **TOTAL** | **927** |

Counts reflect `validation/nv_truncation_audit.json` as of package generation. King Lear and As You Like It / Midsummer have **zero** flagged notes — they will not appear in the workbook.

---

## 10. Questions

Contact the project owner for:

- Witness access issues (401, missing scan)
- Ambiguous note boundaries
- Suspected duplicate or mis-keyed line references

---

*Package generated from live play JSON and `audit_nv_truncation.py` heuristics. Workbook: `validation/contractor_truncation_workbook.json` / `.csv`.*
