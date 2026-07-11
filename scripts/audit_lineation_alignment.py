#!/usr/bin/env python3
"""Click-simulation lineation audit (Moby reading text → Variorum notes).

Mirrors client note retrieval (findNotesForLine / matchesText in index.html) and
adjudicates returned notes against Internet Archive witness text.

For each JSON line with non-empty `play` and at least one note:
  1. Simulate the user selecting that `play` string in the scene.
  2. Run the same text-matching lookup the UI uses (first numeric line-key match).
  3. Compare the returned line key to the expected key.
  4. Score the returned notes against the play's IA witness (exact/high/partial/fail).

End-to-end pass = correct retrieval AND witness exact or high (>= 0.75).

Outputs:
  validation/nv_lineation_alignment.json
  validation/nv_lineation_alignment.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from nv_ia_witness import (  # noqa: E402
    classify_match,
    fetch_play_witness,
    ia_match_score,
    is_cross_ref_note,
    is_short_gloss,
)
from nv_witness_map import WITNESS_BY_PLAY  # noqa: E402

# Same 22-play set as audit_stage_direction_misclassification.py
PLAY_JSONS = [
    ("Romeo and Juliet", "Public/Data/romeo_and_juliet.json"),
    ("Macbeth", "Public/Data/macbeth_notes_cleaned_play.json"),
    ("Hamlet", "Public/Data/hamlet_notes (1).json"),
    ("King Lear", "Public/Data/kinglear_notes.json"),
    ("Othello", "Public/Data/othello_notes_folger.json"),
    ("The Merchant of Venice", "Public/Data/merchant_of_venice.json"),
    ("As You Like It", "Public/Data/as_you_like_it.json"),
    ("The Tempest", "Public/Data/the_tempest.json"),
    ("A Midsummer Night's Dream", "Public/Data/midsummer_nights_dream.json"),
    ("The Winter's Tale", "Public/Data/the_winters_tale.json"),
    ("Much Ado About Nothing", "Public/Data/much_ado_about_nothing.json"),
    ("Twelfth Night", "Public/Data/twelfth_night.json"),
    ("Love's Labour's Lost", "Public/Data/loves_labours_lost.json"),
    ("Antony and Cleopatra", "Public/Data/antony_and_cleopatra.json"),
    ("Richard III", "Public/Data/richard_iii.json"),
    ("Julius Caesar", "Public/Data/julius_caesar.json"),
    ("Cymbeline", "Public/Data/cymbeline.json"),
    ("King John", "Public/Data/king_john.json"),
    ("Coriolanus", "Public/Data/Coriolanus.json"),
    ("Henry IV, Part 1", "Public/Data/henry_iv_part1.json"),
    ("Henry IV, Part 2", "Public/Data/henry_iv_part2.json"),
    ("Troilus and Cressida", "Public/Data/troilus_and_cressida.json"),
]

OUT_JSON = ROOT / "validation" / "nv_lineation_alignment.json"
OUT_MD = ROOT / "validation" / "nv_lineation_alignment.md"

HIGH_THRESHOLD = 0.75


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


def sort_line_keys(keys: list[str]) -> list[str]:
    def key_fn(k: str) -> tuple[int, str]:
        try:
            return (0, f"{int(k):08d}")
        except ValueError:
            return (1, k)

    return sorted(keys, key=key_fn)


def resolve_scene(data: dict, scene_name: str) -> tuple[str, dict] | None:
    scene = data.get(scene_name)
    if isinstance(scene, dict):
        return scene_name, scene
    target = normalize_ws(scene_name).upper()
    for k, v in data.items():
        if not str(k).startswith("ACT") or not isinstance(v, dict):
            continue
        if normalize_ws(k).upper() == target:
            return k, v
        if k.replace(" ", "").upper() == scene_name.replace(" ", "").upper():
            return k, v
    return None


def client_find_notes(
    data: dict, text: str, scene_name: str
) -> dict | None:
    """First-match lookup in numeric line-key order (V8 integer-key ordering)."""
    resolved = resolve_scene(data, scene_name)
    if not resolved:
        return None
    scene_key, scene = resolved
    for line_key in sort_line_keys([k for k in scene if not str(k).startswith("_")]):
        line_data = scene.get(line_key)
        if not isinstance(line_data, dict):
            continue
        play = line_data.get("play")
        if isinstance(play, str) and play.strip() and matches_text(play, text):
            return {
                "scene": scene_key,
                "line_key": str(line_key),
                "play": play,
                "notes": list(line_data.get("notes") or []),
            }
    return None


def all_text_matches(scene: dict, text: str) -> list[str]:
    hits: list[str] = []
    for line_key in sort_line_keys([k for k in scene if not str(k).startswith("_")]):
        line_data = scene.get(line_key)
        if not isinstance(line_data, dict):
            continue
        play = line_data.get("play")
        if isinstance(play, str) and play.strip() and matches_text(play, text):
            hits.append(str(line_key))
    return hits


def witness_tier(note: str, ia_text: str | None) -> str:
    if is_cross_ref_note(note):
        return "exact"
    if is_short_gloss(note):
        return "high"
    if ia_text is None:
        return "no_witness"
    return classify_match(ia_match_score(ia_text, note))


def score_notes(
    notes: list[str], ia_text: str | None, cache: dict[str, str]
) -> str:
    """Primary (first) note witness tier; cached by note text."""
    if not notes:
        return "no_notes"
    note = notes[0]
    if note not in cache:
        cache[note] = witness_tier(note, ia_text)
    return cache[note]


def pct(n: int, d: int) -> float | None:
    return round(100.0 * n / d, 4) if d else None


def audit_play(play_name: str, json_path: Path, ia_text: str | None) -> dict:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    counts: Counter[str] = Counter()
    examples: dict[str, list] = defaultdict(list)

    # Pass 1: collect rows; pass 2: apply witness tiers from unique-note cache.
    rows: list[dict] = []
    unique_notes: set[str] = set()

    for scene_key, scene in data.items():
        if str(scene_key).startswith("_") or scene_key == "DRAMATIS PERSONAE":
            continue
        if not isinstance(scene, dict):
            continue

        for line_key in sort_line_keys([k for k in scene if not str(k).startswith("_")]):
            line_data = scene.get(line_key)
            if not isinstance(line_data, dict):
                continue
            notes = line_data.get("notes") or []
            play = (line_data.get("play") or "").strip()
            if not notes:
                continue
            counts["lines_with_notes"] += 1

            if not play:
                counts["empty_play_with_notes"] += 1
                continue

            counts["clickable_lines"] += 1
            expected_key = str(line_key)
            hits = all_text_matches(scene, play)

            if len(hits) > 1:
                counts["duplicate_play_text_in_scene"] += 1
                note_sets = {
                    tuple(scene[h].get("notes") or []) for h in hits if h in scene
                }
                if len(note_sets) > 1:
                    counts["duplicate_play_different_notes"] += 1

            found = client_find_notes(data, play, scene_key)
            if found is None:
                bucket = "retrieval_no_match"
            elif found["line_key"] == expected_key:
                bucket = "retrieval_correct_key"
            else:
                same_notes = found["notes"] == list(notes)
                bucket = (
                    "retrieval_wrong_key_same_notes"
                    if same_notes
                    else "retrieval_wrong_key_different_notes"
                )

            retrieved_notes = found["notes"] if found else []
            if retrieved_notes:
                unique_notes.add(retrieved_notes[0])

            rows.append(
                {
                    "scene_key": scene_key,
                    "expected_key": expected_key,
                    "bucket": bucket,
                    "found": found,
                    "play": play,
                    "notes": notes,
                    "retrieved_notes": retrieved_notes,
                }
            )

    witness_cache: dict[str, str] = {}
    for i, note in enumerate(sorted(unique_notes), 1):
        witness_cache[note] = witness_tier(note, ia_text)
        if i % 500 == 0:
            print(f"  {play_name}: witness-scored {i}/{len(unique_notes)} unique notes", flush=True)

    for row in rows:
        bucket = row["bucket"]
        counts[bucket] += 1
        retrieved_notes = row["retrieved_notes"]
        tier = score_notes(retrieved_notes, ia_text, witness_cache)
        counts[f"witness_{tier}"] += 1

        if bucket == "retrieval_correct_key" and tier in ("exact", "high"):
            counts["e2e_pass"] += 1
        elif bucket.startswith("retrieval_wrong") or bucket == "retrieval_no_match":
            counts["e2e_retrieval_fail"] += 1
        elif tier in ("exact", "high"):
            counts["e2e_pass"] += 1
        elif tier == "partial":
            counts["e2e_witness_partial"] += 1
        else:
            counts["e2e_witness_fail"] += 1

        if bucket in (
            "retrieval_wrong_key_different_notes",
            "retrieval_no_match",
        ) and len(examples[bucket]) < 3:
            found = row["found"]
            examples[bucket].append(
                {
                    "scene": row["scene_key"],
                    "expected_line": row["expected_key"],
                    "returned_line": found["line_key"] if found else None,
                    "play": row["play"][:120],
                    "expected_note_snip": (row["notes"][0] or "")[:120],
                    "returned_note_snip": (
                        (retrieved_notes[0] if retrieved_notes else "")[:120]
                    ),
                }
            )

    clickable = counts["clickable_lines"]
    return {
        "play": play_name,
        "json": str(json_path.relative_to(ROOT)),
        "has_witness": ia_text is not None,
        "counts": dict(counts),
        "rates": {
            "retrieval_correct_pct": pct(counts["retrieval_correct_key"], clickable),
            "retrieval_wrong_key_different_notes_pct": pct(
                counts["retrieval_wrong_key_different_notes"], clickable
            ),
            "e2e_pass_pct": pct(counts["e2e_pass"], clickable),
            # Diagnostic: lines belonging to in-scene duplicate play-text groups (not all fail retrieval).
            "duplicate_play_different_notes_pct": pct(
                counts["duplicate_play_different_notes"], clickable
            ),
        },
        "examples": dict(examples),
    }


def build_markdown(summary: dict, per_play: list[dict]) -> str:
    c = summary["corpus_counts"]
    clickable = c["clickable_lines"]
    lines = [
        "# Lineation alignment audit (click simulation + witness)",
        "",
        f"Generated audit mirroring `findNotesForLine` / `matchesText` in `index.html`.",
        "",
        "## Corpus summary",
        "",
        f"- Plays audited: **{summary['plays_audited']}**",
        f"- Clickable lines (non-empty `play` + ≥1 note): **{clickable:,}**",
        f"- Empty `play` with notes (not clickable): **{c.get('empty_play_with_notes', 0):,}**",
        "",
        "### Layer 1 — Click retrieval (same JSON line key)",
        "",
        f"- Correct key: **{c['retrieval_correct_key']:,}** ({summary['rates']['retrieval_correct_pct']:.2f}%)",
        f"- Wrong key (same notes): **{c.get('retrieval_wrong_key_same_notes', 0):,}**",
        f"- Wrong key (different notes): **{c.get('retrieval_wrong_key_different_notes', 0):,}** "
        f"({summary['rates']['retrieval_wrong_key_different_notes_pct']:.2f}% of clickable)",
        f"- Lines in duplicate-text groups (diagnostic): **{c.get('duplicate_play_different_notes', 0):,}** "
        f"({summary['rates']['duplicate_play_different_notes_pct']:.2f}% of clickable; not all mis-retrieve)",
        f"- No text match: **{c.get('retrieval_no_match', 0):,}**",
        f"- Duplicate `play` text in scene: **{c.get('duplicate_play_text_in_scene', 0):,}**",
        "",
        "### Layer 2 — End-to-end (retrieval + witness on returned notes)",
        "",
        "Pass = notes returned to the user's click are witness **exact** or **high** (≥0.75), "
        "and when retrieval hits the expected key (or wrong-key collision carries identical notes).",
        "",
        f"- **E2E pass: {c['e2e_pass']:,} ({summary['rates']['e2e_pass_pct']:.2f}%)**",
        f"- E2E retrieval fail: **{c.get('e2e_retrieval_fail', 0):,}**",
        f"- E2E witness partial: **{c.get('e2e_witness_partial', 0):,}**",
        f"- E2E witness fail: **{c.get('e2e_witness_fail', 0):,}**",
        "",
        "### Witness tiers (on retrieved notes)",
        "",
    ]
    for tier in ("exact", "high", "partial", "fail", "no_witness"):
        n = c.get(f"witness_{tier}", 0)
        lines.append(f"- {tier}: **{n:,}** ({pct(n, clickable) or 0:.2f}%)")
    lines.extend(["", "## Per-play breakdown", "", "| Play | Clickable | Retrieval OK | E2E pass | Wrong-key (diff notes) |", "|------|----------:|-------------:|---------:|-----------------------:|"])
    for p in sorted(per_play, key=lambda x: x["play"]):
        cc = p["counts"]
        cl = cc.get("clickable_lines", 0)
        lines.append(
            f"| {p['play']} | {cl:,} | {p['rates']['retrieval_correct_pct']:.2f}% | "
            f"{p['rates']['e2e_pass_pct']:.2f}% | {cc.get('retrieval_wrong_key_different_notes', 0):,} |"
        )
    lines.extend(["", "## Sample retrieval failures", ""])
    for p in per_play:
        ex = p.get("examples") or {}
        if not ex:
            continue
        lines.append(f"### {p['play']}")
        for bucket, items in ex.items():
            for item in items:
                lines.append(
                    f"- **{bucket}** {item['scene']} expected line {item['expected_line']} "
                    f"→ returned {item.get('returned_line')}: `{item['play']}`"
                )
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-json", default=str(OUT_JSON))
    parser.add_argument("--out-md", default=str(OUT_MD))
    parser.add_argument(
        "--exclude",
        action="append",
        default=["Othello"],
        metavar="PLAY",
        help="Play title to omit (default: Othello — Folger TEI spine)",
    )
    args = parser.parse_args()

    excluded = set(args.exclude)
    play_list = [(n, p) for n, p in PLAY_JSONS if n not in excluded]

    per_play: list[dict] = []
    corpus: Counter[str] = Counter()

    for play_name, rel_path in play_list:
        path = ROOT / rel_path
        if not path.exists():
            print(f"SKIP missing: {path}")
            continue
        ia_text = None
        if play_name in WITNESS_BY_PLAY:
            ia_text, src = fetch_play_witness(play_name)
            if ia_text is None:
                print(f"WARNING: no witness for {play_name} ({src})")
        result = audit_play(play_name, path, ia_text)
        per_play.append(result)
        corpus.update(result["counts"])
        print(
            f"{play_name}: clickable={result['counts'].get('clickable_lines', 0)} "
            f"retrieval={result['rates']['retrieval_correct_pct']}% "
            f"e2e={result['rates']['e2e_pass_pct']}%"
        )

    clickable = corpus["clickable_lines"]
    summary = {
        "method": (
            "Simulate user click on each JSON `play` line with notes; "
            "findNotesForLine text match (matchesText); "
            "adjudicate returned notes vs IA witness (exact/high >= 0.75)."
        ),
        "plays_audited": len(per_play),
        "plays_excluded": sorted(excluded),
        "corpus_counts": dict(corpus),
        "rates": {
            "retrieval_correct_pct": pct(corpus["retrieval_correct_key"], clickable),
            "retrieval_wrong_key_different_notes_pct": pct(
                corpus["retrieval_wrong_key_different_notes"], clickable
            ),
            "e2e_pass_pct": pct(corpus["e2e_pass"], clickable),
            "duplicate_play_different_notes_pct": pct(
                corpus["duplicate_play_different_notes"], clickable
            ),
        },
    }

    out = {"summary": summary, "per_play": per_play}
    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out_md.write_text(build_markdown(summary, per_play), encoding="utf-8")

    print("\n" + json.dumps(summary["rates"], indent=2))
    print(f"\nWrote {out_json}")
    print(f"Wrote {out_md}")


if __name__ == "__main__":
    main()
