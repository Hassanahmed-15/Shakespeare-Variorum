# Insertable Literature Memo — Full Fathom Five

*Prepared July 2026 from `literature_review_memo.md`, `seed_papers_summary.md`, and `citing_works_catalog.json`. Blocks below are written for direct insertion into the paper; adjust cross-references to match your section numbering.*

---

## INSERT: Related Work — LLM Post-OCR Correction

Recent work on large-language-model (LLM) post-OCR correction has moved quickly beyond the exploratory studies that first framed the problem. Boros et al. (2024) evaluated fourteen models across eight historical benchmarks in a **text-only**, zero-shot setting and found that unconstrained LLM correction usually **degrades** transcripts relative to ground truth, with dominant failure modes of hallucination, paraphrase, continuation, and embellishment. Zhang et al. (2024) reached a more conditional conclusion for challenging English prosody texts: GPT-4-class models can lower character error rate (CER) when prompts are kept simple, temperature is tuned, and a quality-estimation (QE) router skips already-clean pages or sends the worst pages to re-OCR—an architecture oriented toward retrieval rather than diplomatic fidelity.

The 2025–26 citing literature does not overturn either seed study; it **stratifies** them along modality, supervision, and evaluation philosophy. Kanerva et al. (2025) replicate Boros at ECCO scale and report that most open-weight models fail as post-correctors while GPT-4o yields substantial relative CER reductions on English—gains that remain language- and setting-dependent. Greif et al. (2025) show that **image-conditioned** multimodal post-correction can reach sub-1% CER on German city directories without fine-tuning, suggesting that grounding in page images changes the risk profile relative to Boros's text-only pipeline. Bourne (2025) pursues a complementary supervised paradigm: synthetic-noise fine-tuning yields large CER drops on nineteenth-century newspapers, but at the cost of curated training infrastructure our variorum-scale ingest does not assume.

On evaluation, Levchenko (2025) argues that standard CER is insufficient for scholarly digitization, introducing diplomatic-fidelity metrics (Historical Character Preservation Rate, Archaic Insertion Rate) and finding that post-OCR LLM correction can **degrade** strong multimodal OCR through over-historicization. Backer and Hyman (2025) likewise contend that character metrics alone underestimate utility for computational historical research and advocate discipline-driven downstream assessment. Araújo et al. (2025) confirm prompt sensitivity across Portuguese, French, and English HTR outputs; Koynov and Doan (2025) synthesize zero-shot limits across German and English historical sets; and Machidon and Machidon (2025) caution that LLM refinement can improve readability while normalizing dialectal and historical forms—a failure mode directly relevant to variorum commentary.

Against this backdrop, Full Fathom Five addresses a third question neither Boros nor Zhang poses: not whether LLM correction improves CER on a held-out page sample, but whether a staged OCR-plus-LLM ingest **preserves variorum note content** detectably against independent print witnesses at corpus scale. We therefore treat ingestion as a production stage bounded by witness verification and architectural controls on displayed scholarly text, rather than as a standalone correction experiment evaluated solely against gold transcripts.

---

## INSERT: Methodology — Gemini Stage 2: Permitted Corrections and Modality

**Stage 2: LLM-augmented validation.** Each page's Stage 1 OCR output is passed to Google Gemini together with the **original page image** and volume-level bibliographic context (exploiting Gemini's long context window for cross-page disambiguation of abbreviated citations). This stage is **multimodal**: the model may consult the scan when resolving ambiguous small-type footnotes, italic lemma markers, or split citation blocks. The system prompt constrains the model to **transcription repair**, not editorial rewriting. Permitted operations are: (i) character-level OCR error correction; (ii) restoration of truncated abbreviations (e.g., *Steev.*, *Mal.*, *Clar.*); (iii) reunification of citations split across OCR blocks; and (iv) preservation of italic/roman distinction via lightweight markup conventions. The model is **not** instructed to modernize spelling, paraphrase commentary, interpolate missing material, or continue truncated passages beyond what the page image supports. Stage 2 is a **single-pass** correction step: we do not iterate LLM correction on LLM output, avoiding the error-propagation pattern Zhang et al. (2024) document for second-reader setups.

This design aligns with the post-OCR literature's central lesson that unconstrained generative "correction" is unsafe for heritage text (Boros et al. 2024; Levchenko 2025) while adopting the multimodal grounding Greif et al. (2025) and Levchenko (2025) identify as materially different from text-only post-correction. Analysis-tier LLM calls (OpenAI GPT-4o / GPT-4o-mini at temperature 0.3) are architecturally separate from Stage 2 ingest and are subject to additional output controls described below.

---

## INSERT: Methodology — Verification vs. OCR Evaluation

Our fidelity assurance operates on a **different evidential layer** from the CER/PCIS benchmarks that dominate LLM post-OCR studies. Boros et al. (2024) score correction against human ground truth using the Post-Correction Improvement Score (relative Levenshtein similarity); Zhang et al. (2024) report CER improvement on hand-transcribed pages with an optional GEMBA-style quality router. Both paradigms ask whether a model **improves a transcript relative to a gold reference** on a bounded test set. Full Fathom Five instead asks whether the **deployed corpus** preserves variorum note content against **independent print witnesses** at scale—a question closer to infrastructure QA than to model benchmarking.

Concretely, verification proceeds in four complementary layers:

1. **Tail verification.** For all 23,715 commentary notes, we compare the last ninety characters of each note to Internet Archive `djvu.txt` witness OCR (produced by a toolchain independent of our Tesseract/ABBYY-plus-Gemini ingest) using fuzzy string matching (rapidfuzz partial ratio ≥ 75). **97.8%** of note endings match.

2. **Truncation census.** A union of automated truncation flags across the corpus, post-repair, yields **24** residual flags (**0.10%** of notes).

3. **Reader-focused adjudication.** A stratified sample of 1,100 notes, reviewed for scholarly usability, yields **99.0%** acceptable and an operative truncation estimate of **0.9%** after human adjudication.

4. **Full-span and interior-divergence review.** A stratified sample of 308 notes (192 anchorable in witness text) applies stricter whole-note matching; cases where tails pass but interiors fail are **human-adjudicated**. All 60 interior-divergence failures in this sample were attributed to witness OCR noise or span-boundary artifacts, not to site-side paraphrase or fabrication.

These checks operationalize Boros et al.'s C3 failure taxonomy—hallucination, paraphrase, continuation, embellishment—at **note granularity** without requiring a held-out diplomatic transcription of the entire variorum apparatus. They also differ from Zhang-style QE routing: we do not skip or re-OCR pages based on model-estimated OCR quality during ingest; instead, hard witnesses gate corpus-level claims. We acknowledge a limitation both seed traditions note: IA witnesses are themselves OCR, not diplomatic editions. Our verification therefore detects **truncation, mis-attachment, and platform-side fabrication** more reliably than it certifies absolute character-level identity with nineteenth-century print. That trade-off is intentional for a production scholarly platform: false fluency is more dangerous than unverified character noise in footnote regions (Backer and Hyman 2025; Machidon and Machidon 2025).

---

## INSERT: Methodology — Conservative Design Choices

Several architectural decisions follow directly from the post-OCR literature and from constraints specific to variorum-scale eclectic typography:

- **Independent witnesses.** Verification uses Internet Archive `djvu.txt` files mapped per play, not outputs from the ingest pipeline. This structural independence is stronger than evaluating correction against ground truth drawn from the same OCR pass, though witnesses remain machine transcripts of print.

- **No iterative LLM correction loop.** Stage 2 runs once per page. We do not chain corrector passes, in line with Zhang et al.'s finding that second-reader correction propagates errors.

- **Multimodal ingest, deterministic serve.** Gemini may use page images during ingest; displayed New Variorum commentary is retrieved **verbatim** from JSON and **server-overwritten** into analysis responses after generation, so model paraphrase cannot replace historical notes in the user interface.

- **Prohibition of fabricated attribution in model-generated tiers.** Critical-analysis sections forbid named-critic attribution unless grounded in retrieved sources, addressing LLM citation-fabrication risks documented outside the OCR literature.

- **No fine-tuned correction model.** We do not pursue Bourne-style (2025) synthetic-noise fine-tuning or Kanerva-style (2025) open-weight deployment at ECCO scale; eclectic variorum typography and cross-volume bibliographic context favor a long-context multimodal validator plus corpus verification over per-play supervised correctors.

- **Quality triage deferred.** Zhang-style QE routing and entropy-based skip/re-OCR (Kaltchenko 2025) remain future work for difficult witnesses (e.g., *Troilus and Cressida*, *Othello*), not part of the current production ingest.

---

## INSERT (OPTIONAL): Limitations — Evaluation Scope

The LLM post-OCR literature would reasonably expect a held-out **CER/WER** benchmark for Stage 2, an **ablation** comparing OCR-only and OCR-plus-Gemini ingest, and quantitative **over-correction rates** on already-clean passages (Zhang et al. 2024; Boros et al. 2024). We do not report these experiments. Our evidentiary center of gravity is **corpus fidelity to independent witnesses** and human adjudication of truncation and interior divergence—not character-level improvement against diplomatic gold. Stage-level CER would measure transcript repair in isolation; it would not, by itself, establish that twenty-three thousand commentary notes reach readers without systematic tail loss or platform-side invention, which is the claim our verification protocol is designed to support.

Similarly, we do not apply Boros-style manual error coding to Gemini outputs at scale; automated tail, truncation, and full-span checks substitute at note granularity. Reporting Gemini ingest cost, latency, and temperature specifications remains an engineering transparency item rather than a blocker for the fidelity claims above. These deferrals follow Levchenko (2025) and Backer and Hyman (2025) in treating discipline-appropriate evaluation as **layered**: character metrics for model comparison, witness convergence for production corpus assurance. We report the latter at scale and leave the former to targeted future sampling where ground-truth transcription is feasible.

---

## INSERT: Bibliography — New References

*Format matches existing Full Fathom Five references. Add only entries not already in your bibliography.*

Araújo, Sávio S., Bezerra, Byron L. D. and Neto, Arthur Flor de Sousa. (2025) 'Towards Prompt Engineering and Large Language Models for Post-OCR correction in handwritten texts', *Proceedings of the 16th Symposium in Information and Human Language Technology (STIL 2025)*, doi: 10.5753/stil.2025.37859.

Backer, Samuel and Hyman, Louis. (2025) 'Bootstrapping AI: Interdisciplinary Approaches to Assessing OCR Quality in English-Language Historical Documents', *Proceedings of the 5th International Conference on Natural Language Processing for Digital Humanities (NLP4DH 2025)*, pp. 251–256, doi: 10.18653/v1/2025.nlp4dh-1.21.

Bourne, Jonathan. (2025) 'Scrambled text: fine-tuning language models for OCR error correction using synthetic data', *International Journal on Document Analysis and Recognition*, 28, pp. 741–755, doi: 10.1007/s10032-025-00522-0.

Greif, Gavin, Griesshaber, Niclas and Greif, Robin. (2025) 'Multimodal LLMs for OCR, OCR Post-Correction, and Named Entity Recognition in Historical Documents', *arXiv preprint arXiv:2504.00414*, doi: 10.48550/arXiv.2504.00414.

Kanerva, Jenna, Ledins, Cassandra, Käpyaho, Siiri and Ginter, Filip. (2025) 'OCR Error Post-Correction with LLMs in Historical Documents: No Free Lunches', *Proceedings of the Third Workshop on Resources and Representations for Under-Resourced Languages and Domains (RESOURCEFUL 2025)*, pp. 38–47.

Koynov, Radoslav and Doan, Thi. (2025) 'Opportunities and Challenges of LLMs as Post-OCR Correctors', *Proceedings of the 20th Conference on Computer Science and Information Systems (FedCSIS 2025)*, doi: 10.15439/2025f4697.

Levchenko, Maria. (2025) 'Evaluating LLMs for Historical Document OCR: A Methodological Framework for Digital Humanities', *Proceedings of the First Workshop on Natural Language Processing and Language Models for Digital Humanities (LM4DH 2025)*, pp. 75–85, doi: 10.26615/978-954-452-106-6-007.

Machidon, O. M. and Machidon, A. L. (2025) 'Comparing OCR Pipelines for Folkloristic Text Digitization', *arXiv preprint arXiv:2507.19092*, doi: 10.48550/arXiv.2507.19092.

---

## Editorial notes (do not insert)

1. **Boros and Zhang** are assumed already cited; the Related Work block references them but does not duplicate bibliography entries.

2. **Gemini modality** is stated as multimodal (OCR text + page image) per `scripts/update_methodology_v2.py`. If your deployed ingest ever ran text-only, revise the Stage 2 block accordingly.

3. **Kaltchenko (2025)** is mentioned only in conservative-design / future-work prose; add to bibliography if you retain that sentence.

4. **Interior-divergence adjudication** numbers (60/60 witness noise) come from `validation/nv_fullspan_sample/`; confirm they match your latest Results section before publication.

5. **Temperature 0.3** applies to analysis-tier GPT calls, not to Gemini Stage 2—do not conflate with Zhang et al.'s GPT-4 correction temperature (0.6).

---

*End of insertable memo.*
