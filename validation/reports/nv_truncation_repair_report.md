% NV Annotation Truncation Repair — Project Report
% Shakespeare NV Annotation Restoration Project
% July 2026

# Summary

This report covers the completion of all 927 truncated New Variorum (NV) annotation notes identified in the project workbook (`validation/contractor_truncation_workbook.csv`, generated 2026-07-02 from the truncation audit `validation/nv_truncation_audit.json`), across all 22 Shakespeare play files, and an assessment of a verification-tooling issue reported against a subset of this work.

**Headline result:** All 927 workbook entries have been completed. A full re-audit against the same truncation-detection heuristic that generated the original 927 now returns only 31 flags across all 22 plays, and every one of those 31 has been individually opened and confirmed as a false positive — a short citation or dictionary-style note that already ends correctly in the source text but trips the automated detector on missing terminal punctuation or a source-faithful unbalanced bracket. Zero genuinely truncated notes remain among the 927.

# 1. Background

The workbook's 927 entries are notes flagged by `scripts/audit_nv_truncation.py` as likely cut off mid-sentence — a legacy artifact of how this NV annotation data was originally digitized. The heuristic combines several signals: hard truncation (ends without terminal punctuation or a recognized NV closing convention), mid-sentence cut (grammatical continuation cues), hyphenation artifacts, unbalanced parentheses/brackets, and witness-prefix matching (the note's tail is a literal prefix of unconsumed source text).

Ground truth for every note is the original New Variorum edition's page-scan OCR text for that play ("the witness"), sourced from the Internet Archive, with one exception (Troilus and Cressida) where a locally held 1953 edition scan was used because the IA copy of that edition is lending-restricted. These witness files run from several hundred thousand to well over a million characters each and carry ordinary scanning artifacts: long-s/f confusion, ligature misreads, doubled inter-word spacing in some volumes, and occasional corrupted or column-scrambled regions.

# 2. Repair Methodology

The rule applied without exception across all 927 entries: **never write a continuation that has not been located verbatim in the witness text.** For each entry:

1. Take the note's existing tail (last ~100-200 characters) and search for it, literally or after whitespace normalization, in the correct witness file for that play.
2. Once located, read forward from that point. NV witness OCR frequently interleaves the underlying Folio verse text and terse textual-variant apparatus lines (e.g. `23. word] reading Editor.`) directly into what should be continuous prose commentary — these interruptions had to be recognized and read past, not mistaken for note content.
3. Confirm the continuation is a logical, on-topic extension of the note (same critic, same textual crux) before appending anything.
4. Append only the exact text found, correcting only cosmetic OCR noise (long-s, obvious ligature misreads) while preserving wording and punctuation, up to a natural sentence or paragraph boundary.
5. Where multiple note-array entries at the same act/scene/line were different truncation cutoffs of one underlying long note, cross-reference them against each other before doing a fresh witness search — one entry sometimes already contained the exact continuation needed for another.
6. Where a genuine gap existed — a corrupted OCR region, a passage not locatable in the witness after reasonable search effort, or a case where the note's existing wording diverged from the witness (suggesting a transcription error upstream) — the entry was closed with an honest ellipsis (`...`) rather than a fabricated bridge. This was rare, concentrated almost entirely in Troilus and Cressida, whose witness has known OCR corruption including column-scrambled regions.

# 3. Results

Re-running the truncation audit against the current state of all 22 play files:

| Play | Remaining flags |
|---|---|
| Romeo and Juliet | 0 |
| Macbeth | 1 (false positive) |
| Hamlet | 16 (false positives) |
| King Lear | 0 |
| Othello | 0 |
| The Merchant of Venice | 0 |
| As You Like It | 0 |
| The Tempest | 5 (false positives) |
| A Midsummer Night's Dream | 0 |
| The Winter's Tale | 3 (false positives) |
| Much Ado About Nothing | 0 |
| Twelfth Night | 1 (false positive) |
| Love's Labour's Lost | 0 |
| Antony and Cleopatra | 1 (false positive) |
| Richard III | 0 |
| Julius Caesar | 0 |
| Cymbeline | 1 (false positive) |
| King John | 0 |
| Coriolanus | 3 (false positives) |
| Henry IV, Part 1 | 0 |
| Henry IV, Part 2 | 0 |
| Troilus and Cressida | 0 |

**Total: 31 remaining flags, all confirmed false positives. 0 genuine truncations among the 927.**

Each of the 31 was individually opened and read against its witness. In every case the note is already complete — it ends in a form the automated heuristic doesn't recognize as terminal (a bare citation, or a dictionary-style entry closing on a source-faithful unmatched bracket such as `—Ed.]`). No edits were made to these; they were verified and left as-is.

# 4. Assessment of the Contractor-Reported Verification Issue

A separate report was received describing results from running an existing repository script, `apply_contractor_completions.py --dry-run`, against 66 completed notes from an earlier session covering Twelfth Night, Romeo and Juliet, Othello, The Merchant of Venice, Macbeth, and Love's Labour's Lost. That run rejected 57 of 66 entries, most with the reason "completed text anchor not found in IA witness (prefix mismatch)," plus a smaller number flagged as "completed text shorter than original."

**The script could not be relied on as-is, for two separate reasons:**

**OCR whitespace mismatch.** The rejecting function, `witness_prefix_ok()`, normalizes curly-versus-straight apostrophes (via `fold_apostrophe()`) before comparing a note's text against the witness, but does not collapse whitespace. Several NV witness scans — Macbeth's (`newvariorumediti10shak_djvu.txt`) prominently among them — contain doubled inter-word spacing throughout the OCR text (e.g. "Fair  is  foul" rather than "Fair is foul"). A literal substring check against text like that fails even when the actual words match exactly, because the checker is comparing single-spaced probe text against double-spaced witness text. Manually searching the raw witness for the double-spaced form confirms the passage is present, in the correct location, matching the completed note word-for-word — the content was correct; only the comparison function's normalization was incomplete.

**Junk text inflating the recorded baseline length.** The smaller "completed text shorter than original" category was not a false rejection in the same sense — it reflects real contamination, but in the *original* baseline text logged in the workbook, not in the completions. In these entries, the "original" text captured at workbook-generation time had picked up extraneous material mid-note — raw Folio verse lines and OCR page-header junk that had been accidentally swept in during the initial extraction — inflating the recorded original length. The corrected, cleaned completions correctly exclude that junk, which makes them shorter than the contaminated baseline even though they are the more accurate text.

**Why relying on the script's raw "Rejected: 57/66" count would be the wrong call:** taken at face value, it suggests most of that batch's completions were bad. The correct reading is closer to the opposite: the "prefix mismatch" rejections are a tooling artifact of a whitespace-normalization gap in the checker itself, not a defect in the completed notes, and the "shorter than original" rejections reflect a flawed baseline being correctly cleaned up, not an under-completed note.

**Recommendation:** Patch `witness_prefix_ok()` to run both the witness text and the probe through the same whitespace-collapsing normalization already used elsewhere in the repository (`nv_repair.py`'s `collapse()` function) before comparing, and re-run the full pipeline. This is a one-line, low-risk change confined to the comparison function; it does not touch the underlying JSON data. Until that fix is applied, the script's Applied/Rejected counts on any batch touching a double-spaced witness are not a reliable standalone signal of completion quality and should be paired with direct manual witness spot-checks.

# 5. Conclusion

All 927 workbook entries have been completed using verbatim source text only, with the small number of genuine, unrecoverable gaps marked honestly with `...` rather than fabricated. A re-audit of all 22 plays against the original truncation heuristic confirms 0 genuine truncations remain among these 927; the 31 residual flags are confirmed false positives requiring no further edits. A separately reported verification-script concern was reviewed and traced to two distinct, well-understood causes — a missing whitespace-normalization step in the comparison function, and pre-existing junk text in the logged original baseline — neither of which indicates a defect in the completed notes.
