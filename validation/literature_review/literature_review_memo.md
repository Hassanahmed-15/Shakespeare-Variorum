# Literature Review Memo — Full Fathom Five (July 2026)

*Scope: 63 unique works citing Boros et al. (2024, LaTeCH) and/or Zhang et al. (2024, DocEng), harvested from Semantic Scholar (primary), OpenAlex, and Google Scholar. Titles/abstracts triaged for all; 22 works deep-read (arXiv, ACL Anthology, journal pages). Seed summaries: `seed_papers_summary.md`. Full catalog: `citing_works_catalog.json` / `.md`.*

---

## A) Recommended NEW citations for the paper

### Must-cite (strengthen related work + preempt reviewer questions)

| Priority | Citation | One-line rationale |
|----------|----------|------------------|
| 1 | **Levchenko (2025)** — *Evaluating LLMs for Historical Document OCR: A Methodological Framework for Digital Humanities* (arXiv:2510.06743) | Closest methodological neighbor: argues standard CER is insufficient for diplomatic/s scholarly digitization; introduces fidelity metrics (HCPR, AIR) and finds **post-OCR LLM correction often degrades** multimodal OCR — directly supports your witness-based verification stance and frames why you do not report standalone CER. |
| 2 | **Backer & Hyman (2025)** — *Bootstrapping AI: Interdisciplinary Approaches to Assessing OCR Quality in English-Language Historical Documents* (NLP4DH; cites both Boros and Zhang) | DH-native evaluation argument: OCR metrics can **underestimate utility for historical research**; discipline-driven downstream evaluation is legitimate — justifies your reader/adjudication samples alongside (not instead of) character metrics. |
| 3 | **Kanerva et al. (2025)** — *OCR Error Post-Correction with LLMs in Historical Documents: No Free Lunches* (arXiv:2502.01205) | Large ECCO-scale replication of Boros: most open-weight models fail; **GPT-4o helps English** (~58% relative CER reduction) but gains are language- and setting-dependent — nuance between Boros (mostly harmful) and Zhang (conditional GPT-4 gains). |
| 4 | **Greif, Griesshaber & Greif (2025)** — *Multimodal LLMs for OCR, OCR Post-Correction, and NER in Historical Documents* (arXiv:2504.00414) | Best recent counterpoint: **image-conditioned** mLLM post-correction reaches &lt;1% CER on German city directories without fine-tuning — supports your claim that grounding in page images (not text-only generation) changes the risk profile. |
| 5 | **Bourne (2025)** — *Scrambled text: fine-tuning language models for OCR error correction using synthetic data* (*Int J Digit Libr*; also arXiv:2409.19735) | Positive fine-tuning line Boros defers to: synthetic-noise training yields large CER drops on 19th-c. newspapers — cite as **alternative paradigm** (supervised correction) your pipeline does not pursue, clarifying you chose multimodal ingest + verification instead. |

### Nice-to-have (adds depth without expanding experiments)

| Citation | One-line rationale |
|----------|------------------|
| **Araújo, Bezerra & Neto (2025)** — *Towards Prompt Engineering and LLMs for Post-OCR correction in handwritten texts* (STIL; cites **both** seeds) | Multilingual prompt study (PT/FR/EN) confirming prompt sensitivity and mixed gains — backs simple-prompt + language-specific caution without requiring new ablations. |
| **Koynov & Doan (2025)** — *Opportunities and Challenges of LLMs as Post-OCR Correctors* (FedCSIS; cites Zhang) | Short survey-style synthesis of zero-shot post-OCR limits — lightweight substitute if page count is tight. |
| **Kaltchenko (2025–26)** — *Entropy Heat-Mapping* (arXiv:2505.00746) + *Page-Level Shannon Entropy From Top-k Logprobs Predicts OCR Quality* | Model-native **quality estimation without ground truth** — practical citation if you mention Zhang-style QE routing in future work (skip pages / flag tails). |
| **Angleraud et al. (2026)** — *Structure-Aware Text Recognition for Ancient Greek Critical Editions* (arXiv:2603.02803) | Parallel DH problem: dense scholarly apparatus + structure-aware OCR for critical editions; underscores that **layout/footnote fidelity** is an active research frontier beyond character CER. |
| **Bassanini et al. (2026)** — *Quid est VERITAS?* (arXiv:2603.28108) | Modular archival pipeline (preprocess → extract → refine → enrich) with RAG downstream — architectural kin to your staged ingest + retrieval layers. |
| **Machidon & Machidon (2025)** — *Comparing OCR Pipelines for Folkloristic Text Digitization* (arXiv:2507.19092) | DH cautionary tale: LLM refinement improves readability but **alters dialectal/historical forms** — supports fidelity-over-fluency framing. |
| **CLOCR-C** — *Context Leveraging OCR Correction with Pre-trained Language Models* (arXiv:2408.17428; EMNLP-adjacent line) | Context-conditioned post-correction with measurable gains on historical news — established non-LLM-generative baseline in the neural post-OCR lineage. |
| **Humphries et al. (2025)** — *Unlocking the archives: Using LLMs to transcribe handwritten historical documents* (*Historical Methods*) | Often-cited positive LLM transcription result; cite only if you claim multimodal superiority over HTR — otherwise skip to save space. |

### Already flagged in seed summary — still worth adding if not yet in bibliography

Thomas et al. (2024) fine-tuned Llama post-OCR; Löfgren & Dannélls (2024) ByT5; Schneider & Maurer (2022) re-OCR workflows; Cordell (2017) dirty OCR; Kocmi & Federmann (2023) GEMBA (Zhang's QE).

---

## B) Methodological additions suggested by literature

### Worth adding to the paper (low cost, high reviewer value)

1. **Clarify evaluation layer (1 paragraph).** Literature now converges on a two-tier story: (i) *ingestion/correction quality* (CER, PCIS, or model-native QE) vs (ii) *corpus fidelity to source* (witness agreement, diplomatic preservation). State explicitly that you report (ii) at scale and treat (i) as partially indirect — following Backer & Hyman and Levchenko rather than apologizing for missing CER.

2. **Name the failure modes you guard against.** One sentence mapping Boros's C3 taxonomy (hallucination, paraphrase, continuation, embellishment) to your checks: tail match, truncation census, interior-divergence adjudication, server-side NV overwrite. No new experiments.

3. **Specify Gemini stage-2 modality.** Greif/Levchenko reviewers will ask whether correction is image-grounded or text-only. If stage 2 receives page images, say so; if text-only, soften "image-grounded" wording to "OCR pipeline with multimodal validation where available."

4. **Acknowledge witness OCR circularity.** Zhang and Boros both note that evaluation witnesses are often themselves OCR. One sentence: IA djvu witnesses are independent of the ingestion toolchain but not diplomatic transcriptions — your checks detect **site fabrication and truncation**, not absolute ground truth.

5. **Future-work pointer to QE routing.** Cite Zhang + Kaltchenko together: entropy/QE-based **skip-or-re-OCR** for hard volumes (Troilus, Othello) is literature-aligned and does not commit you to implementing it pre-submission.

### Acknowledge as limitations (do not block submission)

| Literature expectation | Recommended acknowledgment |
|------------------------|---------------------------|
| Held-out CER/WER for Gemini stage | Not measured; fidelity validated via independent witnesses and human adjudication |
| Ablation (OCR-only vs +Gemini) | Not run; architectural choice documented; witness verification is the safety layer |
| Boros-style qualitative error coding on correction output | Deferred; automated tail/full-span checks substitute at note granularity |
| Over-correction rate on clean passages (Zhang U-curve) | Not quantified; truncation-focused census partially addresses tail loss |
| Cost/latency of Gemini ingest | Not reported; note as engineering constraint if space allows |
| Temperature/spec for Gemini OCR stage | Distinguish from GPT analysis tiers (0.3); do not import Zhang's 0.6 without qualification |

**Do not add** pre-submission: full CER benchmark, fine-tuning ablation, or entropy-QE implementation — literature treats these as desirable extensions, not prerequisites when witness fidelity is the primary scholarly claim.

---

## C) Works reviewed but NOT worth citing

| Work | Reason to skip |
|------|----------------|
| **WXImpactBench** (Yu et al. 2025) | Weather-impact benchmark; cites seeds incidentally; no OCR/edition relevance. |
| **Disaster-management social media clustering** (Değirmen-Bektaş et al. 2026) | Tangential NLP; no heritage OCR connection. |
| **Ukrainian multimodal OCR parameter study** (Doskach & Havalko 2025) | Language-specific engineering report. |
| **Nepali structured extraction** (Neupane et al. 2025) | Different task (IE from scans). |
| **AURORA-OCR** (Rakesh et al. 2026) | Neuroevolution + LLM correction on degraded images; engineering-heavy, low DH/edition overlap. |
| **Karjus (2023/2025)** — *Machine-assisted quantitizing designs* | Broad LLM-for-humanities methods; not OCR fidelity. |
| **Hu (2024)** — *Application of LLMs for Digital Libraries* | Classification/summarization for discovery; not transcription fidelity. |
| **Frances++** (Yu & Filgueira 2025) | Semantic enrichment platform; not correction evaluation. |
| **Schonhardt et al. (2026) book chapters** (*Introduction*, *Tools*, *Case Studies*, *Understanding Automated Text Recognition*) | Textbook sections citing Boros pedagogically; not primary research. |
| **Duplicate / metadata-only records** (e.g., second Bootstrapping AI entry without DOI) | Catalog noise. |
| **Arabic GPT enhancement** (2024 JCDL) | Parallel but non-English scholarly-edition context; cite only if expanding multilingual related work. |
| **Thai historical OCR spelling correction** (Intchot & Netisopakul 2025) | Useful locally; low marginal value for NV Shakespeare submission. |

---

## D) Synthesis — positioning Full Fathom Five vs Boros and Zhang

### What the citing literature adds

The 2025–26 citing wave does **not** overturn Boros or Zhang; it **stratifies** them:

- **Text-only, zero-shot post-correction** → still mostly harmful (Boros; Kanerva for open models; Levchenko: post-correction degrades multimodal OCR).
- **Carefully configured GPT-4-class correction with QE routing** → conditional gains on hard English typography (Zhang; Kanerva GPT-4o on ECCO).
- **Image-conditioned (multimodal) OCR/correction** → potentially transformative on some historical material (Greif; Humphries; Levchenko Gemini/Qwen), but introduces new failure modes (**over-historicization**, dialect normalization — Levchenko; Machidon).
- **Supervised / fine-tuned correction** → most reliable CER improvements when training data exists (Bourne; Thomas et al.; CLOCR-C line) — high setup cost for variorum-scale eclectic typography.
- **Evaluation** → moving from CER alone to **diplomatic fidelity + downstream DH utility** (Levchenko; Backer & Hyman) and **model-native uncertainty** for triage (Kaltchenko).

### Three-paper positioning matrix (updated)

| Dimension | Boros 2024 | Zhang 2024 | Full Fathom Five |
|-----------|------------|------------|------------------|
| **Primary question** | When does zero-shot LLM post-correction help? | Can GPT-4 + QE improve PPA OCR for retrieval? | Can we ship faithful NV infrastructure at scale? |
| **LLM role** | Sole text corrector (14 models) | Corrector + GEMBA-style router | Gemini stage-2 correction + GPT analysis tiers |
| **Grounding** | Text-only | Text-only (+ re-OCR branch) | Claims image-grounded ingest; witnesses are separate OCR |
| **Success metric** | PCIS vs GT (mostly negative) | CER % improvement (positive with QE) | 97.8% tail witness match; 0.9% truncation (adjudicated) |
| **Hallucination control** | Documented as dominant failure | QE skip + low temperature | Independent witness verification + NV verbatim overwrite |
| **Scholarly stance** | Exact GT match required | Retrieval-oriented | Faithful transmission; not new diplomatic edition |
| **Literature verdict** | Default skeptical prior | Conditional optimizer | **Risk-managed production architecture** |

### Distinctive contribution (for discussion section)

Full Fathom Five is best read as answering a **third question** neither seed paper addresses: not "does LLM correction improve CER on a held-out page sample?" but "does a staged OCR+LLM pipeline **preserve variorum note content** detectably against independent print witnesses at corpus scale?"

That moves the safety mechanism from **model behavior** (Boros/Zhang) to **infrastructure**:

1. **Ingest** — multimodal correction with bibliographic context (closer to Greif/Levchenko than to Boros's text-only setup).
2. **Verify** — external witnesses + human adjudication (stronger than either seed's GT-only lab evaluation; acknowledges witness OCR limits).
3. **Serve** — deterministic NV retrieval and server-side overwrite block analysis-time fabrication (no analog in Boros/Zhang).

Against Boros: you agree unconstrained generation is dangerous; you add that **corpus-level witness checks** can operationalize their C3 warnings without character-level PCIS.

Against Zhang: you adopt the **spirit** of quality triage (skip/re-OCR hard cases) as future work but substitute **witness agreement** for GEMBA in production QA — appropriate when the product is an edition interface, not a search index.

### One-sentence positioning (usable in paper)

> Whereas Boros et al. demonstrate that text-only LLM post-correction usually degrades historical transcripts and Zhang et al. show conditional gains when GPT-4 correction is quality-routed for retrieval, Full Fathom Five treats LLM ingestion as a **production stage bounded by independent witness verification and architectural controls on displayed scholarly text**, trading standalone CER evaluation for corpus-scale fidelity guarantees appropriate to a scholarly edition platform.

---

## Harvest notes

| Source | Boros cites | Zhang cites | Notes |
|--------|------------|-------------|-------|
| Semantic Scholar | 35 | 12 | Most complete; used as backbone |
| OpenAlex | 9 | 6 | Under-counts recent preprints |
| Google Scholar | 10 | 8 | Pagination partial (rate limits); merged for deduping |
| **Unique merged** | **52** | **19** | **7 cite both; 63 total incl. 1 seed self-hit removed** |

Scholar IDs used: Boros `8103317005463255551`; Zhang `18300382062689824098`.

---

## Top 5 citation recommendations (executive)

1. **Levchenko (2025)** — DH evaluation framework; post-OCR degradation; diplomatic fidelity metrics.  
2. **Backer & Hyman (2025)** — discipline-driven OCR assessment; cites both seeds.  
3. **Kanerva et al. (2025)** — *No Free Lunches*; ECCO-scale Boros replication with GPT-4o nuance.  
4. **Greif et al. (2025)** — multimodal post-correction gains with image grounding.  
5. **Bourne (2025)** — fine-tuning/synthetic-data alternative your pipeline explicitly does not take.

---

*End of memo.*
