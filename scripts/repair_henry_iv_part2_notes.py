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
JSON_PATH = ROOT / "Public/Data/henry_iv_part2.json"
BACKUP = JSON_PATH.with_suffix(".json.pre_repair.backup")
IA_ID = "newvariorumediti23shak"
IA_STREAM = f"{IA_ID}_djvu.txt"
IA_URL = f"https://archive.org/download/{IA_ID}/{IA_STREAM}"
CACHE = ROOT / "data/h4p2_ia_djvu.txt"

PLAY_BLOCK = re.compile(
    r"ACT\s+[IVXLC\d]+\s*,\s*sc\.?\s*\d+\.?\]?\s*(?:HENRY\s+THE\s+FOURTH)?\s*\d*\s*",
    re.I,
)
PAGE_HDR = re.compile(r"HENRY\s+THE\s+FOURTH\s+\d{1,3}\s+", re.I)
RESUME = re.compile(
    r"(it must be|nausea|[a-z]{4,}[\u2018\u2019',])|(?:\u2014|—)\s*\[|(?:\u2014|—)\s*$",
    re.I,
)


def fold_apostrophe(s: str) -> str:
    return s.replace("\u2019", "'").replace("\u2018", "'")


def norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


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


def flex_pattern(text: str, max_words: int = 14) -> re.Pattern[str] | None:
    words = re.findall(r"[A-Za-z0-9\u2019']+", fold_apostrophe(text))
    if len(words) < 4:
        return None
    words = words[:max_words]
    return re.compile(r"\s+".join(re.escape(w) for w in words), re.I)


def deinterleave(text: str) -> str:
    text = PLAY_BLOCK.sub(" ||| ", text)
    text = PAGE_HDR.sub(" ||| ", text)
    parts = [p.strip() for p in text.split("|||") if p.strip()]
    if not parts:
        return norm_space(text)
    out = parts[0]
    for part in parts[1:]:
        if len(re.findall(r"\b[A-Z][a-z]+\b", part)) > 8 and len(part) > 120:
            m = RESUME.search(part)
            if m:
                out += " " + part[m.start() :]
        else:
            out += " " + part
    return norm_space(out)


def truncate_footnote(text: str, min_len: int = 40) -> str:
    if len(text) <= min_len:
        return text.strip()
    for pat in (
        r"—\s*Ed\.\]",
        r"—\s*\[Ed\.\]",
        r"\[Ed\.\]\s*$",
        r"\.\s*—\s*Ed\.\]",
    ):
        m = re.search(pat, text)
        if m and m.end() > min_len:
            return text[: m.end()].strip()
    for m in re.finditer(r"—\s*$", text):
        if min_len < m.end() < 2800:
            return text[: m.end()].strip()
    for m in re.finditer(r"\.\s*—\s*(?=[A-Z\[\"'\u2018(]|$)", text):
        if min_len < m.end() < 2800:
            return text[: m.end()].strip()
    m = re.search(r"\s(\d{1,3})\.\s+(?:[A-Za-z(\[]|\w+\]|\w+\.)", text[min_len:])
    if m:
        return text[: min_len + m.start()].strip()
    if len(text) > 2800:
        cut = text[:2800]
        m = re.search(r"[.!?]\s*—?\s*$", cut)
        if m:
            return cut[: m.end()].strip()
    return text.strip()


def find_note_pos(ia: str, note: str) -> int:
    body = note[note.index("]") + 1 :].strip() if "]" in note else note.strip()
    folded_ia = fold_apostrophe(ia)
    for size in (100, 80, 60, 45, 30):
        if len(body) < size:
            continue
        pat = flex_pattern(body[:size])
        if pat:
            m = pat.search(folded_ia)
            if m:
                return m.start()
    after_critic = re.search(r":\s*(.+)", body)
    if after_critic:
        pat = flex_pattern(after_critic.group(1)[:70])
        if pat:
            m = pat.search(folded_ia)
            if m:
                return m.start()
    words = re.findall(r"[A-Za-z0-9\u2019']+", fold_apostrophe(body))
    for n in (10, 8, 6):
        if len(words) >= n:
            pat = flex_pattern(" ".join(words[:n]), n)
            if pat:
                m = pat.search(folded_ia)
                if m:
                    return m.start()
    return -1


def extract_from_ia(ia: str, pos: int, json_note: str) -> str:
    start = max(0, pos - 120)
    chunk = ia[start : start + 6000]
    m = re.search(r"(\d{1,3}\.\s*)?[\w .'-]+\]\s*[A-Z(]", chunk, re.I)
    if m and m.start() <= (pos - start) + 10:
        chunk = chunk[m.start() :]
    ext = truncate_footnote(deinterleave(chunk))
    if "]" in json_note:
        json_lemma = json_note[: json_note.index("]") + 1]
        em = re.match(r"^(\d{1,3}\.\s*)?[^\]]+\]\s*", ext)
        ext = json_lemma + (" " + ext[em.end() :].lstrip() if em else " " + ext)
    return norm_space(ext)


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
