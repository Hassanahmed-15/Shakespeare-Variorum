#!/usr/bin/env python3
"""Rebuild Othello notes JSON: MIT/Moby play text + Variorum notes (from Folger-aligned source).

Maps notes from othello_notes_folger.json onto Public/Data/otello.json spine
via per-scene text similarity (same align_scene logic as Folger pipeline).

Usage:
  python3 scripts/rebuild_othello_mit.py
  python3 scripts/rebuild_othello_mit.py --out Public/Data/othello_notes.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.folger_tei.align_nv_to_folger import (  # noqa: E402
    _ratio_score,
    align_scene,
    normalize_for_match,
)

MIT_SPINE = ROOT / "Public/Data/othello.json"
NOTES_SRC = ROOT / "Public/Data/othello_notes_folger.json"
DEFAULT_OUT = ROOT / "Public/Data/othello_notes.json"
REVIEW_OUT = ROOT / "validation/othello_mit_alignment_review.json"


def mit_scene_to_folger(scene_key: str) -> str:
    m = re.match(r"ACT\s+(\d+)\s+SCENE\s+(\d+)", scene_key.strip(), re.I)
    if m:
        return f"ACT {int(m.group(1))}, SCENE {int(m.group(2))}"
    return scene_key


def is_stage_direction(play: str) -> bool:
    t = (play or "").strip()
    return t.startswith("[") and t.endswith("]")


def build_mit_units(mit_scene: dict[str, Any]) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []

    def sort_key(k: str) -> tuple:
        if k.isdigit():
            return (0, int(k))
        return (1, k)

    for line_key in sorted(mit_scene.keys(), key=sort_key):
        if str(line_key).startswith("_"):
            continue
        obj = mit_scene[line_key]
        if isinstance(obj, str):
            play = obj
        elif isinstance(obj, dict):
            play = obj.get("play") or obj.get("text") or ""
        else:
            continue
        units.append(
            {
                "play": play,
                "anchor": str(line_key),
                "kind": "sd" if is_stage_direction(play) else "speech",
            }
        )
    return units


def extract_folger_nv_lines(folger_scene: dict[str, Any]) -> list[tuple[str, str, list[Any]]]:
    lines: list[tuple[str, str, list[Any]]] = []
    for key in folger_scene:
        if str(key).startswith("_"):
            continue
        obj = folger_scene[key]
        if not isinstance(obj, dict):
            continue
        play = obj.get("play") or ""
        notes = list(obj.get("notes") or [])
        if play or notes:
            lines.append((str(key), play, notes))
    return lines


def extract_note_quote(note: str) -> str | None:
    """Pull a play-text phrase from common Variorum note citation patterns."""
    text = (note or "").strip()
    if not text:
        return None
    # Editor: 'Thou told'st me' — comment (apostrophes inside quotes are common)
    m = re.search(r":\s*'(.+?)'\s*(?:—|-)", text)
    if m:
        cand = m.group(1).strip(" .,;:")
        if len(cand) >= 6:
            return cand
    m = re.search(r"'(.+?)'\s*(?:—|-)", text)
    if m:
        cand = m.group(1).strip(" .,;:")
        if len(cand) >= 6 and not cand.lower().startswith(("editor", "textual")):
            return cand
    m = re.search(r"\b([A-Za-z][A-Za-z .'\-]{5,80})\]", text)
    if m:
        cand = m.group(1).strip(" .,;:")
        if len(cand) >= 6:
            return cand
    return None


def quote_in_play(quote: str, play: str) -> bool:
    qn = normalize_for_match(quote)
    pn = normalize_for_match(play)
    if not qn or not pn:
        return False
    if qn in pn:
        return True
    return _ratio_score(qn, pn) >= 0.72


def best_mit_line_for_quote(
    quote: str,
    mit_units: list[dict[str, Any]],
    *,
    current_key: str | None = None,
) -> tuple[str | None, float]:
    qn = normalize_for_match(quote)
    if not qn:
        return current_key, 0.0
    q_tokens = {t for t in qn.split() if len(t) > 2}
    best_key: str | None = current_key
    best_score = 0.0
    for unit in mit_units:
        play = unit.get("play") or ""
        pn = normalize_for_match(play)
        if not pn:
            continue
        score = _ratio_score(qn, pn)
        if qn in pn:
            score = max(score, 0.95)
        p_tokens = {t for t in pn.split() if len(t) > 2}
        if q_tokens and p_tokens:
            overlap = len(q_tokens & p_tokens) / len(q_tokens)
            if overlap >= 0.5:
                score = max(score, 0.5 + overlap * 0.4)
        if score > best_score:
            best_score = score
            best_key = unit["anchor"]
    return best_key, best_score


def reanchor_notes_by_quote(
    scene_obj: dict[str, Any],
    mit_units: list[dict[str, Any]],
    *,
    min_score: float = 0.48,
) -> int:
    """Move notes onto MIT lines whose play text contains the note's quoted phrase."""
    moved = 0
    pending: list[tuple[str, str, str]] = []
    for line_key, ent in scene_obj.items():
        play = ent.get("play") or ""
        kept: list[Any] = []
        for note in ent.get("notes") or []:
            quote = extract_note_quote(str(note))
            if not quote or quote_in_play(quote, play):
                kept.append(note)
                continue
            target, score = best_mit_line_for_quote(quote, mit_units, current_key=line_key)
            if target and target != line_key and score >= min_score:
                pending.append((target, line_key, note))
                moved += 1
            else:
                kept.append(note)
        ent["notes"] = kept

    for target, _source, note in pending:
        scene_obj.setdefault(target, {"play": "", "notes": []})
        scene_obj[target].setdefault("notes", []).append(note)
    return moved


def rebuild(
    mit_path: Path = MIT_SPINE,
    notes_src: Path = NOTES_SRC,
    out_path: Path = DEFAULT_OUT,
    review_path: Path = REVIEW_OUT,
) -> dict[str, Any]:
    mit = json.loads(mit_path.read_text(encoding="utf-8"))
    folger = json.loads(notes_src.read_text(encoding="utf-8"))

    out: dict[str, Any] = {}
    if "DRAMATIS PERSONAE" in folger:
        out["DRAMATIS PERSONAE"] = folger["DRAMATIS PERSONAE"]

    all_review: list[dict[str, Any]] = []
    total_notes_in = 0
    total_notes_out = 0
    scenes_built = 0
    quote_reanchored = 0

    mit_scenes = [k for k in mit if k.startswith("ACT")]
    for mit_scene_key in sorted(mit_scenes, key=lambda s: (
        int(re.search(r"ACT\s+(\d+)", s, re.I).group(1)),
        int(re.search(r"SCENE\s+(\d+)", s, re.I).group(1)),
    )):
        folger_key = mit_scene_to_folger(mit_scene_key)
        mit_scene = mit.get(mit_scene_key) or {}
        folger_scene = folger.get(folger_key) or {}

        mit_units = build_mit_units(mit_scene)
        nv_lines = extract_folger_nv_lines(folger_scene)
        total_notes_in += sum(len(n) for _, _, n in nv_lines)

        notes_by_key, review = align_scene(nv_lines, mit_units)
        # MIT Moby sometimes collapses short herald scenes; keep orphaned notes on scene entry.
        unmatched = [r for r in review if r.get("notes")]
        if unmatched and mit_units:
            fallback_key = mit_units[0]["anchor"]
            kept_review: list[dict[str, Any]] = []
            for row in review:
                if row.get("notes"):
                    notes_by_key.setdefault(fallback_key, []).extend(row["notes"])
                    row["reason"] = row.get("reason", "unmatched") + "_fallback_to_first_line"
                    row["fallbackLineKey"] = fallback_key
                else:
                    kept_review.append(row)
            review = kept_review
        for row in review:
            row["mitScene"] = mit_scene_key
            row["folgerScene"] = folger_key
        all_review.extend(review)

        scene_obj: dict[str, Any] = {}
        for u in mit_units:
            lk = u["anchor"]
            play = u.get("play") or ""
            notes = list(notes_by_key.get(lk, []))
            scene_obj[lk] = {"play": play, "notes": notes}

        quote_reanchored += reanchor_notes_by_quote(scene_obj, mit_units)
        for lk, ent in scene_obj.items():
            total_notes_out += len(ent.get("notes") or [])

        out[mit_scene_key] = scene_obj
        scenes_built += 1

    out["_meta"] = {
        "textSource": "MIT Shakespeare (Moby); public domain",
        "notesSource": "New Variorum Othello (1886); mapped from Folger-aligned JSON",
        "alignment": "nv_notes_mapped_by_scene_text_similarity_to_mit_spine",
        "quoteReanchored": quote_reanchored,
        "mitSpine": str(mit_path.relative_to(ROOT)),
        "notesSourceFile": str(notes_src.relative_to(ROOT)),
        "scenes": scenes_built,
        "notesMapped": total_notes_out,
        "notesSourceCount": total_notes_in,
        "reviewRows": len(all_review),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    review_payload = {
        "out": str(out_path.relative_to(ROOT)),
        "summary": out["_meta"],
        "review": all_review,
    }
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(json.dumps(review_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return out["_meta"]


def main() -> int:
    ap = argparse.ArgumentParser(description="Rebuild Othello on MIT spine with NV notes.")
    ap.add_argument("--mit", type=Path, default=MIT_SPINE)
    ap.add_argument("--notes-src", type=Path, default=NOTES_SRC)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--review", type=Path, default=REVIEW_OUT)
    args = ap.parse_args()

    meta = rebuild(args.mit, args.notes_src, args.out, args.review)
    print(
        f"Wrote {args.out} — {meta['scenes']} scenes, "
        f"{meta['notesMapped']} notes mapped ({meta['reviewRows']} review rows)"
    )
    print(f"Review: {args.review}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
