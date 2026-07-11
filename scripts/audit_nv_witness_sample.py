#!/usr/bin/env python3
"""Stratified witness-sample audit: N notes per play, spread across acts.

Compares each sampled note to Internet Archive (or local) witness text using
span anchoring (start + end), not opening-word overlap alone.

Outputs:
  validation/nv_witness_sample/manifest.json
  validation/nv_witness_sample/results.json
  validation/nv_witness_sample/rate_table.md
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_nv_fidelity_all_plays import PLAYS  # noqa: E402
from audit_nv_truncation import is_witness_prefix  # noqa: E402
from nv_ia_witness import (  # noqa: E402
    fetch_ia_text,
    fold_apostrophe,
    ia_match_score,
    is_cross_ref_note,
    is_short_gloss,
    _note_body,
)
from nv_witness_map import LOCAL_WITNESS_BY_PLAY, WITNESS_BY_PLAY, WITNESS_CANDIDATES  # noqa: E402

OUT_DIR = ROOT / "validation" / "nv_witness_sample"
DEFAULT_SAMPLE_N = 50

# Additional cached witnesses for multi-volume plays (beyond WITNESS_CANDIDATES).
EXTRA_WITNESSES: dict[str, list[tuple[str, str]]] = {}

APPARATUS_SPLICE_RE = re.compile(
    r"\d+\.\s+[a-z][\w\s\-']{0,24}\]\s*"
    r"(?:WALKER|POPE|THEOBALD|JOHNSON|MALONE|STEEVENS|CAPELL|HANMER|COLERIDGE|DEL\.|HUNTER)",
    re.I,
)


def parse_act(scene_key: str) -> int:
    m = re.search(r"ACT\s+(\d+)", str(scene_key), re.I)
    return int(m.group(1)) if m else 0


def iter_note_records(data: dict) -> list[dict]:
    rows: list[dict] = []
    for scene, scene_data in data.items():
        if str(scene).startswith("_") or not isinstance(scene_data, dict):
            continue
        act = parse_act(scene)
        for line_num, obj in scene_data.items():
            if not isinstance(obj, dict):
                continue
            for note_idx, note in enumerate(obj.get("notes") or []):
                if not isinstance(note, str) or not note.strip():
                    continue
                rows.append(
                    {
                        "scene": scene,
                        "act": act,
                        "line": str(line_num),
                        "note_idx": note_idx,
                        "note": note,
                        "ref": f"{scene} / line {line_num} / note {note_idx}",
                    }
                )
    return rows


def stratify_sample_by_act(rows: list[dict], n: int) -> list[dict]:
    """Pick up to n notes, spread evenly across acts (at least 1 per act when possible)."""
    if len(rows) <= n:
        return list(rows)

    by_act: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        by_act[row["act"]].append(row)

    acts = sorted(a for a in by_act if a > 0) or sorted(by_act)
    if not acts:
        rows = sorted(rows, key=lambda r: (r["scene"], r["line"], r["note_idx"]))
        step = max(1, len(rows) // n)
        return rows[::step][:n]

    picked: list[dict] = []
    base = n // len(acts)
    extra = n % len(acts)

    for i, act in enumerate(acts):
        quota = base + (1 if i < extra else 0)
        act_rows = sorted(by_act[act], key=lambda r: (r["scene"], r["line"], r["note_idx"]))
        if quota >= len(act_rows):
            picked.extend(act_rows)
            continue
        step = max(1, len(act_rows) // quota)
        for j in range(0, len(act_rows), step):
            picked.append(act_rows[j])
            if sum(1 for p in picked if p["act"] == act) >= quota:
                break

    # Fill any shortfall from remaining pool.
    if len(picked) < n:
        seen = {r["ref"] for r in picked}
        pool = sorted(rows, key=lambda r: (r["act"], r["scene"], r["line"], r["note_idx"]))
        for row in pool:
            if row["ref"] not in seen:
                picked.append(row)
                seen.add(row["ref"])
            if len(picked) >= n:
                break

    picked = sorted(picked, key=lambda r: (r["act"], r["scene"], r["line"], r["note_idx"]))
    return picked[:n]


def witness_specs(play: str, default_ia: str, default_stream: str) -> list[tuple[str, str]]:
    specs: list[tuple[str, str]] = []
    local = LOCAL_WITNESS_BY_PLAY.get(play)
    if local is not None:
        specs.append((f"local:{local.name}", str(local)))
    primary = WITNESS_BY_PLAY.get(play, (default_ia, default_stream))
    specs.append(primary)
    for item in WITNESS_CANDIDATES.get(play, []):
        if item not in specs:
            specs.append(item)
    for item in EXTRA_WITNESSES.get(play, []):
        if item not in specs:
            specs.append(item)
    # de-dupe preserving order
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str]] = []
    for item in specs:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def load_witnesses(play: str, default_ia: str, default_stream: str) -> list[tuple[str, str]]:
    loaded: list[tuple[str, str]] = []
    for ia_id, stream in witness_specs(play, default_ia, default_stream):
        if stream.startswith("/") or stream.startswith(str(ROOT)):
            path = Path(stream)
            if path.is_file():
                text = path.read_text(encoding="utf-8", errors="replace")
                loaded.append((ia_id, text))
            continue
        text, _src = fetch_ia_text(ia_id, stream)
        if text is not None:
            loaded.append((ia_id, text))
    return loaded


def _words(s: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9']+", fold_apostrophe(s))


def normalize_for_match(s: str) -> str:
    s = fold_apostrophe(s)
    s = re.sub(r"-\s+", "", s)  # de-hyphenate line-break artifacts
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def find_start(folded_ia: str, note: str) -> re.Match[str] | None:
    body = _note_body(note)
    words = _words(body)
    for n_start in (12, 10, 8, 6):
        if len(words) < n_start:
            continue
        start_pat = re.compile(r"\s+".join(re.escape(w) for w in words[:n_start]), re.I)
        sm = start_pat.search(folded_ia)
        if sm:
            return sm
    return None


def _fuzzy_locate(folded_ia: str, note: str) -> int | None:
    """Find approximate note position when strict word-chain match fails (OCR gaps)."""
    body = fold_apostrophe(_note_body(note))

    critic = re.match(r"^([A-Z][A-Za-z .'\-]*(?:\([^)]+\))+)\s*:\s*", body)
    if critic:
        anchor = critic.group(1)
        pos = folded_ia.lower().find(anchor.lower())
        if pos >= 0:
            return pos

    words = [w for w in re.findall(r"[A-Za-z']{4,}", body) if len(w) >= 4][:16]
    for skip in (0, 1, 2):
        chunk = words[skip : skip + 5]
        if len(chunk) < 4:
            continue
        pat = re.compile(r"\s+".join(re.escape(w) for w in chunk), re.I)
        sm = pat.search(folded_ia)
        if sm:
            return sm.start()

    # Last resort: locate a distinctive 30-char substring from the note body.
    for size in (80, 60, 40):
        needle = re.sub(r"\s+", " ", body[:size]).strip()
        if len(needle) < 30:
            continue
        pos = folded_ia.lower().find(needle.lower())
        if pos >= 0:
            return pos
    return None


def locate_note(folded_ia: str, note: str) -> int | None:
    sm = find_start(folded_ia, note)
    if sm:
        return sm.start()
    return _fuzzy_locate(folded_ia, note)


def find_span(folded_ia: str, note: str) -> tuple[int, int] | None:
    sm = find_start(folded_ia, note)
    if sm is None:
        return None

    words = _words(_note_body(note))
    search_to = sm.start() + max(len(note) * 2, 1200)
    for n_end in (12, 10, 8, 6):
        if len(words) < n_end:
            continue
        end_words = words[-n_end:]
        end_pat = re.compile(r"\s+".join(re.escape(w) for w in end_words), re.I)
        em = end_pat.search(folded_ia, sm.start(), search_to)
        if em:
            return sm.start(), em.end()
    return None


def word_bag_overlap(a: str, b: str) -> float:
    wa = {w for w in normalize_for_match(a).split() if len(w) >= 3}
    wb = {w for w in normalize_for_match(b).split() if len(w) >= 3}
    if not wa:
        return 0.0
    return len(wa & wb) / len(wa)


def has_apparatus_splice(note: str) -> bool:
    if len(note) < 250:
        return False
    return bool(APPARATUS_SPLICE_RE.search(note[150:]))


def classify_note(note: str, ia_text: str, *, ia_id: str) -> dict:
    if is_cross_ref_note(note) or is_short_gloss(note):
        return {
            "verdict": "exempt",
            "reason": "cross_ref_or_gloss",
            "witness_id": ia_id,
        }

    folded = fold_apostrophe(ia_text)
    note_folded = fold_apostrophe(note)

    if has_apparatus_splice(note):
        return {
            "verdict": "defective",
            "reason": "apparatus_splice",
            "witness_id": ia_id,
        }

    start_match = find_start(folded, note)
    start = start_match.start() if start_match else locate_note(folded, note)
    if start is None:
        score = ia_match_score(ia_text, note)
        if score >= 0.75:
            return {
                "verdict": "uncertain",
                "reason": "anchor_only",
                "score": round(score, 3),
                "witness_id": ia_id,
            }
        return {
            "verdict": "defective",
            "reason": "not_in_witness",
            "score": round(score, 3),
            "witness_id": ia_id,
        }

    start_pos = start
    span = find_span(folded, note)
    if span is not None:
        witness_seg = folded[span[0] : span[1]]
    else:
        win_len = int(len(note) * 1.2) + 80
        witness_seg = folded[start_pos : start_pos + win_len]

    overlap = word_bag_overlap(note_folded, witness_seg)
    ratio = len(normalize_for_match(note_folded)) / max(len(normalize_for_match(witness_seg)), 1)

    if is_witness_prefix(folded, note):
        return {
            "verdict": "defective",
            "reason": "truncated",
            "overlap": round(overlap, 3),
            "witness_id": ia_id,
        }

    if ratio > 1.35 and overlap < 0.85:
        return {
            "verdict": "defective",
            "reason": "extra_content",
            "overlap": round(overlap, 3),
            "length_ratio": round(ratio, 3),
            "witness_id": ia_id,
        }

    if overlap >= 0.80:
        return {
            "verdict": "faithful",
            "reason": "span_match" if span else "window_match",
            "overlap": round(overlap, 3),
            "witness_id": ia_id,
        }
    if overlap >= 0.60:
        return {
            "verdict": "ocr_ok",
            "reason": "ocr_tolerance",
            "overlap": round(overlap, 3),
            "witness_id": ia_id,
        }
    return {
        "verdict": "defective",
        "reason": "text_drift",
        "overlap": round(overlap, 3),
        "witness_id": ia_id,
    }


VERDICT_RANK = {
    "faithful": 5,
    "ocr_ok": 4,
    "exempt": 3,
    "uncertain": 2,
    "defective": 1,
}


def best_classify(note: str, witnesses: list[tuple[str, str]]) -> dict:
    if not witnesses:
        return {"verdict": "defective", "reason": "no_witness", "witness_id": None}

    results = [classify_note(note, text, ia_id=wid) for wid, text in witnesses]
    if any(r["verdict"] == "exempt" for r in results):
        return next(r for r in results if r["verdict"] == "exempt")

    # Prefer the witness with highest word overlap (handles multi-volume plays).
    scored = [r for r in results if r.get("overlap") is not None]
    if scored:
        best = max(scored, key=lambda r: (VERDICT_RANK.get(r["verdict"], 0), r.get("overlap", 0)))
    else:
        results.sort(key=lambda r: (VERDICT_RANK.get(r["verdict"], 0), r.get("score", 0)), reverse=True)
        best = results[0]
    best["candidates"] = len(results)
    return best


def audit_play(spec: dict, sample_n: int) -> dict:
    path = ROOT / spec["json"]
    if not path.is_file():
        return {"play": spec["play"], "error": f"missing {spec['json']}"}

    data = json.loads(path.read_text(encoding="utf-8"))
    all_rows = iter_note_records(data)
    sample = stratify_sample_by_act(all_rows, sample_n)
    witnesses = load_witnesses(spec["play"], spec["ia"], spec["ia_stream"])

    counts = defaultdict(int)
    by_act: dict[int, defaultdict] = defaultdict(lambda: defaultdict(int))
    details = []

    for row in sample:
        result = best_classify(row["note"], witnesses)
        verdict = result["verdict"]
        counts[verdict] += 1
        by_act[row["act"]][verdict] += 1
        details.append(
            {
                "ref": row["ref"],
                "act": row["act"],
                "len": len(row["note"]),
                **result,
            }
        )

    scored = sample_n - counts["exempt"]
    verifiable = sample_n - counts["exempt"] - counts["uncertain"]
    faithful = counts["faithful"]
    ocr_ok = counts["ocr_ok"]
    defective = counts["defective"]
    uncertain = counts["uncertain"]

    return {
        "play": spec["play"],
        "year": spec["year"],
        "json_file": spec["json"],
        "total_notes_in_play": len(all_rows),
        "sample_n": len(sample),
        "acts_represented": sorted({r["act"] for r in sample}),
        "witness_ids": [w[0] for w in witnesses],
        "counts": dict(counts),
        "strict_accuracy_pct": round(100 * faithful / scored, 1) if scored else None,
        "lenient_accuracy_pct": round(100 * (faithful + ocr_ok) / scored, 1) if scored else None,
        "defective_pct": round(100 * defective / scored, 1) if scored else None,
        "uncertain_pct": round(100 * uncertain / scored, 1) if scored else None,
        "verifiable_n": verifiable,
        "strict_among_verifiable_pct": round(100 * faithful / verifiable, 1) if verifiable else None,
        "lenient_among_verifiable_pct": round(100 * (faithful + ocr_ok) / verifiable, 1) if verifiable else None,
        "defective_among_verifiable_pct": round(100 * defective / verifiable, 1) if verifiable else None,
        "exempt_n": counts["exempt"],
        "by_act": {str(k): dict(v) for k, v in sorted(by_act.items())},
        "sample": details,
    }


def corpus_summary(rows: list[dict]) -> dict:
    ok_rows = [r for r in rows if not r.get("error")]
    total_sample = sum(r["sample_n"] for r in ok_rows)
    total_scored = sum(r["sample_n"] - r.get("exempt_n", 0) for r in ok_rows)
    faithful = sum(r["counts"].get("faithful", 0) for r in ok_rows)
    ocr_ok = sum(r["counts"].get("ocr_ok", 0) for r in ok_rows)
    defective = sum(r["counts"].get("defective", 0) for r in ok_rows)
    uncertain = sum(r["counts"].get("uncertain", 0) for r in ok_rows)
    verifiable = total_scored - uncertain
    exempt = sum(r.get("exempt_n", 0) for r in ok_rows)

    return {
        "plays": len(ok_rows),
        "sample_n": total_sample,
        "scored_n": total_scored,
        "exempt_n": exempt,
        "verifiable_n": verifiable,
        "unverifiable_n": uncertain,
        "faithful_n": faithful,
        "ocr_ok_n": ocr_ok,
        "defective_n": defective,
        "uncertain_n": uncertain,
        "strict_accuracy_pct": round(100 * faithful / total_scored, 1) if total_scored else None,
        "lenient_accuracy_pct": round(100 * (faithful + ocr_ok) / total_scored, 1) if total_scored else None,
        "defective_pct": round(100 * defective / total_scored, 1) if total_scored else None,
        "uncertain_pct": round(100 * uncertain / total_scored, 1) if total_scored else None,
        "unverifiable_pct": round(100 * uncertain / total_scored, 1) if total_scored else None,
        "strict_among_verifiable_pct": round(100 * faithful / verifiable, 1) if verifiable else None,
        "lenient_among_verifiable_pct": round(
            100 * (faithful + ocr_ok) / verifiable, 1
        ) if verifiable else None,
        "defective_among_verifiable_pct": round(100 * defective / verifiable, 1) if verifiable else None,
        "95_ci_verifiable_margin": round(
            1.96
            * (faithful / verifiable * (1 - faithful / verifiable) / verifiable) ** 0.5
            * 100,
            1,
        ) if verifiable else None,
    }


def write_rate_table(rows: list[dict], summary: dict, sample_n: int) -> str:
    lines = [
        f"# NV Witness Sample Audit — {sample_n} notes/play (act-stratified)",
        "",
        f"**Date:** {date.today().isoformat()}",
        f"**Method:** Span-anchored comparison vs Internet Archive OCR witness(es) per play.",
        f"**Sample:** Up to {sample_n} notes per play, spread across acts.",
        "",
        "## Corpus summary (sample estimate)",
        "",
        f"| Metric | Value |",
        f"|--------|------:|",
        f"| Plays | {summary['plays']} |",
        f"| Notes sampled | {summary['sample_n']} |",
        f"| Scored (excl. cross-ref/gloss) | {summary['scored_n']} |",
        f"| Located in witness (verifiable) | {summary['verifiable_n']} ({round(100*summary['verifiable_n']/summary['scored_n'],1)}%) |",
        f"| **Accuracy (verifiable notes, strict)** | **{summary['strict_among_verifiable_pct']}%** |",
        f"| Accuracy (verifiable, + OCR tolerance) | {summary['lenient_among_verifiable_pct']}% |",
        f"| Defective (verifiable only) | {summary['defective_among_verifiable_pct']}% |",
        f"| Unverifiable (witness locate failed) | {summary['unverifiable_pct']}% |",
        f"| Exempt (cross-ref / short gloss) | {summary['exempt_n']} |",
        "",
        "Approx. 95% CI on strict accuracy among verifiable notes: "
        f"±{summary['95_ci_verifiable_margin']} percentage points.",
        "",
        "## Verdict definitions",
        "",
        "- **faithful** — start and end anchored in witness; ≥82% word overlap; no continuation past end",
        "- **ocr_ok** — anchored; 65–82% overlap (likely OCR noise)",
        "- **defective** — truncated, apparatus splice, extra content, text drift, or not in witness",
        "- **uncertain** — opening matches witness but span not confirmed",
        "- **exempt** — cross-reference or short gloss (auto-verifiable form)",
        "",
        "## Per-play results",
        "",
        "| Play | Sampled | Acts | Verifiable | Strict† | Lenient† | Defect† | Unverif. |",
        "|------|--------:|-----:|-----------:|--------:|---------:|--------:|---------:|",
    ]

    for r in sorted(rows, key=lambda x: x.get("play", "")):
        if r.get("error"):
            lines.append(f"| {r['play']} | — | — | ERROR | — | — | — |")
            continue
        acts = len(r.get("acts_represented") or [])
        lines.append(
            f"| {r['play']} | {r['sample_n']} | {acts} | {r.get('verifiable_n', '—')} | "
            f"{r.get('strict_among_verifiable_pct', '—')} | {r.get('lenient_among_verifiable_pct', '—')} | "
            f"{r.get('defective_among_verifiable_pct', '—')} | {r.get('uncertain_pct', '—')} |"
        )

    lines.extend(
        [
            "",
            "† Strict / Lenient / Defect percentages are among **verifiable** notes only.",
            "",
            "## Caveats",
            "",
            "- Rates are **sample estimates**, not a census of all ~23,738 notes.",
            "- Witness text is OCR from Internet Archive scans; lenient bucket absorbs typical OCR variance.",
            "- Multi-volume plays search several cached witnesses; some defects may still hide between volumes.",
            "",
            "Regenerate: `python3 scripts/audit_nv_witness_sample.py`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Stratified NV witness sample audit")
    ap.add_argument("--sample-n", type=int, default=DEFAULT_SAMPLE_N, help="Notes per play (default 50)")
    ap.add_argument("--play", action="append", help="Limit to one or more play titles")
    args = ap.parse_args()

    specs = PLAYS
    if args.play:
        wanted = set(args.play)
        specs = [s for s in PLAYS if s["play"] in wanted]
        if not specs:
            print("No matching plays", file=sys.stderr)
            return 1

    rows = [audit_play(spec, args.sample_n) for spec in specs]
    summary = corpus_summary(rows)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "date": date.today().isoformat(),
        "sample_n_per_play": args.sample_n,
        "method": "act-stratified witness span match",
        "corpus_summary": summary,
        "plays": [
            {
                "play": r["play"],
                "sample_n": r.get("sample_n"),
                "acts_represented": r.get("acts_represented"),
                "strict_accuracy_pct": r.get("strict_accuracy_pct"),
                "lenient_accuracy_pct": r.get("lenient_accuracy_pct"),
                "defective_pct": r.get("defective_pct"),
            }
            for r in rows
            if not r.get("error")
        ],
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / "results.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / "rate_table.md").write_text(write_rate_table(rows, summary, args.sample_n), encoding="utf-8")

    print(f"Wrote {OUT_DIR}/manifest.json")
    print(f"Wrote {OUT_DIR}/results.json")
    print(f"Wrote {OUT_DIR}/rate_table.md\n")
    print(
        f"Corpus sample ({summary['sample_n']} notes, {summary['plays']} plays):\n"
        f"  verifiable:              {summary['verifiable_n']} / {summary['scored_n']} scored\n"
        f"  strict (verifiable):     {summary['strict_among_verifiable_pct']}%\n"
        f"  lenient (verifiable):    {summary['lenient_among_verifiable_pct']}%\n"
        f"  defective (verifiable):  {summary['defective_among_verifiable_pct']}%\n"
        f"  unverifiable:            {summary['unverifiable_pct']}%\n"
    )
    print(f"{'Play':<32} {'Verif':>5} {'Strict':>7} {'Defect':>7} {'Unverif':>8}")
    for r in rows:
        if r.get("error"):
            print(f"{r['play']:<32} ERROR")
            continue
        print(
            f"{r['play']:<32} {r.get('verifiable_n', 0):>5} "
            f"{str(r.get('strict_among_verifiable_pct', '—')):>7} "
            f"{str(r.get('defective_among_verifiable_pct', '—')):>7} "
            f"{str(r.get('uncertain_pct', '—')):>7}%"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
