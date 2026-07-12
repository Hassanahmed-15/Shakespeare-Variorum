#!/usr/bin/env python3
"""
Align Othello's existing Folger-anchored NV notes JSON to an MIT/Moby spine.

Reuses align_scene / build_merged_play / apply_note_overrides from
scripts/folger_tei/align_nv_to_folger.py unchanged -- those functions only
depend on the generic spine shape (scene_key -> [{kind, anchor, play, ...}]),
not on anything Folger-specific.

Input notes source: Public/Data/othello_notes_folger.json (already scene- and
line-keyed, already carrying NV notes). We treat each of its entries as an
"nv_line" (old_key, play_text, notes) the same way align_nv_to_folger.py
treats legacy integer-keyed rows -- the aligner re-derives placement from
text similarity, not from trusting the source key scheme.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.folger_tei.align_nv_to_folger import (  # noqa: E402
    align_scene,
    apply_note_overrides,
)
from scripts.mit.ingest_mit_html import parse_mit_play  # noqa: E402


def build_merged_play_mit(
    spine: dict[str, Any],
    notes_by_anchor: dict[str, list[Any]],
    dramatis: dict[str, Any] | None,
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if dramatis is not None:
        out["DRAMATIS PERSONAE"] = dramatis

    for scene_key, units in spine["scenes"].items():
        scene_obj: dict[str, Any] = {}
        for u in units:
            anchor = u.get("anchor") or ""
            line_key = anchor.replace(" ", "_") if anchor.startswith("SD") else anchor
            lookup = line_key if anchor.startswith("SD") else anchor
            notes = list(notes_by_anchor.get(lookup, []))
            scene_obj[line_key] = {
                "play": u.get("play") or "",
                "notes": notes,
                "mitAnchor": anchor,
                "kind": u.get("kind", "speech"),
            }
        out[scene_key] = scene_obj

    out["_meta"] = {
        "textSource": "MIT/Moby Shakespeare, shakespeare.mit.edu (public domain)",
        "playId": spine.get("play_id"),
        "alignment": "nv_notes_mapped_by_scene_text_similarity_folger_to_mit",
        "sourceNotesFile": "Public/Data/othello_notes_folger.json",
    }
    return out


def run_align_mit(
    mit_html_path: Path,
    folger_notes_path: Path,
    out_path: Path,
    review_path: Path,
    overrides_path: Path | None = None,
) -> None:
    spine = parse_mit_play(mit_html_path)
    source = json.loads(folger_notes_path.read_text(encoding="utf-8"))

    notes_by_anchor: dict[str, list[Any]] = {}
    all_review: list[dict[str, Any]] = []

    for scene_key, scene_data in source.items():
        if scene_key == "DRAMATIS PERSONAE" or scene_key.startswith("_"):
            continue
        if not isinstance(scene_data, dict):
            continue
        if scene_key not in spine["scenes"]:
            all_review.append(
                {
                    "reason": "folger_scene_not_in_mit_spine",
                    "scene": scene_key,
                }
            )
            continue

        nv_lines: list[tuple[str, str, list[Any]]] = []
        for lk, ent in scene_data.items():
            if not isinstance(ent, dict):
                continue
            play = ent.get("play") or ""
            notes = ent.get("notes") or []
            if not play and not notes:
                continue
            nv_lines.append((str(lk), play, notes))

        fol_units = spine["scenes"][scene_key]
        merged_notes, review = align_scene(nv_lines, fol_units)
        for anc, lst in merged_notes.items():
            notes_by_anchor.setdefault(anc, []).extend(lst)
        for r in review:
            r["scene"] = scene_key
        all_review.extend(review)

    dramatis = source.get("DRAMATIS PERSONAE")
    merged = build_merged_play_mit(spine, notes_by_anchor, dramatis)

    overrides_data: dict[str, Any] | None = None
    if overrides_path is not None and overrides_path.is_file():
        overrides_data = json.loads(overrides_path.read_text(encoding="utf-8"))
        merged.setdefault("_meta", {})["noteOverridesFile"] = str(overrides_path)
    apply_note_overrides(merged, overrides_data)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    review_path.write_text(json.dumps(all_review, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path} and {review_path}")


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(
        description="Align Othello's Folger-keyed NV notes to an MIT/Moby HTML spine."
    )
    ap.add_argument("--mit-html", type=Path, required=True)
    ap.add_argument("--folger-notes", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--review", type=Path, required=True)
    ap.add_argument("--overrides", type=Path, default=None)
    args = ap.parse_args()
    run_align_mit(args.mit_html, args.folger_notes, args.out, args.review, overrides_path=args.overrides)


if __name__ == "__main__":
    main()
