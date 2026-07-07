#!/usr/bin/env python3
"""Verify every note in a given play's JSON against its correct witness text,
using fuzzy matching tolerant of OCR noise (garbled individual words) but not
tolerant of genuinely absent/fabricated content.

Fast approach: pre-split the witness into overlapping word-boundary chunks
once, then for each note's tail use rapidfuzz.process.extractOne (C-optimized)
to find the best-matching chunk. Notes scoring below a threshold are flagged
for manual review, with the best-matching witness context printed.

Usage: python3 scripts/verify_all_notes.py "<Play Name>" [tail_len] [threshold]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from rapidfuzz import fuzz, process

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_nv_fidelity_all_plays import PLAYS  # noqa: E402
from nv_ia_witness import fetch_ia_text, fold_apostrophe  # noqa: E402
from nv_witness_map import (  # noqa: E402
    WITNESS_BY_PLAY,
    WITNESS_AUDIT_FALLBACK,
    LOCAL_WITNESS_BY_PLAY,
)

TAIL_LEN_DEFAULT = 90
THRESHOLD_DEFAULT = 75
CHUNK_WORDS = 30
CHUNK_STRIDE_WORDS = 10


def norm(s: str) -> str:
    s = re.sub(r"\s+", " ", s)
    s = fold_apostrophe(s)
    s = s.replace("ſ", "f")
    s = s.replace("œ", "oe").replace("æ", "ae")
    s = s.replace("—", "-").replace("–", "-")
    s = s.replace(""", '"').replace(""", '"')
    s = re.sub(r"[^a-z0-9 ]", "", s.lower())
    s = re.sub(r"\s+", " ", s).strip()
    return s


def get_witness(play: str) -> tuple[str | None, str]:
    if play in LOCAL_WITNESS_BY_PLAY:
        lp = LOCAL_WITNESS_BY_PLAY[play]
        if lp.is_file():
            return lp.read_text(encoding="utf-8"), str(lp)
    wit = WITNESS_BY_PLAY.get(play)
    if wit:
        ia_id, ia_stream = wit
        text, src = fetch_ia_text(ia_id, ia_stream)
        if text is not None:
            return text, src
        fb = WITNESS_AUDIT_FALLBACK.get(play)
        if fb:
            text, src = fetch_ia_text(*fb)
            if text is not None:
                return text, src
    return None, "unavailable"


def collect_notes(data: dict) -> list[dict]:
    items = []
    for scene, scene_data in data.items():
        if str(scene).startswith("_") or not isinstance(scene_data, dict):
            continue
        for line_num, obj in scene_data.items():
            if not isinstance(obj, dict):
                continue
            for note_idx, note in enumerate(obj.get("notes") or []):
                if not isinstance(note, str) or not note.strip():
                    continue
                items.append(
                    {
                        "scene": scene,
                        "line": str(line_num),
                        "note_idx": note_idx,
                        "note": note,
                    }
                )
    return items


def build_chunks(witness_norm: str, chunk_words: int, stride_words: int) -> list[tuple[str, int]]:
    """Split into overlapping word-based chunks; return (chunk_text, char_offset) pairs."""
    words = witness_norm.split(" ")
    chunks: list[tuple[str, int]] = []
    # precompute cumulative char offsets for each word start
    offsets = [0]
    for w in words:
        offsets.append(offsets[-1] + len(w) + 1)
    i = 0
    n = len(words)
    while i < n:
        j = min(i + chunk_words, n)
        chunk = " ".join(words[i:j])
        chunks.append((chunk, offsets[i]))
        if j == n:
            break
        i += stride_words
    return chunks


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: verify_all_notes.py '<Play Name>' [tail_len] [threshold]", file=sys.stderr)
        sys.exit(1)
    play = sys.argv[1]
    tail_len = int(sys.argv[2]) if len(sys.argv) > 2 else TAIL_LEN_DEFAULT
    threshold = float(sys.argv[3]) if len(sys.argv) > 3 else THRESHOLD_DEFAULT

    spec = next((p for p in PLAYS if p["play"] == play), None)
    if spec is None:
        print(f"Unknown play: {play}", file=sys.stderr)
        sys.exit(1)

    jf = spec.get("json_file") or spec.get("json")
    path_obj = ROOT / jf
    data = json.loads(path_obj.read_text(encoding="utf-8"))
    notes = collect_notes(data)

    witness_text, witness_src = get_witness(play)
    if witness_text is None:
        print(f"WITNESS UNAVAILABLE for {play}")
        sys.exit(2)

    witness_norm = norm(witness_text)
    chunks = build_chunks(witness_norm, CHUNK_WORDS, CHUNK_STRIDE_WORDS)
    chunk_texts = [c[0] for c in chunks]

    total = len(notes)
    ok = 0
    fail = 0
    fails = []

    for item in notes:
        note = item["note"]
        stripped = note.rstrip()
        if stripped.endswith("...") and len(stripped) < 10:
            ok += 1
            continue
        tail_chars = stripped[-tail_len:]
        needle = norm(tail_chars)
        if len(needle) < 20:
            ok += 1
            continue
        result = process.extractOne(needle, chunk_texts, scorer=fuzz.partial_ratio)
        if result is None:
            fail += 1
            fails.append((item, tail_chars, 0.0, -1))
            continue
        _, score, idx = result
        if score < threshold:
            fail += 1
            fails.append((item, tail_chars, score, chunks[idx][1]))
        else:
            ok += 1

    print(f"=== {play} — witness: {witness_src}")
    print(f"Total notes: {total}  OK: {ok}  FAIL: {fail}")
    for item, tail, score, pos in fails:
        ref = f"{item['scene']} | line {item['line']} | note {item['note_idx']}"
        print(f"  FAIL {ref} (score={score:.0f})")
        print(f"    tail: {tail!r}")
        if pos != -1:
            print(f"    best witness match near pos {pos}: {witness_norm[max(0,pos-30):pos+len(tail)+60]!r}")


if __name__ == "__main__":
    main()
