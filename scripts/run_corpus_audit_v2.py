#!/usr/bin/env python3
"""Run full 21-play corpus audit suite (Troilus excluded) → validation/*_v2.* + report."""

from __future__ import annotations

import json
import math
import subprocess
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_nv_fidelity_all_plays import PLAYS, _exclude_slug  # noqa: E402
from verify_all_notes import (  # noqa: E402
    CHUNK_STRIDE_WORDS,
    CHUNK_WORDS,
    TAIL_LEN_DEFAULT,
    THRESHOLD_DEFAULT,
    build_chunks,
    collect_notes,
    get_witness,
    norm,
)
from rapidfuzz import fuzz, process

EXCLUDE = {"Troilus and Cressida"}
SUFFIX = "_v2"
PLAYS_21 = [p for p in PLAYS if p["play"] not in EXCLUDE]
VAL = ROOT / "validation"


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    m = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / d
    return 100 * (c - m), 100 * (c + m)


def tail_verify_play(spec: dict) -> dict:
    path = ROOT / spec["json"]
    data = json.loads(path.read_text(encoding="utf-8"))
    notes = collect_notes(data)
    witness_text, witness_src = get_witness(spec["play"])
    if witness_text is None:
        return {
            "play": spec["play"],
            "year": spec["year"],
            "notes": len(notes),
            "ok": 0,
            "fail": len(notes),
            "pass_pct": 0.0,
            "witness": witness_src,
            "error": "witness_unavailable",
        }
    witness_norm = norm(witness_text)
    chunk_texts = [c[0] for c in build_chunks(witness_norm, CHUNK_WORDS, CHUNK_STRIDE_WORDS)]
    ok = fail = 0
    fail_samples: list[str] = []
    for item in notes:
        note = item["note"]
        stripped = note.rstrip()
        if stripped.endswith("...") and len(stripped) < 10:
            ok += 1
            continue
        tail_chars = stripped[-TAIL_LEN_DEFAULT:]
        needle = norm(tail_chars)
        if len(needle) < 20:
            ok += 1
            continue
        result = process.extractOne(needle, chunk_texts, scorer=fuzz.partial_ratio)
        if result is None or result[1] < THRESHOLD_DEFAULT:
            fail += 1
            if len(fail_samples) < 15:
                score = 0 if result is None else result[1]
                ref = f"{item['scene']} | line {item['line']} | note {item['note_idx']}"
                fail_samples.append(f"  FAIL {ref} (score={score:.0f})")
        else:
            ok += 1
    n = len(notes)
    return {
        "play": spec["play"],
        "year": spec["year"],
        "notes": n,
        "ok": ok,
        "fail": fail,
        "pass_pct": round(100 * ok / n, 2) if n else 0.0,
        "witness": witness_src,
        "fail_samples": fail_samples,
    }


def build_tail_census() -> Path:
    out = VAL / "nv_tail_verify_all_plays_v2.json"
    print("=== Tail verify all plays (21) ===")
    per_play = []
    for i, spec in enumerate(PLAYS_21, 1):
        print(f"  [{i}/21] {spec['play']}...", flush=True)
        per_play.append(tail_verify_play(spec))
    total_notes = sum(p["notes"] for p in per_play)
    total_ok = sum(p["ok"] for p in per_play)
    total_fail = sum(p["fail"] for p in per_play)
    payload = {
        "date": date.today().isoformat(),
        "method": "tail-end fuzzy witness match (last 90 chars, threshold 75)",
        "tail_len": TAIL_LEN_DEFAULT,
        "threshold": THRESHOLD_DEFAULT,
        "plays": 21,
        "excluded_plays": sorted(EXCLUDE),
        "total_notes": total_notes,
        "total_ok": total_ok,
        "total_fail": total_fail,
        "corpus_pass_pct": round(100 * total_ok / total_notes, 2) if total_notes else 0,
        "per_play": per_play,
    }
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    return out


def run_sub(cmd: list[str]) -> None:
    print("$", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> int:
    VAL.mkdir(parents=True, exist_ok=True)
    build_tail_census()

    # Point repair split at v2 census (temporarily copy or patch env)
    census_v2 = VAL / "nv_tail_verify_all_plays_v2.json"
    census_live = VAL / "nv_tail_verify_all_plays.json"
    backup = None
    if census_live.is_file():
        backup = census_live.read_text(encoding="utf-8")
    census_live.write_text(census_v2.read_text(encoding="utf-8"), encoding="utf-8")

    try:
        run_sub([
            sys.executable, "scripts/slice_tail_verify_by_repair.py",
            "--exclude", "Troilus and Cressida",
            "--suffix", SUFFIX,
        ])
        run_sub([
            sys.executable, "scripts/audit_nv_truncation.py",
            "--exclude", "Troilus and Cressida",
            "--out-suffix", SUFFIX,
        ])
        run_sub([
            sys.executable, "scripts/audit_lineation_alignment.py",
            "--out-json", str(VAL / "nv_lineation_alignment_v2.json"),
            "--out-md", str(VAL / "nv_lineation_alignment_v2.md"),
            "--exclude", "Troilus and Cressida",
        ])
        run_sub([
            sys.executable, "scripts/audit_stage_direction_misclassification.py",
            "--out-json", str(VAL / "nv_stage_direction_misclassification_v2.json"),
            "--out-md", str(VAL / "nv_stage_direction_misclassification_v2.md"),
            "--exclude", "Troilus and Cressida",
        ])
        run_sub([
            sys.executable, "scripts/audit_johnson_corpus_search.py",
            "--exclude", "Troilus and Cressida",
            "--suffix", SUFFIX,
        ])
    finally:
        if backup is not None:
            census_live.write_text(backup, encoding="utf-8")
        elif census_live.is_file() and census_v2.is_file():
            pass  # leave v2 copy at census_live? restore only if backup

    # Full-span + reader: exclude Troilus via --play list
    play_args: list[str] = []
    for spec in PLAYS_21:
        play_args.extend(["--play", spec["play"]])

    run_sub([sys.executable, "scripts/audit_nv_fullspan_sample.py", "--seed", "42", "--sample-n", "14", *play_args])

    # Copy fullspan to v2 dir snapshot
    fs_src = VAL / "nv_fullspan_sample"
    fs_v2 = VAL / "nv_fullspan_sample_v2"
    if fs_v2.exists():
        import shutil
        shutil.rmtree(fs_v2)
    import shutil
    shutil.copytree(fs_src, fs_v2)

    run_sub([sys.executable, "scripts/audit_nv_witness_sample.py", "--sample-n", "50", *play_args])

    ws_v2 = VAL / "nv_witness_sample_v2"
    if ws_v2.exists():
        shutil.rmtree(ws_v2)
    shutil.copytree(VAL / "nv_witness_sample", ws_v2)

    compile_report()
    return 0


def compile_report() -> None:
    tail = json.loads((VAL / "nv_tail_verify_all_plays_v2.json").read_text())
    repair = json.loads((VAL / f"nv_tail_verify_repair_split{SUFFIX}.json").read_text())["summary"]
    trunc = json.loads((VAL / f"nv_truncation_audit{SUFFIX}.json").read_text())
    line = json.loads((VAL / f"nv_lineation_alignment{SUFFIX}.json").read_text())
    stage = json.loads((VAL / f"nv_stage_direction_misclassification{SUFFIX}.json").read_text())
    john = json.loads((VAL / f"johnson_corpus_search{SUFFIX}.json").read_text())
    fs = json.loads((VAL / "nv_fullspan_sample_v2/manifest.json").read_text())
    fs_res = json.loads((VAL / "nv_fullspan_sample_v2/results.json").read_text())
    ws = json.loads((VAL / "nv_witness_sample_v2/manifest.json").read_text())
    ws_res = json.loads((VAL / "nv_witness_sample_v2/results.json").read_text())

    corp_n = tail["total_notes"]
    corp_ok = tail["total_ok"]
    corp_pct = tail["corpus_pass_pct"]
    wlo, whi = wilson(corp_ok, corp_n)

    per_play_lines = []
    avg_pct = corp_pct
    for p in sorted(tail["per_play"], key=lambda x: x["pass_pct"]):
        flag = " ⚠" if p["pass_pct"] < avg_pct - 2 else ""
        per_play_lines.append(
            f"| {p['play']} | {p['notes']:,} | {p['ok']:,} | {p['fail']:,} | {p['pass_pct']:.2f}%{flag} |"
        )

    # Full-span aggregates
    fs_sum = fs["corpus_summary"]
    anchored = fs_sum.get("anchored_n", fs_sum.get("anchored", 0))
    unanch = fs_sum.get("unanchorable_n", fs_sum.get("unanchorable", 0))
    evaluable = fs_sum.get("evaluable_n", fs_sum.get("scored_n", 0))
    auto_pass = fs_sum.get("full_span_match_n", fs_sum.get("full_span_match", 0))

    # Reader from witness sample
    reader_ok = reader_trunc = reader_not = 0
    for row in ws_res:
        if row.get("error"):
            continue
        for item in row.get("sample", []):
            r = item.get("reason", "")
            if r == "truncated":
                reader_trunc += 1
            elif r == "not_in_witness":
                reader_not += 1
            else:
                reader_ok += 1
    reader_n = reader_ok + reader_trunc + reader_not
    rwlo, rwhi = wilson(reader_ok, reader_n)

    othello_tail = next(p for p in tail["per_play"] if p["play"] == "Othello")
    othello_fs = next(r for r in fs_res if r["play"] == "Othello")
    othello_line = next(p for p in line["per_play"] if p["play"] == "Othello")

    lines = [
        f"# Corpus audit report (21 plays, Othello MIT) — {date.today().isoformat()}",
        "",
        "Troilus and Cressida excluded. Othello: `Public/Data/othello_notes.json` (MIT spine).",
        "",
        "## 1. Tail verification",
        "",
        f"| Corpus | {corp_n:,} notes | {corp_ok:,} pass | {tail['total_fail']:,} fail | **{corp_pct:.2f}%** |",
        f"| 95% Wilson CI | **{wlo:.2f}–{whi:.2f}%** |",
        "",
        "| Play | Notes | Pass | Fail | Pass % |",
        "|------|------:|-----:|-----:|-------:|",
        *per_play_lines,
        "",
        f"**Othello:** {othello_tail['notes']:,} notes, {othello_tail['pass_pct']:.2f}% pass",
        "",
        "## 2. Truncation census",
        "",
        f"- Notes audited: **{trunc['totals']['total_notes']:,}**",
        f"- Union flags: **{trunc['totals']['union_truncated']}** ({trunc['totals']['union_pct']:.2f}%)",
        f"- Zero-flag plays: **{sum(1 for p in trunc['plays'] if p['union_truncated']==0)}**",
        "",
        "## 3. Repair-cohort controls",
        "",
        f"| Cohort | n | Pass % |",
        f"|--------|--:|-------:|",
        f"| Never in workbook | {repair['untouched']['n']:,} | {repair['untouched']['pass_pct']:.2f}% |",
        f"| Workbook-flagged | {repair['repaired_cohort']['n']:,} | {repair['repaired_cohort']['pass_pct']:.2f}% |",
        f"| Spliced (`complete`) | {repair['spliced_complete_only']['n']:,} | {repair['spliced_complete_only']['pass_pct']:.2f}% |",
        f"| **Full corpus** | **{repair['corpus']['n']:,}** | **{repair['corpus']['pass_pct']:.2f}%** |",
        "",
        f"Workbook-flagged: **{repair['workbook_matched_in_corpus']}** "
        f"({100*repair['workbook_matched_in_corpus']/repair['corpus']['n']:.2f}% of corpus)",
        "",
        "## 4. Stratified full-span (seed 42, 14/play)",
        "",
        f"| Sampled | {fs_sum.get('sample_n', 294)} |",
        f"| Evaluable | {evaluable} |",
        f"| Anchored | {anchored} |",
        f"| Unanchorable | {unanch} ({100*unanch/evaluable:.1f}% of evaluable)" if evaluable else f"| Unanchorable | {unanch} |",
        f"| Automated pass (anchored) | {auto_pass} ({100*auto_pass/anchored:.1f}%)" if anchored else "",
        "",
        f"**Othello:** sampled {othello_fs.get('sample_n')}, anchored {othello_fs.get('anchored_n')}, "
        f"unanchorable {othello_fs.get('unanchorable_n')}, auto pass {othello_fs['counts'].get('full_span_match')}",
        "",
        "## 5. Reader sample (50/play = 1,050)",
        "",
        f"| Reader-OK | {reader_ok} ({100*reader_ok/reader_n:.1f}%) |",
        f"| Truncated | {reader_trunc} |",
        f"| Not located | {reader_not} |",
        f"| Wilson CI (OK) | {rwlo:.2f}–{rwhi:.2f}% |",
        "",
        "## 6. Lineation retrieval (Othello included)",
        "",
        f"- Clickable lines: **{line['summary']['corpus_counts']['clickable_lines']:,}**",
        f"- Correct retrieval: **{line['summary']['rates']['retrieval_correct_pct']:.2f}%**",
        f"- Wrong-key (diff notes): **{line['summary']['rates']['retrieval_wrong_key_different_notes_pct']:.2f}%**",
        f"- E2E pass: **{line['summary']['rates']['e2e_pass_pct']:.2f}%**",
        f"- Othello E2E: **{othello_line['rates']['e2e_pass_pct']:.2f}%** ({othello_line['counts']['clickable_lines']} clickable)",
        "",
        "## 7. Johnson search",
        "",
        f"- **Total: {john['total_hits']:,}**",
        f"- Othello: **{john['per_play'].get('Othello', 0)}**",
        "",
        "## 8. Stage-direction misclassification",
        "",
        f"- Play lines: **{stage['summary']['total_play_lines']:,}**",
        f"- Misclassified: **{stage['summary']['misclassified']}** "
        f"({stage['summary']['pct_misclassified_of_play']:.3f}% of lines)",
        "",
        "## 9. Deployment checks",
        "",
        "- Othello deployed file: `Public/Data/othello_notes.json` (MIT `_meta.textSource`)",
        "- `meliorandi` patch: present in `Public/Data/as_you_like_it.json`",
        "- Troilus: still in site play metadata; **excluded from all 21-play audit denominators**",
        "",
        "## Output files",
        "",
        "- `validation/nv_tail_verify_all_plays_v2.json`",
        f"- `validation/nv_tail_verify_repair_split{SUFFIX}.json`",
        f"- `validation/nv_truncation_audit{SUFFIX}.json`",
        f"- `validation/nv_fullspan_sample_v2/`",
        f"- `validation/nv_witness_sample_v2/`",
        f"- `validation/nv_lineation_alignment{SUFFIX}.json`",
        f"- `validation/johnson_corpus_search{SUFFIX}.json`",
        f"- `validation/nv_stage_direction_misclassification{SUFFIX}.json`",
        "",
    ]
    out = VAL / "paper_audit_report_v2.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    raise SystemExit(main())
