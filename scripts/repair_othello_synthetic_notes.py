#!/usr/bin/env python3
"""Remove synthetic-prefix notes from Othello Folger JSON and optionally fill from IA."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from nv_ia_witness import SYNTHETIC_RE, fetch_ia_text  # noqa: E402

JSON_PATH = ROOT / "Public/Data/othello_notes_folger.json"
MIRROR_PATH = ROOT / "Public/Data/othello_notes.json"
SITE_MIRROR = ROOT / "My Website/Public/Data/othello_notes_folger.json"
BACKUP = JSON_PATH.with_suffix(".json.pre_synth_repair.backup")
IA_ID = "newvariorumediti13shak"
IA_STREAM = f"{IA_ID}_djvu.txt"

_H4P2 = importlib.util.spec_from_file_location(
    "h4p2_repair", ROOT / "scripts/repair_henry_iv_part2_notes.py"
)
_h4p2 = importlib.util.module_from_spec(_H4P2)
_H4P2.loader.exec_module(_h4p2)

# Play-line keywords -> NV lemma prefix to search in IA for synth-only lines.
FILL_HINTS: dict[str, tuple[str, str]] = {
    "1.1.4": ("But]", "7.  But]"),
    "1.1.5": ("matter,", "8.  matter,"),
    "1.1.16": ("conclusion", "18,  19.  warre"),
    "1.1.23": ("squadron", "Neuer]"),
    "1.1.26": ("Tongued", "27.  Tongued]"),
    "1.1.34": ("lieutenant", "Lieutenant]"),
    "1.1.36": ("hangman", "36"),
    "1.1.44": ("content", "content"),
    "1.1.46": ("masters", "masters"),
    "1.1.47": ("followed", "followed"),
    "1.1.52": ("cashiered", "cashiered"),
    "1.1.53": ("Whip me", "Whip"),
    "1.1.54": ("trimmed", "trimmed"),
    "1.1.56": ("shows of service", "service"),
}


def play_keywords(play: str) -> list[str]:
    text = re.sub(r"^[A-Z]+:\s*", "", play.strip())
    words = re.findall(r"[A-Za-z']+", text)
    return [w for w in words if len(w) > 3][:6]


def try_extract(ia: str, line_key: str, play: str) -> str | None:
    hint = FILL_HINTS.get(line_key)
    if hint:
        lemma, search = hint
        pos = ia.find(search)
        if pos >= 0:
            ext = _h4p2.extract_from_ia(ia, pos, f"{lemma} placeholder")
            if ext and len(ext) > 40 and not SYNTHETIC_RE.match(ext):
                return ext
    for kw in play_keywords(play):
        pat = _h4p2.flex_pattern(kw, 1)
        if pat:
            m = pat.search(_h4p2.fold_apostrophe(ia))
            if m:
                chunk = ia[max(0, m.start() - 80) : m.start() + 400]
                em = re.search(r"(\d{1,3}\.\s*)?[\w .'-]+\]\s*[A-Z(]", chunk, re.I)
                if em:
                    ext = _h4p2.extract_from_ia(ia, max(0, m.start() - 80) + em.start(), "")
                    if ext and len(ext) > 40:
                        return ext
    return None


def repair(data: dict, ia: str | None, *, fill_empty: bool) -> dict:
    stats = {
        "synthetic_removed": 0,
        "lines_stripped": 0,
        "filled_from_ia": 0,
        "still_empty": 0,
    }
    for scene, scene_data in data.items():
        if str(scene).startswith("_") or not isinstance(scene_data, dict):
            continue
        for line_key, line_data in scene_data.items():
            if not isinstance(line_data, dict):
                continue
            notes = line_data.get("notes") or []
            kept = [n for n in notes if not SYNTHETIC_RE.match(n.strip())]
            removed = len(notes) - len(kept)
            if removed:
                stats["synthetic_removed"] += removed
                stats["lines_stripped"] += 1
            if not kept and fill_empty and ia:
                ext = try_extract(ia, str(line_key), line_data.get("play", ""))
                if ext:
                    kept = [ext]
                    stats["filled_from_ia"] += 1
            if not kept and removed:
                stats["still_empty"] += 1
            line_data["notes"] = kept
    return stats


def sync_mirrors(text: str) -> None:
    MIRROR_PATH.write_text(text, encoding="utf-8")
    if SITE_MIRROR.parent.is_dir():
        SITE_MIRROR.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-fill", action="store_true", help="Strip synth only; do not IA-fill")
    args = ap.parse_args()

    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    ia_text = None
    if not args.no_fill:
        ia_text, _ = fetch_ia_text(IA_ID, IA_STREAM)

    stats = repair(data, ia_text, fill_empty=not args.no_fill)
    print(
        f"Removed {stats['synthetic_removed']} synthetic notes on "
        f"{stats['lines_stripped']} lines; "
        f"IA-filled {stats['filled_from_ia']}; "
        f"empty after strip {stats['still_empty']}"
    )

    if not args.dry_run:
        if not BACKUP.is_file():
            shutil.copy2(JSON_PATH, BACKUP)
        out = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        JSON_PATH.write_text(out, encoding="utf-8")
        sync_mirrors(out)
        print(f"Wrote {JSON_PATH.relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
