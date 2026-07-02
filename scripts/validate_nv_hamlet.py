#!/usr/bin/env python3
"""Hamlet New Variorum accuracy audit.

Level 1: canonical hamlet_notes (1).json vs site hamlet.json (note fidelity)
Level 2: sample notes vs Internet Archive Furness Hamlet
Level 3: coverage; soliloquy spot-check (To be or not to be must have 2 note blocks)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from nv_ia_witness import classify_match, fetch_ia_text, ia_match_score  # noqa: E402

CANONICAL = ROOT / "Public/Data/hamlet_notes (1).json"
SITE_JSON = ROOT / "Public/Data/hamlet.json"
IA_ID = "newvariorumediti02shak"
IA_STREAM = "newvariorumediti02shak_djvu.txt"
IA_ITEM = f"https://archive.org/details/{IA_ID}"
SAMPLE_SIZE = 40


def normalize_scene_key(key: str) -> str:
    m = re.match(r"ACT\s+(\d+)\s*,?\s*SCENE\s+(\d+)", key.strip(), re.I)
    if m:
        return f"ACT {int(m.group(1))}, SCENE {int(m.group(2))}"
    return key.strip()


def iter_note_lines(data: dict) -> list[dict]:
    rows = []
    for scene, scene_data in data.items():
        if str(scene).startswith("_") or not isinstance(scene_data, dict):
            continue
        norm_scene = normalize_scene_key(scene)
        for line_key, line_data in scene_data.items():
            if not isinstance(line_data, dict):
                continue
            notes = line_data.get("notes") or []
            if not notes:
                continue
            rows.append(
                {
                    "scene": norm_scene,
                    "line_key": line_key,
                    "play": line_data.get("play", ""),
                    "notes": notes,
                }
            )
    return rows


def compare_canonical_vs_site(canonical: dict, site: dict) -> dict:
    c_rows = {(r["scene"], r["line_key"]): r["notes"] for r in iter_note_lines(canonical)}
    s_rows = {(r["scene"], r["line_key"]): r["notes"] for r in iter_note_lines(site)}
    only_c = set(c_rows) - set(s_rows)
    only_s = set(s_rows) - set(c_rows)
    changed = sum(1 for k in c_rows if k in s_rows and c_rows[k] != s_rows[k])
    identical = not only_c and not only_s and not changed
    return {
        "canonical_note_lines": len(c_rows),
        "site_note_lines": len(s_rows),
        "identical": identical,
        "only_canonical": len(only_c),
        "only_site": len(only_s),
        "differing_notes": changed,
        "summary": (
            "identical note payloads"
            if identical
            else f"only_canonical={len(only_c)}, only_site={len(only_s)}, differing={changed}"
        ),
    }


def soliloquy_check(data: dict) -> dict:
    for scene, scene_data in data.items():
        if not str(scene).startswith("ACT") or "3" not in str(scene) or "SCENE 1" not in normalize_scene_key(str(scene)):
            continue
        if not isinstance(scene_data, dict):
            continue
        for line_key, line_data in scene_data.items():
            play = (line_data.get("play") or "").lower()
            if "to be" in play and "not to be" in play:
                notes = line_data.get("notes") or []
                return {
                    "scene": normalize_scene_key(str(scene)),
                    "line_key": line_key,
                    "note_count": len(notes),
                    "note_lengths": [len(n) for n in notes],
                    "has_johnson_block": any("JOHNSON" in n.upper() for n in notes),
                    "has_del_block": any("DEL." in n or "DEL:" in n for n in notes),
                    "pass": len(notes) >= 2,
                }
    return {"pass": False, "error": "soliloquy line not found"}


def stratified_sample(rows: list[dict], n: int) -> list[dict]:
    if len(rows) <= n:
        return rows
    rows = sorted(rows, key=lambda r: (r["scene"], r["line_key"]))
    step = max(1, len(rows) // n)
    picks = rows[::step][:n]
    for anchor in ("3, SCENE 1",):
        for r in rows:
            if anchor in r["scene"] and r not in picks:
                picks.append(r)
    return picks[: n + 2]


def fetch_ia_witness() -> str:
    text, _src = fetch_ia_text(IA_ID, IA_STREAM)
    if text is None:
        raise OSError(f"could not load IA witness for {IA_ID}")
    return text


def main() -> int:
    print("=== Hamlet NV Accuracy Audit ===\n")
    if not CANONICAL.is_file():
        print(f"ERROR: missing {CANONICAL}")
        return 1
    if not SITE_JSON.is_file():
        print(f"ERROR: missing {SITE_JSON} — run scripts/sync_hamlet_from_canonical.py")
        return 1

    canonical = json.loads(CANONICAL.read_text(encoding="utf-8"))
    site = json.loads(SITE_JSON.read_text(encoding="utf-8"))

    l1 = compare_canonical_vs_site(canonical, site)
    print("--- Level 1: canonical vs site hamlet.json ---")
    for k, v in l1.items():
        print(f"  {k}: {v}")

    sol = soliloquy_check(site)
    print("\n--- Soliloquy spot-check (To be or not to be) ---")
    for k, v in sol.items():
        print(f"  {k}: {v}")

    sample = stratified_sample(iter_note_lines(canonical), SAMPLE_SIZE)
    print("\nFetching Internet Archive plain text …")
    try:
        ia_text = fetch_ia_witness()
        buckets = {"exact": 0, "high": 0, "partial": 0, "fail": 0}
        for row in sample:
            best = max((ia_match_score(ia_text, n) for n in row["notes"][:3]), default=0.0)
            buckets[classify_match(best)] += 1
        l2 = {"buckets": buckets, "ia_chars": len(ia_text)}
        print("\n--- Level 2: sample vs IA ---")
        print(f"  IA: {IA_ITEM}")
        print(f"  buckets: {buckets}")
    except Exception as e:
        print(f"WARN: IA compare skipped ({e})")
        l2 = None

    c_notes = sum(len(r["notes"]) for r in iter_note_lines(canonical))
    print("\n--- Level 3: coverage ---")
    print(f"  canonical note strings: {c_notes}")
    print(f"  annotated lines: {l1['canonical_note_lines']}")

    ok = l1["identical"] and sol.get("pass", False)
    report = {
        "play": "hamlet",
        "level1": l1,
        "soliloquy_check": sol,
        "level2": l2,
        "level3": {"canonical_note_strings": c_notes, "annotated_lines": l1["canonical_note_lines"]},
        "pass": ok,
        "ia_item": IA_ITEM,
    }
    out_path = ROOT / "validation" / "hamlet_nv_audit.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {out_path}")
    print(f"\nOverall: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
