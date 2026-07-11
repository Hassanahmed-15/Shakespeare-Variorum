# Full Fathom Five Citation Audit — Status

**Last updated:** 2026-07-04  
**Status:** Complete (22 plays, 50 passages)

## Sample

| Parameter | Value |
|---|---|
| Profile | `full` (22 NV corpus plays) |
| Total passages | **50** (2–3 per play, stratified) |
| Model | gpt-4o |
| NV section injected | 16 plays |

## Results (sample estimates, not census)

| Scope | n | Correct | Wrong details | Fabricated | Unverifiable |
|---|---:|---:|---:|---:|---:|
| Overall | 200 | 82.5% | 0.0% | **0.0%** | 17.5% |
| Model-generated sections | 187 | 81.3% | 0.0% | **0.0%** | 18.7% |
| New Variorum Analysis (injected) | 13 | **100.0%** | 0.0% | **0.0%** | 0.0% |

**35 citations** flagged `unverifiable_needs_human_review` — see `unverifiable_citations.json`.

## Deliverables

| Artifact | Path |
|---|---|
| Sample manifest | `sample_manifest.json` |
| Raw model outputs | `sample_raw_outputs.json` |
| Classified citations | `citations_classified.json` |
| Unverifiable queue | `unverifiable_citations.json` |
| Rate table | `rate_table.json`, `rate_table.md` |
| Run log | `run.log` |

## Layer audits (NV / Onions / Schmidt only)

Geneva Bible and LEME excluded. Re-classified from existing raw outputs (no new API calls).

| Layer | Citations | Correct | Fabricated | Path |
|---|---:|---:|---:|---|
| **NV (injected apparatus)** | 13 | 100.0% | 0.0% | `layers/nv/rate_table.md` |
| **Onions** | 79 | 100.0% | 0.0% | `layers/onions/rate_table.md` |
| **Schmidt** | 70 | 100.0% | 0.0% | `layers/schmidt/rate_table.md` |

```bash
python3 scripts/audit_fff_citation_accuracy.py --profile full --total-passages 50 --classify-layers
python3 scripts/audit_fff_citation_accuracy.py --classify-layers nv onions  # subset
```
