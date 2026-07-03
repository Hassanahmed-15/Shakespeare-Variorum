#!/usr/bin/env python3
"""Repair union-truncated Twelfth Night NV notes from IA witness."""

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
    collect_notes,
    ends_terminal,
    is_clipped,
    is_hard_truncation,
    is_hyphen_artifact,
    is_mid_sentence_cut,
    is_unbalanced_parens,
    is_witness_prefix,
)
from nv_ia_witness import fetch_ia_text, fold_apostrophe  # noqa: E402
from nv_witness_map import WITNESS_BY_PLAY  # noqa: E402

JSON_PATH = ROOT / "Public/Data/twelfth_night.json"
SITE_MIRROR = ROOT / "My Website/Public/Data/twelfth_night.json"
BACKUP = JSON_PATH.with_suffix(".json.pre_trunc_repair.backup")

_H4P2 = importlib.util.spec_from_file_location(
    "h4p2_repair", ROOT / "scripts/repair_henry_iv_part2_notes.py"
)
_h4p2 = importlib.util.module_from_spec(_H4P2)
_H4P2.loader.exec_module(_h4p2)

TN_PLAY_BLOCK = re.compile(
    r"ACT\s+[IVXLC\d]+\s*,\s*sc\.?\s*[ivxlc\d]+\.?\]?\s*(?:OR, WHAT YOU WILL)?\s*\d*\s*",
    re.I,
)
TN_PAGE_HDR = re.compile(r"(?:\d+\s+)?TWELFE\s+NIGHT\s+\[ACT\s+", re.I)
TN_FN_HDR = re.compile(r"\{\d+\.\s*[^\}]+\]\s*", re.I)
TN_CONTAM = re.compile(r"ACT\s+[IVXLC\d]+\s*,\s*sc\.", re.I)


def is_union_truncated(note: str, folded_ia: str) -> bool:
    return bool(
        is_clipped(note)
        or is_hard_truncation(note)
        or is_mid_sentence_cut(note)
        or is_hyphen_artifact(note)
        or is_unbalanced_parens(note)
        or is_witness_prefix(folded_ia, note)
    )


def count_union(data: dict, folded_ia: str) -> int:
    return sum(1 for item in collect_notes(data) if is_union_truncated(item["note"], folded_ia))


def note_body(note: str) -> str:
    n = note.strip()
    if n.startswith("]"):
        return n[1:].strip()
    if "]" in n:
        return n[n.index("]") + 1 :].strip()
    return n


def deinterleave_tn(text: str) -> str:
    text = TN_PLAY_BLOCK.sub(" ", text)
    text = TN_PAGE_HDR.sub(" ", text)
    text = TN_FN_HDR.sub(" ", text)
    text = re.sub(r"\s*\|\|\|\s*", " ", text)
    return _h4p2.norm_space(text)


def match_fold(s: str) -> str:
    s = fold_apostrophe(s.replace("…", "..."))
    s = re.sub(r"[,;:]+\s*", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def note_words(body: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9]+", match_fold(body))


def flex_pat(words: list[str]) -> re.Pattern[str]:
    return re.compile(
        r"(?:\s+|,\s*|\n\s*)".join(re.escape(w) for w in words),
        re.I,
    )


def find_note_pos(ia: str, note: str) -> int:
    pos = _h4p2.find_note_pos(ia, note)
    if pos >= 0:
        return pos

    body = re.sub(r"^\d{1,3}\.\s*", "", note_body(note))
    words = note_words(body)
    if len(words) < 4:
        return -1

    folded_ia = fold_apostrophe(ia)
    for n in (12, 10, 8, 6, 4):
        if len(words) < n:
            continue
        tail = words[-n:]
        tail_pat = flex_pat(tail)
        head_n = min(6, len(words))
        head_pat = flex_pat(words[:head_n])
        for m in tail_pat.finditer(folded_ia):
            window_start = max(0, m.start() - max(len(note) * 2, 400))
            hm = head_pat.search(folded_ia, window_start, m.start() + 40)
            if hm:
                return hm.start()
            if n >= 8:
                return max(0, m.start() - min(len(note), 800))
    return -1


def prefix_ok(note: str, ext: str) -> bool:
    body = re.sub(r"^\d{1,3}\.\s*", "", note_body(note))
    ext_body = note_body(ext) if "]" in ext or ext.strip().startswith("]") else ext
    body_fold = match_fold(body).lower()
    ext_fold = match_fold(ext_body).lower()
    for size in (80, 60, 40, 25):
        if len(body) < size:
            continue
        if body_fold[:size] in ext_fold:
            return True
    words = re.findall(r"[A-Za-z0-9']+", body_fold)
    if len(words) >= 4:
        return bool(flex_pat(words[:4]).search(ext_fold))
    return False


def looks_contaminated(note: str) -> bool:
    return bool(TN_CONTAM.search(note) and re.search(r"OR, WHAT YOU WILL", note, re.I))


def find_tail_end(ia: str, note: str) -> int:
    """Index in ia immediately after the note's trailing words."""
    body = re.sub(r"^\d{1,3}\.\s*", "", note_body(note))
    words = note_words(body)
    if len(words) < 4:
        return -1
    folded_ia = fold_apostrophe(ia)
    head_pat = flex_pat(words[: min(6, len(words))])
    for n in (10, 8, 6, 4):
        if len(words) < n:
            continue
        tail_pat = flex_pat(words[-n:])
        matches = list(tail_pat.finditer(folded_ia))
        if not matches:
            continue
        if len(matches) == 1:
            return matches[0].end()
        for m in matches:
            if head_pat.search(
                folded_ia, max(0, m.start() - max(len(note) * 2, 500)), m.start() + 40
            ):
                return m.end()
    return -1


def truncate_continuation(text: str, min_len: int = 8) -> str:
    text = deinterleave_tn(text)
    search = text[:4000]
    for pat in (
        r"—\s*ED\.\s*\]",
        r"—\s*Ed\.\]",
        r"\[Ed\.\]",
        r"\[ED\.\]",
        r"\.\s*—\s*Ed\.\]",
        r"true one\.\s*—\s*ED\.\s*\]",
    ):
        m = re.search(pat, search, re.I)
        if m and m.end() >= min_len:
            return _h4p2.norm_space(text[: m.end()])
    ext = _h4p2.truncate_footnote(text, min_len=min_len)
    if ends_terminal(ext.rstrip()):
        return ext
    m = re.search(r"[.!?](?:\s*—|\s*\[Ed\.\]|\s*$)", text[min_len:4000])
    if m:
        return _h4p2.norm_space(text[: min_len + m.end()])
    return ext


def extend_note(ia: str, note: str) -> str | None:
    tail_end = find_tail_end(ia, note)
    if tail_end < 0:
        return None
    rest = ia[tail_end : tail_end + 5000]
    addon = truncate_continuation(rest, min_len=8)
    if len(addon) < 8:
        return None
    combined = _h4p2.norm_space(note.rstrip() + " " + addon.lstrip())
    if len(combined) <= len(note) + 12:
        return None
    return combined


def extract_from_ia(ia: str, pos: int, json_note: str) -> str:
    chunk = ia[pos : pos + 6000]
    ext = _h4p2.truncate_footnote(deinterleave_tn(chunk))
    if json_note.strip().startswith("]"):
        if not ext.startswith("]"):
            ext = "] " + ext.lstrip()
    elif "]" in json_note:
        json_lemma = json_note[: json_note.index("]") + 1]
        em = re.match(r"^(\d{1,3}\.\s*)?[^\]]+\]\s*", ext)
        ext = json_lemma + (" " + ext[em.end() :].lstrip() if em else " " + ext)
    return _h4p2.norm_space(ext)


def repair_acceptable(ext: str, note: str, folded_ia: str) -> bool:
    if looks_contaminated(ext):
        return False
    if len(ext) <= len(note) + 12:
        return False
    if is_mid_sentence_cut(ext) or is_clipped(ext) or is_hyphen_artifact(ext):
        return False
    if is_witness_prefix(folded_ia, ext):
        return False
    if ext.strip().startswith("]") and ends_terminal(ext.rstrip()):
        return True
    if ends_terminal(ext.rstrip()) and not is_mid_sentence_cut(ext):
        return True
    return not is_hard_truncation(ext)


def try_repair_note(ia: str, note: str, folded_ia: str) -> str | None:
    ext = extend_note(ia, note)
    if ext and repair_acceptable(ext, note, folded_ia):
        return ext

    pos = find_note_pos(ia, note)
    if pos < 0:
        return None
    ext = extract_from_ia(ia, pos, note)
    if len(ext) <= len(note) + 12:
        return None
    if len(ext) > max(5000, len(note) * 6):
        return None
    if looks_contaminated(ext):
        return None
    if not prefix_ok(note, ext):
        return None
    if not repair_acceptable(ext, note, folded_ia):
        return None
    return ext


def needs_extension(note: str, folded_ia: str) -> bool:
    if is_mid_sentence_cut(note) or is_clipped(note) or is_hyphen_artifact(note):
        return True
    if is_witness_prefix(folded_ia, note):
        return True
    if note.strip().startswith("]") and ends_terminal(note.rstrip()):
        return False
    if is_hard_truncation(note):
        return True
    return False


def repair(data: dict, ia: str, folded_ia: str, *, dry_run: bool = False) -> dict:
    stats = {"truncated_before": 0, "repaired": 0, "unresolved": 0, "truncated_after": 0}

    for scene, scene_data in data.items():
        if not str(scene).startswith("ACT") or not isinstance(scene_data, dict):
            continue
        for line_data in scene_data.values():
            if not isinstance(line_data, dict):
                continue
            notes = line_data.get("notes") or []
            for i, note in enumerate(notes):
                if not is_union_truncated(note, folded_ia):
                    continue
                stats["truncated_before"] += 1
                if not needs_extension(note, folded_ia):
                    stats["unresolved"] += 1
                    continue

                ext = try_repair_note(ia, note, folded_ia)
                if ext is None:
                    stats["unresolved"] += 1
                    continue
                if not dry_run:
                    notes[i] = ext
                stats["repaired"] += 1

    stats["truncated_after"] = count_union(data, folded_ia)
    return stats


def sync_mirrors(text: str) -> None:
    if SITE_MIRROR.parent.is_dir():
        SITE_MIRROR.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    ia_id, stream = WITNESS_BY_PLAY["Twelfth Night"]
    ia, src = fetch_ia_text(ia_id, stream)
    if ia is None:
        print(f"ERROR: witness unavailable: {src}", file=sys.stderr)
        return 1

    folded_ia = fold_apostrophe(ia)
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    stats = repair(data, ia, folded_ia, dry_run=args.dry_run)
    stats.update({"play": "Twelfth Night", "ia_id": ia_id, "witness": src})

    print(
        f"{stats['truncated_before']}|{stats['repaired']}|{stats['truncated_after']}|{stats['unresolved']}"
    )

    if args.dry_run:
        return 0

    if stats["repaired"]:
        if not BACKUP.is_file():
            shutil.copy2(JSON_PATH, BACKUP)
        out = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        JSON_PATH.write_text(out, encoding="utf-8")
        sync_mirrors(out)
        print(f"Wrote {JSON_PATH.relative_to(ROOT)}")
        if SITE_MIRROR.is_file():
            print(f"Synced {SITE_MIRROR.relative_to(ROOT)}")

    audit = ROOT / "validation/twelfth_night_trunc_repair.json"
    audit.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
