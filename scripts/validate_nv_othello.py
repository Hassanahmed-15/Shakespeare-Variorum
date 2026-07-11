#!/usr/bin/env python3
"""Othello New Variorum accuracy audit (Levels 1–3 starter).

Level 1: local JSON vs deployed site JSON (corpus fidelity)
Level 2: sample note strings vs Internet Archive plain text (IA fidelity)
Level 3: lines with notes but empty/missing commentary; anchor coverage
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LOCAL_JSON = ROOT / "Public/Data/othello_notes.json"
SITE_URL = "https://newvariorum.com/Public/Data/othello_notes.json"
IA_TXT_URL = "https://archive.org/stream/newvariorumediti13shak/newvariorumediti13shak_djvu.txt"
IA_ITEM = "https://archive.org/details/newvariorumediti13shak"
SAMPLE_SIZE = 40


def normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def normalize_match(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[\[\]:,\s]+", " ", s)
    return normalize_ws(s)


def strip_speaker(s: str) -> str:
    return re.sub(r"^[A-Z][A-Z\s.'-]*:\s*", "", s, flags=re.I).strip()


def matches_text(play_line: str, search_text: str) -> bool:
    """Port of index.html matchesText (client lookup)."""
    np = normalize_match(play_line)
    ns = normalize_match(search_text)
    nps = normalize_match(strip_speaker(play_line))
    nss = normalize_match(strip_speaker(search_text))
    if np == ns:
        return True
    if nps and nps == nss:
        return True
    max_len = max(len(nps), len(nss))
    min_len = min(len(nps), len(nss))
    if max_len > 0 and min_len / max_len > 0.85:
        if nps in nss or nss in nps:
            return True
    return False


def client_find_notes(data: dict, text: str, scene_name: str) -> dict | None:
    scene = data.get(scene_name)
    if not scene:
        for k in data:
            if k.startswith("ACT") and normalize_ws(k).upper() == normalize_ws(scene_name).upper():
                scene = data[k]
                scene_name = k
                break
    if not scene:
        return None
    for line_key, line_data in scene.items():
        if not isinstance(line_data, dict):
            continue
        play = line_data.get("play")
        if play and matches_text(play, text):
            return {
                "scene": scene_name,
                "line_key": line_key,
                "folgerAnchor": line_data.get("folgerAnchor"),
                "play": play,
                "notes": list(line_data.get("notes") or []),
            }
    return None


def server_text_search(data: dict, text: str, limit: int = 10) -> list[dict]:
    """Port of searchAllScenesForText (fallback when no leading line number)."""
    search_lower = text.lower().strip()
    results = []
    for scene_name, scene_data in data.items():
        if scene_name.startswith("_") or not isinstance(scene_data, dict):
            continue
        for line_key, line_data in scene_data.items():
            if not isinstance(line_data, dict):
                continue
            play = line_data.get("play")
            if not isinstance(play, str):
                continue
            pl = play.lower().strip()
            if search_lower in pl or pl in search_lower:
                results.append(
                    {
                        "scene": scene_name,
                        "line_key": line_key,
                        "play": play,
                        "notes": list(line_data.get("notes") or []),
                    }
                )
                if len(results) >= limit:
                    return results
        if len(results) >= limit:
            break
    return results


def iter_note_lines(data: dict) -> list[dict]:
    rows = []
    for scene, scene_data in data.items():
        if scene.startswith("_") or not isinstance(scene_data, dict):
            continue
        for line_key, line_data in scene_data.items():
            if not isinstance(line_data, dict):
                continue
            notes = line_data.get("notes") or []
            if not notes:
                continue
            rows.append(
                {
                    "scene": scene,
                    "line_key": line_key,
                    "folgerAnchor": line_data.get("folgerAnchor"),
                    "play": line_data.get("play", ""),
                    "notes": notes,
                    "note_count": len(notes),
                    "note_chars": sum(len(n) for n in notes),
                }
            )
    return rows


def stratified_sample(rows: list[dict], n: int) -> list[dict]:
    if len(rows) <= n:
        return rows
    rows = sorted(rows, key=lambda r: (r["scene"], r["line_key"]))
    picks = []
    step = max(1, len(rows) // n)
    for i in range(0, len(rows), step):
        picks.append(rows[i])
        if len(picks) >= n:
            break
    # ensure opening soliloquy-ish and heavy-note lines
    for anchor in ("1.1.1", "1.1.2", "3.3.170", "3.3.171"):
        for r in rows:
            if r.get("folgerAnchor") == anchor and r not in picks:
                picks.append(r)
    return picks[:n]


def note_fingerprint(note: str) -> str:
    """First critic tag + 80 chars for IA search."""
    m = re.match(r"^([A-Za-z .'-]+):", note.strip())
    tag = m.group(1) if m else ""
    body = re.sub(r"\s+", " ", note)[:120]
    return f"{tag}|{body}"


def ia_match_score(ia_text: str, note: str) -> float:
    note_clean = re.sub(r"\s+", " ", note.strip())
    if len(note_clean) < 40:
        needle = note_clean[:60]
    else:
        # critic-led substring
        m = re.match(r"^[A-Za-z .'-]+:\s*(.{30,120})", note_clean)
        needle = m.group(1) if m else note_clean[:80]
    needle = needle.strip(" \"'[]")
    if len(needle) < 20:
        return 0.0
    if needle.lower() in ia_text.lower():
        return 1.0
    # fuzzy on sliding windows is expensive; compare to best chunk match via words
    words = [w for w in re.findall(r"[A-Za-z']{4,}", needle.lower())[:12]]
    if not words:
        return 0.0
    ia_low = ia_text.lower()
    hits = sum(1 for w in words if w in ia_low)
    return hits / len(words)


@dataclass
class Level1Result:
    local_note_lines: int
    site_note_lines: int
    json_identical: bool
    json_diff_summary: str
    retrieval_pass: int
    retrieval_fail: int
    failures: list[str]


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "nv-validate/1.0", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def fetch_ia_text() -> str:
    req = urllib.request.Request(IA_TXT_URL, headers={"User-Agent": "nv-validate/1.0"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        return resp.read().decode("utf-8", errors="replace")


def compare_corpus(local: dict, site: dict) -> tuple[bool, str]:
    if local == site:
        return True, "byte-identical after JSON parse"
    # structural compare on note-bearing lines
    diffs = []
    local_rows = {(r["scene"], r["line_key"]): r["notes"] for r in iter_note_lines(local)}
    site_rows = {(r["scene"], r["line_key"]): r["notes"] for r in iter_note_lines(site)}
    if local_rows.keys() != site_rows.keys():
        only_l = len(set(local_rows) - set(site_rows))
        only_s = len(set(site_rows) - set(local_rows))
        diffs.append(f"note-line keys differ (local-only={only_l}, site-only={only_s})")
    changed = 0
    for k in local_rows:
        if k in site_rows and local_rows[k] != site_rows[k]:
            changed += 1
    if changed:
        diffs.append(f"{changed} shared keys with differing notes[]")
    return (not diffs, "; ".join(diffs) if diffs else "identical note payloads")


def run_level1(local: dict, site: dict) -> Level1Result:
    local_rows = iter_note_lines(local)
    site_rows = iter_note_lines(site)
    sample = stratified_sample(local_rows, SAMPLE_SIZE)
    identical, diff_summary = compare_corpus(local, site)
    failures = []
    passed = 0
    for row in sample:
        play = row["play"]
        scene = row["scene"]
        expected_notes = row["notes"]
        client = client_find_notes(local, play, scene)
        server = server_text_search(local, play, limit=1)
        client_notes = (client or {}).get("notes")
        server_notes = (server[0] if server else {}).get("notes")
        ok_client = client_notes == expected_notes
        ok_server = server_notes == expected_notes
        if ok_client and ok_server:
            passed += 1
        else:
            failures.append(
                f"{scene}/{row['line_key']} anchor={row.get('folgerAnchor')} "
                f"client={'OK' if ok_client else 'MISMATCH'} "
                f"server={'OK' if ok_server else 'MISMATCH'}"
            )
    return Level1Result(
        local_note_lines=len(local_rows),
        site_note_lines=len(site_rows),
        json_identical=identical,
        json_diff_summary=diff_summary,
        retrieval_pass=passed,
        retrieval_fail=len(failures),
        failures=failures[:15],
    )


def run_level2(local: dict, ia_text: str, sample_rows: list[dict]) -> dict:
    buckets = {"exact": 0, "high": 0, "partial": 0, "fail": 0}
    examples = []
    for row in sample_rows:
        best = 0.0
        best_note = ""
        for note in row["notes"][:3]:
            sc = ia_match_score(ia_text, note)
            if sc > best:
                best = sc
                best_note = note[:100]
        if best >= 0.95:
            buckets["exact"] += 1
            label = "exact"
        elif best >= 0.75:
            buckets["high"] += 1
            label = "high"
        elif best >= 0.45:
            buckets["partial"] += 1
            label = "partial"
        else:
            buckets["fail"] += 1
            label = "fail"
            examples.append(
                {
                    "anchor": row.get("folgerAnchor"),
                    "play": row["play"][:60],
                    "score": round(best, 2),
                    "note": best_note,
                }
            )
    return {"buckets": buckets, "fail_examples": examples[:8], "ia_chars": len(ia_text)}


def run_level3(local: dict) -> dict:
    total_lines = 0
    with_notes = 0
    empty_play_with_notes = 0
    notes_empty_play = 0
    for scene, scene_data in local.items():
        if scene.startswith("_") or not isinstance(scene_data, dict):
            continue
        for _, line_data in scene_data.items():
            if not isinstance(line_data, dict):
                continue
            total_lines += 1
            notes = line_data.get("notes") or []
            play = (line_data.get("play") or "").strip()
            if notes:
                with_notes += 1
                if not play:
                    empty_play_with_notes += 1
            if play and not notes:
                notes_empty_play += 1
    return {
        "total_spine_lines": total_lines,
        "lines_with_notes": with_notes,
        "lines_with_notes_but_empty_play": empty_play_with_notes,
        "lines_with_play_but_no_notes": notes_empty_play,
        "note_coverage_pct": round(100 * with_notes / total_lines, 2) if total_lines else 0,
    }


def main() -> int:
    print("=== Othello NV Accuracy Audit ===\n")
    local = json.loads(LOCAL_JSON.read_text(encoding="utf-8"))
    print(f"Local corpus: {LOCAL_JSON}")

    print("Fetching deployed JSON …")
    try:
        site = fetch_json(SITE_URL)
        print(f"Site corpus: {SITE_URL}")
    except Exception as e:
        print(f"WARN: could not fetch live site ({e}); Level 1 site compare skipped")
        site = local

    l1 = run_level1(local, site)
    print("\n--- Level 1: Corpus & retrieval fidelity ---")
    print(f"Note-bearing lines (local): {l1.local_note_lines}")
    print(f"Note-bearing lines (site):  {l1.site_note_lines}")
    print(f"Local vs site notes:        {l1.json_diff_summary}")
    print(
        f"Client+server retrieval:    {l1.retrieval_pass}/{l1.retrieval_pass + l1.retrieval_fail} "
        f"passed on {SAMPLE_SIZE}-line stratified sample"
    )
    if l1.failures:
        print("Failures:")
        for f in l1.failures:
            print(f"  - {f}")

    sample = stratified_sample(iter_note_lines(local), SAMPLE_SIZE)
    print("\nFetching Internet Archive plain text …")
    try:
        ia_text = fetch_ia_text()
        l2 = run_level2(local, ia_text, sample)
        print("\n--- Level 2: JSON notes vs IA volume (sample) ---")
        print(f"IA source: {IA_ITEM}")
        print(f"IA text size: {l2['ia_chars']:,} chars")
        b = l2["buckets"]
        total = sum(b.values())
        print(
            f"Note-line matches: exact={b['exact']}, high={b['high']}, "
            f"partial={b['partial']}, fail={b['fail']} (n={total})"
        )
        if l2["fail_examples"]:
            print("Lowest-scoring examples:")
            for ex in l2["fail_examples"]:
                print(f"  - {ex['anchor']} score={ex['score']}: {ex['note']!r}")
    except Exception as e:
        print(f"WARN: IA compare skipped ({e})")
        l2 = None

    l3 = run_level3(local)
    print("\n--- Level 3: Alignment / coverage ---")
    for k, v in l3.items():
        print(f"{k}: {v}")

    out = {
        "play": "othello",
        "level1": l1.__dict__,
        "level2": l2,
        "level3": l3,
        "ia_item": IA_ITEM,
    }
    report_path = ROOT / "validation" / "othello_nv_audit.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
