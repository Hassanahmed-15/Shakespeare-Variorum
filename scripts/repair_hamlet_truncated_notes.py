#!/usr/bin/env python3
"""Repair truncated Hamlet NV notes via IA witness (editi11)."""

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
    collect_notes,
    is_hard_truncation,
    is_hyphen_artifact,
    is_mid_sentence_cut,
    is_unbalanced_parens,
    is_witness_prefix,
)
from nv_ia_witness import fetch_ia_text, fold_apostrophe  # noqa: E402
from nv_witness_map import WITNESS_BY_PLAY  # noqa: E402

JSON_PATH = ROOT / "Public/Data/hamlet_notes (1).json"
BACKUP = JSON_PATH.with_suffix(".json.pre_trunc_repair.backup")
IA_ID, IA_STREAM = WITNESS_BY_PLAY["Hamlet"]

_H4P2 = importlib.util.spec_from_file_location(
    "h4p2_repair", ROOT / "scripts/repair_henry_iv_part2_notes.py"
)
_h4p2 = importlib.util.module_from_spec(_H4P2)
_H4P2.loader.exec_module(_h4p2)

HAMLET_PAGE = re.compile(r"\bHAMLET\s+[A-Z]?\d{1,4}\b", re.I)
PLAY_SPEAKER = re.compile(
    r"\b(Ham|Hor|Queen|King|Oph|Pol|Laer|Mar|Ros|Guil|Cor|Osr|Fort)\.\s",
    re.I,
)
NEXT_FN = re.compile(r"\n\s*\d{1,3}\.\s+[\w .'\u2019-]+\]\s*[A-Z(]", re.I)


def word_pat(words: list[str]) -> re.Pattern[str] | None:
    if len(words) < 3:
        return None
    return re.compile(r"\s+".join(re.escape(w) for w in words), re.I)


def find_note_pos_hamlet(ia: str, note: str) -> int:
    pos = _h4p2.find_note_pos(ia, note)
    if pos >= 0:
        return pos

    folded = fold_apostrophe(ia)
    body = note[note.index("]") + 1 :].strip() if "]" in note else note.strip()
    words = re.findall(r"[A-Za-z0-9\u2019']+", fold_apostrophe(body))

    if "]" in note:
        lemma = note[: note.index("]") + 1]
        lw = re.findall(r"[A-Za-z0-9\u2019']+", fold_apostrophe(lemma))
        for n in (10, 8, 6, 4):
            if len(lw) + len(words) >= n + 2:
                pat = word_pat(lw + words[: max(2, n - len(lw))])
                if pat and (m := pat.search(folded)):
                    return m.start()
        for n in (6, 4, 2):
            if len(lw) >= n and (pat := word_pat(lw[:n])) and (m := pat.search(folded)):
                return m.start()

    if len(words) < 4:
        return -1

    for n in (14, 10, 8, 6):
        if len(words) >= n and (pat := word_pat(words[:n])) and (m := pat.search(folded)):
            return m.start()

    if "]" in note:
        lemma = fold_apostrophe(note[: note.index("]") + 1]).lower()
        for n in (12, 10, 8, 6):
            if len(words) >= n and (pat := word_pat(words[-n:])):
                for m in pat.finditer(folded):
                    window = folded[max(0, m.start() - 220) : m.start() + 20].lower()
                    if lemma.replace(" ", "")[:14] in window.replace(" ", ""):
                        return m.start()
    return -1


def cut_footnote_chunk(chunk: str, min_keep: int) -> str:
    cut = len(chunk)
    for pat in (HAMLET_PAGE, PLAY_SPEAKER, re.compile(r"\bEnter\s+[A-Z]", re.I)):
        m = pat.search(chunk, min_keep)
        if m:
            cut = min(cut, m.start())
    m = NEXT_FN.search(chunk, min_keep)
    if m:
        cut = min(cut, m.start())
    return chunk[:cut]


def append_suffix_from_ia(ia: str, note: str) -> str | None:
    if "]" not in note:
        return None
    body = note[note.index("]") + 1 :].strip()
    words = re.findall(r"[A-Za-z0-9\u2019']+", fold_apostrophe(body))
    if len(words) < 4:
        return None
    folded = fold_apostrophe(ia)
    for n in (10, 8, 6, 4):
        pat = word_pat(words[-n:])
        if not pat:
            continue
        m = pat.search(folded)
        if not m:
            continue
        tail = cut_footnote_chunk(ia[m.end() : m.end() + 600], 0)
        tail = _h4p2.norm_space(fold_apostrophe(tail))
        if not tail or len(tail) < 2:
            return None
        joiner = "" if note.endswith(("-", "—")) or tail.startswith((".", ",", ";", ":", ")", "]")) else " "
        merged = _h4p2.norm_space(note + joiner + tail)
        if len(merged) > len(note) + 3:
            return merged
    return None


def acceptable_repair(ext: str) -> bool:
    if looks_hamlet_contaminated(ext):
        return False
    if HAMLET_PAGE.search(ext):
        return False
    if re.search(r"\b\d{1,3}\s+\d{1,3}\s+\d{1,3}\b", ext):
        return False
    if re.search(r"\b(List,\s*list|Where is he gone|Enter [A-Z]|To be or not)\b", ext, re.I):
        return False
    if re.search(r"HAMLET\s*\[|\bAdieu,\s*adieu", ext, re.I):
        return False
    tail = ext.rstrip()
    if not re.search(r"[\.\!\?\]\u2014—\"']\s*$", tail):
        return False
    return True


def looks_hamlet_contaminated(note: str) -> bool:
    if _h4p2.looks_contaminated(note):
        return True
    body = note.split("]", 1)[-1] if "]" in note else note
    if PLAY_SPEAKER.search(body):
        return True
    if re.search(r"\bEnter\s+[A-Z]", body):
        return True
    if re.search(r"\bact\s+[ivxlc\d]+\s*,\s*sc\.", body, re.I) and HAMLET_PAGE.search(body):
        return True
    return False


def extract_from_ia_hamlet(ia: str, pos: int, json_note: str) -> str:
    start = max(0, pos - 60)
    chunk = ia[start : start + 4000]
    rel = pos - start
    lm = re.search(
        r"(\d{1,3}\.\s*)?[\w .'\u2019-]+\]\s*[A-Z(]",
        chunk[max(0, rel - 30) :],
        re.I,
    )
    if lm:
        chunk = chunk[max(0, rel - 30) + lm.start() :]

    chunk = cut_footnote_chunk(chunk, max(30, len(json_note) // 3))
    ext = _h4p2.norm_space(fold_apostrophe(chunk))
    ext = _h4p2.truncate_footnote(ext)

    if "]" in json_note:
        json_lemma = json_note[: json_note.index("]") + 1]
        em = re.match(r"^(\d{1,3}\.\s*)?[^\]]+\]\s*", ext)
        ext = json_lemma + (" " + ext[em.end() :].lstrip() if em else " " + ext)

    note_fold = _h4p2.norm_space(fold_apostrophe(json_note))
    ext_fold = _h4p2.norm_space(fold_apostrophe(ext))
    if not ext_fold.lower().startswith(note_fold[: min(50, len(note_fold))].lower()):
        return json_note
    return _h4p2.norm_space(ext)


def truncation_signals(note: str, folded_ia: str) -> list[str]:
    s: list[str] = []
    if is_clipped(note):
        s.append("is_clipped")
    if is_hard_truncation(note):
        s.append("hard_truncation")
    if is_mid_sentence_cut(note):
        s.append("mid_sentence_cut")
    if is_hyphen_artifact(note):
        s.append("hyphen_artifact")
    if is_unbalanced_parens(note):
        s.append("unbalanced_parens")
    if is_witness_prefix(folded_ia, note):
        s.append("witness_prefix")
    return s


def is_truncated(note: str, folded_ia: str) -> bool:
    return bool(truncation_signals(note, folded_ia))


def count_truncated(data: dict, folded_ia: str) -> int:
    return sum(1 for item in collect_notes(data) if is_truncated(item["note"], folded_ia))


def repair(data: dict, ia: str, *, dry_run: bool = False) -> dict:
    folded_ia = fold_apostrophe(ia)
    stats = {
        "truncated_before": count_truncated(data, folded_ia),
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
                pos = find_note_pos_hamlet(ia, note)
                ext = None
                if pos >= 0:
                    ext = extract_from_ia_hamlet(ia, pos, note)
                if ext is None or ext == note:
                    ext = append_suffix_from_ia(ia, note)
                if ext is None or ext == note:
                    stats["unresolved"] += 1
                    continue
                if len(ext) > max(4000, len(note) * 6):
                    stats["unresolved"] += 1
                    continue
                if looks_hamlet_contaminated(ext) or not acceptable_repair(ext):
                    stats["unresolved"] += 1
                    continue
                if len(ext) > len(note) + 5 and not is_truncated(ext, folded_ia):
                    if not dry_run:
                        notes[i] = ext
                    stats["repaired"] += 1
                    if len(stats["examples"]) < 8:
                        stats["examples"].append(
                            {
                                "before_len": len(note),
                                "after_len": len(ext),
                                "tail": ext[-120:],
                            }
                        )
                else:
                    stats["unresolved"] += 1

    stats["truncated_after"] = (
        count_truncated(data, folded_ia)
        if not dry_run
        else stats["truncated_before"] - stats["repaired"]
    )
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    ia, src = fetch_ia_text(IA_ID, IA_STREAM)
    if ia is None:
        print(f"ERROR: witness unavailable ({src})", file=sys.stderr)
        return 1

    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    stats = repair(data, ia, dry_run=args.dry_run)
    stats.update({"play": "Hamlet", "ia_id": IA_ID, "witness": src})

    print(f"IA witness: {IA_ID} ({len(ia):,} chars)")
    print(
        f"{stats['truncated_before']}|{stats['repaired']}|"
        f"{stats['truncated_after']}|{stats['unresolved']}"
    )
    for ex in stats["examples"]:
        print(f"  + {ex['before_len']} -> {ex['after_len']} …{ex['tail']}")

    if args.dry_run:
        return 0

    if stats["repaired"]:
        if not BACKUP.is_file():
            shutil.copy2(JSON_PATH, BACKUP)
            print(f"Backup → {BACKUP.relative_to(ROOT)}")
        JSON_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"Wrote {JSON_PATH.relative_to(ROOT)}")

    out = ROOT / "validation" / "hamlet_trunc_repair.json"
    out.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
