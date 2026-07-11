# Seed Papers Summary — Literature Review Coordination

*Generated from PDF extraction of three seed papers (July 2026).*

---

## 1. Boros et al. (2024) — LaTeCH-CLfL

**Citation:** Boros, Emanuela, Ehrmann, Maud, Romanello, Matteo, Najem-Meyer, Sven and Kaplan, Frédéric. (2024) *Post-Correction of Historical Text Transcripts with Large Language Models: An Exploratory Study*, LaTeCH-CLfL 2024, pp. 133–159.

### Core method

| Dimension | Detail |
|-----------|--------|
| **Task** | Zero-/few-shot LLM post-correction of noisy historical transcripts (OCR, HTR, ASR) — text-only; no page images |
| **Models (14)** | GPT-2, GPT-3, GPT-3.5, GPT-4; BLOOM/BLOOMZ (560M–7.1B); OPT (350M, 6.7B); LLaMA / LLaMA-2 (7B) |
| **Datasets (8)** | icdar-2017/2019 (OCR, newspapers/monographs, EN/FR); overproof (AU newspapers); impresso-nzz (ABBYY OCR, black letter); ajmc-primary / ajmc-mixed (Tesseract, classical commentaries, mixed scripts); htrec (HTR, Byzantine Greek); ina (ASR, French radio) |
| **Prompts (5)** | Basic-1 (“Correct the text”); Basic-2 (spelling/grammar); Complex-1 (OCR/historical context); Complex-2 (structured “TEXT TO CORRECT / CORRECTED TEXT”); Complex-3 (Complex-2 translated per language) |
| **Settings** | Zero-shot and few-shot (3 demo examples from lowest quality bands); single-pass generation; output post-processing (trim prompts, discard outputs >1.5× input length) |
| **Text units** | Line, sentence (aligned to GT then split), region (full document) |
| **Primary metric** | **Post-Correction Improvement Score (PCIS)** — relative change in Levenshtein similarity to ground truth between original transcription and LLM output |
| **Qualitative eval** | ~2,500 manual annotation pairs; 10-category error taxonomy in 4 groups (C1 unanswered; C2 slight deviation; C3 strong deviation/hallucination; C4 bad GT) |

### Key findings

- **Overall: LLMs usually degrade historical transcripts.** Even the “best” setup (sentence-level, Complex-2, zero-shot, post-processed) mostly lowers quality; the research question becomes which setup is “least worst.”
- **Prompting:** Generic “correct text” prompts cause the strongest degradation; informing the model that input is OCR/ASR/HTR and constraining output format helps modestly. Few-shot almost always hurts except marginally for GPT-3.5/4.
- **Models:** GPT-3.5 and GPT-4 best; smallest open models ≈ GPT-2/3. BLOOMZ beats BLOOM on multilingual ajmc-mixed; GPT-4 alone rescues htrec from severe degradation.
- **Document type:** Atypical material (ajmc mixed scripts, htrec papyri) degrades most; newspaper OCR closer to training distribution fares less badly.
- **OCR quality bands:** Noisiest inputs sometimes improve (room to correct); near-clean inputs are often **over-corrected** — a major failure mode.
- **Manual analysis:** Majority of errors are C3 (strong deviation); dominant behaviors include **pure hallucination** (LLaMA-2-7B, BLOOMZ-7.1B), **paraphrase instead of correction** (GPT family), **text continuation** (LLaMA-2-7B), **partial answers** (BLOOMZ), **embellishment** (GPT-4).

### Limitations (authors')

- Single-pass generation only (time/budget/compute).
- GT alignment/segmentation imperfect; GT itself not guaranteed perfect.
- Few-shot examples randomly chosen, not curated.
- Aggregated results; finer per-setting analysis deferred.

### Recommendations for historical / scholarly text

Explicit future-work directions (not a prescriptive “how-to” for editors):

1. **More tailored prompts** per document type.
2. **Separate error detection and correction** (chain-of-thought).
3. **Temperature search**, **fine-tuning**, **model self-evaluation**.
4. **Consolidate error taxonomy** on focused datasets.
5. Implicit lesson from results: unconstrained generative correction is **not** a scalable fix for heritage backlogs; neural seq2seq post-correction (Amrhein & Clematide 2018; Nguyen et al. 2020; Rigaud et al. 2019) and **re-transcription / re-OCR pipelines** (Schneider & Maurer 2022) remain the serious alternatives.

Background framing stresses that historical sources require **no change to already-correct text** (Schaefer & Neudecker 2020) — directly at odds with LLM over-correction.

### Related-work bibliography (LLM OCR / HTR / post-correction)

**Neural post-correction & benchmarks**

- Amrhein & Clematide (2018) — supervised OCR error detection/correction, statistical + NMT
- Chiron et al. (2017a,b) — ICDAR post-OCR competitions; downstream impact on search/NLP
- Nguyen et al. (2020) — BERT for post-OCR detection/correction
- Rigaud et al. (2019) — ICDAR 2019 post-OCR competition
- Gupta et al. (2021) — unsupervised multi-view post-OCR with LMs
- Soper et al. (2021) — BART fine-tuned for historical newspaper post-correction
- Schaefer & Neudecker (2020) — two-step automatic OCR post-correction
- Schneider & Maurer (2022) — rerunning OCR workflows
- Todorov & Colavizza (2020, 2022) — transfer learning; language modeling on historical OCR
- van Strien et al. (2020) — impact of OCR on digital library use
- Evershed & Fitch (2014) — context-based noisy OCR correction

**Recognition infrastructure**

- Reul et al. (2019) — OCR4all
- Kahle et al. (2017) — Transkribus (HTR)
- Engl (2020) — early modern full texts
- Pavlopoulos et al. (2023) / Platanou et al. (2022) — HTREC / Byzantine HTR

**LLMs generally (not post-OCR-specific)**

- Brown et al. (2020); Chowdhery et al. (2022); Scao et al. (2022); Zhang et al. (2022); Touvron et al. (2023a,b); Bommasani et al. (2022)
- GEC-with-GPT studies: Wu et al. (2023); Fang et al. (2023); Loem et al. (2023); Coyne et al. (2023); Ostling & Kurfalı (2022)
- Huang et al. (2023) — hallucination survey

**Heritage / DH context**

- Terras (2011); Padilla (2019); McGillivray et al. (2020); Ehrmann et al. (2020, 2022); Romanello et al. (2021) — ajmc

**Code:** https://github.com/impresso/llm-transcript-postcorrection

---

## 2. Zhang et al. (2024) — DocEng

**Citation:** Zhang, James, Haverals, Wouter, Naydan, Mary and Kernighan, Brian W. (2024) *Post-OCR Correction with OpenAI’s GPT Models on Challenging English Prosody Texts*, DocEng ’24, article 9.

### Core method

| Dimension | Detail |
|-----------|--------|
| **Corpus** | Princeton Prosody Archive (PPA) — 693 “typographically unique” works (musical notation, diacritics, phonetic scripts); OCR from ECCO/HathiTrust (~2008-era) |
| **Ground truth** | 21 hand-transcribed pages (challenging scans/typography); page-level correction |
| **Models** | GPT-3.5-turbo, GPT-4, GPT-4-turbo via OpenAI API |
| **Prompts** | Shared system prompt (only some text erroneous; correct per author intent). User variants: **Vanilla** (directive + overcorrection penalty); **TU definition**; **work metadata** (title, author, year); **temperature** sweep (0–1.2); **correctness-aware** (CER fed to model — oracle only); **second reader** (two-pass) |
| **QE pipeline** | Modified GEMBA (Kocmi & Federmann 2023): score OCR 0–100; **<30 → re-OCR with Tesseract**; **>80 → skip correction**; else run GPT correction |
| **Metric** | **CER** (character error rate via Levenshtein); reported as **% improvement** over baseline OCR |
| **Cost** | ~3.5 h, ~$11 per full experimental run (10 repeats × 3 models × configs) |

### Key findings

- **GPT-4 best** (mean CER 26.81% after correction vs 31.08% for 3.5-turbo); GPT-4-turbo slightly worse than GPT-4.
- **Prompt engineering largely ineffective** — vanilla/context-free correction competitive; metadata and TU context did not help; second reader **hurts** (error propagation).
- **Temperature matters:** GPT-4 at **temp 0.6** → **18.92% mean CER improvement** without QE.
- **U-shaped difficulty:** models struggle when OCR is **already good** (overcorrection) or **extremely bad**; QE routing fixes this.
- **With QE pipeline:** mean CER improvements up to **38.83%** (GPT-4-turbo); GPT-4 → 19.84% absolute CER.
- **Goal:** retrieval/search quality, not diplomatic edition.

### Limitations (authors')

- Small sample (21 pages); limited test repetitions.
- PPA data not publicly shareable (permissions).
- Manual transcriptions acknowledged imperfect but consistent.
- No fine-tuning; prompt-only, low-resource.

### Recommendations for historical / scholarly text

- **Route by OCR quality** before LLM correction: re-OCR the worst pages; leave high-quality pages untouched.
- **Keep prompts simple**; avoid over-long context that distracts the model.
- **Lower temperature** (~0.6) for GPT-4 on historical English.
- **Avoid iterative second-pass correction** without safeguards.
- Transcription principles preserve author errors and mark non-Unicode symbols — LLMs not yet reliable on special symbols (@SPECIAL_CHAR@).
- Framed for **search/retrieval**, not scholarly diplomatic fidelity.

### Related-work bibliography

- **Boros et al. (2024)** — cited as negative benchmark (LLMs worsen text / hallucinate)
- **Thomas, Gaizauskas & Lu (2024)** — Llama 2 fine-tuned on 19th-c. British newspapers; major gains vs transformer baseline
- **Löfgren & Dannélls (2024)** — ByT5 post-OCR for Swedish newspapers (LaTeCH-CLfL)
- **Davydkin et al. (2023)** — Cyrillic handwriting post-OCR data generation
- **Yasin et al. (2023)** — transformer NMT post-OCR for cursive Urdu
- **Todorov & Colavizza (2020)** — transfer learning post-OCR + NER
- **Cordell (2017)** — “dirty OCR” and DH search
- **Hostetler (2023)** — PPA typographically unique tour
- **Jiao et al. (2023)** — ChatGPT translation
- **Zhang et al. (2023)** — “Does Correction Remain A Problem For LLMs?”
- **Kocmi & Federmann (2023)** — GEMBA translation QE
- **Bsharat et al. (2024)** — prompt instruction principles

**Code:** https://github.com/jzhang512/post-ocr-correction

---

## 3. User paper — *Full Fathom Five: Transforming the New Variorum Shakespeare*

**File:** `full_fathom_five (18).pdf` (22 pp.)

### Exactly what is claimed about OCR / LLM correction

**Abstract / headline claims**

- “Multi-phase optical character recognition (OCR) process with **validation by large language models**”
- Multi-part verification: **0.9% residual truncation** (human-adjudicated sampling); **97.8%** of note endings match independent print witnesses; stratified full-span sample found **no genuine interior divergence** after adjudication of automated failures

**OCR pipeline (3 stages)**

1. **Stage 1:** Raw UTF-8 text read from each page image (spatial layout preserved). Witness verification section names underlying engines as **Tesseract/ABBYY** on page images; stage 1 itself does not name the engine.
2. **Stage 2:** **Google Gemini** (1M-token context) — processes **entire volume bibliography + current page** in parallel. Performs character-level correction, truncated-abbreviation repair, citation reunification, italic/roman preservation.
3. **Stage 3:** Regex parsing into act/scene/line/speaker/stage direction/commentary entries; critic surname expansion at digitization time.

**Design claims tied to Boros/Zhang literature**

- Pipeline combines “**image-grounded OCR** with structured post-processing” (related work: correction “**grounded in the page image**” vs free-running generation).
- Boros et al.: unconstrained LLM post-correction usually **degrades** input; worst failures = **paraphrase and invention** — these are “explicit targets” of fidelity checks; paper claims **no instance** of either in verification.
- Zhang et al.: GPT-4-class models can improve challenging period typography when **carefully configured**; temperature **0.3** for analysis tiers; future work cites Zhang’s **quality-triaged re-OCR** for hard witnesses (Troilus, Othello).

**What is NOT claimed**

- No **CER/WER** reported for the OCR/LLM correction stage itself.
- No held-out ground-truth transcription experiment for the ingestion pipeline.
- LLM correction is **not** evaluated as a standalone ablation (with vs without Gemini stage).

**Verification scope (separate from OCR metric)**

| Check | Scale | Result |
|-------|-------|--------|
| Tail verification (last 90 chars, rapidfuzz ≥75 vs IA djvu.txt witnesses) | 23,715 notes | 97.8% pass |
| Truncation census (union flags, post-repair) | 23,715 notes | 24 flags (0.10%) |
| Reader-focused sample (human adjudication) | 1,100 notes | 99.0% OK; **0.9% truncated** (operative truncation estimate) |
| Full-span stratified sample | 308 notes; 192 anchored | 67.2% auto pass; **60 interior-divergence cases all adjudicated as witness OCR noise**, not site fabrication |
| Citation audit (retrieval layers) | 50 passages, 162 citations | 100% traceable; no fabrication in grounded layers |

**LLM use beyond OCR (analysis tiers)**

- OpenAI **gpt-4o** / **gpt-4o-mini** (Netlify functions); Claude as fallback/A-B.
- **Deterministic retrieval** of Onions, Schmidt, Geneva Bible, LEME — injected into prompts; NV commentary **server-overwritten verbatim** after generation.
- Model-generated critical sections **prohibit named critic attribution** to block citation fabrication.
- Experimental AI labeled; NV notes never pass through the model for display.

### Current citations in related work and methodology

**Boros et al. (2024)** — Related Work §LLM post-correction:

- Fourteen models, eight benchmarks; unconstrained correction usually degrades; paraphrase/invention risks.
- Shapes project stance: image-grounded correction + witness verification.

**Zhang et al. (2024)** — Related Work + Constraining Model Output + Future Directions:

- GPT-4-class models can improve challenging typography when configured.
- Temperature 0.3 for stability (analysis, not OCR stage).
- Future: re-OCR hard witnesses using Zhang-style quality triage.

**Adjacent LLM / citation literature**

- Walters & Wilder (2023); Sun et al. (2024) — fabricated citations in LLM output.

**Not cited in OCR/LLM correction context (gaps vs seed bibliographies)**

- Thomas et al. (2024) fine-tuned Llama post-OCR
- Löfgren & Dannélls (2024) ByT5 newspapers
- Cordell (2017) dirty OCR
- ICDAR / neural post-correction line (Amrhein, Nguyen, Rigaud, Soper, etc.)
- Boros’s recommended alternatives: detection/correction split, fine-tuning, re-OCR workflows (Schneider & Maurer)
- GEMBA / quality-estimation routing (Zhang’s core contribution)

### Gaps where literature would expect more

| Expected in LLM-OCR literature | User paper status |
|-------------------------------|-------------------|
| **CER/WER** on correction stage with held-out GT | Absent — fidelity measured against **independent witness OCR**, not human diplomatic transcription |
| **Ablation:** OCR only vs +Gemini vs +manual | Not reported |
| **Prompt / model specification** for Gemini correction stage | Model named; **prompts not specified**; unclear if stage 2 is multimodal (page image + text) or text-only despite “image-grounded” language |
| **Hallucination taxonomy** (Boros C1–C4) | Addressed indirectly via witness matching; no structured error coding of correction stage |
| **Over-correction rate** on clean passages | Not quantified (Zhang/Boros emphasize this failure mode) |
| **Human eval of OCR quality** | Reader sample evaluates **note completeness/fidelity to print**, not character-level OCR |
| **Independent replication** | Acknowledged as future need |
| **Cost / scale** reporting for Gemini ingestion | Not reported |
| **Temperature** for Gemini OCR stage | Only cited for GPT analysis tiers (0.3) |
| **QE routing** (Zhang) | Cited for future witness re-OCR, **not** used in current ingestion pipeline |
| **User study** for AI tiers | Informal n=5 readers; structured study proposed as future work |

**Internal tension to flag for lit review**

- Claims “image-grounded” correction, but methodology describes stage 1 as text extraction and stage 2 as Gemini on bibliography + page **text** — literature reader may expect explicit multimodal grounding or CER against GT, as in Zhang/Boros experimental norms.

---

## 4. Cross-paper synthesis — coordination notes

### Convergent lessons

1. **Unconstrained LLM post-correction is risky** for heritage text (Boros: usually degrades; Zhang: overcorrects good OCR).
2. **Fidelity ≠ fluency** — scholarly use requires exact reproduction, not plausible rewriting.
3. **Quality triage** beats one-size-fits-all correction (Zhang QE; Boros: noisy vs clean bands behave oppositely).
4. **Verification must be independent** of the correction toolchain (user paper’s IA djvu witnesses vs Tesseract/ABBYY+Gemini ingestion — structurally sound, but witnesses are also OCR).

### How user paper positions against seeds

| Aspect | Boros | Zhang | User (Full Fathom Five) |
|--------|-------|-------|-------------------------|
| LLM role in OCR | Evaluated as sole corrector | Evaluated as corrector + QE router | Gemini as stage-2 corrector with bibliography context |
| Metric | PCIS / Levenshtein similarity | CER | Fuzzy witness match, truncation census, human adjudication |
| Hallucination control | Documented as dominant failure | QE skip + low temperature | Witness verification + architectural overwrite for NV text |
| Scholarly text stance | Exact GT match required | Retrieval-oriented | Infrastructure / faithful transmission; not new edition |
| Recommendation | Fine-tune, specialized prompts, re-OCR | Simple prompts, temp 0.6, QE pipeline | Image-grounded + witness verify; cites both seeds |

### Priority citations to add or develop in full literature review

1. **Thomas et al. (2024)** — positive LLM post-OCR via fine-tuning (counterpoint to Boros zero-shot; nuance Zhang prompt-only).
2. **Löfgren & Dannélls (2024)** — contemporary neural post-OCR in same LaTeCH venue as Boros.
3. **Schneider & Maurer (2022)** — re-OCR as alternative/complement to LLM correction (user future direction aligns).
4. **Cordell (2017)** — DH framing for dirty OCR / search.
5. **Kocmi & Federmann (2023)** — if adopting Zhang-style QE for witness triage.
6. **Amrhein & Clematide (2018); Nguyen et al. (2020); Soper et al. (2021)** — established post-correction baselines Boros assumes.

### Suggested claims discipline for user paper revision

- Separate **ingestion OCR evaluation** (needs CER or sampled GT) from **corpus fidelity verification** (witness agreement — already strong).
- Clarify **multimodal vs text-only** Gemini stage-2.
- Report **ablation** or acknowledge as limitation explicitly.
- When citing Zhang for temperature, note their finding applies to **GPT-4 OCR correction at 0.6**, not necessarily Gemini at 0.3 on variorum footnotes.
- When citing Boros, acknowledge verification detects paraphrase/invention at **note level**, not character-level PCIS.

---

## 5. Quick-reference bibliographic entries (for BibTeX harvest)

```
@inproceedings{boros2024postcorrection,
  author = {Boros, Emanuela and Ehrmann, Maud and Romanello, Matteo and Najem-Meyer, Sven and Kaplan, Fr{\'e}d{\'e}ric},
  title = {Post-correction of Historical Text Transcripts with Large Language Models: An Exploratory Study},
  booktitle = {LaTeCH-CLfL 2024},
  pages = {133--159},
  year = {2024}
}

@inproceedings{zhang2024postocr,
  author = {Zhang, James and Haverals, Wouter and Naydan, Mary and Kernighan, Brian W.},
  title = {Post-OCR Correction with OpenAI's GPT Models on Challenging English Prosody Texts},
  booktitle = {DocEng '24},
  year = {2024},
  doi = {10.1145/3685650.3685669}
}
```

---

*End of seed summary.*
