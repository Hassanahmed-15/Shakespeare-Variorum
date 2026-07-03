#!/usr/bin/env python3
"""Repair clipped NV notes using the correct Internet Archive witness per play."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_nv_fidelity_all_plays import PLAYS, is_clipped  # noqa: E402
from nv_ia_witness import fetch_ia_text  # noqa: E402
from nv_witness_map import WITNESS_BY_PLAY  # noqa: E402

_H4P2 = importlib.util.spec_from_file_location(
    "h4p2_repair", ROOT / "scripts/repair_henry_iv_part2_notes.py"
)
_h4p2 = importlib.util.module_from_spec(_H4P2)
_H4P2.loader.exec_module(_h4p2)


def repair_file(play: str, json_rel: str, *, dry_run: bool = False) -> dict:
    path = ROOT / json_rel
    ia_id, stream = WITNESS_BY_PLAY[play]
    ia_text, src = fetch_ia_text(ia_id, stream)
    if ia_text is None:
        return {"play": play, "error": f"witness unavailable: {src}"}

    data = json.loads(path.read_text(encoding="utf-8"))
    stats = _h4p2.repair(data, ia_text, dry_run=dry_run)
    stats.update({"play": play, "ia_id": ia_id, "witness": src})

    if not dry_run and stats["repaired"]:
        backup = path.with_suffix(path.suffix + ".pre_clip_repair.backup")
        if not backup.is_file():
            shutil.copy2(path, backup)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        stats["wrote"] = str(path.relative_to(ROOT))
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--play", help="Repair one play (exact name from audit list)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--min-clipped", type=int, default=1, help="Only repair if clipped count >= N")
    args = ap.parse_args()

    targets = [s for s in PLAYS if not args.play or s["play"] == args.play]
    if args.play and not targets:
        print(f"Unknown play: {args.play}", file=sys.stderr)
        return 1

    rows = []
    for spec in targets:
        path = ROOT / spec["json"]
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        clipped_before = sum(
            1
            for scene, scene_data in data.items()
            if str(scene).startswith("ACT") and isinstance(scene_data, dict)
            for line_data in scene_data.values()
            if isinstance(line_data, dict)
            for note in line_data.get("notes") or []
            if is_clipped(note)
        )
        if clipped_before < args.min_clipped:
            continue
        stats = repair_file(spec["play"], spec["json"], dry_run=args.dry_run)
        rows.append(stats)
        print(
            f"{spec['play']:<32} clip {stats.get('clipped_before', '?'):>4} -> "
            f"{stats.get('clipped_after', '?'):>4}  repaired {stats.get('repaired', 0):>4}  "
            f"unresolved {stats.get('unresolved', 0):>4}"
        )

    out = ROOT / "validation" / "nv_clip_repair.json"
    out.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
