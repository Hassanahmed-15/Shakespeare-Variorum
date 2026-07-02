#!/usr/bin/env python3
"""
Rebuild Othello notes to Macbeth parity, then Folger-align for production.

Macbeth on the site uses macbeth_correct.json from a structured DOCX ingest
(OCR → Gemini cleanup → PLAY TEXT + SCHOLARLY COMMENTARY → JSON).
Othello's current summaries predate Folger alignment; re-aligning alone cannot fix them.

Pipeline (run from repository root):

  1. Place othello correct.docx in repo root (same format as macbeth correct.docx).
  2. python3 convert_othello_correct_to_json.py
  3. python3 scripts/rebuild_othello_notes.py --align
  4. python3 scripts/validate_nv_othello.py
  5. python3 scripts/audit_nv_fidelity_all_plays.py  # Othello → Tier A target

This script runs steps 3–4 when --align is passed and reports Macbeth-parity gates.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "Public/Data/othello_notes_legacy.json"
FOLGER_OUT = ROOT / "Public/Data/othello_notes_folger.json"
FOLGER_MIRROR = ROOT / "Public/Data/othello_notes.json"
TEI = ROOT / "Public/Data/folger_tei/Oth.xml"
REVIEW = ROOT / "Public/Data/othello_folger_alignment_review.json"
MACBETH_REF = ROOT / "Public/Data/macbeth_correct.json"

SYNTHETIC_RE = re.compile(
    r"^(Editorial note|Annotation|Gloss|Note|Textual|Lexical|Critical note):",
    re.I,
)
PARAPHRASE_RE = re.compile(
    r"(notes various|discussion of|Debate among|Explanatory note|On the colloquial|and other editors note)",
    re.I,
)


def collect_notes(data: dict) -> list[str]:
    notes: list[str] = []
    for scene, scene_data in data.items():
        if str(scene).startswith("_") or not isinstance(scene_data, dict):
            continue
        for obj in scene_data.values():
            if isinstance(obj, dict) and obj.get("notes"):
                notes.extend(obj["notes"])
    return notes


def parity_metrics(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    notes = collect_notes(data)
    if not notes:
        return {"file": path.name, "note_strings": 0}
    lens = [len(n) for n in notes]
    return {
        "file": path.name,
        "note_strings": len(notes),
        "avg_len": round(statistics.mean(lens)),
        "median_len": round(statistics.median(lens)),
        "pct_under_250": round(100 * sum(1 for x in lens if x < 250) / len(lens), 1),
        "synthetic_prefix": sum(1 for n in notes if SYNTHETIC_RE.match(n.strip())),
        "paraphrase_style": sum(
            1 for n in notes
            if len(n) < 300 and (" — " in n or "—" in n) and PARAPHRASE_RE.search(n)
        ),
    }


def run_align() -> None:
    if not LEGACY.is_file():
        raise SystemExit(
            f"Missing {LEGACY.relative_to(ROOT)} — run convert_othello_correct_to_json.py first."
        )
    if not TEI.is_file():
        raise SystemExit(f"Missing Folger TEI: {TEI.relative_to(ROOT)}")
    cmd = [
        sys.executable,
        "-m",
        "scripts.folger_tei.align_nv_to_folger",
        "--tei",
        str(TEI),
        "--legacy",
        str(LEGACY),
        "--out",
        str(FOLGER_OUT),
        "--review",
        str(REVIEW),
    ]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True, env={**os.environ, "PYTHONPATH": str(ROOT)})
    # Site loads both filenames in some paths; keep mirror in sync.
    FOLGER_MIRROR.write_text(FOLGER_OUT.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Synced {FOLGER_MIRROR.relative_to(ROOT)}")


def print_gate_report() -> int:
    othello = parity_metrics(FOLGER_OUT)
    macbeth = parity_metrics(MACBETH_REF) if MACBETH_REF.is_file() else {}
    print("\n=== Macbeth parity gates (Othello vs macbeth_correct.json) ===")
    for key in ("note_strings", "avg_len", "median_len", "pct_under_250", "synthetic_prefix", "paraphrase_style"):
        o_val = othello.get(key, "—")
        m_val = macbeth.get(key, "—")
        ok = ""
        if key in ("synthetic_prefix", "paraphrase_style") and isinstance(o_val, int):
            ok = " OK" if o_val == 0 else " FAIL"
        print(f"  {key}: Othello={o_val}  Macbeth={m_val}{ok}")
    failed = (othello.get("synthetic_prefix") or 0) > 0 or (othello.get("paraphrase_style") or 0) > 0
    return 1 if failed else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Rebuild Othello notes to Macbeth parity.")
    ap.add_argument("--align", action="store_true", help="Run Folger aligner on othello_notes_legacy.json")
    ap.add_argument("--validate", action="store_true", help="Run validate_nv_othello.py after align")
    ap.add_argument("--report-only", action="store_true", help="Print parity metrics for current folger JSON")
    args = ap.parse_args()

    if args.report_only:
        return print_gate_report()

    if args.align:
        run_align()

    code = print_gate_report()

    if args.validate:
        subprocess.run([sys.executable, str(ROOT / "scripts/validate_nv_othello.py")], cwd=ROOT, check=False)

    if not args.align and not args.report_only:
        print(__doc__)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
