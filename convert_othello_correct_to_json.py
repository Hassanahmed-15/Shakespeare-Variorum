#!/usr/bin/env python3
"""
Convert othello correct.docx to legacy integer-key JSON (Macbeth-parity ingest).

Same DOCX layout as macbeth correct.docx:
  - ACT X, SCENE Y
  - ========PLAY TEXT========
  - Numbered lines: 1. text, 2. SPEAKER: text, ...
  - ========SCHOLARLY COMMENTARY========
  - Commentary: 1. phrase] SCHOLAR: note text

Output: Public/Data/othello_notes_legacy.json — feed to align_nv_to_folger.py.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Reuse the Macbeth parser (identical DOCX structure).
from convert_macbeth_correct_to_json import convert_macbeth_correct_to_json


def convert_othello_correct_to_json(
    docx_path: str,
    output_json_path: str | None = None,
) -> dict:
    script_dir = Path(__file__).resolve().parent
    if output_json_path is None:
        output_json_path = str(script_dir / "Public" / "Data" / "othello_notes_legacy.json")

    data = convert_macbeth_correct_to_json(docx_path, output_json_path)

    # Replace Macbeth dramatis placeholder with Othello cast from pre-normalize backup when present.
    backup = script_dir / "Public" / "Data" / "othello_notes.pre_normalize.backup.json"
    if backup.is_file():
        backup_data = json.loads(backup.read_text(encoding="utf-8"))
        if "DRAMATIS PERSONAE" in backup_data:
            data["DRAMATIS PERSONAE"] = backup_data["DRAMATIS PERSONAE"]
            out = Path(output_json_path)
            out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"  Restored DRAMATIS PERSONAE from {backup.name}")

    return data


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description="Convert othello correct.docx to legacy NV JSON.")
    ap.add_argument(
        "docx",
        nargs="?",
        default=str(script_dir / "othello correct.docx"),
        help="Path to structured Othello DOCX (default: othello correct.docx in repo root)",
    )
    ap.add_argument(
        "-o",
        "--out",
        default=str(script_dir / "Public" / "Data" / "othello_notes_legacy.json"),
        help="Output legacy JSON path",
    )
    args = ap.parse_args()
    if not os.path.isfile(args.docx):
        print(f"Error: {args.docx} not found.", file=sys.stderr)
        print(
            "Create it with the Macbeth-parity pipeline: OCR the Furness Othello PDF "
            "(newvariorumediti13shak), Gemini cleanup, then structure as PLAY TEXT + "
            "SCHOLARLY COMMENTARY per scene.",
            file=sys.stderr,
        )
        return 1
    convert_othello_correct_to_json(args.docx, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
