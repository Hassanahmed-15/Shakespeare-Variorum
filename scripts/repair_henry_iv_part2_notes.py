#!/usr/bin/env python3
"""Repair truncated Henry IV Part 2 variorum notes from IA editi23 witness.

Shaaber (1940) NV commentary in djvu.txt interleaves play text with footnotes.
This script re-extracts clipped note strings by matching note bodies in IA text,
stripping ACT/SCENE page intrusions, and writing the completed apparatus back.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from nv_ia_witness import fold_apostrophe  # noqa: E402
from nv_repair import (  # noqa: E402
    RESUME,
    deinterleave_default as deinterleave,
    extract_from_ia,
    find_note_pos,
    flex_pattern,
    norm_space,
    truncate_footnote,
)

JSON_PATH = ROOT / "Public/Data/henry_iv_part2.json"
BACKUP = JSON_PATH.with_suffix(".json.pre_repair.backup")
IA_ID = "newvariorumediti23shak"
IA_STREAM = f"{IA_ID}_djvu.txt"
IA_URL = f"https://archive.org/download/{IA_ID}/{IA_STREAM}"
CACHE = ROOT / "data/h4p2_ia_djvu.txt"


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


def looks_contaminated(note: str) -> bool:
    return bool(
        re.search(r"ACT\s+[IVXLC\d]+\s*,\s*sc\.", note, re.I)
        and re.search(r"HENRY\s+THE\s+FOURTH", note, re.I)
    )


def fetch_ia(cache_only: bool = False) -> str:
    if CACHE.is_file() and CACHE.stat().st_size > 100_000:
        return CACHE.read_text(encoding="utf-8", errors="replace")
    if cache_only:
        raise SystemExit(f"Missing cached IA text: {CACHE}")
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(IA_URL, headers={"User-Agent": "nv-repair-h4p2/1.0"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        text = resp.read().decode("utf-8", errors="replace")
    CACHE.write_text(text, encoding="utf-8")
    return text


def repair(data: dict, ia: str, dry_run: bool = False) -> dict:
    stats = {
        "clipped_before": 0,
        "clipped_after": 0,
        "repaired": 0,
        "unresolved": 0,
        "examples": [],
    }

    for scene, scene_data in data.items():
        if not str(scene).startswith("ACT") or not isinstance(scene_data, dict):
            continue
        for line_data in scene_data.values():
            if not isinstance(line_data, dict):
                continue
            notes = line_data.get("notes") or []
            for i, note in enumerate(notes):
                if not is_clipped(note):
                    continue
                stats["clipped_before"] += 1
                pos = find_note_pos(ia, note)
                if pos < 0:
                    stats["unresolved"] += 1
                    continue
                ext = extract_from_ia(ia, pos, note)
                if len(ext) > max(3500, len(note) * 6):
                    stats["unresolved"] += 1
                    continue
                if looks_contaminated(ext):
                    stats["unresolved"] += 1
                    continue
                if len(ext) > len(note) + 12 and not is_clipped(ext):
                    if not dry_run:
                        notes[i] = ext
                    stats["repaired"] += 1
                    if len(stats["examples"]) < 8:
                        stats["examples"].append(
                            {"before_len": len(note), "after_len": len(ext), "tail": ext[-120:]}
                        )
                else:
                    stats["unresolved"] += 1

    for scene, scene_data in data.items():
        if not str(scene).startswith("ACT") or not isinstance(scene_data, dict):
            continue
        for line_data in scene_data.values():
            if not isinstance(line_data, dict):
                continue
            for note in line_data.get("notes") or []:
                if is_clipped(note):
                    stats["clipped_after"] += 1
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--cache-only", action="store_true")
    args = ap.parse_args()

    if not JSON_PATH.is_file():
        print(f"ERROR: missing {JSON_PATH}", file=sys.stderr)
        return 1

    ia = fetch_ia(cache_only=args.cache_only)
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    stats = repair(data, ia, dry_run=args.dry_run)

    print(f"IA witness: {IA_ID} ({len(ia):,} chars)")
    print(f"Clipped before: {stats['clipped_before']}")
    print(f"Repaired:       {stats['repaired']}")
    print(f"Unresolved:     {stats['unresolved']}")
    print(f"Clipped after:  {stats['clipped_after']}")
    for ex in stats["examples"]:
        print(f"  + {ex['before_len']} -> {ex['after_len']} chars …{ex['tail']}")

    if args.dry_run:
        return 0

    if stats["repaired"]:
        if JSON_PATH.is_file() and not BACKUP.is_file():
            shutil.copy2(JSON_PATH, BACKUP)
            print(f"Backup → {BACKUP.relative_to(ROOT)}")
        JSON_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {JSON_PATH.relative_to(ROOT)}")

    audit_path = ROOT / "validation/henry_iv_part2_repair.json"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(
        json.dumps({"ia_id": IA_ID, "ia_url": IA_URL, **stats}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {audit_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
