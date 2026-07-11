#!/usr/bin/env python3
"""Quantify Othello Folger TEI alignment success for paper statistics.

Compares deployed `othello_notes_folger.json` against Folger TEI spine
(`Public/Data/folger_tei/Oth.xml`). Play text in the merged JSON is sourced
from TEI in `build_merged_play`; this audit measures how completely spine
units received a `folgerAnchor` and TEI-faithful `play` string.

Also reports note-mapping results from `align_nv_to_folger` review JSON when
present (legacy integer-key input → Folger anchors).

Output: validation/othello_folger_alignment_stats.json
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from folger_tei.align_nv_to_folger import _ratio_score, normalize_for_match  # noqa: E402
from folger_tei.ingest_folger_tei import parse_folger_play  # noqa: E402

DEPLOYED = ROOT / "Public/Data/othello_notes_folger.json"
TEI = ROOT / "Public/Data/folger_tei/Oth.xml"
REVIEW = ROOT / "Public/Data/othello_folger_alignment_review.json"
OUT = ROOT / "validation/othello_folger_alignment_stats.json"


def tei_anchor_index(spine: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for units in spine["scenes"].values():
        for u in units:
            anchor = u.get("anchor") or ""
            key = anchor.replace(" ", "_") if anchor.startswith("SD") else anchor
            out[key] = u.get("play") or ""
            out[anchor] = u.get("play") or ""
    return out


def main() -> int:
    merged = json.loads(DEPLOYED.read_text(encoding="utf-8"))
    spine = parse_folger_play(TEI)
    tei = tei_anchor_index(spine)

    buckets = {
        "all_with_play": {"total": 0, "exact": 0, "speech": 0, "stage": 0, "dramatis": 0},
        "act_scene_only": {"total": 0, "exact": 0, "speech": 0, "stage": 0},
        "note_lines": {"total": 0, "with_folger_anchor": 0},
    }
    speech = {"total": 0, "exact": 0}
    stage = {"total": 0, "exact": 0}

    for scene, lines in merged.items():
        if scene.startswith("_") or not isinstance(lines, dict):
            continue
        is_dramatis = scene == "DRAMATIS PERSONAE"
        for lk, ent in lines.items():
            if not isinstance(ent, dict):
                continue
            play = (ent.get("play") or "").strip()
            notes = ent.get("notes") or []
            if notes:
                buckets["note_lines"]["total"] += 1
                if ent.get("folgerAnchor"):
                    buckets["note_lines"]["with_folger_anchor"] += 1
            if not play:
                continue

            buckets["all_with_play"]["total"] += 1
            if is_dramatis:
                buckets["all_with_play"]["dramatis"] += 1
            kind = ent.get("kind") or ("stage" if play.startswith("[") else "speech")
            if kind == "stage":
                buckets["all_with_play"]["stage"] += 1
            else:
                buckets["all_with_play"]["speech"] += 1

            ref = ent.get("folgerAnchor") or lk
            tei_key = ref.replace(" ", "_") if str(ref).startswith("SD") else ref
            tei_play = tei.get(tei_key) or tei.get(ref) or ""
            ratio = _ratio_score(normalize_for_match(play), normalize_for_match(tei_play))
            exact = ratio >= 0.99

            if exact:
                buckets["all_with_play"]["exact"] += 1

            if not is_dramatis:
                buckets["act_scene_only"]["total"] += 1
                if exact:
                    buckets["act_scene_only"]["exact"] += 1
                if kind == "stage":
                    stage["total"] += 1
                    if exact:
                        stage["exact"] += 1
                else:
                    speech["total"] += 1
                    if exact:
                        speech["exact"] += 1

    def pct(num: int, den: int) -> float | None:
        return round(100 * num / den, 2) if den else None

    review_rows = []
    if REVIEW.is_file():
        review_rows = json.loads(REVIEW.read_text(encoding="utf-8"))

    note_strings = sum(
        len(ent.get("notes") or [])
        for scene, lines in merged.items()
        if isinstance(lines, dict)
        for ent in lines.values()
        if isinstance(ent, dict)
    )

    stats = {
        "date": date.today().isoformat(),
        "play": "Othello",
        "method": (
            "Deployed merged JSON vs Folger TEI (Oth.xml): each line with non-empty "
            "'play' compared by normalized fuzzy ratio; exact = ratio >= 0.99. "
            "Note-mapping review from align_nv_to_folger --review JSON when present."
        ),
        "sources": {
            "deployed_json": str(DEPLOYED.relative_to(ROOT)),
            "folger_tei": str(TEI.relative_to(ROOT)),
            "alignment_review": str(REVIEW.relative_to(ROOT)) if REVIEW.is_file() else None,
        },
        "line_references_all_spine_units_with_play_text": {
            "matched_exact": buckets["all_with_play"]["exact"],
            "total": buckets["all_with_play"]["total"],
            "pct": pct(buckets["all_with_play"]["exact"], buckets["all_with_play"]["total"]),
            "dramatis_rows_excluded_from_denominator_below": buckets["all_with_play"]["dramatis"],
        },
        "line_references_act_scene_only": {
            "matched_exact": buckets["act_scene_only"]["exact"],
            "total": buckets["act_scene_only"]["total"],
            "pct": pct(buckets["act_scene_only"]["exact"], buckets["act_scene_only"]["total"]),
        },
        "by_kind_act_scene_only": {
            "dialogue_speech": {
                "matched_exact": speech["exact"],
                "total": speech["total"],
                "pct": pct(speech["exact"], speech["total"]),
            },
            "stage_direction": {
                "matched_exact": stage["exact"],
                "total": stage["total"],
                "pct": pct(stage["exact"], stage["total"]),
            },
        },
        "note_bearing_lines": {
            "with_folger_anchor": buckets["note_lines"]["with_folger_anchor"],
            "total": buckets["note_lines"]["total"],
            "pct": pct(
                buckets["note_lines"]["with_folger_anchor"],
                buckets["note_lines"]["total"],
            ),
            "note_strings_total": note_strings,
        },
        "alignment_review_failures": {
            "rows": len(review_rows),
            "note_strings_unplaced": sum(len(r.get("notes") or []) for r in review_rows),
        },
        "paper_recommendation": {
            "replace_over_95_with": f"{pct(buckets['all_with_play']['exact'], buckets['all_with_play']['total'])}%",
            "act_scene_only": f"{pct(buckets['act_scene_only']['exact'], buckets['act_scene_only']['total'])}%",
            "scope": "Othello only; Folger TEI alignment is not run on other plays.",
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(
        f"Act/scene line references: {stats['line_references_act_scene_only']['matched_exact']}/"
        f"{stats['line_references_act_scene_only']['total']} "
        f"({stats['line_references_act_scene_only']['pct']}%)"
    )
    print(
        f"All spine units w/ play text: {stats['line_references_all_spine_units_with_play_text']['matched_exact']}/"
        f"{stats['line_references_all_spine_units_with_play_text']['total']} "
        f"({stats['line_references_all_spine_units_with_play_text']['pct']}%)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
