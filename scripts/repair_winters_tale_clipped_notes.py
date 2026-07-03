#!/usr/bin/env python3
"""Repair truncated Winter's Tale NV notes from IA witness (winterstale0007unse)."""

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

from audit_nv_fidelity_all_plays import is_clipped  # noqa: E402
from audit_nv_truncation import (  # noqa: E402
    is_hyphen_artifact,
    is_mid_sentence_cut,
    is_unbalanced_parens,
    is_witness_prefix,
)
from nv_ia_witness import fetch_ia_text, fold_apostrophe  # noqa: E402
from nv_witness_map import WITNESS_BY_PLAY  # noqa: E402

JSON_PATH = ROOT / "Public/Data/the_winters_tale.json"
SITE_MIRROR = ROOT / "My Website/Public/Data/the_winters_tale.json"
BACKUP = JSON_PATH.with_suffix(".json.pre_clip_repair.backup")

_H4P2 = importlib.util.spec_from_file_location(
    "h4p2", ROOT / "scripts/repair_henry_iv_part2_notes.py"
)
_h4p2 = importlib.util.module_from_spec(_H4P2)
_H4P2.loader.exec_module(_h4p2)

PLAY_BLOCK = re.compile(
    r"ACT\s+[IVXLC\d]+\s*,\s*sc\.?\s*\d+\.?\]?\s*(?:THE\s+WINTERS\s+TALE)?\s*\d*\s*",
    re.I,
)
PAGE_HDR = re.compile(r"THE\s+WINTERS\s+TALE\s+\d{1,3}\s+", re.I)
PAGE_HDR2 = re.compile(r"THE\s+WINTERS\s+TALE\s+\[act[^\]]+\]\.?\s*\d*\s*", re.I)
INTRUSION = re.compile(
    r"ACT\s+[IVXLC\d]+,\s*SC\.\s*[ivxlc\d]+\.\]?\s*(?:THE\s+WINTERS\s+TALE.*?)?(?="
    r"ferently|age\)|\d{1,3}\.\s+[A-Za-z(\[]|\Z)",
    re.I | re.S,
)
ACT_HDR = re.compile(r"ACT\s+[IVXLC\d]+,\s*SC\.\s*[ivxlc\d]+\.\]?\s*", re.I)
PLAY_LINE = re.compile(
    r"(?:Mam|Her|Leo|Pol|Flo|Per|Aut|Clown|Shep|Cam)\.\s+[A-Z].{20,200}?(?=\d{1,3}\.\s|\Z)",
    re.S,
)


def strip_intrusions(text: str) -> str:
    text = INTRUSION.sub(" ", text)
    text = ACT_HDR.sub(" ", text)
    text = PLAY_LINE.sub(" ", text)
    text = PAGE_HDR.sub(" ", text)
    text = PAGE_HDR2.sub(" ", text)
    text = PLAY_BLOCK.sub(" ", text)
    return _h4p2.norm_space(text)


def collapse(s: str) -> str:
    return re.sub(r"\s+", "", fold_apostrophe(s).lower())


def deinterleave_wt(text: str) -> str:
    text = PLAY_BLOCK.sub(" ||| ", text)
    text = PAGE_HDR.sub(" ||| ", text)
    text = PAGE_HDR2.sub(" ||| ", text)
    parts = [p.strip() for p in text.split("|||") if p.strip()]
    if not parts:
        return _h4p2.norm_space(text)
    out = parts[0]
    for part in parts[1:]:
        if len(re.findall(r"\b[A-Z][a-z]+\b", part)) > 8 and len(part) > 120:
            m = _h4p2.RESUME.search(part)
            if m:
                out += " " + part[m.start() :]
        else:
            out += " " + part
    return _h4p2.norm_space(out)


def collapsed_pos(ia: str, idx: int) -> int:
    ci = 0
    for i, ch in enumerate(fold_apostrophe(ia).lower()):
        if not ch.isspace():
            if ci == idx:
                return i
            ci += 1
    return -1


def find_note_pos(ia: str, note: str) -> int:
    pos = _h4p2.find_note_pos(ia, note)
    if pos >= 0:
        return pos
    body = note[note.index("]") + 1 :].strip() if "]" in note else note.strip()
    body = re.sub(r"^\d{1,3}\.\s*", "", body)
    ia_c = collapse(ia)
    for size in (120, 100, 80, 60, 45, 30):
        if len(body) < size:
            continue
        needle = collapse(body[:size])
        if len(needle) < 25:
            continue
        idx = ia_c.find(needle)
        if idx >= 0:
            return collapsed_pos(ia, idx)
    return -1


def extract_from_ia(ia: str, pos: int, json_note: str) -> str:
    start = max(0, pos - 120)
    chunk = ia[start : start + 6000]
    m = re.search(r"(\d{1,3}\.\s*)?[\w .'-]+\]\s*[A-Z(]", chunk, re.I)
    if m and m.start() <= (pos - start) + 10:
        chunk = chunk[m.start() :]
    ext = _h4p2.truncate_footnote(deinterleave_wt(chunk))
    ext = strip_intrusions(ext)
    if "]" in json_note:
        json_lemma = json_note[: json_note.index("]") + 1]
        em = re.match(r"^(\d{1,3}\.\s*)?[^\]]+\]\s*", ext)
        ext = json_lemma + (" " + ext[em.end() :].lstrip() if em else " " + ext)
    return _h4p2.norm_space(ext)


def is_truncated(note: str, folded_ia: str) -> bool:
    wp = bool(folded_ia and is_witness_prefix(folded_ia, note))
    if wp:
        return True
    if is_hyphen_artifact(note):
        return True
    if is_unbalanced_parens(note) and len(note) < 500:
        return True
    if is_mid_sentence_cut(note) and len(note) < 600:
        return True
    if is_clipped(note):
        return True
    return False


def looks_contaminated(note: str) -> bool:
    if re.search(r"WINTERS\s+TALE", note, re.I):
        return True
    if re.search(r"ACT\s+[IVXLC\d]+\s*,\s*sc\.", note, re.I):
        return True
    if re.search(r"\b(?:Mam|Her|Leo|Pol|Flo|Per|Aut)\.\s+[A-Z][a-z]{3,}", note):
        return True
    if len(re.findall(r"\]\s*[A-Z][a-z]+(?:\s*\([^)]*\))?\s*:", note)) > 3:
        return True
    return False


def note_prefix_ok(original: str, extracted: str) -> bool:
    body_o = original[original.index("]") + 1 :].strip() if "]" in original else original
    body_e = extracted[extracted.index("]") + 1 :].strip() if "]" in extracted else extracted
    for size in (50, 40, 30, 20):
        if len(body_o) < size:
            continue
        if collapse(body_o[:size]) in collapse(body_e[: max(size + 40, 80)]):
            return True
    return False


def count_clipped(data: dict) -> int:
    n = 0
    for scene, sd in data.items():
        if not str(scene).startswith("ACT"):
            continue
        for obj in sd.values():
            if isinstance(obj, dict):
                for note in obj.get("notes") or []:
                    if is_clipped(note):
                        n += 1
    return n


def repair(data: dict, ia: str, folded_ia: str, *, dry_run: bool = False) -> dict:
    stats = {
        "clipped_before": count_clipped(data),
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
                if not is_truncated(note, folded_ia):
                    continue
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
                if not note_prefix_ok(note, ext):
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

    stats["clipped_after"] = count_clipped(data)
    return stats


def sync_mirror(text: str) -> None:
    if SITE_MIRROR.parent.is_dir():
        SITE_MIRROR.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    ia_id, stream = WITNESS_BY_PLAY["The Winter's Tale"]
    ia, src = fetch_ia_text(ia_id, stream)
    if ia is None:
        print(f"ERROR: witness unavailable: {src}", file=sys.stderr)
        return 1

    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    folded_ia = fold_apostrophe(ia)
    stats = repair(data, ia, folded_ia, dry_run=args.dry_run)
    stats.update({"play": "The Winter's Tale", "ia_id": ia_id, "witness": src})

    print(
        f"before={stats['clipped_before']} repaired={stats['repaired']} "
        f"after={stats['clipped_after']} unresolved={stats['unresolved']}"
    )
    for ex in stats["examples"]:
        print(f"  + {ex['before_len']} -> {ex['after_len']} …{ex['tail']}")

    if args.dry_run:
        return 0

    if stats["repaired"]:
        if JSON_PATH.is_file() and not BACKUP.is_file():
            shutil.copy2(JSON_PATH, BACKUP)
            print(f"Backup → {BACKUP.relative_to(ROOT)}")
        out = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        JSON_PATH.write_text(out, encoding="utf-8")
        sync_mirror(out)
        print(f"Wrote {JSON_PATH.relative_to(ROOT)}")
        if SITE_MIRROR.is_file():
            print(f"Synced {SITE_MIRROR.relative_to(ROOT)}")

    audit = ROOT / "validation/nv_clip_repair.json"
    existing = json.loads(audit.read_text()) if audit.is_file() else []
    existing = [r for r in existing if r.get("play") != "The Winter's Tale"]
    existing.append(stats)
    audit.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
