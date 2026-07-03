#!/usr/bin/env python3
"""Pick the best IA witness per play by sampling note match rates."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_nv_fidelity_all_plays import PLAYS, collect_notes, sample_notes  # noqa: E402
from nv_ia_witness import fetch_ia_text, score_note_sample  # noqa: E402
from nv_witness_map import WITNESS_BY_PLAY, WITNESS_CANDIDATES  # noqa: E402

OUT = ROOT / "validation" / "nv_witness_resolution.json"
SAMPLE_N = 20


def candidates_for(play: str, default_ia: str, default_stream: str) -> list[tuple[str, str]]:
    cands = list(WITNESS_CANDIDATES.get(play, []))
    primary = WITNESS_BY_PLAY.get(play, (default_ia, default_stream))
    if primary not in cands:
        cands.insert(0, primary)
    # de-dupe
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str]] = []
    for item in cands:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def main() -> int:
    rows = []
    for spec in PLAYS:
        path = ROOT / spec["json"]
        notes = collect_notes(json.loads(path.read_text(encoding="utf-8")))
        sample = sample_notes(notes, SAMPLE_N)
        best = None
        tried = []
        for ia_id, stream in candidates_for(spec["play"], spec["ia"], spec["ia_stream"]):
            text, src = fetch_ia_text(ia_id, stream)
            if text is None:
                tried.append({"ia_id": ia_id, "status": "missing", "src": src})
                continue
            l2 = score_note_sample(text, sample)
            row = {
                "ia_id": ia_id,
                "stream": stream,
                "src": src,
                "exact_high_pct": l2["exact_high_pct"],
                "fail_pct": l2["fail_pct"],
            }
            tried.append(row)
            if best is None or row["exact_high_pct"] > best["exact_high_pct"]:
                best = row
        rows.append({"play": spec["play"], "best": best, "tried": tried})
        print(
            f"{spec['play']:<32} best={best['ia_id'] if best else '?':28} "
            f"L2={best['exact_high_pct'] if best else '—'}%"
        )

    OUT.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
