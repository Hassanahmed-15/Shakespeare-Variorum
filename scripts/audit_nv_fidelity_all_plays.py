#!/usr/bin/env python3
"""Audit New Variorum note fidelity across all 22 dramatic NV volumes."""

from __future__ import annotations

import json
import re
import statistics
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "validation" / "nv_fidelity_all_plays.json"
OUT_CSV = ROOT / "validation" / "nv_fidelity_all_plays.csv"
SAMPLE_N = 30

# 22 NV dramatic volumes (Richard II excluded — site lists as forthcoming)
PLAYS = [
    {"play": "Romeo and Juliet", "year": 1871, "json": "Public/Data/romeo_and_juliet.json",
     "ia": "newvariorumediti00shak", "ia_stream": "newvariorumediti00shak_djvu.txt"},
    {"play": "Macbeth", "year": 1873, "json": "Public/Data/macbeth_notes_cleaned_play.json",
     "ia": "newvariorumediti10shak", "ia_stream": "newvariorumediti10shak_djvu.txt"},
    {"play": "Hamlet", "year": 1877, "json": "Public/Data/hamlet_notes (1).json",
     "ia": "newvariorumediti02shak", "ia_stream": "newvariorumediti02shak_djvu.txt"},
    {"play": "King Lear", "year": 1880, "json": "Public/Data/kinglear_notes.json",
     "ia": "newvariorumediti03shak", "ia_stream": "newvariorumediti03shak_djvu.txt"},
    {"play": "Othello", "year": 1886, "json": "Public/Data/othello_notes_folger.json",
     "ia": "newvariorumediti13shak", "ia_stream": "newvariorumediti13shak_djvu.txt"},
    {"play": "The Merchant of Venice", "year": 1888, "json": "Public/Data/merchant_of_venice.json",
     "ia": "newvariorumediti04shak", "ia_stream": "newvariorumediti04shak_djvu.txt"},
    {"play": "As You Like It", "year": 1890, "json": "Public/Data/as_you_like_it.json",
     "ia": "newvariorumediti05shak", "ia_stream": "newvariorumediti05shak_djvu.txt"},
    {"play": "The Tempest", "year": 1892, "json": "Public/Data/the_tempest.json",
     "ia": "newvariorumediti06shak", "ia_stream": "newvariorumediti06shak_djvu.txt"},
    {"play": "A Midsummer Night's Dream", "year": 1895, "json": "Public/Data/midsummer_nights_dream.json",
     "ia": "newvariorumediti07shak", "ia_stream": "newvariorumediti07shak_djvu.txt"},
    {"play": "The Winter's Tale", "year": 1898, "json": "Public/Data/the_winters_tale.json",
     "ia": "newvariorumediti08shak", "ia_stream": "newvariorumediti08shak_djvu.txt"},
    {"play": "Much Ado About Nothing", "year": 1899, "json": "Public/Data/much_ado_about_nothing.json",
     "ia": "newvariorumediti09shak", "ia_stream": "newvariorumediti09shak_djvu.txt"},
    {"play": "Twelfth Night", "year": 1901, "json": "Public/Data/twelfth_night.json",
     "ia": "newvariorumediti11shak", "ia_stream": "newvariorumediti11shak_djvu.txt"},
    {"play": "Love's Labour's Lost", "year": 1904, "json": "Public/Data/loves_labours_lost.json",
     "ia": "newvariorumediti12shak", "ia_stream": "newvariorumediti12shak_djvu.txt"},
    {"play": "Antony and Cleopatra", "year": 1907, "json": "Public/Data/antony_and_cleopatra.json",
     "ia": "newvariorumediti14shak", "ia_stream": "newvariorumediti14shak_djvu.txt"},
    {"play": "Richard III", "year": 1908, "json": "Public/Data/richard_iii.json",
     "ia": "newvariorumediti15shak", "ia_stream": "newvariorumediti15shak_djvu.txt"},
    {"play": "Julius Caesar", "year": 1913, "json": "Public/Data/julius_caesar.json",
     "ia": "newvariorumediti16shak", "ia_stream": "newvariorumediti16shak_djvu.txt"},
    {"play": "Cymbeline", "year": 1913, "json": "Public/Data/cymbeline.json",
     "ia": "newvariorumediti17shak", "ia_stream": "newvariorumediti17shak_djvu.txt"},
    {"play": "King John", "year": 1919, "json": "Public/Data/king_john.json",
     "ia": "newvariorumediti18shak", "ia_stream": "newvariorumediti18shak_djvu.txt"},
    {"play": "Coriolanus", "year": 1928, "json": "Public/Data/Coriolanus.json",
     "ia": "newvariorumediti19shak", "ia_stream": "newvariorumediti19shak_djvu.txt"},
    {"play": "Henry IV, Part 1", "year": 1936, "json": "Public/Data/henry_iv_part1.json",
     "ia": "newvariorumediti21shak", "ia_stream": "newvariorumediti21shak_djvu.txt"},
    {"play": "Henry IV, Part 2", "year": 1940, "json": "Public/Data/henry_iv_part2.json",
     "ia": "newvariorumediti23shak", "ia_stream": "newvariorumediti23shak_djvu.txt"},
    {"play": "Troilus and Cressida", "year": 1953, "json": "Public/Data/troilus_and_cressida.json",
     "ia": "newvariorumediti22shak", "ia_stream": "newvariorumediti22shak_djvu.txt"},
]

SYNTHETIC_RE = re.compile(
    r"^(Editorial note|Annotation|Gloss|Note|Textual|Lexical|Critical note|Dramatic note|Editorial comment):",
    re.I,
)
PARAPHRASE_RE = re.compile(
    r"(notes various|discussion of|Debate among|Explanatory note|On the colloquial|and other editors note)",
    re.I,
)


def alnum(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


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
        }
    lens = [len(n) for n in notes]
    synthetic = sum(1 for n in notes if SYNTHETIC_RE.match(n.strip()))
    paraphrase = sum(
        1 for n in notes
        if len(n) < 300 and (" — " in n or "—" in n) and PARAPHRASE_RE.search(n)
    )
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
    }


def ia_verdict(note: str, ia_alnum: str) -> str:
    frag = alnum(note)
    if len(frag) < 40:
        return "short_lemma"
    for size in (80, 60, 40):
        if len(frag) >= size and frag[:size] in ia_alnum:
            return "ia_traceable"
    if len(note) < 220 and (" — " in note or PARAPHRASE_RE.search(note) or SYNTHETIC_RE.match(note)):
        return "paraphrase"
    return "unverified"


def fetch_ia_alnum(ia_id: str, stream: str) -> tuple[str | None, str | None]:
    url = f"https://archive.org/stream/{ia_id}/{stream}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "nv-fidelity-audit/1.0"})
        with urllib.request.urlopen(req, timeout=90) as resp:
            text = resp.read().decode("utf-8", errors="replace")
        return alnum(text), url
    except Exception as e:
        return None, f"{url} ({e})"


def sample_notes(notes: list[str], n: int) -> list[str]:
    if len(notes) <= n:
        return notes
    step = max(1, len(notes) // n)
    return notes[::step][:n]


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

    ia_alnum, ia_meta = fetch_ia_alnum(spec["ia"], spec["ia_stream"])
    if ia_alnum is None:
        row["ia_status"] = "fetch_failed"
        row["ia_url"] = ia_meta
        row["ia_sample_n"] = 0
        row["ia_traceable_pct"] = None
        row["paraphrase_pct"] = None
        return row

    row["ia_status"] = "ok"
    row["ia_url"] = ia_meta
    sample = sample_notes(notes, SAMPLE_N) if notes else []
    counts = {"ia_traceable": 0, "paraphrase": 0, "unverified": 0, "short_lemma": 0}
    for note in sample:
        counts[ia_verdict(note, ia_alnum)] += 1
    row["ia_sample_n"] = len(sample)
    row["ia_traceable_pct"] = round(100 * counts["ia_traceable"] / len(sample), 1) if sample else None
    row["paraphrase_pct"] = round(100 * counts["paraphrase"] / len(sample), 1) if sample else None
    row["ia_unverified_pct"] = round(100 * counts["unverified"] / len(sample), 1) if sample else None
    row["ia_short_lemma_pct"] = round(100 * counts["short_lemma"] / len(sample), 1) if sample else None
    return row


def main() -> int:
    rows = [audit_play(spec) for spec in PLAYS]
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")

    headers = [
        "play", "year", "note_strings", "avg_len", "median_len", "pct_under_250",
        "pct_over_800", "synthetic_prefix", "paraphrase_style", "ia_status",
        "ia_traceable_pct", "paraphrase_pct", "ia_unverified_pct",
    ]
    lines = [",".join(headers)]
    for r in rows:
        lines.append(",".join(str(r.get(h, "")) for h in headers))
    OUT_CSV.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {OUT_JSON}\nWrote {OUT_CSV}\n")
    print(f"{'Play':<32} {'Notes':>6} {'Avg':>5} {'<250%':>6} {'>800%':>6} {'Synth':>5} {'IA%':>6} {'Para%':>6}")
    for r in rows:
        if r.get("error"):
            print(f"{r['play']:<32} ERROR: {r['error']}")
            continue
        print(
            f"{r['play']:<32} {r['note_strings']:>6} {r['avg_len']:>5} "
            f"{r['pct_under_250']:>6} {r['pct_over_800']:>6} {r['synthetic_prefix']:>5} "
            f"{str(r.get('ia_traceable_pct','—')):>6} {str(r.get('paraphrase_pct','—')):>6}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
