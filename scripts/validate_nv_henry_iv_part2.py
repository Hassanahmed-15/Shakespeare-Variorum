#!/usr/bin/env python3
"""Henry IV Part 2 New Variorum fidelity audit (Shaaber 1940 / IA editi23)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from nv_ia_witness import (  # noqa: E402
    PARAPHRASE_RE as PARA,
    SYNTHETIC_RE as SYNTH,
    classify_match,
    fetch_ia_text,
    ia_match_score,
)

JSON_PATH = ROOT / "Public/Data/henry_iv_part2.json"
IA_ID = "newvariorumediti23shak"
IA_STREAM = f"{IA_ID}_djvu.txt"
IA_ITEM = f"https://archive.org/details/{IA_ID}"
SAMPLE_SIZE = 40


def is_clipped(note: str) -> bool:
    n = note.strip()
    if not n:
        return False
    if re.search(
        r"\b(to|the|a|an|of|in|that|which|with|for|as|is|are|was|were|be|"
        r"have|has|had|not|but|on|at|from)\s*$",
        n,
        re.I,
    ):
        return True
    if re.search(r"-\s*$", n):
        return True
    if n.count("(") > n.count(")"):
        return True
    if n.rstrip()[-1:] in ";:,":
        return True
    return False


def collect_notes(data: dict) -> list[str]:
    notes: list[str] = []
    for scene, scene_data in data.items():
        if str(scene).startswith("_") or not isinstance(scene_data, dict):
            continue
        for obj in scene_data.values():
            if isinstance(obj, dict) and obj.get("notes"):
                notes.extend(obj["notes"])
    return notes


def iter_note_lines(data: dict) -> list[dict]:
    rows = []
    for scene, scene_data in data.items():
        if str(scene).startswith("_") or not isinstance(scene_data, dict):
            continue
        for line_key, line_data in scene_data.items():
            if not isinstance(line_data, dict):
                continue
            notes = line_data.get("notes") or []
            if notes:
                rows.append({"scene": scene, "line_key": line_key, "notes": notes})
    return rows


def stratified_sample(rows: list[dict], n: int) -> list[dict]:
    if len(rows) <= n:
        return rows
    rows = sorted(rows, key=lambda r: (r["scene"], r["line_key"]))
    step = max(1, len(rows) // n)
    return rows[::step][:n]


def fetch_ia_witness() -> str:
    text, _src = fetch_ia_text(IA_ID, IA_STREAM)
    if text is None:
        raise OSError(f"could not load IA witness for {IA_ID}")
    return text


def main() -> int:
    print("=== Henry IV Part 2 NV Fidelity Audit ===\n")
    if not JSON_PATH.is_file():
        print(f"ERROR: missing {JSON_PATH}")
        return 1

    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    notes = collect_notes(data)
    clipped = sum(1 for n in notes if is_clipped(n))
    clip_rate = round(100 * clipped / len(notes), 2) if notes else 0.0
    synthetic = sum(1 for n in notes if SYNTH.match(n.strip()))
    paraphrase = sum(
        1
        for n in notes
        if len(n) < 300 and (" — " in n or "—" in n) and PARA.search(n)
    )

    print("--- Structural fidelity ---")
    print(f"  note strings: {len(notes)}")
    print(f"  annotated lines: {len(iter_note_lines(data))}")
    print(f"  synthetic_prefix: {synthetic}")
    print(f"  paraphrase_style: {paraphrase}")
    print(f"  clipped_notes: {clipped} ({clip_rate}%)")

    sample = stratified_sample(iter_note_lines(data), SAMPLE_SIZE)
    print("\nFetching Internet Archive plain text …")
    try:
        ia_text = fetch_ia_witness()
        buckets = {"exact": 0, "high": 0, "partial": 0, "fail": 0}
        for row in sample:
            best = max((ia_match_score(ia_text, n) for n in row["notes"][:3]), default=0.0)
            buckets[classify_match(best)] += 1
        l2 = {"buckets": buckets, "ia_chars": len(ia_text)}
        print("\n--- IA sample (editi23) ---")
        print(f"  IA: {IA_ITEM}")
        print(f"  buckets: {buckets}")
    except Exception as e:
        print(f"WARN: IA compare skipped ({e})")
        l2 = None

    ok = synthetic == 0 and paraphrase == 0 and clip_rate <= 4.0
    report = {
        "play": "henry_iv_part2",
        "ia_item": IA_ITEM,
        "note_strings": len(notes),
        "annotated_lines": len(iter_note_lines(data)),
        "synthetic_prefix": synthetic,
        "paraphrase_style": paraphrase,
        "clipped_notes": clipped,
        "clipped_pct": clip_rate,
        "level2": l2,
        "pass": ok,
        "tier": "A" if ok else "B",
    }
    out_path = ROOT / "validation/henry_iv_part2_nv_audit.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {out_path}")
    print(f"\nOverall: {'PASS (Tier A)' if ok else 'FAIL (Tier B)'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
