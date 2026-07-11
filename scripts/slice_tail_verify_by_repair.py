#!/usr/bin/env python3
"""Re-slice tail-verify by repair workbook cohort.

`validation/nv_tail_verify_all_plays.json` has per-play aggregates only (no per-note
rows). This script scores the 927 workbook-flagged notes with verify_all_notes logic
and derives the untouched cohort by subtraction from the corpus census totals.

Outputs:
  validation/nv_tail_verify_repair_split.json
  validation/nv_tail_verify_repair_split.md
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

from rapidfuzz import fuzz, process

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_nv_fidelity_all_plays import PLAYS, _exclude_slug  # noqa: E402
from apply_contractor_completions import load_workbook  # noqa: E402
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

OUT_JSON = ROOT / "validation" / "nv_tail_verify_repair_split.json"
OUT_MD = ROOT / "validation" / "nv_tail_verify_repair_split.md"
WORKBOOK = ROOT / "validation" / "contractor_truncation_workbook.json"
TAIL_CENSUS = ROOT / "validation" / "nv_tail_verify_all_plays.json"


def _out_paths(suffix: str) -> tuple[Path, Path]:
    if not suffix:
        return OUT_JSON, OUT_MD
    stem = suffix if suffix.startswith("_") else f"_{suffix}"
    return (
        OUT_JSON.with_name(f"{OUT_JSON.stem}{stem}{OUT_JSON.suffix}"),
        OUT_MD.with_name(f"{OUT_MD.stem}{stem}{OUT_MD.suffix}"),
    )


def _corpus_totals(census: dict, excluded: set[str]) -> tuple[int, int, int, float | None]:
    per_play = census["per_play"]
    if excluded:
        rows = [p for p in per_play if p["play"] not in excluded]
        n = sum(p["notes"] for p in rows)
        ok = sum(p["ok"] for p in rows)
        fail = sum(p["fail"] for p in rows)
    else:
        n = census["total_notes"]
        ok = census["total_ok"]
        fail = census["total_fail"]
    pct = round(100 * ok / n, 2) if n else None
    return n, ok, fail, pct


def workbook_key(entry: dict) -> tuple[str, str, str, int]:
    return (
        entry["play_name"],
        entry["act_scene"],
        str(entry["line_key"]),
        int(entry["note_index"]),
    )


def tail_score(note: str, chunk_texts: list[str]) -> tuple[float, str]:
    stripped = note.rstrip()
    if stripped.endswith("...") and len(stripped) < 10:
        return 100.0, "auto_pass_short_ellipsis"
    tail_chars = stripped[-TAIL_LEN_DEFAULT:]
    needle = norm(tail_chars)
    if len(needle) < 20:
        return 100.0, "auto_pass_short_tail"
    result = process.extractOne(needle, chunk_texts, scorer=fuzz.partial_ratio)
    if result is None:
        return 0.0, "no_chunk_match"
    return float(result[1]), "partial_ratio"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Play title(s) to omit (repeatable), e.g. 'Troilus and Cressida'",
    )
    ap.add_argument(
        "--suffix",
        default=None,
        help="Output filename suffix (default: _no_<slug> when --exclude is set)",
    )
    args = ap.parse_args()
    excluded = {name.strip() for name in args.exclude if name.strip()}
    plays = [spec for spec in PLAYS if spec["play"] not in excluded]
    if not plays:
        print("No plays left after exclusions.", file=sys.stderr)
        return 1

    suffix = args.suffix
    if suffix is None and excluded:
        suffix = _exclude_slug(excluded)
    out_json, out_md = _out_paths(suffix or "")

    wb_all = load_workbook(WORKBOOK)
    wb_excluded = [e for e in wb_all if e["play_name"] in excluded]
    wb = [e for e in wb_all if e["play_name"] not in excluded]
    census = json.loads(TAIL_CENSUS.read_text(encoding="utf-8"))

    # Index current corpus notes by key
    note_by_key: dict[tuple, dict] = {}
    for spec in plays:
        play = spec["play"]
        jf = spec.get("json_file") or spec.get("json")
        path = ROOT / jf
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in collect_notes(data):
            key = (play, item["scene"], str(item["line"]), int(item["note_idx"]))
            note_by_key[key] = {
                "play": play,
                "ref": f"{item['scene']} / line {item['line']} / note {item['note_idx']}",
                "note": item["note"],
                "note_len": len(item["note"]),
            }

    play_chunks: dict[str, list[str]] = {}
    crossref: list[dict] = []
    not_in_corpus: list[dict] = []

    for entry in wb:
        key = workbook_key(entry)
        status = (entry.get("status") or "").strip()
        row = note_by_key.get(key)
        if row is None:
            not_in_corpus.append(
                {
                    "play": entry["play_name"],
                    "act_scene": entry["act_scene"],
                    "line_key": str(entry["line_key"]),
                    "note_index": int(entry["note_index"]),
                    "status": status,
                }
            )
            continue

        play = key[0]
        if play not in play_chunks:
            wit, _ = get_witness(play)
            if wit is None:
                raise SystemExit(f"witness unavailable for {play}")
            chunks = build_chunks(norm(wit), CHUNK_WORDS, CHUNK_STRIDE_WORDS)
            play_chunks[play] = [c[0] for c in chunks]

        score, method = tail_score(row["note"], play_chunks[play])
        before = entry.get("current_note_text") or ""
        after = entry.get("completed_note_text") or ""
        text_changed = status == "complete" and bool(after.strip()) and after != before

        crossref.append(
            {
                "play": play,
                "ref": row["ref"],
                "workbook_status": status,
                "text_changed_in_workbook": text_changed,
                "char_count_before": entry.get("char_count_before"),
                "char_count_after": entry.get("char_count_after"),
                "tail_score": round(score, 1),
                "tail_pass": score >= THRESHOLD_DEFAULT,
                "score_method": method,
                "note_len": row["note_len"],
            }
        )

    repaired_n = len(crossref)
    repaired_pass = sum(1 for r in crossref if r["tail_pass"])
    repaired_fail = repaired_n - repaired_pass

    corpus_n, corpus_pass, corpus_fail, corpus_pass_pct = _corpus_totals(census, excluded)

    untouched_n = corpus_n - repaired_n
    untouched_pass = corpus_pass - repaired_pass
    untouched_fail = corpus_fail - repaired_fail

    def pct(ok: int, n: int) -> float | None:
        return round(100 * ok / n, 2) if n else None

    status_groups: dict[str, list] = defaultdict(list)
    for r in crossref:
        status_groups[r["workbook_status"]].append(r)

    repaired_by_status = {}
    for status, rows in sorted(status_groups.items()):
        n = len(rows)
        ok = sum(1 for r in rows if r["tail_pass"])
        repaired_by_status[status] = {
            "n": n,
            "pass": ok,
            "fail": n - ok,
            "pass_pct": pct(ok, n),
        }

    spliced = [r for r in crossref if r["text_changed_in_workbook"]]
    spliced_ok = sum(1 for r in spliced if r["tail_pass"])

    summary = {
        "date": date.today().isoformat(),
        "method": "verify_all_notes.py logic (last 90 chars, partial_ratio >= 75)",
        "limitation": (
            "nv_tail_verify_all_plays.json stores per-play aggregates only; "
            "workbook cohort scored per-note; untouched cohort derived by subtraction "
            "from corpus census totals."
        ),
        "repair_manifest": str(WORKBOOK.relative_to(ROOT)),
        "tail_census_source": str(TAIL_CENSUS.relative_to(ROOT)),
        "play_count": len(plays),
        "excluded_plays": sorted(excluded),
        "workbook_entries": len(wb_all),
        "workbook_entries_excluded": len(wb_excluded),
        "workbook_entries_in_cohort": len(wb),
        "workbook_matched_in_corpus": repaired_n,
        "workbook_not_in_corpus": len(not_in_corpus),
        "corpus": {
            "n": corpus_n,
            "pass": corpus_pass,
            "fail": corpus_fail,
            "pass_pct": corpus_pass_pct,
        },
        "untouched": {
            "n": untouched_n,
            "pass": untouched_pass,
            "fail": untouched_fail,
            "pass_pct": pct(untouched_pass, untouched_n),
            "derivation": "corpus_totals_minus_workbook_cohort",
        },
        "repaired_cohort": {
            "n": repaired_n,
            "pass": repaired_pass,
            "fail": repaired_fail,
            "pass_pct": pct(repaired_pass, repaired_n),
        },
        "repaired_by_status": repaired_by_status,
        "spliced_complete_only": {
            "n": len(spliced),
            "pass": spliced_ok,
            "fail": len(spliced) - spliced_ok,
            "pass_pct": pct(spliced_ok, len(spliced)),
        },
    }

    payload = {
        "summary": summary,
        "workbook_crossref": crossref,
        "workbook_not_in_corpus": not_in_corpus,
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    u, r, c = summary["untouched"], summary["repaired_cohort"], summary["corpus"]
    sp = summary["spliced_complete_only"]
    lines = [
        "# Tail-verify repair cohort split",
        "",
        f"**Date:** {summary['date']}",
        "",
        summary["limitation"],
        "",
    ]
    if excluded:
        lines.append(
            f"**Excluded plays ({len(excluded)}):** {', '.join(sorted(excluded))}"
        )
        lines.append("")
    lines.extend(
        [
        f"Repair manifest: `{WORKBOOK.name}` ({summary['workbook_entries']} entries, "
        f"{summary['workbook_entries_excluded']} excluded, "
        f"{summary['workbook_matched_in_corpus']} matched in current corpus)",
        "",
        "## Two-group split",
        "",
        "| Cohort | Notes | Pass | Fail | Pass % |",
        "|--------|------:|-----:|-----:|-------:|",
        f"| Never in workbook | {u['n']:,} | {u['pass']:,} | {u['fail']:,} | **{u['pass_pct']}%** |",
        f"| Workbook-flagged (repair cohort) | {r['n']:,} | {r['pass']:,} | {r['fail']:,} | **{r['pass_pct']}%** |",
        f"| Full corpus (census) | {c['n']:,} | {c['pass']:,} | {c['fail']:,} | **{c['pass_pct']}%** |",
        "",
        "## By workbook status",
        "",
        "| Status | n | Pass % |",
        "|--------|--:|-------:|",
        ]
    )
    for status, st in sorted(summary["repaired_by_status"].items()):
        lines.append(f"| {status} | {st['n']} | {st['pass_pct']}% |")
    lines.extend(
        [
            "",
            "## Spliced only (`complete` + text changed)",
            "",
            f"| n | Pass | Fail | Pass % |",
            f"|--:|-----:|-----:|-------:|",
            f"| {sp['n']} | {sp['pass']} | {sp['fail']} | **{sp['pass_pct']}%** |",
            "",
            f"Auditable per-note cross-ref: `{out_json.name}` → `workbook_crossref`",
        ]
    )
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    print(f"Untouched: {u['n']} → {u['pass_pct']}% pass")
    print(f"Workbook:  {r['n']} → {r['pass_pct']}% pass")
    print(f"Spliced:   {sp['n']} → {sp['pass_pct']}% pass")
    print(f"Not in corpus: {len(not_in_corpus)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
