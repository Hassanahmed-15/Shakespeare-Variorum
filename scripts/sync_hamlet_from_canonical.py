#!/usr/bin/env python3
"""Sync Public/Data/hamlet.json from canonical hamlet_notes (1).json (no note merging)."""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "Public/Data/hamlet_notes (1).json"
OUT = ROOT / "Public/Data/hamlet.json"
MY_WEBSITE_OUT = ROOT / "My Website/Public/Data/hamlet.json"
BACKUP = OUT.with_suffix(".json.pre_sync.backup")


def normalize_scene_key(key: str) -> str:
    """Match index.html normalizeSceneKey: ACT N, SCENE M (comma, Arabic)."""
    n = key.strip()
    m = re.match(r"ACT\s+(\d+)\s+SCENE\s+(\d+)", n, re.I)
    if m:
        return f"ACT {int(m.group(1))}, SCENE {int(m.group(2))}"
    m = re.match(r"ACT\s+(\d+)\s*,\s*SCENE\s+(\d+)", n, re.I)
    if m:
        return f"ACT {int(m.group(1))}, SCENE {int(m.group(2))}"
    return key


def sync() -> dict:
    if not CANONICAL.is_file():
        raise SystemExit(f"Missing canonical file: {CANONICAL}")

    src = json.loads(CANONICAL.read_text(encoding="utf-8"))
    out: dict = {}
    for scene_key, scene_data in src.items():
        nk = normalize_scene_key(scene_key) if str(scene_key).startswith("ACT") else scene_key
        out[nk] = scene_data

    if OUT.is_file():
        shutil.copy2(OUT, BACKUP)
        print(f"Backed up existing {OUT.name} → {BACKUP.name}")

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")

    if MY_WEBSITE_OUT.parent.is_dir():
        MY_WEBSITE_OUT.write_text(OUT.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Wrote {MY_WEBSITE_OUT.relative_to(ROOT)}")

    def note_stats(data: dict) -> tuple[int, int]:
        lines = notes = 0
        for scene, sd in data.items():
            if str(scene).startswith("_") or not isinstance(sd, dict):
                continue
            for obj in sd.values():
                if isinstance(obj, dict) and obj.get("notes"):
                    lines += 1
                    notes += len(obj["notes"])
        return lines, notes

    cl, cn = note_stats(out)
    print(f"  annotated lines: {cl}, note strings: {cn}")
    return out


def main() -> int:
    sync()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
