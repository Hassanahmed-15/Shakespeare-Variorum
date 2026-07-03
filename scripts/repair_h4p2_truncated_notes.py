#!/usr/bin/env python3
"""Repair truncated Henry IV Part 2 NV notes from IA editi23 witness."""

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

from audit_nv_truncation import (  # noqa: E402
    ends_nv_terminal,
    is_clipped,
    is_hard_truncation,
    is_hyphen_artifact,
    is_mid_sentence_cut,
    is_unbalanced_parens,
    is_witness_prefix,
)
from nv_bracket_orphan import is_bracket_orphan, recover_lemma_from_ia  # noqa: E402
from nv_hyphen_splice import splice_hyphen  # noqa: E402
from nv_ia_witness import fetch_ia_text, fold_apostrophe  # noqa: E402
from nv_witness_map import WITNESS_BY_PLAY  # noqa: E402

JSON_PATH = ROOT / "Public/Data/henry_iv_part2.json"
BACKUP = JSON_PATH.with_suffix(".json.pre_clip_repair.backup")
SITE_MIRROR = ROOT / "My Website/Public/Data/henry_iv_part2.json"
PLAY = "Henry IV, Part 2"

_H4P2 = importlib.util.spec_from_file_location(
    "h4p2_repair", ROOT / "scripts/repair_henry_iv_part2_notes.py"
)
_h4p2 = importlib.util.module_from_spec(_H4P2)
_H4P2.loader.exec_module(_h4p2)


def norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def is_truncated(note: str, folded_ia: str | None) -> bool:
    return (
        is_clipped(note)
        or is_hard_truncation(note)
        or is_mid_sentence_cut(note)
        or is_hyphen_artifact(note)
        or is_unbalanced_parens(note)
        or (folded_ia is not None and is_witness_prefix(folded_ia, note))
    )


def strip_lemma_prefix(lemma: str) -> str:
    return re.sub(r"^\d{1,3}\.\s*", "", lemma.strip()).lstrip("'\"")


def find_via_body_prefix(ia: str, note: str) -> int:
    note_clean = re.sub(r"\s+", " ", note.strip())
    body = note_clean[note_clean.index("]") + 1 :].strip() if "]" in note_clean else note_clean
    body = re.sub(r"^\d{1,3}\.\s*", "", body)
    folded_ia = fold_apostrophe(ia)
    for size in (100, 80, 60, 45, 30):
        if len(body) < size:
            continue
        words = re.findall(r"[A-Za-z0-9']+", fold_apostrophe(body[:size]))
        if len(words) < 4:
            continue
        pat = re.compile(r"\s+".join(re.escape(w) for w in words[:14]), re.I)
        m = pat.search(folded_ia)
        if m:
            return m.start()
    critic = re.match(r"^[A-Za-z .'-]+:\s*(.{30,120})", note_clean)
    needle = (critic.group(1) if critic else note_clean[:80]).strip(" \"'[]")
    if len(needle) >= 20:
        idx = folded_ia.lower().find(fold_apostrophe(needle).lower())
        if idx >= 0:
            return idx
    return -1


def find_note_pos_h4p2(ia: str, note: str) -> int:
    pos = _h4p2.find_note_pos(ia, note)
    if pos >= 0:
        return pos

    folded_ia = fold_apostrophe(ia)
    if "]" in note:
        lemma = note[: note.index("]") + 1]
        for variant in (lemma, strip_lemma_prefix(lemma)):
            pat = _h4p2.flex_pattern(variant.replace("]", " ]"), max_words=10)
            if pat:
                m = pat.search(folded_ia)
                if m:
                    return m.start()

    body = note[note.index("]") + 1 :].strip() if "]" in note else note.strip()
    words = re.findall(r"[A-Za-z0-9\u2019']+", fold_apostrophe(body))
    for n in (12, 10, 8, 6):
        if len(words) >= n:
            tail = " ".join(words[-n:])
            pat = _h4p2.flex_pattern(tail, n)
            if pat:
                m = pat.search(folded_ia)
                if m:
                    return max(0, m.start() - 200)
    return find_via_body_prefix(ia, note)


def extract_from_ia_h4p2(ia: str, pos: int, json_note: str) -> str:
    start = max(0, pos - 120)
    chunk = ia[start : start + 8000]
    m = re.search(r"(\d{1,3}\.\s*)?[\w .'\"-]+\]\s*[A-Z(]", chunk, re.I)
    if m and m.start() <= (pos - start) + 40:
        chunk = chunk[m.start() :]
    ext = _h4p2.truncate_footnote(_h4p2.deinterleave(chunk))
    if "]" in json_note:
        json_lemma = json_note[: json_note.index("]") + 1]
        em = re.match(r"^(\d{1,3}\.\s*)?[^\]]+\]\s*", ext)
        ext = json_lemma + (" " + ext[em.end() :].lstrip() if em else " " + ext)
    return norm_space(ext)


def is_fixed(note: str, folded_ia: str | None) -> bool:
    return not is_truncated(note, folded_ia)


def try_hyphen_splice(ia: str, note: str, folded_ia: str | None) -> str | None:
    ext = splice_hyphen(ia, note)
    if ext and len(ext) > len(note) + 5 and is_fixed(ext, folded_ia):
        return ext
    return None


def repair_bracket_orphans(data: dict, ia: str, *, dry_run: bool = False) -> int:
    fixed = 0
    for scene, scene_data in data.items():
        if str(scene).startswith("_") or not isinstance(scene_data, dict):
            continue
        for line_data in scene_data.values():
            if not isinstance(line_data, dict):
                continue
            notes = line_data.get("notes") or []
            for i, note in enumerate(notes):
                if not is_bracket_orphan(note):
                    continue
                ext = recover_lemma_from_ia(ia, note)
                if ext and ext != note.strip():
                    if not dry_run:
                        notes[i] = ext
                    fixed += 1
    return fixed


def try_repair_note(ia: str, note: str, folded_ia: str) -> str | None:
    if is_hyphen_artifact(note):
        ext = try_hyphen_splice(ia, note, folded_ia)
        if ext:
            return ext

    pos = find_note_pos_h4p2(ia, note)
    if pos < 0:
        return None
    ext = extract_from_ia_h4p2(ia, pos, note)
    if len(ext) > max(4000, len(note) * 8):
        return None
    if _h4p2.looks_contaminated(ext):
        return None

    improved = len(ext) > len(note) + 8 and is_fixed(ext, folded_ia)
    if not improved and len(ext) > len(note) + 8:
        improved = not is_hard_truncation(ext) and not is_mid_sentence_cut(ext)
    if not improved and len(ext) > len(note) + 8 and is_clipped(note):
        improved = not is_clipped(ext)
    if not improved and is_bracket_orphan(note) and ext.startswith("[") and is_fixed(ext, folded_ia):
        improved = True
    return ext if improved else None


def repair(data: dict, ia: str, *, dry_run: bool = False) -> dict:
    folded_ia = fold_apostrophe(ia)
    stats = {
        "bracket_orphans_fixed": repair_bracket_orphans(data, ia, dry_run=dry_run),
        "before": 0,
        "repaired": 0,
        "after": 0,
        "unresolved": 0,
        "examples": [],
    }

    for scene, scene_data in data.items():
        if str(scene).startswith("_") or not isinstance(scene_data, dict):
            continue
        for line_data in scene_data.values():
            if not isinstance(line_data, dict):
                continue
            notes = line_data.get("notes") or []
            for i, note in enumerate(notes):
                if not is_truncated(note, folded_ia):
                    continue
                stats["before"] += 1
                ext = try_repair_note(ia, note, folded_ia)
                if ext is None:
                    stats["unresolved"] += 1
                    continue
                if not dry_run:
                    notes[i] = ext
                stats["repaired"] += 1
                if len(stats["examples"]) < 6:
                    stats["examples"].append(
                        {
                            "before_len": len(note),
                            "after_len": len(ext),
                            "tail": ext[-100:],
                        }
                    )

    for scene, scene_data in data.items():
        if str(scene).startswith("_") or not isinstance(scene_data, dict):
            continue
        for line_data in scene_data.values():
            if not isinstance(line_data, dict):
                continue
            for note in line_data.get("notes") or []:
                if is_truncated(note, folded_ia):
                    stats["after"] += 1
    return stats


def sync_mirrors(text: str) -> None:
    if SITE_MIRROR.parent.is_dir():
        SITE_MIRROR.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    ia_id, stream = WITNESS_BY_PLAY[PLAY]
    ia_text, src = fetch_ia_text(ia_id, stream)
    if ia_text is None:
        print(f"ERROR: witness unavailable: {src}", file=sys.stderr)
        return 1

    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    stats = repair(data, ia_text, dry_run=args.dry_run)

    print(f"Play: {PLAY}")
    print(f"IA: {ia_id} ({src})")
    print(
        f"bracket_orphans={stats['bracket_orphans_fixed']} "
        f"before={stats['before']} repaired={stats['repaired']} "
        f"after={stats['after']} unresolved={stats['unresolved']}"
    )
    for ex in stats["examples"]:
        print(f"  + {ex['before_len']} -> {ex['after_len']} …{ex['tail']}")

    if not args.dry_run and (stats["repaired"] or stats["bracket_orphans_fixed"]):
        if not BACKUP.is_file():
            shutil.copy2(JSON_PATH, BACKUP)
            print(f"Backup → {BACKUP.relative_to(ROOT)}")
        out = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        JSON_PATH.write_text(out, encoding="utf-8")
        sync_mirrors(out)
        print(f"Wrote {JSON_PATH.relative_to(ROOT)}")

    audit = ROOT / "validation/henry_iv_part2_repair.json"
    audit.write_text(
        json.dumps({"play": PLAY, "ia_id": ia_id, "witness": src, **stats}, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
