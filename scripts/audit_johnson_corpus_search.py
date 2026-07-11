#!/usr/bin/env python3
"""Count corpus-wide Johnson keyword hits in deployed NV note JSON (site PLAY_FILES).

Matches the site all-play annotation search when the user queries "Johnson":
case-insensitive substring match in each note string (not primary-annotator filter).

Outputs:
  validation/johnson_corpus_search.json
  validation/johnson_corpus_search_no_troilus.json  (when --exclude is set)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 22 deployed NV dramatic volumes (same set as site about-page list / PLAY_FILES subset)
DEPLOYED_22 = {
    "Romeo and Juliet": "Public/Data/romeo_and_juliet.json",
    "Macbeth": "Public/Data/macbeth_correct.json",
    "Hamlet": "Public/Data/hamlet_notes (1).json",
    "King Lear": "Public/Data/kinglear_notes.json",
    "Othello": "Public/Data/othello_notes_folger.json",
    "Merchant of Venice": "Public/Data/merchant_of_venice.json",
    "As You Like It": "Public/Data/as_you_like_it.json",
    "The Tempest": "Public/Data/the_tempest.json",
    "A Midsummer Night's Dream": "Public/Data/midsummer_nights_dream.json",
    "The Winter's Tale": "Public/Data/the_winters_tale.json",
    "Much Ado About Nothing": "Public/Data/much_ado_about_nothing.json",
    "Twelfth Night": "Public/Data/twelfth_night.json",
    "Love's Labour's Lost": "Public/Data/loves_labours_lost.json",
    "Antony and Cleopatra": "Public/Data/antony_and_cleopatra.json",
    "Richard III": "Public/Data/richard_iii.json",
    "Julius Caesar": "Public/Data/julius_caesar.json",
    "Cymbeline": "Public/Data/cymbeline.json",
    "King John": "Public/Data/king_john.json",
    "Coriolanus": "Public/Data/Coriolanus.json",
    "Henry IV Part 1": "Public/Data/henry_iv_part1.json",
    "Henry IV Part 2": "Public/Data/henry_iv_part2.json",
    "Troilus and Cressida": "Public/Data/troilus_and_cressida.json",
}

NEEDLE_DEFAULT = "johnson"


def count_hits(plays: dict[str, str], needle: str) -> dict:
    needle_l = needle.lower()
    per_play: dict[str, int] = {}
    for play, rel in plays.items():
        path = ROOT / rel
        data = json.loads(path.read_text(encoding="utf-8"))
        n = 0
        for scene_key, scene_val in data.items():
            if scene_key == "DRAMATIS PERSONAE" or not isinstance(scene_val, dict):
                continue
            for item in scene_val.values():
                if not isinstance(item, dict):
                    continue
                for note in item.get("notes") or []:
                    if isinstance(note, str) and needle_l in note.lower():
                        n += 1
        per_play[play] = n
    total = sum(per_play.values())
    return {
        "date": date.today().isoformat(),
        "method": (
            f'Case-insensitive "{needle}" substring in each notes[] string; '
            "same hit definition as site keyword search (query token must appear in note text)."
        ),
        "needle": needle,
        "plays": len(plays),
        "total_hits": total,
        "per_play": dict(sorted(per_play.items(), key=lambda kv: (-kv[1], kv[0]))),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Johnson corpus-wide search audit")
    ap.add_argument("--needle", default=NEEDLE_DEFAULT)
    ap.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Play title(s) to omit (repeatable), e.g. 'Troilus and Cressida'",
    )
    ap.add_argument(
        "--suffix",
        default=None,
        help="Output filename suffix (default: _no_<slug> when --exclude is set)",
    )
    args = ap.parse_args()
    excluded = {name.strip() for name in args.exclude if name.strip()}
    plays = {k: v for k, v in DEPLOYED_22.items() if k not in excluded}
    if not plays:
        print("No plays left after exclusions", file=sys.stderr)
        return 1

    summary = count_hits(plays, args.needle)
    summary["excluded"] = sorted(excluded)

    if excluded:
        slug = args.suffix
        if slug is None:
            slug = "_no_troilus" if excluded == {"Troilus and Cressida"} else (
                "_no_" + re.sub(r"[^a-z0-9]+", "_", sorted(excluded)[0].lower()).strip("_")
            )
        out = ROOT / "validation" / f"johnson_corpus_search{slug}.json"
    else:
        out = ROOT / "validation" / "johnson_corpus_search.json"

    out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out.relative_to(ROOT)}")
    print(f"Total: {summary['total_hits']:,} ({summary['plays']} plays)")
    if excluded:
        tro = summary["per_play"].get("Troilus and Cressida", 0)
        if "Troilus and Cressida" in excluded:
            full = count_hits(DEPLOYED_22, args.needle)
            print(f"22-play baseline: {full['total_hits']:,}")
            print(f"Excluded Troilus hits: {DEPLOYED_22.get('Troilus and Cressida') and full['per_play'].get('Troilus and Cressida', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
