#!/usr/bin/env python3
"""Repair truncated Coriolanus NV notes from IA tragedieofcoriol0002edit witness."""

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
    is_clipped,
    is_hard_truncation,
    is_hyphen_artifact,
    is_mid_sentence_cut,
    is_unbalanced_parens,
)
from nv_hyphen_splice import splice_hyphen  # noqa: E402
from nv_ia_witness import fetch_ia_text, fold_apostrophe  # noqa: E402
from nv_witness_map import WITNESS_BY_PLAY  # noqa: E402

JSON_PATH = ROOT / "Public/Data/Coriolanus.json"
BACKUP = JSON_PATH.with_suffix(".json.pre_clip_repair.backup")
SITE_MIRROR = ROOT / "My Website/Public/Data/Coriolanus.json"
PLAY = "Coriolanus"

_H4P2 = importlib.util.spec_from_file_location(
    "h4p2_repair", ROOT / "scripts/repair_henry_iv_part2_notes.py"
)
_h4p2 = importlib.util.module_from_spec(_H4P2)
_H4P2.loader.exec_module(_h4p2)

PLAY_BLOCK = re.compile(
    r"ACT\s+[IVXLC\d]+\s*,\s*sc\.?\s*[ivxlc\d]+\.?\]?\s*",
    re.I,
)
COR_HDR = re.compile(r"CORIOLANUS\s+\d{1,3}\s+", re.I)
SCENE_HDR = re.compile(r"\[ACT\s+[IVXLC\d]+,\s*sc\.\s*[ivxlc\d]+\.", re.I)
PAGE_NUM = re.compile(r"^\s*\d{1,3}\s*$")
PLAY_SPEAKER = re.compile(r"^[A-Za-z]{2,5}[,.]\s+[A-Z\u017f]", re.M)
RESUME = re.compile(
    r"(?:^|\s)(?:to|of|the|and|that|which|many|it must be|nausea|"
    r"[a-z]{4,}[\u2018\u2019',])|(?:\u2014|—)\s*\[|(?:\u2014|—)\s*$",
    re.I,
)
NEXT_NOTE = re.compile(
    r"\n\s*\d{1,3}\.\s+[\w .'\-\u2019]+\]\s*[A-Z(\[]|\n\s*ACT\s+[IVXLC]",
    re.I,
)


def norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def collapse(s: str) -> str:
    return re.sub(r"\s+", "", fold_apostrophe(s).lower())


def collapsed_pos(ia: str, idx: int) -> int:
    ci = 0
    for i, ch in enumerate(fold_apostrophe(ia).lower()):
        if not ch.isspace():
            if ci == idx:
                return i
            ci += 1
    return -1


def is_truncated(note: str) -> bool:
    return (
        is_clipped(note)
        or is_hard_truncation(note)
        or is_mid_sentence_cut(note)
        or is_hyphen_artifact(note)
        or is_unbalanced_parens(note)
    )


def is_fixed(note: str) -> bool:
    return not is_truncated(note)


def deinterleave_cor(text: str) -> str:
    text = PLAY_BLOCK.sub(" ||| ", text)
    text = COR_HDR.sub(" ||| ", text)
    text = SCENE_HDR.sub(" ||| ", text)
    parts = [p.strip() for p in text.split("|||") if p.strip()]
    if not parts:
        return norm_space(text)
    out = parts[0]
    for part in parts[1:]:
        lines = [ln.strip() for ln in part.splitlines() if ln.strip()]
        if lines and all(PAGE_NUM.match(ln) for ln in lines):
            continue
        if len(part) < 100 and PLAY_SPEAKER.search(part):
            continue
        if len(re.findall(r"\b[A-Z][a-z]+\b", part)) > 10 and len(part) > 150:
            m = RESUME.search(part)
            if m:
                out += " " + part[m.start() :]
                continue
        if part and (
            part[0].islower()
            or part.lstrip().startswith(
                ("to ", "of ", "the ", "and ", "that ", "which ")
            )
        ):
            out += " " + part
        elif re.search(r"[A-Za-z .'-]+:\s", part) or "—" in part or "Ed." in part:
            out += " " + part
    return norm_space(out)


def strip_lemma_prefix(lemma: str) -> str:
    return re.sub(r"^\d{1,3}\.\s*", "", lemma.strip()).lstrip("'\"")


def find_note_pos_cor(ia: str, note: str) -> int:
    pos = _h4p2.find_note_pos(ia, note)
    if pos >= 0:
        return pos

    folded_ia = fold_apostrophe(ia)
    ia_c = collapse(ia)

    for size in (160, 120, 100, 80, 60, 45, 30):
        if len(note) < size:
            continue
        needle = collapse(note[:size])
        if len(needle) < 25:
            continue
        idx = ia_c.find(needle)
        if idx >= 0:
            return collapsed_pos(ia, idx)

    if "]" in note:
        lemma = note[: note.index("]") + 1]
        for variant in (lemma, strip_lemma_prefix(lemma)):
            pat = _h4p2.flex_pattern(variant.replace("]", " ]"), max_words=10)
            if pat:
                m = pat.search(folded_ia)
                if m:
                    return m.start()

    body = note[note.index("]") + 1 :].strip() if "]" in note else note.strip()
    body = re.sub(r"^\d{1,3}\.\s*", "", body)
    words = re.findall(r"[A-Za-z0-9\u2019']+", fold_apostrophe(body))
    for n in (12, 10, 8, 6):
        if len(words) >= n:
            tail = " ".join(words[-n:])
            pat = _h4p2.flex_pattern(tail, n)
            if pat:
                m = pat.search(folded_ia)
                if m:
                    return max(0, m.start() - 200)

    critic = re.match(r"^[A-Za-z .'.-]+:\s*(.{20,120})", body)
    if critic:
        for chunk in (critic.group(1)[:70], critic.group(1)[:45]):
            pat = _h4p2.flex_pattern(chunk)
            if pat:
                m = pat.search(folded_ia)
                if m:
                    return max(0, m.start() - 120)

    for size in (80, 60, 45, 30):
        if len(body) >= size:
            idx = folded_ia.find(fold_apostrophe(body[:size]))
            if idx >= 0:
                return idx
            needle = collapse(body[:size])
            if len(needle) >= 25:
                cidx = ia_c.find(needle)
                if cidx >= 0:
                    return collapsed_pos(ia, cidx)
    return -1


def extract_from_ia_cor(ia: str, pos: int, json_note: str) -> str:
    start = max(0, pos - 120)
    chunk = ia[start : start + 8000]
    m = re.search(r"(\d{1,3}\.\s*)?[\w .'\"-]+\]\s*[A-Z(]", chunk, re.I)
    if m and m.start() <= (pos - start) + 40:
        chunk = chunk[m.start() :]
    ext = _h4p2.truncate_footnote(deinterleave_cor(chunk))
    if "]" in json_note:
        json_lemma = json_note[: json_note.index("]") + 1]
        em = re.match(r"^(\d{1,3}\.\s*)?[^\]]+\]\s*", ext)
        ext = json_lemma + (" " + ext[em.end() :].lstrip() if em else " " + ext)
    return norm_space(ext)


def try_repair(ia: str, note: str) -> str | None:
    if is_hyphen_artifact(note):
        ext = splice_hyphen(ia, note, next_note_pat=NEXT_NOTE)
        if ext and is_fixed(ext):
            return ext

    pos = find_note_pos_cor(ia, note)
    if pos < 0:
        return None
    ext = extract_from_ia_cor(ia, pos, note)
    if len(ext) > max(4000, len(note) * 8):
        return None
    if _h4p2.looks_contaminated(ext):
        return None

    improved = len(ext) > len(note) + 8 and is_fixed(ext)
    if not improved and len(ext) > len(note) + 8:
        improved = not is_hard_truncation(ext) and not is_mid_sentence_cut(ext)
    if not improved and is_fixed(ext) and len(ext) >= len(note) - 50:
        improved = not is_hard_truncation(note) or is_fixed(ext)
    return ext if improved else None


def repair(data: dict, ia: str, *, dry_run: bool = False) -> dict:
    stats = {
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
                if not is_truncated(note):
                    continue
                stats["before"] += 1
                ext = try_repair(ia, note)
                if ext:
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
                else:
                    stats["unresolved"] += 1

    for scene, scene_data in data.items():
        if str(scene).startswith("_") or not isinstance(scene_data, dict):
            continue
        for line_data in scene_data.values():
            if not isinstance(line_data, dict):
                continue
            for note in line_data.get("notes") or []:
                if is_truncated(note):
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
        f"before={stats['before']} repaired={stats['repaired']} "
        f"after={stats['after']} unresolved={stats['unresolved']}"
    )
    for ex in stats["examples"]:
        print(f"  + {ex['before_len']} -> {ex['after_len']} …{ex['tail']}")

    if not args.dry_run and stats["repaired"]:
        if not BACKUP.is_file():
            shutil.copy2(JSON_PATH, BACKUP)
            print(f"Backup → {BACKUP.relative_to(ROOT)}")
        out = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        JSON_PATH.write_text(out, encoding="utf-8")
        sync_mirrors(out)
        print(f"Wrote {JSON_PATH.relative_to(ROOT)}")
        if SITE_MIRROR.is_file():
            print(f"Mirror → {SITE_MIRROR.relative_to(ROOT)}")

    audit = ROOT / "validation/nv_coriolanus_repair.json"
    audit.write_text(
        json.dumps({"play": PLAY, "ia_id": ia_id, "witness": src, **stats}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
