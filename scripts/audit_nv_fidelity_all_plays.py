#!/usr/bin/env python3
"""Audit New Variorum note fidelity across all 22 dramatic NV volumes."""

from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from nv_ia_witness import (  # noqa: E402
    PARAPHRASE_RE,
    SYNTHETIC_RE,
    fetch_ia_text,
    score_note_sample,
)

OUT_JSON = ROOT / "validation" / "nv_fidelity_all_plays.json"
OUT_CSV = ROOT / "validation" / "nv_fidelity_all_plays.csv"
OUT_SUMMARY = ROOT / "validation" / "nv_fidelity_summary.json"
SAMPLE_N = 35
TIER_A_L2_MIN = 85.0
CLIP_MAX_PCT = 4.0

# 22 NV dramatic volumes (Richard II excluded — site lists as forthcoming)
PLAYS = [
    {"play": "Romeo and Juliet", "year": 1871, "json": "Public/Data/romeo_and_juliet.json",
     "ia": "newvariorumediti01shak", "ia_stream": "newvariorumediti01shak_djvu.txt"},
    {"play": "Macbeth", "year": 1873, "json": "Public/Data/macbeth_notes_cleaned_play.json",
     "ia": "newvariorumediti10shak", "ia_stream": "newvariorumediti10shak_djvu.txt"},
    {"play": "Hamlet", "year": 1877, "json": "Public/Data/hamlet_notes (1).json",
     "ia": "newvariorumediti02shak", "ia_stream": "newvariorumediti02shak_djvu.txt"},
    {"play": "King Lear", "year": 1880, "json": "Public/Data/kinglear_notes.json",
     "ia": "kinglearthenewva0005shak", "ia_stream": "kinglearthenewva0005shak_djvu.txt"},
    {"play": "Othello", "year": 1886, "json": "Public/Data/othello_notes_folger.json",
     "ia": "newvariorumediti13shak", "ia_stream": "newvariorumediti13shak_djvu.txt"},
    {"play": "The Merchant of Venice", "year": 1888, "json": "Public/Data/merchant_of_venice.json",
     "ia": "newvariorumediti0000unse_h5u1", "ia_stream": "newvariorumediti0000unse_h5u1_djvu.txt"},
    {"play": "As You Like It", "year": 1890, "json": "Public/Data/as_you_like_it.json",
     "ia": "newvariorumediti05shak", "ia_stream": "newvariorumediti05shak_djvu.txt"},
    {"play": "The Tempest", "year": 1892, "json": "Public/Data/the_tempest.json",
     "ia": "tempestnewvarior0009unse", "ia_stream": "tempestnewvarior0009unse_djvu.txt"},
    {"play": "A Midsummer Night's Dream", "year": 1895, "json": "Public/Data/midsummer_nights_dream.json",
     "ia": "newvariorumediti07shak", "ia_stream": "newvariorumediti07shak_djvu.txt"},
    {"play": "The Winter's Tale", "year": 1898, "json": "Public/Data/the_winters_tale.json",
     "ia": "winterstale0007unse", "ia_stream": "winterstale0007unse_djvu.txt"},
    {"play": "Much Ado About Nothing", "year": 1899, "json": "Public/Data/much_ado_about_nothing.json",
     "ia": "in.ernet.dli.2015.94001", "ia_stream": "2015.94001.A-New-Variorum-Edition-Of-Shakespearemuch-Adoe-About-Nothingvol12ed2_djvu.txt"},
    {"play": "Twelfth Night", "year": 1901, "json": "Public/Data/twelfth_night.json",
     "ia": "newvariorumediti11shak", "ia_stream": "newvariorumediti11shak_djvu.txt"},
    {"play": "Love's Labour's Lost", "year": 1904, "json": "Public/Data/loves_labours_lost.json",
     "ia": "newvariorumediti12shak", "ia_stream": "newvariorumediti12shak_djvu.txt"},
    {"play": "Antony and Cleopatra", "year": 1907, "json": "Public/Data/antony_and_cleopatra.json",
     "ia": "tragedieofanthon0000hora", "ia_stream": "tragedieofanthon0000hora_djvu.txt"},
    {"play": "Richard III", "year": 1908, "json": "Public/Data/richard_iii.json",
     "ia": "newvariorumediti15shak", "ia_stream": "newvariorumediti15shak_djvu.txt"},
    {"play": "Julius Caesar", "year": 1913, "json": "Public/Data/julius_caesar.json",
     "ia": "newvariorumediti16shak", "ia_stream": "newvariorumediti16shak_djvu.txt"},
    {"play": "Cymbeline", "year": 1913, "json": "Public/Data/cymbeline.json",
     "ia": "unset0000unse_m8h0", "ia_stream": "unset0000unse_m8h0_djvu.txt"},
    {"play": "King John", "year": 1919, "json": "Public/Data/king_john.json",
     "ia": "in.ernet.dli.2015.262202", "ia_stream": "2015.262202.A-New_djvu.txt"},
    {"play": "Coriolanus", "year": 1928, "json": "Public/Data/Coriolanus.json",
     "ia": "tragedieofcoriol0002edit", "ia_stream": "tragedieofcoriol0002edit_djvu.txt"},
    {"play": "Henry IV, Part 1", "year": 1936, "json": "Public/Data/henry_iv_part1.json",
     "ia": "newvariorumediti21shak", "ia_stream": "newvariorumediti21shak_djvu.txt"},
    {"play": "Henry IV, Part 2", "year": 1940, "json": "Public/Data/henry_iv_part2.json",
     "ia": "newvariorumediti23shak", "ia_stream": "newvariorumediti23shak_djvu.txt"},
    {"play": "Troilus and Cressida", "year": 1953, "json": "Public/Data/troilus_and_cressida.json",
     "ia": "newvariorumediti22shak", "ia_stream": "newvariorumediti22shak_djvu.txt"},
]


def is_clipped(note: str) -> bool:
    n = note.strip()
    if not n:
        return False
    if re.search(
        r"\b(to|the|a|an|of|in|that|which|with|for|as|is|are|was|were|be|"
        r"have|has|had|not|but|on|at|from)\s*$",
        n,
        re.I,
    ):
        return True
    if re.search(r"-\s*$", n):
        return True
    if n.count("(") > n.count(")"):
        return True
    if n.rstrip()[-1:] in ";:,":
        return True
    return False


def collect_notes(data: dict) -> list[str]:
    notes: list[str] = []
    for scene, scene_data in data.items():
        if str(scene).startswith("_") or not isinstance(scene_data, dict):
            continue
        for obj in scene_data.values():
            if isinstance(obj, dict) and obj.get("notes"):
                notes.extend(obj["notes"])
    return notes


def structural_metrics(notes: list[str]) -> dict:
    if not notes:
        return {
            "note_strings": 0,
            "avg_len": 0,
            "median_len": 0,
            "pct_under_250": 0,
            "pct_over_800": 0,
            "synthetic_prefix": 0,
            "paraphrase_style": 0,
            "long_nv_style": 0,
            "clipped_notes": 0,
            "clipped_pct": 0.0,
        }
    lens = [len(n) for n in notes]
    synthetic = sum(1 for n in notes if SYNTHETIC_RE.match(n.strip()))
    paraphrase = sum(
        1 for n in notes
        if len(n) < 300 and (" — " in n or "—" in n) and PARAPHRASE_RE.search(n)
    )
    clipped = sum(1 for n in notes if is_clipped(n))
    long_style = sum(1 for n in notes if len(n) > 800)
    return {
        "note_strings": len(notes),
        "avg_len": round(statistics.mean(lens)),
        "median_len": round(statistics.median(lens)),
        "pct_under_250": round(100 * sum(1 for x in lens if x < 250) / len(lens), 1),
        "pct_over_800": round(100 * sum(1 for x in lens if x > 800) / len(lens), 1),
        "synthetic_prefix": synthetic,
        "paraphrase_style": paraphrase,
        "long_nv_style": long_style,
        "clipped_notes": clipped,
        "clipped_pct": round(100 * clipped / len(notes), 2),
    }


def sample_notes(notes: list[str], n: int) -> list[str]:
    if len(notes) <= n:
        return notes
    step = max(1, len(notes) // n)
    return notes[::step][:n]


def assign_tier(metrics: dict, l2: dict | None) -> str:
    if metrics["synthetic_prefix"] > 0 or metrics["paraphrase_style"] > 0:
        return "C"
    if metrics["clipped_pct"] > CLIP_MAX_PCT:
        return "B"
    if l2 is None:
        return "A" if metrics["synthetic_prefix"] == 0 else "B"
    if l2["exact_high_pct"] >= TIER_A_L2_MIN and l2["fail_pct"] == 0:
        return "A"
    if l2["exact_high_pct"] >= TIER_A_L2_MIN:
        return "A"
    return "B"


def audit_play(spec: dict) -> dict:
    path = ROOT / spec["json"]
    if not path.exists():
        return {"play": spec["play"], "error": f"missing {spec['json']}"}

    data = json.loads(path.read_text(encoding="utf-8"))
    notes = collect_notes(data)
    metrics = structural_metrics(notes)
    row = {
        "play": spec["play"],
        "year": spec["year"],
        "json_file": spec["json"],
        "ia_id": spec["ia"],
        **metrics,
    }

    ia_text, ia_meta = fetch_ia_text(spec["ia"], spec["ia_stream"])
    if ia_text is None:
        row["ia_status"] = "fetch_failed"
        row["ia_url"] = ia_meta
        row["ia_sample_n"] = 0
        row["l2_exact_pct"] = None
        row["l2_exact_high_pct"] = None
        row["l2_partial_pct"] = None
        row["l2_fail_pct"] = None
        row["tier"] = assign_tier(metrics, None)
        return row

    row["ia_status"] = "ok"
    row["ia_url"] = ia_meta
    sample = sample_notes(notes, SAMPLE_N) if notes else []
    l2 = score_note_sample(ia_text, sample)
    row["ia_sample_n"] = l2["sample_n"]
    row["l2_exact_pct"] = l2["exact_pct"]
    row["l2_exact_high_pct"] = l2["exact_high_pct"]
    row["l2_partial_pct"] = l2["partial_pct"]
    row["l2_fail_pct"] = l2["fail_pct"]
    row["l2_buckets"] = l2["buckets"]
    # legacy column names for downstream readers
    row["ia_traceable_pct"] = l2["exact_high_pct"]
    row["ia_unverified_pct"] = l2["fail_pct"]
    row["paraphrase_pct"] = round(
        100 * metrics["paraphrase_style"] / max(metrics["note_strings"], 1), 1
    )
    row["tier"] = assign_tier(metrics, l2)
    return row


def build_summary(rows: list[dict]) -> list[dict]:
    summary = []
    for r in rows:
        if r.get("error"):
            continue
        summary.append({
            "play": r["play"],
            "notes": r["note_strings"],
            "avg": r["avg_len"],
            "med": r["median_len"],
            "u250": r["pct_under_250"],
            "o800": r["pct_over_800"],
            "synth": r["synthetic_prefix"],
            "para": r["paraphrase_style"],
            "long": r["long_nv_style"],
            "clipped_pct": r["clipped_pct"],
            "ia_pct": r.get("l2_exact_high_pct"),
            "l2_exact_pct": r.get("l2_exact_pct"),
            "tier": r.get("tier", "?"),
        })
    return summary


def main() -> int:
    rows = [audit_play(spec) for spec in PLAYS]
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    OUT_SUMMARY.write_text(json.dumps(build_summary(rows), indent=2) + "\n", encoding="utf-8")

    headers = [
        "play", "year", "note_strings", "avg_len", "median_len", "pct_under_250",
        "pct_over_800", "synthetic_prefix", "paraphrase_style", "clipped_pct",
        "ia_status", "l2_exact_high_pct", "l2_fail_pct", "tier",
    ]
    lines = [",".join(headers)]
    for r in rows:
        lines.append(",".join(str(r.get(h, "")) for h in headers))
    OUT_CSV.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_SUMMARY}")
    print(f"Wrote {OUT_CSV}\n")
    print(
        f"{'Play':<32} {'Notes':>6} {'Synth':>5} {'L2%':>6} {'Fail':>5} {'Tier':>4}"
    )
    for r in rows:
        if r.get("error"):
            print(f"{r['play']:<32} ERROR: {r['error']}")
            continue
        print(
            f"{r['play']:<32} {r['note_strings']:>6} {r['synthetic_prefix']:>5} "
            f"{str(r.get('l2_exact_high_pct','—')):>6} "
            f"{str(r.get('l2_fail_pct','—')):>5} {r.get('tier','?'):>4}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
