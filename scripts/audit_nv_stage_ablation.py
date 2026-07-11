#!/usr/bin/env python3
"""Stage-1 vs stage-2 witness ablation on a fixed stratified note sample.

Compares tail + full-span verification on:
  - Stage 1: earliest available pre-repair backup per play (proxy for raw ingest OCR)
  - Stage 2: deployed Public/Data JSON (current corrected corpus)

Outputs (validation/*_ablation.*):
  nv_stage_ablation_manifest.json
  nv_stage_ablation_results.json
  nv_stage_ablation_rate_table.json
  nv_stage_ablation_rate_table.md
  nv_stage_ablation_edit_diffs.json
  nv_stage_ablation_edit_summary.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zlib
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

from rapidfuzz import fuzz, process

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_nv_fidelity_all_plays import PLAYS  # noqa: E402
from audit_nv_fullspan_sample import (  # noqa: E402
    classify_note,
    play_seed,
    stratify_random_sample,
)
from audit_nv_witness_sample import iter_note_records  # noqa: E402
from verify_all_notes import (  # noqa: E402
    CHUNK_STRIDE_WORDS,
    CHUNK_WORDS,
    TAIL_LEN_DEFAULT,
    THRESHOLD_DEFAULT,
    build_chunks,
    get_witness,
    norm,
)

OUT = ROOT / "validation"
DEFAULT_SAMPLE_TOTAL = 300
DEFAULT_SEED = 42

# Earliest backup kind first (closest to ingest / raw OCR layer on disk).
BACKUP_KIND_RANK: dict[str, int] = {
    "pre_normalize": 0,
    "pre_sync": 1,
    "pre_repair": 2,
    "pre_trunc_repair": 3,
    "pre_trunc_repair2": 3,
    "pre_phase2_repair": 4,
    "pre_phase2_skipped_repair": 4,
    "pre_troilus_repair": 5,
    "pre_synth_repair": 6,
    "pre_clip_repair": 7,
    "pre_contractor_repair": 8,
}

ABBREV_RE = re.compile(
    r"\b([A-Z][A-Za-z]{1,5})([,.]?)\b|\b([A-Z]{2,6})\.\b"
)
HYPHEN_BREAK_RE = re.compile(r"-\s*$|(?<=\w)-\s+(?=\w)")
CITATION_JOIN_RE = re.compile(
    r"(?:\]\s*|\(\d{4}\)\s*|\bed\.\s*|\bff\.\s*)",
    re.I,
)


def backup_kind(path: Path) -> str | None:
    name = path.name
    if ".json." not in name:
        return None
    mid = name.split(".json.", 1)[1]
    if mid.endswith(".backup"):
        return mid[:-7]
    return None


def resolve_stage1_backup(deployed_json: Path) -> tuple[Path | None, str]:
    """Return (backup_path, label) for earliest pre-repair snapshot."""
    parent = deployed_json.parent
    stem = deployed_json.name
    if stem.endswith(".json"):
        base = stem[:-5]
    else:
        base = deployed_json.stem

    candidates: list[tuple[int, Path, str]] = []
    for path in parent.glob(f"{base}.json.*.backup"):
        kind = backup_kind(path)
        if kind is None:
            continue
        rank = BACKUP_KIND_RANK.get(kind, 99)
        candidates.append((rank, path, kind))
    # Also allow *.pre_normalize.backup.json style
    for path in parent.glob(f"{base}.*.backup.json"):
        kind = "pre_normalize" if "pre_normalize" in path.name else "other"
        rank = BACKUP_KIND_RANK.get(kind, 99)
        candidates.append((rank, path, kind))

    if not candidates:
        return None, "missing"
    candidates.sort(key=lambda x: (x[0], x[1].name))
    _, path, kind = candidates[0]
    return path, kind


def load_note_map(data: dict) -> dict[str, str]:
    return {row["ref"]: row["note"] for row in iter_note_records(data)}


def lookup_note(data: dict, ref: str) -> str | None:
    return load_note_map(data).get(ref)


def draw_sample(total_n: int, seed: int) -> list[dict]:
    rows: list[dict] = []
    for spec in PLAYS:
        path = ROOT / spec["json"]
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for row in iter_note_records(data):
            rows.append({**row, "play": spec["play"], "year": spec["year"], "json": spec["json"]})

    per_play = total_n // len(PLAYS)
    extra = total_n % len(PLAYS)
    picked: list[dict] = []
    for i, spec in enumerate(PLAYS):
        play_rows = [r for r in rows if r["play"] == spec["play"]]
        n = per_play + (1 if i < extra else 0)
        if not play_rows:
            continue
        sample = stratify_random_sample(play_rows, n, seed=play_seed(seed, spec["play"]))
        picked.extend(sample)
    return sorted(picked, key=lambda r: (r["play"], r["act"], r["scene"], r["line"], r["note_idx"]))[:total_n]


def tail_verify_note(
    note: str,
    chunk_texts: list[str],
    *,
    tail_len: int = TAIL_LEN_DEFAULT,
    threshold: float = THRESHOLD_DEFAULT,
) -> tuple[bool, float]:
    stripped = note.rstrip()
    if stripped.endswith("...") and len(stripped) < 10:
        return True, 100.0
    tail_chars = stripped[-tail_len:]
    needle = norm(tail_chars)
    if len(needle) < 20:
        return True, 100.0
    result = process.extractOne(needle, chunk_texts, scorer=fuzz.partial_ratio)
    if result is None:
        return False, 0.0
    _, score, _ = result
    return score >= threshold, float(score)


def summarize_verification(results: list[dict], *, label: str) -> dict:
    tail_pass = sum(1 for r in results if r[f"{label}_tail_pass"])
    full_counts = Counter(r[f"{label}_full_verdict"] for r in results)
    scored = sum(1 for r in results if r[f"{label}_full_verdict"] != "exempt")
    anchored = scored - full_counts.get("unanchorable", 0)
    full_pass = full_counts.get("full_span_match", 0)
    return {
        "n": len(results),
        "tail_pass_n": tail_pass,
        "tail_pass_pct": round(100 * tail_pass / len(results), 2) if results else None,
        "full_verdict_counts": dict(full_counts),
        "scored_n": scored,
        "anchored_n": anchored,
        "full_span_pass_n": full_pass,
        "full_span_pass_scored_pct": round(100 * full_pass / scored, 2) if scored else None,
        "full_span_pass_anchored_pct": round(100 * full_pass / anchored, 2) if anchored else None,
        "interior_divergence_n": full_counts.get("interior_divergence", 0),
        "span_mismatch_n": full_counts.get("span_mismatch", 0),
        "unanchorable_n": full_counts.get("unanchorable", 0),
        "exempt_n": full_counts.get("exempt", 0),
    }


def word_diffs(a: str, b: str) -> list[tuple[str, str]]:
    wa = re.findall(r"[A-Za-z0-9']+|[^\w\s]", a)
    wb = re.findall(r"[A-Za-z0-9']+|[^\w\s]", b)
    sm = SequenceMatcher(None, wa, wb)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        out.append((" ".join(wa[i1:i2]), " ".join(wb[j1:j2])))
    return out


def categorize_edit(stage1: str, stage2: str) -> str:
    if stage1 == stage2:
        return "unchanged"

    s1, s2 = stage1, stage2
    len_ratio = len(s2) / max(len(s1), 1)

    # Large tail extension (truncation / witness completion) → other
    if len(s2) > len(s1) + 80:
        prefix = s1[: min(30, len(s1))].strip()
        if prefix and s2.startswith(prefix):
            return "other"

    # Large shortening (mega-note split / splice) → other
    if len(s1) > len(s2) + 80 and s2 and s1.startswith(s2[: min(30, len(s2))].strip()):
        return "other"

    # Hyphen / block-split reunification
    if HYPHEN_BREAK_RE.search(s1) and not HYPHEN_BREAK_RE.search(s2):
        return "citation_rejoin"
    if s1.count("- ") > s2.count("- ") and CITATION_JOIN_RE.search(s1 + s2):
        return "citation_rejoin"
    if re.search(r"\w-\s*\n\s*\w", s1) and not re.search(r"\w-\s*\n\s*\w", s2):
        return "citation_rejoin"

    diffs = word_diffs(s1, s2)
    if not diffs:
        if norm(s1) == norm(s2):
            return "spelling_normalization"
        return "other"

    # Single-character / very short token repairs
    char_like = all(
        len(o) <= 2 and len(n) <= 2 for o, n in diffs
    )
    if char_like and len(diffs) <= 8:
        return "character_repair"

    # Abbreviation restoration: Steeu→Steev, missing terminal period on caps
    abbrev_hits = 0
    for old, new in diffs:
        if re.match(r"^[A-Z][a-z]{1,4}[,.]?$", old) or re.match(r"^[A-Z]{2,6}\.?$", old):
            if new.startswith(old.rstrip("., ")[:3]) or old.rstrip("., ")[:3] in new:
                abbrev_hits += 1
        if old.rstrip(".") == new.rstrip(".") and (old.endswith(".") ^ new.endswith(".")):
            abbrev_hits += 1
    if abbrev_hits >= max(1, len(diffs) // 2):
        return "abbreviation_restoration"

    # Mostly word substitutions of similar length
    sub_pairs = [(o, n) for o, n in diffs if o and n]
    if sub_pairs:
        avg_old = sum(len(o) for o, _ in sub_pairs) / len(sub_pairs)
        avg_new = sum(len(n) for _, n in sub_pairs) / len(sub_pairs)
        if 3 <= avg_old <= 12 and 3 <= avg_new <= 12 and len(sub_pairs) <= 6:
            return "spelling_normalization"

    # Near-identical with small edit distance
    ratio = SequenceMatcher(None, norm(s1), norm(s2)).ratio()
    if ratio >= 0.92 and len(s2) - len(s1) < 20:
        return "character_repair"

    return "other"


def run_ablation(sample: list[dict]) -> tuple[list[dict], list[dict], dict]:
    witness_cache: dict[str, tuple] = {}
    results: list[dict] = []
    edit_rows: list[dict] = []
    stage1_sources: Counter = Counter()

    for row in sample:
        play = row["play"]
        ref = row["ref"]
        deployed_path = ROOT / row["json"]
        stage1_path, stage1_kind = resolve_stage1_backup(deployed_path)
        stage1_sources[stage1_kind] += 1

        deployed_data = json.loads(deployed_path.read_text(encoding="utf-8"))
        stage2_text = lookup_note(deployed_data, ref) or row["note"]

        if stage1_path and stage1_path.is_file():
            stage1_data = json.loads(stage1_path.read_text(encoding="utf-8"))
            stage1_text = lookup_note(stage1_data, ref)
            if stage1_text is None:
                stage1_text = stage2_text
                stage1_kind = "missing_ref_fallback"
        else:
            stage1_text = stage2_text
            stage1_kind = "missing"

        if play not in witness_cache:
            wit, src = get_witness(play)
            if wit is None:
                witness_cache[play] = (None, src, [], [])
            else:
                wnorm = norm(wit)
                chunks = build_chunks(wnorm, CHUNK_WORDS, CHUNK_STRIDE_WORDS)
                witness_cache[play] = (wit, src, chunks, [c[0] for c in chunks])

        wit, wit_src, chunks, chunk_texts = witness_cache[play]
        rec = {
            "play": play,
            "ref": ref,
            "json": row["json"],
            "stage1_source": str(stage1_path.relative_to(ROOT)) if stage1_path else None,
            "stage1_backup_kind": stage1_kind,
            "stage1_len": len(stage1_text),
            "stage2_len": len(stage2_text),
            "text_changed": stage1_text != stage2_text,
        }

        if wit is None:
            rec.update(
                {
                    "witness_error": wit_src,
                    "stage1_tail_pass": None,
                    "stage2_tail_pass": None,
                    "stage1_full_verdict": "witness_unavailable",
                    "stage2_full_verdict": "witness_unavailable",
                }
            )
            results.append(rec)
            continue

        from nv_ia_witness import fold_apostrophe  # noqa: E402

        folded_ia = fold_apostrophe(wit)

        for label, text in (("stage1", stage1_text), ("stage2", stage2_text)):
            tail_pass, tail_score = tail_verify_note(text, chunk_texts)
            full = classify_note(text, folded_ia, chunks)
            rec[f"{label}_tail_pass"] = tail_pass
            rec[f"{label}_tail_score"] = round(tail_score, 1)
            rec[f"{label}_full_verdict"] = full["verdict"]
            rec[f"{label}_full_ratio"] = full.get("full_ratio")
            rec[f"{label}_tail_ratio"] = full.get("tail_ratio")

        edit_cat = categorize_edit(stage1_text, stage2_text)
        rec["edit_category"] = edit_cat
        results.append(rec)

        if stage1_text != stage2_text:
            edit_rows.append(
                {
                    "play": play,
                    "ref": ref,
                    "edit_category": edit_cat,
                    "stage1_backup_kind": stage1_kind,
                    "stage1_len": len(stage1_text),
                    "stage2_len": len(stage2_text),
                    "len_delta": len(stage2_text) - len(stage1_text),
                    "stage1_tail_pass": rec["stage1_tail_pass"],
                    "stage2_tail_pass": rec["stage2_tail_pass"],
                    "stage1_full_verdict": rec["stage1_full_verdict"],
                    "stage2_full_verdict": rec["stage2_full_verdict"],
                    "stage1_excerpt": stage1_text[:240],
                    "stage2_excerpt": stage2_text[:240],
                }
            )

    meta = {
        "stage1_proxy": "Earliest *.pre_*_repair.backup per deployed JSON (ingest OCR layer on disk)",
        "stage2": "Deployed Public/Data JSON (current corrected corpus)",
        "stage1_backup_kind_counts": dict(stage1_sources),
    }
    return results, edit_rows, meta


def write_rate_md(summary: dict, edit_summary: dict) -> str:
    s1 = summary["stage1"]
    s2 = summary["stage2"]
    delta = summary["delta_stage2_minus_stage1"]
    lines = [
        "# NV Stage-1 vs Stage-2 Witness Ablation (300-note sample)",
        "",
        f"**Date:** {date.today().isoformat()}",
        "",
        "## Sample",
        "",
        f"- Notes: **{summary['sample_n']}** stratified across **{summary['n_plays']}** plays",
        f"- Seed: **{summary['seed']}**",
        "",
        "## Text sources",
        "",
        f"- **Stage 1:** {summary['stage1_definition']}",
        f"- **Stage 2:** {summary['stage2_definition']}",
        "",
        "**Limitation:** True Tesseract/ABBYY-only stage-1 JSON is not archived separately.",
        "Stage 1 here is the **earliest `*.pre_*_repair.backup`** per play—the least post-processed",
        "note text on disk (typically pre-phase-2 or pre-clip witness repair). Gemini correction",
        "occurred upstream of these snapshots; this ablation measures **automated witness-repair",
        "and deployment edits**, not OCR-vs-Gemini in isolation.",
        "",
        "Backup kinds used:",
        "",
    ]
    for kind, n in sorted(summary.get("stage1_backup_kinds", {}).items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"- `{kind}`: {n} notes")
    lines.extend(
        [
            "",
            "## Tail verification (last 90 chars, partial_ratio ≥ 75)",
            "",
            "| Stage | Pass n | Pass % |",
            "|-------|-------:|-------:|",
            f"| Stage 1 (raw OCR proxy) | {s1['tail_pass_n']} | **{s1['tail_pass_pct']}%** |",
            f"| Stage 2 (deployed) | {s2['tail_pass_n']} | **{s2['tail_pass_pct']}%** |",
            f"| Δ (stage2 − stage1) | {delta['tail_pass_n']:+d} | **{delta['tail_pass_pct']:+.2f} pp** |",
            "",
            "## Full-span verification (tail-bounded span, fuzz.ratio ≥ 75)",
            "",
            "| Stage | Scored | Anchored | Full-span pass | Pass % (scored) | Pass % (anchored) |",
            "|-------|-------:|---------:|---------------:|----------------:|------------------:|",
            f"| Stage 1 | {s1['scored_n']} | {s1['anchored_n']} | {s1['full_span_pass_n']} | "
            f"{s1['full_span_pass_scored_pct']}% | {s1['full_span_pass_anchored_pct']}% |",
            f"| Stage 2 | {s2['scored_n']} | {s2['anchored_n']} | {s2['full_span_pass_n']} | "
            f"{s2['full_span_pass_scored_pct']}% | {s2['full_span_pass_anchored_pct']}% |",
            "",
            f"Δ full-span pass (anchored): **{delta['full_span_pass_anchored_pct']:+.2f} pp** "
            f"({delta['full_span_pass_n']:+d} notes)",
            "",
            "## Stage-1 → stage-2 edits on sample",
            "",
            f"- Changed notes: **{edit_summary['changed_n']}** / {edit_summary['total_n']} "
            f"({edit_summary['changed_pct']}%)",
            f"- Unchanged: {edit_summary['unchanged_n']}",
            "",
            "| Category | Count | % of changed |",
            "|----------|------:|-------------:|",
        ]
    )
    for cat, n in edit_summary["by_category"].items():
        pct = round(100 * n / edit_summary["changed_n"], 1) if edit_summary["changed_n"] else 0
        lines.append(f"| {cat} | {n} | {pct}% |")
    if edit_summary.get("other_truncation_completion_n"):
        lines.append("")
        lines.append(
            f"Of **other**, {edit_summary['other_truncation_completion_n']} are large tail extensions "
            f"(stage-2 longer by >80 chars, shared prefix)—witness truncation completion."
        )
    lines.extend(
        [
            "",
            "## Verification lift on changed notes only",
            "",
            f"- Tail pass: stage1 {edit_summary['changed_tail_stage1_pass_pct']}% → "
            f"stage2 {edit_summary['changed_tail_stage2_pass_pct']}% "
            f"({edit_summary['changed_tail_lift_pp']:+.2f} pp)",
            f"- Full-span pass (anchored): stage1 {edit_summary['changed_full_stage1_pass_anchored_pct']}% → "
            f"stage2 {edit_summary['changed_full_stage2_pass_anchored_pct']}% "
            f"({edit_summary['changed_full_lift_pp']:+.2f} pp)",
            "",
            "Regenerate: `python3 scripts/audit_nv_stage_ablation.py`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sample-n", type=int, default=DEFAULT_SAMPLE_TOTAL)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = ap.parse_args()

    sample = draw_sample(args.sample_n, args.seed)
    results, edit_rows, run_meta = run_ablation(sample)

    s1 = summarize_verification(results, label="stage1")
    s2 = summarize_verification(results, label="stage2")

    changed = [r for r in results if r.get("text_changed")]
    unchanged_n = len(results) - len(changed)
    cat_counts = Counter(r["edit_category"] for r in results if r.get("text_changed"))
    cat_counts["unchanged"] = unchanged_n

    def anchored_full_pass(r: dict, label: str) -> bool:
        return r.get(f"{label}_full_verdict") == "full_span_match"

    changed_tail_s1 = sum(1 for r in changed if r.get("stage1_tail_pass"))
    changed_tail_s2 = sum(1 for r in changed if r.get("stage2_tail_pass"))
    changed_full_s1 = sum(
        1
        for r in changed
        if r.get("stage1_full_verdict") not in ("exempt", "unanchorable", "witness_unavailable")
        and anchored_full_pass(r, "stage1")
    )
    changed_full_s2 = sum(
        1
        for r in changed
        if r.get("stage2_full_verdict") not in ("exempt", "unanchorable", "witness_unavailable")
        and anchored_full_pass(r, "stage2")
    )
    changed_anchored = sum(
        1
        for r in changed
        if r.get("stage2_full_verdict") not in ("exempt", "unanchorable", "witness_unavailable")
    )

    truncation_completion_n = sum(
        1
        for r in changed
        if r.get("edit_category") == "other" and (r["stage2_len"] - r["stage1_len"]) > 80
    )

    edit_summary = {
        "total_n": len(results),
        "changed_n": len(changed),
        "unchanged_n": unchanged_n,
        "changed_pct": round(100 * len(changed) / len(results), 2) if results else 0,
        "by_category": dict(
            sorted(
                ((k, v) for k, v in cat_counts.items() if k != "unchanged"),
                key=lambda x: (-x[1], x[0]),
            )
        ),
        "other_truncation_completion_n": truncation_completion_n,
        "changed_tail_stage1_pass_pct": round(100 * changed_tail_s1 / len(changed), 2) if changed else None,
        "changed_tail_stage2_pass_pct": round(100 * changed_tail_s2 / len(changed), 2) if changed else None,
        "changed_tail_lift_pp": round(
            100 * (changed_tail_s2 - changed_tail_s1) / len(changed), 2
        )
        if changed
        else None,
        "changed_full_stage1_pass_anchored_pct": round(100 * changed_full_s1 / changed_anchored, 2)
        if changed_anchored
        else None,
        "changed_full_stage2_pass_anchored_pct": round(100 * changed_full_s2 / changed_anchored, 2)
        if changed_anchored
        else None,
        "changed_full_lift_pp": round(100 * (changed_full_s2 - changed_full_s1) / changed_anchored, 2)
        if changed_anchored
        else None,
    }

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sample_n": len(sample),
        "n_plays": len(PLAYS),
        "seed": args.seed,
        "stage1_definition": run_meta["stage1_proxy"],
        "stage2_definition": run_meta["stage2"],
        "stage1_backup_kinds": run_meta["stage1_backup_kind_counts"],
        "stage1": s1,
        "stage2": s2,
        "delta_stage2_minus_stage1": {
            "tail_pass_n": s2["tail_pass_n"] - s1["tail_pass_n"],
            "tail_pass_pct": round((s2["tail_pass_pct"] or 0) - (s1["tail_pass_pct"] or 0), 2),
            "full_span_pass_n": s2["full_span_pass_n"] - s1["full_span_pass_n"],
            "full_span_pass_scored_pct": round(
                (s2["full_span_pass_scored_pct"] or 0) - (s1["full_span_pass_scored_pct"] or 0), 2
            ),
            "full_span_pass_anchored_pct": round(
                (s2["full_span_pass_anchored_pct"] or 0) - (s1["full_span_pass_anchored_pct"] or 0), 2
            ),
        },
        "edit_summary": edit_summary,
    }

    manifest = {
        "sample_n": len(sample),
        "seed": args.seed,
        "generated_at": summary["generated_at"],
        "notes": [{"play": r["play"], "ref": r["ref"]} for r in sample],
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "nv_stage_ablation_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (OUT / "nv_stage_ablation_results.json").write_text(
        json.dumps({"summary": summary, "results": results}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (OUT / "nv_stage_ablation_rate_table.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    (OUT / "nv_stage_ablation_rate_table.md").write_text(
        write_rate_md(summary, edit_summary), encoding="utf-8"
    )
    (OUT / "nv_stage_ablation_edit_diffs.json").write_text(
        json.dumps(edit_rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (OUT / "nv_stage_ablation_edit_summary.json").write_text(
        json.dumps(edit_summary, indent=2) + "\n", encoding="utf-8"
    )

    print(f"Sample: {len(sample)} notes")
    print(f"Stage1 tail pass: {s1['tail_pass_pct']}%  |  Stage2: {s2['tail_pass_pct']}%")
    print(
        f"Stage1 full-span (anchored): {s1['full_span_pass_anchored_pct']}%  |  "
        f"Stage2: {s2['full_span_pass_anchored_pct']}%"
    )
    print(f"Changed notes: {edit_summary['changed_n']} ({edit_summary['changed_pct']}%)")
    print("Wrote validation/nv_stage_ablation_*")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
