#!/usr/bin/env python3
"""Harvest unresolved truncated note tails for COMPLETIONS curation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_nv_fidelity_all_plays import PLAYS  # noqa: E402
from audit_nv_truncation import collect_notes, is_union_truncated, tail_preview  # noqa: E402
from nv_ia_witness import fetch_ia_text, fold_apostrophe  # noqa: E402

OUT = ROOT / "validation/unresolved_tails_phase2.json"


def main() -> int:
    items: list[dict] = []
    for spec in PLAYS:
        path = ROOT / spec["json"]
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        ia_text, _ = fetch_ia_text(spec["ia"], spec["ia_stream"])
        folded = fold_apostrophe(ia_text) if ia_text else None
        for item in collect_notes(data):
            note = item["note"]
            if not is_union_truncated(note, folded):
                continue
            prefix = note[:120] if len(note) > 120 else note
            items.append(
                {
                    "play": spec["play"],
                    "ref": item["ref"],
                    "prefix": prefix,
                    "tail": tail_preview(note, 120),
                    "len": len(note),
                }
            )

    items.sort(key=lambda x: (-len(x["play"]), x["play"]))
    OUT.write_text(json.dumps({"count": len(items), "items": items[:500]}, indent=2) + "\n")
    print(f"Harvested {len(items)} unresolved tails -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
