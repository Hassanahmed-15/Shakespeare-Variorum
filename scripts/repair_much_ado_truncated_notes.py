#!/usr/bin/env python3
"""Repair truncated Much Ado About Nothing NV notes from IA vol. XII witness."""

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
from nv_ia_witness import fetch_ia_text, fold_apostrophe  # noqa: E402
from nv_witness_map import WITNESS_BY_PLAY  # noqa: E402

JSON_PATH = ROOT / "Public/Data/much_ado_about_nothing.json"
BACKUP = JSON_PATH.with_suffix(".json.pre_clip_repair.backup")
SITE_MIRROR = ROOT / "My Website/Public/Data/much_ado_about_nothing.json"
PLAY = "Much Ado About Nothing"

_H4P2 = importlib.util.spec_from_file_location(
    "h4p2_repair", ROOT / "scripts/repair_henry_iv_part2_notes.py"
)
_h4p2 = importlib.util.module_from_spec(_H4P2)
_H4P2.loader.exec_module(_h4p2)

PLAY_BLOCK = re.compile(
    r"ACT\s+[IVXLC\d]+\s*,?\s*SC\.?\s*[IVXLC\d]*\.?\]?\s*",
    re.I,
)
MUCH_ADO_HDR = re.compile(r"MUCH\s+AD(?:O|OE)\s+ABOUT\s+NOTHING", re.I)
SCENE_HDR = re.compile(r"\[act\s+[IVXLC\d]+,\s*sc\.\s*[ivxlc\d]+\.", re.I)
NOTE_LEMMA = re.compile(r"^\[[^\]]+\]\s*$", re.I)
PAGE_NUM = re.compile(r"^\s*\d{1,3}\s*$")
PLAY_SPEAKER = re.compile(r"^[A-Za-z]{2,5}[,.]\s+[A-Z\u017f]", re.M)
RESUME = re.compile(
    r"(?:^|\s)(?:to|of|the|and|ence|with|that|which|many|"
    r"[a-z]{4,}[\u2018\u2019',])|(?:\u2014|—)\s*\[|(?:\u2014|—)\s*$",
    re.I,
)


def norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def is_truncated(note: str) -> bool:
    return (
        is_clipped(note)
        or is_hard_truncation(note)
        or is_mid_sentence_cut(note)
        or is_hyphen_artifact(note)
        or is_unbalanced_parens(note)
    )


def deinterleave_much_ado(text: str) -> str:
    text = PLAY_BLOCK.sub(" ||| ", text)
    text = MUCH_ADO_HDR.sub(" ||| ", text)
    text = SCENE_HDR.sub(" ||| ", text)
    text = re.sub(r"\[[iIvV]\.\s+[^\]]+\]\s*", " ||| ", text)
    parts = [p.strip() for p in text.split("|||") if p.strip()]
    if not parts:
        return norm_space(text)
    out = parts[0]
    for part in parts[1:]:
        lines = [ln.strip() for ln in part.splitlines() if ln.strip()]
        if not lines:
            continue
        if all(PAGE_NUM.match(ln) for ln in lines):
            continue
        if NOTE_LEMMA.match(part.strip()):
            continue
        if len(part) < 100 and PLAY_SPEAKER.search(part):
            continue
        if len(re.findall(r"\b[A-Z][a-z]+\b", part)) > 10 and len(part) > 150:
            m = RESUME.search(part)
            if m:
                out += " " + part[m.start() :]
                continue
        if part[0].islower() or part.lstrip().startswith(
            ("to ", "of ", "the ", "and ", "ence ", "with ", "that ", "which ")
        ):
            out += " " + part
        elif re.search(r"[A-Za-z .'-]+:\s", part) or "—" in part or "Ed." in part:
            out += " " + part
    return norm_space(out)


def strip_lemma_prefix(lemma: str) -> str:
    s = re.sub(r"^\d{1,3}\.\s*", "", lemma.strip())
    s = re.sub(r"^[IVXLCivxlc]+\.\s*", "", s)
    return s.lstrip("'\"")


def strip_body_prefix(body: str) -> str:
    return re.sub(r"^\d{1,3}\.\s*", "", body.strip())


def note_words(text: str) -> list[str]:
    return [
        w.strip("'\"")
        for w in re.findall(r"[A-Za-z0-9\u2019']+", fold_apostrophe(text))
        if w.strip("'\"")
    ]


def loose_pattern(text: str, max_words: int = 14) -> re.Pattern[str] | None:
    words = note_words(text)
    if len(words) < 4:
        return None
    words = words[:max_words]
    return re.compile(r"\W*".join(re.escape(w) for w in words), re.I)


def candidate_positions(ia: str, note: str) -> list[int]:
    folded_ia = fold_apostrophe(ia)
    positions: set[int] = set()

    def add_from_pattern(text: str, *, max_words: int = 14) -> None:
        for maker in (_h4p2.flex_pattern, loose_pattern):
            pat = maker(text, max_words)
            if not pat:
                continue
            for m in pat.finditer(folded_ia):
                positions.add(m.start())

    if "]" in note:
        lemma = note[: note.index("]") + 1]
        inner = strip_lemma_prefix(lemma).rstrip("]").rstrip(":")
        variants = [lemma, strip_lemma_prefix(lemma)]
        if inner:
            variants.extend(
                [
                    f"{inner}]",
                    f"I. {inner}]",
                    f"[{inner.lower()}]",
                    f"{inner}:]",
                ]
            )
        for variant in variants:
            for prefix in ("", "75. ", "50. ", "44. ", "33. ", "309-314. ", "22, 23. "):
                add_from_pattern((prefix + variant).replace("]", " ]"))

    body = strip_body_prefix(note[note.index("]") + 1 :].strip() if "]" in note else note.strip())
    if note.rstrip().endswith("-"):
        add_from_pattern(body.rstrip("- ").strip(), max_words=12)

    critic = re.match(r"^([A-Za-z .'.-]+)\s*(\([^)]+\))\s*:\s*(.{15,120})", body)
    if critic:
        name, cite, rest = critic.groups()
        cite_words = re.findall(r"[A-Za-z0-9]+", cite)
        for chunk in (
            f"{name} {' '.join(cite_words)}",
            f"{name} {' '.join(cite_words)} {rest[:50]}",
            rest[:70],
            rest[:45],
        ):
            add_from_pattern(chunk)

    words = note_words(body)
    for size in (14, 12, 10, 8, 6):
        if len(words) >= size:
            add_from_pattern(" ".join(words[:size]), max_words=size)
    if len(note) > 800:
        for size in (12, 10, 8, 6):
            if len(words) >= size:
                add_from_pattern(" ".join(words[-size:]), max_words=size)

    pos = _h4p2.find_note_pos(ia, note)
    if pos >= 0:
        positions.add(pos)
    return sorted(positions)


def pick_best_position(ia: str, note: str, positions: list[int]) -> int:
    if not positions:
        return -1
    best_pos = -1
    best_score = -1.0
    for pos in positions:
        ext = extract_from_ia_much_ado(ia, pos, note)
        if not ext or not shares_anchor(note, ext) or not shares_tail(note, ext):
            continue
        score = len(ext)
        if len(ext) > len(note) + 8 and is_fixed(ext):
            score += 5000
        elif is_fixed(ext):
            score += 1000
        if score > best_score:
            best_score = score
            best_pos = pos
    return best_pos


def find_note_pos_much_ado(ia: str, note: str) -> int:
    positions = candidate_positions(ia, note)
    return pick_best_position(ia, note, positions)


def shares_tail(note: str, ext: str, min_words: int = 5) -> bool:
    from audit_nv_truncation import ends_terminal

    if ends_terminal(note.strip()):
        return True
    tail_words = note_words(note)[-min_words:]
    if len(tail_words) < 3:
        return True
    pat = loose_pattern(" ".join(tail_words), min_words)
    return bool(pat and pat.search(fold_apostrophe(ext)))


def extend_after_tail(note: str, text: str) -> str:
    from audit_nv_truncation import ends_terminal

    if ends_terminal(note.strip()):
        return text
    tail_words = note_words(note)[-8:]
    if len(tail_words) < 4:
        return text
    folded = fold_apostrophe(text)
    pat = loose_pattern(" ".join(tail_words), len(tail_words))
    if not pat:
        return text
    m = pat.search(folded)
    if not m:
        return text
    rest = deinterleave_much_ado(text[m.end() : m.end() + 1200])
    end = len(rest)
    for pat_end in (
        r"\.\s*—\s*Ed\.\]",
        r"\.\s*$",
        r"—\s*Ed\.\]",
    ):
        em = re.search(pat_end, rest)
        if em and em.end() > 20:
            end = min(end, em.end())
            break
    return norm_space(text[: m.end()] + rest[:end])


def truncate_footnote_much_ado(text: str, json_note: str, min_len: int = 40) -> str:
    text = deinterleave_much_ado(text)
    if len(json_note) < 220:
        for pat in (
            r"\s—\s+HARTLEY\s+COLERIDGE",
            r"\s—\s+[A-Z][A-Za-z .'-]{4,}\s*\(",
            r"\.\s—\s+[A-Z][A-Za-z .'-]{4,}\s*\(",
        ):
            m = re.search(pat, text[min_len:], re.I)
            if m:
                text = text[: min_len + m.start()].strip()
                break

    cap = min(len(text), max(12000, len(json_note) + 2500))
    chunk = text[:cap]
    last_ed = None
    for m in re.finditer(
        r"(?:Aut Christopher North.*?—\s*Ed\.\])|(?:—\s*Ed\.\])",
        chunk,
        re.I | re.S,
    ):
        if m.end() > min_len:
            last_ed = m
    if last_ed:
        text = chunk[: last_ed.end()].strip()
    else:
        text = _h4p2.truncate_footnote(text)
    return extend_after_tail(json_note, text)


def shares_anchor(note: str, ext: str, min_words: int = 6) -> bool:
    body = strip_body_prefix(note[note.index("]") + 1 :].strip() if "]" in note else note.strip())
    note_words_list = note_words(body)[:min_words]
    if len(note_words_list) < 4:
        return True
    pat = loose_pattern(" ".join(note_words_list), min_words)
    return bool(pat and pat.search(fold_apostrophe(ext)))


def extract_from_ia_much_ado(ia: str, pos: int, json_note: str) -> str:
    start = max(0, pos - 120)
    span = max(8000, len(json_note) + 4000)
    chunk = ia[start : start + span]
    m = re.search(r"(\d{1,3}\.\s*)?[\w .'\"-]+\]\s*[A-Z(]", chunk, re.I)
    if m and m.start() <= (pos - start) + 40:
        chunk = chunk[m.start() :]
    ext = truncate_footnote_much_ado(chunk, json_note)
    if "]" in json_note:
        json_lemma = json_note[: json_note.index("]") + 1]
        em = re.match(r"^(\d{1,3}\.\s*)?[^\]]+\]\s*", ext)
        ext = json_lemma + (" " + ext[em.end() :].lstrip() if em else " " + ext)
    return norm_space(ext)


def is_fixed(note: str) -> bool:
    return not is_truncated(note)


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
                pos = find_note_pos_much_ado(ia, note)
                if pos < 0:
                    stats["unresolved"] += 1
                    continue
                ext = extract_from_ia_much_ado(ia, pos, note)
                if len(ext) > max(12000, len(note) * 12):
                    stats["unresolved"] += 1
                    continue
                if not shares_anchor(note, ext) or not shares_tail(note, ext):
                    stats["unresolved"] += 1
                    continue
                if _h4p2.looks_contaminated(ext):
                    stats["unresolved"] += 1
                    continue
                improved = len(ext) > len(note) + 8 and is_fixed(ext)
                if not improved and len(ext) > len(note) + 8:
                    improved = not is_hard_truncation(ext) and not is_mid_sentence_cut(ext)
                if improved:
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

    audit = ROOT / "validation/nv_much_ado_repair.json"
    audit.write_text(
        json.dumps({"play": PLAY, "ia_id": ia_id, "witness": src, **stats}, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
