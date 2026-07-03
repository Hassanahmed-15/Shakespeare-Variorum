#!/usr/bin/env python3
"""Payment-gate verification for contractor NV truncation repairs."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_nv_fidelity_all_plays import PLAYS  # noqa: E402
from audit_nv_truncation import audit_play, collect_notes, is_union_truncated  # noqa: E402
from apply_contractor_completions import load_workbook  # noqa: E402
from nv_ia_witness import fetch_ia_text, fold_apostrophe  # noqa: E402
from nv_witness_map import WITNESS_AUDIT_FALLBACK, WITNESS_BY_PLAY  # noqa: E402

DEFAULT_WORKBOOK = ROOT / "validation" / "contractor_truncation_workbook.json"
ACCEPTABLE_STATUSES = {"complete", "no_change_needed"}


def workbook_status_report(entries: list[dict]) -> dict:
    by_status: dict[str, int] = defaultdict(int)
    incomplete: list[dict] = []
    for entry in entries:
        status = (entry.get("status") or "pending").strip().lower()
        by_status[status] += 1
        if status not in ACCEPTABLE_STATUSES:
            incomplete.append(entry)
        elif status == "complete" and not (entry.get("completed_note_text") or "").strip():
            incomplete.append(entry)
        elif status == "no_change_needed" and not (entry.get("contractor_notes") or "").strip():
            incomplete.append(entry)
    return {
        "total": len(entries),
        "by_status": dict(by_status),
        "incomplete": incomplete,
        "workbook_ok": len(incomplete) == 0,
    }


def audit_all_plays() -> tuple[list[dict], int]:
    rows = []
    total_union = 0
    for spec in PLAYS:
        row = audit_play(spec)
        rows.append(row)
        if not row.get("error"):
            total_union += row["union_truncated"]
    return rows, total_union


def spot_check_entries(entries: list[dict], sample_n: int = 5) -> list[dict]:
    """Random-ish sample: first N completed entries per play with witness check."""
    import random

    by_play: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        if (entry.get("status") or "").strip().lower() == "complete":
            by_play[entry["play_name"]].append(entry)

    checks: list[dict] = []
    for play_name, play_entries in sorted(by_play.items()):
        sample = play_entries[:sample_n] if len(play_entries) <= sample_n else random.sample(play_entries, sample_n)
        ia_id, stream = WITNESS_BY_PLAY[play_name]
        ia_text, _src = fetch_ia_text(ia_id, stream)
        if ia_text is None:
            fallback = WITNESS_AUDIT_FALLBACK.get(play_name)
            if fallback:
                ia_text, _src = fetch_ia_text(fallback[0], fallback[1])
        folded = fold_apostrophe(ia_text) if ia_text else ""
        for entry in sample:
            completed = entry.get("completed_note_text") or entry.get("current_note_text") or ""
            body = completed[completed.index("]") + 1 :].strip() if "]" in completed else completed.strip()
            probe = body[:60]
            found = bool(folded and probe.lower() in folded.lower())
            checks.append(
                {
                    "play_name": play_name,
                    "ref": f"{entry['act_scene']} / line {entry['line_key']} / note {entry['note_index']}",
                    "witness_found": found,
                    "witness_ia_id": entry.get("witness_ia_id"),
                }
            )
    return checks


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workbook", type=Path, default=DEFAULT_WORKBOOK)
    ap.add_argument("--allow-remaining", type=int, default=0, help="Max union-truncated notes still acceptable")
    ap.add_argument("--spot-check", type=int, default=3, help="Completed entries to spot-check per play (0=skip)")
    ap.add_argument("--json-out", type=Path, help="Write verification report JSON")
    args = ap.parse_args()

    entries = load_workbook(args.workbook)
    wb = workbook_status_report(entries)
    audit_rows, total_union = audit_all_plays()

    per_play = []
    failing_plays = []
    for row in audit_rows:
        if row.get("error"):
            per_play.append({**row, "pass": False})
            failing_plays.append(row["play"])
            continue
        passed = row["union_truncated"] <= args.allow_remaining
        per_play.append(
            {
                "play": row["play"],
                "union_truncated": row["union_truncated"],
                "total_notes": row["total_notes"],
                "pass": passed,
            }
        )
        if not passed:
            failing_plays.append(row["play"])

    spot_checks = spot_check_entries(entries, sample_n=args.spot_check) if args.spot_check else []
    witness_misses = [c for c in spot_checks if not c["witness_found"]]

    report = {
        "workbook": wb,
        "audit_totals": {
            "union_truncated": total_union,
            "allow_remaining": args.allow_remaining,
        },
        "per_play": per_play,
        "spot_checks": spot_checks,
        "witness_spot_misses": len(witness_misses),
        "pass": wb["workbook_ok"] and total_union <= args.allow_remaining,
    }

    print("=== Contractor workbook status ===")
    print(f"Total entries: {wb['total']}")
    for status, count in sorted(wb["by_status"].items()):
        print(f"  {status}: {count}")
    if wb["incomplete"]:
        print(f"INCOMPLETE: {len(wb['incomplete'])} entries not ready")
        for entry in wb["incomplete"][:5]:
            print(
                f"  - {entry['play_name']} / {entry['act_scene']} / line {entry['line_key']} / note {entry['note_index']} ({entry.get('status')})"
            )
    else:
        print("All workbook entries marked complete or no_change_needed with required fields.")

    print("\n=== Post-apply truncation audit ===")
    print(f"{'Play':<32} {'Union':>6} {'Pass':>6}")
    print("-" * 48)
    for row in per_play:
        if "error" in row:
            print(f"{row['play']:<32} ERROR")
            continue
        mark = "YES" if row["pass"] else "NO"
        print(f"{row['play']:<32} {row['union_truncated']:>6} {mark:>6}")
    print("-" * 48)
    print(f"{'TOTAL':<32} {total_union:>6}")

    if spot_checks:
        print(f"\n=== Witness spot-check ({len(spot_checks)} samples) ===")
        print(f"Misses: {len(witness_misses)}")
        for miss in witness_misses[:5]:
            print(f"  - {miss['play_name']} / {miss['ref']}")

    overall = report["pass"]
    print(f"\n{'PASS' if overall else 'FAIL'}: payment gate {'open' if overall else 'closed'}")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {args.json_out}")

    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
