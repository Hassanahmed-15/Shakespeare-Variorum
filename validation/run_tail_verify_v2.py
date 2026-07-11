#!/usr/bin/env python3
"""One-off batch tail verify -> validation/nv_tail_verify_all_plays_v2.json"""
from __future__ import annotations
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from rapidfuzz import fuzz, process
from audit_nv_fidelity_all_plays import PLAYS
from verify_all_notes import (
    TAIL_LEN_DEFAULT, THRESHOLD_DEFAULT, build_chunks, collect_notes, get_witness, norm,
)

def verify_play(spec):
    play = spec["play"]
    path = ROOT / (spec.get("json_file") or spec.get("json"))
    notes = collect_notes(json.loads(path.read_text(encoding="utf-8")))
    witness_text, witness_src = get_witness(play)
    if witness_text is None:
        return {"play": play, "year": spec.get("year"), "error": "witness unavailable", "notes": len(notes)}
    chunk_texts = [c[0] for c in build_chunks(norm(witness_text), 30, 10)]
    ok = fail = 0
    fail_samples = []
    for item in notes:
        stripped = item["note"].rstrip()
        if stripped.endswith("...") and len(stripped) < 10:
            ok += 1
            continue
        needle = norm(stripped[-TAIL_LEN_DEFAULT:])
        if len(needle) < 20:
            ok += 1
            continue
        result = process.extractOne(needle, chunk_texts, scorer=fuzz.partial_ratio)
        if result is None or result[1] < THRESHOLD_DEFAULT:
            fail += 1
            if len(fail_samples) < 15 and result:
                fail_samples.append(
                    f"  FAIL {item['scene']} | line {item['line']} | note {item['note_idx']} (score={result[1]:.0f})"
                )
        else:
            ok += 1
    n = len(notes)
    return {
        "play": play, "year": spec.get("year"), "notes": n, "ok": ok, "fail": fail,
        "pass_pct": round(100 * ok / n, 2) if n else None, "witness": witness_src,
        "fail_samples": fail_samples,
    }

def main():
    per_play = []
    for i, spec in enumerate(PLAYS, 1):
        print(f"[{i}/{len(PLAYS)}] {spec['play']}...", flush=True)
        per_play.append(verify_play(spec))
    total_notes = sum(p.get("notes", 0) for p in per_play if "error" not in p)
    total_ok = sum(p.get("ok", 0) for p in per_play if "error" not in p)
    total_fail = sum(p.get("fail", 0) for p in per_play if "error" not in p)
    payload = {
        "date": date.today().isoformat(),
        "method": "tail-end fuzzy witness match (last 90 chars, threshold 75)",
        "tail_len": TAIL_LEN_DEFAULT,
        "threshold": THRESHOLD_DEFAULT,
        "plays": len([p for p in per_play if "error" not in p]),
        "total_notes": total_notes,
        "total_ok": total_ok,
        "total_fail": total_fail,
        "corpus_pass_pct": round(100 * total_ok / total_notes, 2) if total_notes else None,
        "per_play": sorted(per_play, key=lambda p: (p.get("pass_pct") or 0, p["play"])),
    }
    out = ROOT / "validation" / "nv_tail_verify_all_plays_v2.json"
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    print(f"Corpus: {total_ok}/{total_notes} = {payload['corpus_pass_pct']}%")

if __name__ == "__main__":
    main()
