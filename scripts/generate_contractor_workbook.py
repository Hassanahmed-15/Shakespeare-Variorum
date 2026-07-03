#!/usr/bin/env python3
"""Build contractor truncation workbook from live play JSON + audit heuristics."""

from __future__ import annotations

import csv
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_nv_fidelity_all_plays import PLAYS  # noqa: E402
from audit_nv_truncation import (  # noqa: E402
    collect_notes,
    is_clipped,
    is_hard_truncation,
    is_hyphen_artifact,
    is_mid_sentence_cut,
    is_unbalanced_parens,
    is_witness_prefix,
)
from nv_ia_witness import fetch_ia_text, fold_apostrophe  # noqa: E402
from nv_witness_map import WITNESS_AUDIT_FALLBACK, WITNESS_BY_PLAY  # noqa: E402

OUT_JSON = ROOT / "validation" / "contractor_truncation_workbook.json"
OUT_CSV = ROOT / "validation" / "contractor_truncation_workbook.csv"

WORKBOOK_FIELDS = [
    "play_name",
    "play_file",
    "act_scene",
    "line_key",
    "note_index",
    "current_note_text",
    "truncation_signals",
    "witness_ia_id",
    "witness_url",
    "status",
    "completed_note_text",
    "contractor_notes",
    "char_count_before",
    "char_count_after",
]


def witness_url(ia_id: str) -> str:
    return f"https://archive.org/details/{ia_id}"


def truncation_signals(note: str, folded_ia: str | None) -> list[str]:
    signals: list[str] = []
    if is_clipped(note):
        signals.append("is_clipped")
    if is_hard_truncation(note):
        signals.append("hard_truncation")
    if is_mid_sentence_cut(note):
        signals.append("mid_sentence_cut")
    if is_hyphen_artifact(note):
        signals.append("hyphen_artifact")
    if is_unbalanced_parens(note):
        signals.append("unbalanced_parens")
    if folded_ia is not None and is_witness_prefix(folded_ia, note):
        signals.append("witness_prefix")
    return signals


def load_folded_witness(play: str, ia_id: str, ia_stream: str) -> tuple[str, str]:
    ia_text, _src = fetch_ia_text(ia_id, ia_stream)
    if ia_text is not None:
        return ia_id, fold_apostrophe(ia_text)
    fallback = WITNESS_AUDIT_FALLBACK.get(play)
    if fallback:
        fb_id, fb_stream = fallback
        ia_text, _src = fetch_ia_text(fb_id, fb_stream)
        if ia_text is not None:
            return fb_id, fold_apostrophe(ia_text)
    return ia_id, ""


def build_entries() -> list[dict]:
    entries: list[dict] = []
    for spec in PLAYS:
        play = spec["play"]
        path = ROOT / spec["json"]
        if not path.is_file():
            continue

        canonical_id, _stream = WITNESS_BY_PLAY[play]
        ia_id, folded_ia = load_folded_witness(play, spec["ia"], spec["ia_stream"])
        play_file = Path(spec["json"]).stem
        data = json.loads(path.read_text(encoding="utf-8"))

        for item in collect_notes(data):
            note = item["note"]
            signals = truncation_signals(note, folded_ia or None)
            if not signals:
                continue
            entries.append(
                {
                    "play_name": play,
                    "play_file": play_file,
                    "act_scene": item["scene"],
                    "line_key": item["line"],
                    "note_index": item["note_idx"],
                    "current_note_text": note,
                    "truncation_signals": signals,
                    "witness_ia_id": ia_id,
                    "witness_url": witness_url(ia_id),
                    "status": "pending",
                    "completed_note_text": "",
                    "contractor_notes": "",
                    "char_count_before": len(note),
                    "char_count_after": 0,
                }
            )
    entries.sort(
        key=lambda e: (
            e["play_name"],
            e["act_scene"],
            int(e["line_key"]) if e["line_key"].isdigit() else e["line_key"],
            e["note_index"],
        )
    )
    return entries


def write_csv(entries: list[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=WORKBOOK_FIELDS, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for entry in entries:
            row = dict(entry)
            row["truncation_signals"] = ";".join(entry["truncation_signals"])
            writer.writerow(row)


def main() -> int:
    entries = build_entries()
    payload = {
        "generated": date.today().isoformat(),
        "source_audit": "validation/nv_truncation_audit.json",
        "methodology": "Union of is_clipped, hard_truncation, mid_sentence_cut, hyphen_artifact, unbalanced_parens, witness_prefix (see audit_nv_truncation.py)",
        "total_entries": len(entries),
        "entries": entries,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_csv(entries, OUT_CSV)
    print(f"Wrote {len(entries)} entries to {OUT_JSON}")
    print(f"Wrote {OUT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
