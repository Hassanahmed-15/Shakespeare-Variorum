# Full Fathom Five Citation Accuracy Audit

- Plays (N): **22**
- Profile: **full**
- NV corpus plays: **22** (NV section injected: **16**)
- Contrast (non-NV) plays: **0**
- Passages per play: **50 total (50 sampled)**
- Total passages: **50**
- Model: **gpt-4o**
- Generated: 2026-07-04T23:28:49.177037+00:00

## Method

Stratified sample (soliloquy, dialogue, stage direction, textually contested) × N plays.
Analyses generated with the same Full Fathom Five prompt and retrieved-source grounding
(Onions, Schmidt, LEME, Geneva) as `functions/shakespeare.js`. New Variorum Analysis
is server-overwritten from local play JSON before citation extraction.

Classifications: `verifiable_correct`, `real_source_wrong_details`, `fabricated`,
`unverifiable_needs_human_review`. Rates are sample estimates, not a corpus census.

## Rate table

| Scope | n | Correct % | Wrong details % | Fabricated % | Unverifiable % |
|---|---:|---:|---:|---:|---:|
| Overall | 200 | 82.5 | 0.0 | 0.0 | 17.5 |
| Model-generated sections | 187 | 81.28 | 0.0 | 0.0 | 18.72 |
| New Variorum Analysis (injected) | 13 | 100.0 | 0.0 | 0.0 | 0.0 |
