# Stage 2 Gemini System Prompt Audit

**Source:** subagent `389de79f` (repository search, 2026-07-09)

## Finding

The **verbatim Stage 2 Gemini system prompt is not in this repository.** No notebook (`.ipynb`), ingest script, or prompt file contains the text sent to Gemini during OCR ingest. Repo-wide search for `Google Gemini`, `genai`, `GenerativeModel`, and Stage 2 ingest code returns only methodology prose and literature memos—not deployable prompt strings.

The only in-repo claim about what the prompt *instructed* appears in methodology generator scripts (secondhand description, not the prompt itself).

## Primary source quotes

### `scripts/update_methodology_v2.py` line 124

> **Stage 2: LLM-Augmented Validation.** We passed each page's raw OCR output to Google Gemini (selected for its 1M-token context window, which permitted processing an entire volume's worth of surrounding pages as disambiguation context). The model received the OCR text alongside the original page image and a system prompt instructing it to: correct character-level OCR errors, restore truncated abbreviations, re-join citations split across OCR blocks, and preserve the italic/roman distinction using Markdown conventions.

### `scripts/update_methodology.py` line 148

> **Stage 2: LLM-Augmented Validation and Error Correction.** We employed Google Gemini as a contextual validation layer, selected specifically for its large context window capacity, which permitted processing entire pages while maintaining awareness of the relationships between play text, commentary, and footnote apparatus. The model received both the raw OCR output and, where available, the original page image, enabling it to identify and correct character-level errors that standard OCR post-processing heuristics would miss. Gemini proved particularly effective at three categories of correction: (1) resolving abbreviated citations where single-character OCR errors rendered references unidentifiable (e.g., distinguishing "Steev." from "Steeu." or "Clar." from "Clar,"); (2) accurately reading dense footnote typography where character boundaries were ambiguous; and (3) preserving the complex typographic conventions of historical scholarly editions, including italicized lemma markers, parenthetical attributions, and nested quotation structures.

**Note:** v2 line 124 is the only line that explicitly says "a system prompt instructing it to…" v1 line 148 describes observed correction behavior; it does not quote prompt text.

## (a) Permitted operations — from line 124 only

| # | Operation | Exact quote (`update_methodology_v2.py:124`) |
|---|-----------|-----------------------------------------------|
| 1 | Character-level OCR repair | "correct character-level OCR errors" |
| 2 | Abbreviation restoration | "restore truncated abbreviations" |
| 3 | Citation reunification | "re-join citations split across OCR blocks" |
| 4 | Italic/roman markup | "preserve the italic/roman distinction using Markdown conventions" |

Inputs also described at line 124: raw OCR text, original page image, volume-level surrounding context (1M-token window).

## (b) Prohibitions — not in any prompt file

No repository file contains negative instructions ("do not…") from the Stage 2 Gemini system prompt.

`validation/literature_review/insertable_literature_memo.md` line 21 lists prohibitions as **author inference**, not prompt quotes:

> The model is **not** instructed to modernize spelling, paraphrase commentary, interpolate missing material, or continue truncated passages beyond what the page image supports.

The same line also states "The system prompt constrains the model to **transcription repair**, not editorial rewriting"—that framing is memo prose; it is not backed by a recoverable prompt string in-repo.

| Claimed prohibition (memo L21) | In prompt file? | Evidence |
|--------------------------------|-----------------|----------|
| No spelling modernization | No | Author inference |
| No paraphrase of commentary | No | Author inference |
| No interpolation of missing material | No | Author inference |
| No continuation beyond page image | No | Author inference |
| Transcription repair only (not editorial rewrite) | No | Author inference |

## Recommendation

1. **Recover the prompt** from the original ingest notebook, deployment logs, or API call history if the paper needs a verbatim block quote.
2. **Until recovered**, describe Stage 2 constraints indirectly, e.g. *"Our methodology describes the prompt as instructing the model to correct character-level OCR errors, restore truncated abbreviations, re-join split citations, and preserve italic/roman distinction via Markdown"*—do **not** present memo prohibitions or paraphrased bullet lists as verbatim prompt text.
3. **Distinguish sources:** cite `update_methodology_v2.py:124` for permitted ops; treat `insertable_literature_memo.md:21` as drafting guidance only unless validated against the recovered prompt.

## Files checked (not Stage 2 ingest prompt)

- `PROMPT_notebook_llm_concise.txt` — line-number correction task (unrelated)
- `PROMPT_correct_scholarly_line_numbers.md` — line-number correction (unrelated)
- Analysis-tier system prompts in `scripts/update_methodology_v2.py` (~L210+) — Full Fathom Five reader analysis, not ingest
