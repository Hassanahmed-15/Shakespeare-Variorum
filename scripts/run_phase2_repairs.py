#!/usr/bin/env python3
"""Phase 2 NV truncation repair orchestrator."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_nv_truncation import collect_notes, is_union_truncated  # noqa: E402
from nv_ia_witness import fetch_ia_text, fold_apostrophe  # noqa: E402
from nv_repair import (  # noqa: E402
    repair_pass,
    split_mega_notes_in_data,
)
from nv_witness_map import WITNESS_BY_PLAY  # noqa: E402

SITE_DATA = ROOT / "My Website/Public/Data"

PLAYS: dict[str, dict] = {
    "Coriolanus": {
        "json": ROOT / "Public/Data/Coriolanus.json",
        "mega_split": True,
    },
    "King John": {
        "json": ROOT / "Public/Data/king_john.json",
        "mega_split": True,
    },
    "The Winter's Tale": {
        "json": ROOT / "Public/Data/the_winters_tale.json",
        "mega_split": True,
    },
    "Antony and Cleopatra": {
        "json": ROOT / "Public/Data/antony_and_cleopatra.json",
    },
    "Julius Caesar": {
        "json": ROOT / "Public/Data/julius_caesar.json",
    },
    "Cymbeline": {
        "json": ROOT / "Public/Data/cymbeline.json",
    },
    "Henry IV, Part 2": {
        "json": ROOT / "Public/Data/henry_iv_part2.json",
    },
    "Henry IV, Part 1": {
        "json": ROOT / "Public/Data/henry_iv_part1.json",
    },
    "The Tempest": {
        "json": ROOT / "Public/Data/the_tempest.json",
    },
    "Richard III": {
        "json": ROOT / "Public/Data/richard_iii.json",
    },
    "Hamlet": {
        "json": ROOT / "Public/Data/hamlet.json",
    },
    "Troilus and Cressida": {
        "json": ROOT / "Public/Data/troilus_and_cressida.json",
        "script": "repair_troilus_clipped_notes",
    },
}


def count_union(data: dict, folded_ia: str | None) -> int:
    return sum(
        1 for item in collect_notes(data) if is_union_truncated(item["note"], folded_ia)
    )


def sync_mirror(json_path: Path, text: str) -> None:
    mirror = SITE_DATA / json_path.name
    if mirror.parent.is_dir():
        mirror.write_text(text, encoding="utf-8")


def backup_json(json_path: Path) -> None:
    bak = json_path.with_suffix(".json.pre_phase2_repair.backup")
    if not bak.is_file() and json_path.is_file():
        shutil.copy2(json_path, bak)


def process_play(name: str, spec: dict, *, dry_run: bool = False, repair_only: bool = False) -> dict:
    json_path: Path = spec["json"]
    if not json_path.is_file():
        return {"play": name, "error": f"missing {json_path}"}

    ia_id, stream = WITNESS_BY_PLAY[name]
    ia_text, src = fetch_ia_text(ia_id, stream)
    if ia_text is None:
        return {"play": name, "error": f"witness unavailable: {src}"}

    data = json.loads(json_path.read_text(encoding="utf-8"))
    folded = fold_apostrophe(ia_text)
    before = count_union(data, folded)
    result: dict = {
        "play": name,
        "ia_id": ia_id,
        "witness": src,
        "truncated_before": before,
        "mega_split": {},
        "repair": {},
    }

    if spec.get("mega_split") and not repair_only:
        result["mega_split"] = split_mega_notes_in_data(data)

    result["repair"] = repair_pass(
        data, ia_text, play=name, folded_ia=folded, dry_run=dry_run, max_passes=6
    )
    if spec.get("mega_split") and not repair_only:
        extra = repair_pass(
            data, ia_text, play=name, folded_ia=folded, dry_run=dry_run, max_passes=6
        )
        result["repair"]["repaired"] += extra["repaired"]
        result["repair"]["after"] = extra["after"]
        result["repair"]["unresolved"] = extra["unresolved"]
        result["repair"]["examples"].extend(extra.get("examples", []))
    after = before - result["repair"]["repaired"] if dry_run else count_union(data, folded)
    result["truncated_after"] = after
    result["repaired_this_phase"] = result["repair"]["repaired"]

    if not dry_run and (result["repair"]["repaired"] or result["mega_split"].get("split_events")):
        backup_json(json_path)
        out = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        json_path.write_text(out, encoding="utf-8")
        sync_mirror(json_path, out)

    audit = ROOT / f"validation/phase2_{json_path.stem}_repair.json"
    audit.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--play", action="append", help="Limit to named play(s)")
    ap.add_argument("--skip-troilus", action="store_true")
    ap.add_argument("--repair-only", action="store_true", help="Skip mega-note split")
    args = ap.parse_args()

    targets = PLAYS
    if args.play:
        targets = {k: v for k, v in PLAYS.items() if k in args.play}
    if args.skip_troilus:
        targets = {k: v for k, v in targets.items() if k != "Troilus and Cressida"}

    results = []
    for name, spec in targets.items():
        if spec.get("script") == "repair_troilus_clipped_notes":
            continue
        print(f"\n=== {name} ===")
        r = process_play(name, spec, dry_run=args.dry_run, repair_only=args.repair_only)
        results.append(r)
        if "error" in r:
            print(f"  ERROR: {r['error']}")
        else:
            ms = r.get("mega_split") or {}
            print(
                f"  truncated {r['truncated_before']} -> {r['truncated_after']} "
                f"(repaired {r['repaired_this_phase']}, mega_splits={ms.get('split_events', 0)})"
            )

    summary_path = ROOT / "validation/phase2_repair_summary.json"
    summary_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {summary_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
