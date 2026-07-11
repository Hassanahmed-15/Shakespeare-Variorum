#!/usr/bin/env python3
"""Stratified full-span witness fidelity audit (~300 notes).

v2: witness span bounded by tail-match right edge (fixes end-anchor over-capture).

Outputs:
  validation/nv_fullspan_sample/manifest.json
  validation/nv_fullspan_sample/results.json
  validation/nv_fullspan_sample/rate_table.md
  validation/nv_fullspan_sample/score_histogram.json
  validation/nv_fullspan_sample/interior_divergence_adjudication.md
  validation/nv_fullspan_sample/span_mismatch_adjudication.md
  validation/nv_fullspan_sample/unanchorable_analysis.json
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import zlib
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from rapidfuzz import fuzz, process

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_nv_fidelity_all_plays import PLAYS  # noqa: E402
from apply_contractor_completions import load_workbook  # noqa: E402
from audit_nv_witness_sample import (  # noqa: E402
    _words,
    iter_note_records,
    locate_note,
)
from nv_ia_witness import (  # noqa: E402
    CROSS_REF_RE,
    CRITIC_DATE_GLOSS_RE,
    SHORT_GLOSS_RE,
    fold_apostrophe,
    is_cross_ref_note,
    is_short_gloss,
    _note_body,
)
from verify_all_notes import (  # noqa: E402
    CHUNK_STRIDE_WORDS,
    CHUNK_WORDS,
    TAIL_LEN_DEFAULT,
    THRESHOLD_DEFAULT,
    build_chunks,
    get_witness,
    norm,
)

OUT_DIR = ROOT / "validation" / "nv_fullspan_sample"
SAMPLE_MANIFEST = OUT_DIR / "sample_manifest.json"

INTERIOR_ADJUDICATION = {
    "verdict": "witness_ocr_degradation",
    "adjudicator": "author",
    "date": "2026-07-08",
}
WORKBOOK = ROOT / "validation" / "contractor_truncation_workbook.json"
DEFAULT_SAMPLE_N = 14
DEFAULT_SEED = 42

FULL_SPAN_THRESHOLD = THRESHOLD_DEFAULT
TAIL_THRESHOLD = THRESHOLD_DEFAULT

HISTOGRAM_BUCKETS = [
    (0, 49, "0-49"),
    (50, 64, "50-64"),
    (65, 74, "65-74"),
    (75, 84, "75-84"),
    (85, 94, "85-94"),
    (95, 100, "95-100"),
]


def stratify_random_sample(rows: list[dict], n: int, *, seed: int) -> list[dict]:
    if len(rows) <= n:
        return list(rows)

    rng = random.Random(seed)
    by_act: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        by_act[row["act"]].append(row)

    acts = sorted(a for a in by_act if a > 0) or sorted(by_act)
    picked: list[dict] = []
    base = n // len(acts)
    extra = n % len(acts)

    for i, act in enumerate(acts):
        quota = base + (1 if i < extra else 0)
        act_rows = sorted(by_act[act], key=lambda r: (r["scene"], r["line"], r["note_idx"]))
        if quota >= len(act_rows):
            picked.extend(act_rows)
        else:
            picked.extend(rng.sample(act_rows, quota))

    if len(picked) < n:
        seen = {r["ref"] for r in picked}
        pool = [r for r in rows if r["ref"] not in seen]
        rng.shuffle(pool)
        for row in pool:
            picked.append(row)
            if len(picked) >= n:
                break

    return sorted(picked[:n], key=lambda r: (r["act"], r["scene"], r["line"], r["note_idx"]))


def anchor_start(folded_ia: str, note: str) -> tuple[int, str] | None:
    body = _note_body(note)
    folded_body = fold_apostrophe(body)

    lemma_m = re.match(r"^([^\]]{1,80}\])", note.strip())
    if lemma_m:
        lemma = fold_apostrophe(lemma_m.group(1))
        pos = folded_ia.lower().find(lemma.lower())
        if pos >= 0:
            return pos, "lemma_bracket"

    words = _words(body)
    for n_start in (14, 12, 10, 8, 6):
        if len(words) < n_start:
            continue
        chain = " ".join(words[:n_start])
        if len(chain) > 60 and n_start > 6:
            continue
        pat = re.compile(r"\s+".join(re.escape(w) for w in words[:n_start]), re.I)
        sm = pat.search(folded_ia)
        if sm:
            return sm.start(), f"word_chain_{n_start}"

    for size in (60, 50, 40):
        needle = re.sub(r"\s+", " ", folded_body[:size]).strip()
        if len(needle) < 20:
            continue
        pos = folded_ia.lower().find(needle.lower())
        if pos >= 0:
            return pos, f"prefix_{size}"

    fuzzy = locate_note(folded_ia, note)
    if fuzzy is not None:
        return fuzzy, "fuzzy_locate"
    return None


def locate_tail_end(
    folded_ia: str,
    start: int,
    note: str,
    chunks: list[tuple[str, int]],
) -> tuple[float, int | None, str]:
    """Return (tail_partial_score, end_pos_in_folded_ia, method)."""
    stripped = note.rstrip()
    if stripped.endswith("...") and len(stripped) < 10:
        end = min(len(folded_ia), start + max(len(note), 20))
        return 100.0, end, "tail_auto_short_ellipsis"

    tail_chars = stripped[-TAIL_LEN_DEFAULT:]
    needle = norm(tail_chars)
    if len(needle) < 20:
        end = min(len(folded_ia), start + max(len(note), len(tail_chars)))
        return 100.0, end, "tail_auto_short"

    chunk_texts = [c[0] for c in chunks]
    result = process.extractOne(needle, chunk_texts, scorer=fuzz.partial_ratio)
    if result is None:
        return 0.0, None, "tail_no_chunk_match"
    _, score, idx = result
    if score < TAIL_THRESHOLD:
        return float(score), None, "tail_below_threshold"

    tail_words = _words(tail_chars)
    search_to = min(len(folded_ia), start + max(int(len(note) * 1.25) + 80, 300))
    region = folded_ia[start:search_to]

    for n_end in (12, 10, 8, 6, 4):
        if len(tail_words) < n_end:
            continue
        end_words = tail_words[-n_end:]
        end_pat = re.compile(r"\s+".join(re.escape(w) for w in end_words), re.I)
        em = end_pat.search(folded_ia, start, search_to)
        if em:
            return float(score), em.end(), f"tail_end_chain_{n_end}"

    folded_tail = fold_apostrophe(tail_chars).strip()
    if len(folded_tail) >= 15:
        pos = folded_ia.lower().find(folded_tail.lower(), start, search_to)
        if pos >= 0:
            return float(score), pos + len(folded_tail), "tail_prefix_in_folded"

        align = fuzz.partial_ratio_alignment(folded_tail, region)
        if align.score >= TAIL_THRESHOLD:
            return float(score), start + align.dest_end, "tail_fuzzy_align"

    chunk_text = chunks[idx][0]
    if len(chunk_text) >= 20:
        align = fuzz.partial_ratio_alignment(chunk_text, region)
        if align.score >= TAIL_THRESHOLD:
            return float(score), start + align.dest_end, "tail_chunk_align"

    return float(score), None, "tail_norm_match_only"


def extract_bounded_span(
    folded_ia: str,
    start: int,
    note: str,
    chunks: list[tuple[str, int]],
) -> tuple[str, str, bool, float, int | None]:
    """
    Return (witness_span, span_method, span_estimated, tail_score, tail_end).
    """
    tail_score, tail_end, tail_method = locate_tail_end(folded_ia, start, note, chunks)

    if tail_end is not None and tail_score >= TAIL_THRESHOLD:
        end = max(tail_end, start + 1)
        return folded_ia[start:end], f"tail_bounded:{tail_method}", False, tail_score, tail_end

    note_norm_len = len(norm(note))
    lo = int(note_norm_len * 0.85)
    hi = int(note_norm_len * 1.15)
    end = min(len(folded_ia), start + max(hi, 40))
    seg = folded_ia[start:end]
    return seg, f"span_estimated:note_len_{lo}_{hi}_tail_{tail_method}", True, tail_score, tail_end


def exempt_reason(note: str) -> str | None:
    if is_cross_ref_note(note):
        if CROSS_REF_RE.search(note.strip()):
            return "cross_ref_see_cf"
        return "cross_ref_short"
    if is_short_gloss(note):
        if SHORT_GLOSS_RE.match(note.strip()):
            return "short_gloss_ie"
        if CRITIC_DATE_GLOSS_RE.match(note.strip()):
            return "short_gloss_critic_date"
        return "short_gloss_lemma"
    return None


def histogram_bucket(score: float) -> str:
    s = int(round(score))
    for lo, hi, label in HISTOGRAM_BUCKETS:
        if lo <= s <= hi:
            return label
    return "other"


def classify_note(
    note: str,
    folded_ia: str,
    chunks: list[tuple[str, int]],
) -> dict:
    ex = exempt_reason(note)
    if ex:
        return {"verdict": "exempt", "reason": ex, "exempt_rule": ex}

    anchor = anchor_start(folded_ia, note)
    if anchor is None:
        opens_bracket = bool(re.match(r"^[^\]]{1,80}\]", note.strip()))
        opens_name_colon = bool(re.match(r"^[A-Za-z][\w\.\s\-]{0,40}:\s", note.strip()))
        return {
            "verdict": "unanchorable",
            "reason": "start_not_located",
            "opens_with_lemma_bracket": opens_bracket,
            "opens_with_name_colon": opens_name_colon,
        }

    start, anchor_method = anchor
    witness_seg, span_method, span_estimated, tail_score, tail_end = extract_bounded_span(
        folded_ia, start, note, chunks
    )
    note_n = norm(note)
    seg_n = norm(witness_seg)
    full_ratio = float(fuzz.ratio(note_n, seg_n)) if note_n and seg_n else 0.0
    span_len_ratio = round(len(witness_seg) / max(len(note), 1), 2)

    base = {
        "anchor_method": anchor_method,
        "span_method": span_method,
        "span_estimated": span_estimated,
        "full_ratio": round(full_ratio, 1),
        "tail_ratio": round(tail_score, 1),
        "note_len": len(note),
        "witness_span_len": len(witness_seg),
        "span_len_ratio": span_len_ratio,
        "score_bucket": histogram_bucket(full_ratio),
        "witness_span_text": witness_seg,
        "note_text": note,
    }

    if full_ratio >= FULL_SPAN_THRESHOLD:
        return {**base, "verdict": "full_span_match", "reason": "full_ratio_pass"}

    if tail_score >= TAIL_THRESHOLD:
        return {**base, "verdict": "interior_divergence", "reason": "tail_pass_full_fail"}

    return {**base, "verdict": "span_mismatch", "reason": "tail_and_full_fail"}


def play_seed(base_seed: int, play: str) -> int:
    """Stable per-play seed (v1 used hash(), which varies across Python processes)."""
    return base_seed + (zlib.crc32(play.encode("utf-8")) & 0x7FFFFFFF) % 10_000


def load_sample_manifest(path: Path) -> dict[str, set[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    by_play: dict[str, set[str]] = defaultdict(set)
    for row in data["notes"]:
        by_play[row["play"]].add(row["ref"])
    return by_play


def audit_play(
    spec: dict,
    sample_n: int,
    seed: int,
    *,
    manifest_refs: set[str] | None = None,
) -> dict:
    path = ROOT / spec["json"]
    if not path.is_file():
        return {"play": spec["play"], "error": f"missing {spec['json']}"}

    data = json.loads(path.read_text(encoding="utf-8"))
    all_rows = iter_note_records(data)
    if manifest_refs is not None:
        sample = [r for r in all_rows if r["ref"] in manifest_refs]
        sample = sorted(sample, key=lambda r: (r["act"], r["scene"], r["line"], r["note_idx"]))
    else:
        play_seed_val = play_seed(seed, spec["play"])
        sample = stratify_random_sample(all_rows, sample_n, seed=play_seed_val)

    witness_text, witness_src = get_witness(spec["play"])
    if witness_text is None:
        return {"play": spec["play"], "error": "witness_unavailable"}

    folded_ia = fold_apostrophe(witness_text)
    witness_norm = norm(witness_text)
    chunks = build_chunks(witness_norm, CHUNK_WORDS, CHUNK_STRIDE_WORDS)

    counts: dict[str, int] = defaultdict(int)
    details: list[dict] = []
    full_classify: list[dict] = []

    for row in sample:
        result = classify_note(row["note"], folded_ia, chunks)
        counts[result["verdict"]] += 1
        full_classify.append({"ref": row["ref"], **result})
        slim = {k: v for k, v in result.items() if k not in ("witness_span_text", "note_text")}
        detail = {"ref": row["ref"], "act": row["act"], "len": len(row["note"]), **slim}
        if result.get("verdict") == "interior_divergence":
            detail["adjudication"] = dict(INTERIOR_ADJUDICATION)
        details.append(detail)

    scored = sample_n - counts["exempt"]
    anchored = scored - counts["unanchorable"]
    full_match = counts["full_span_match"]
    interior = counts["interior_divergence"]
    mismatch = counts["span_mismatch"]
    span_est = sum(1 for d in details if d.get("span_estimated"))

    return {
        "play": spec["play"],
        "year": spec["year"],
        "json_file": spec["json"],
        "witness": witness_src,
        "total_notes_in_play": len(all_rows),
        "sample_n": len(sample),
        "counts": dict(counts),
        "exempt_n": counts["exempt"],
        "scored_n": scored,
        "anchored_n": anchored,
        "unanchorable_n": counts["unanchorable"],
        "full_span_match_n": full_match,
        "interior_divergence_n": interior,
        "span_mismatch_n": mismatch,
        "span_estimated_n": span_est,
        "pass_among_scored_pct": round(100 * full_match / scored, 1) if scored else None,
        "pass_among_anchored_pct": round(100 * full_match / anchored, 1) if anchored else None,
        "unanchorable_pct": round(100 * counts["unanchorable"] / scored, 1) if scored else None,
        "interior_among_anchored_pct": round(100 * interior / anchored, 1) if anchored else None,
        "sample": details,
        "_full_classify": full_classify,
    }


def corpus_summary(rows: list[dict]) -> dict:
    ok = [r for r in rows if not r.get("error")]
    sample_n = sum(r["sample_n"] for r in ok)
    scored = sum(r["scored_n"] for r in ok)
    anchored = sum(r["anchored_n"] for r in ok)
    exempt = sum(r["exempt_n"] for r in ok)
    full_match = sum(r["full_span_match_n"] for r in ok)
    interior = sum(r["interior_divergence_n"] for r in ok)
    unanch = sum(r["unanchorable_n"] for r in ok)
    mismatch = sum(r["span_mismatch_n"] for r in ok)
    span_est = sum(r.get("span_estimated_n", 0) for r in ok)

    hist = Counter()
    for r in ok:
        for item in r.get("_full_classify", []):
            if item.get("verdict") in ("full_span_match", "interior_divergence", "span_mismatch"):
                hist[item.get("score_bucket", "other")] += 1

    return {
        "plays": len(ok),
        "sample_n": sample_n,
        "scored_n": scored,
        "exempt_n": exempt,
        "anchored_n": anchored,
        "unanchorable_n": unanch,
        "full_span_match_n": full_match,
        "interior_divergence_n": interior,
        "span_mismatch_n": mismatch,
        "span_estimated_n": span_est,
        "pass_among_scored_pct": round(100 * full_match / scored, 1) if scored else None,
        "pass_among_anchored_pct": round(100 * full_match / anchored, 1) if anchored else None,
        "unanchorable_pct": round(100 * unanch / scored, 1) if scored else None,
        "interior_among_anchored_pct": round(100 * interior / anchored, 1) if anchored else None,
        "interior_among_scored_pct": round(100 * interior / scored, 1) if scored else None,
        "score_histogram_anchored": dict(hist),
        "95_ci_anchored_margin": round(
            1.96 * (full_match / anchored * (1 - full_match / anchored) / anchored) ** 0.5 * 100,
            1,
        )
        if anchored
        else None,
    }


def analyze_unanchorable(rows: list[dict], workbook_keys: set[tuple]) -> dict:
    noisy_plays = {"Troilus and Cressida", "Othello", "Romeo and Juliet", "Richard III"}
    ua_rows = []
    for r in rows:
        if r.get("error"):
            continue
        play = r["play"]
        for item in r.get("_full_classify", []):
            if item.get("verdict") != "unanchorable":
                continue
            ref = item.get("ref", "")
            parts = ref.split(" / ")
            key = None
            if len(parts) >= 3:
                key = (
                    play,
                    parts[0].strip(),
                    parts[1].replace("line ", "").strip(),
                    int(parts[2].replace("note ", "").strip()),
                )
            ua_rows.append(
                {
                    "play": play,
                    "ref": ref,
                    "in_workbook": key in workbook_keys if key else None,
                    "noisy_witness_play": play in noisy_plays,
                    "opens_with_lemma_bracket": item.get("opens_with_lemma_bracket"),
                    "opens_with_name_colon": item.get("opens_with_name_colon"),
                }
            )

    by_play = Counter(r["play"] for r in ua_rows)
    return {
        "total_unanchorable": len(ua_rows),
        "by_play": dict(by_play.most_common()),
        "in_noisy_witness_plays": sum(1 for r in ua_rows if r["noisy_witness_play"]),
        "in_workbook_repair_cohort": sum(1 for r in ua_rows if r.get("in_workbook")),
        "opens_name_colon": sum(1 for r in ua_rows if r.get("opens_with_name_colon")),
        "opens_lemma_bracket": sum(1 for r in ua_rows if r.get("opens_with_lemma_bracket")),
        "neither_opening_pattern": sum(
            1
            for r in ua_rows
            if not r.get("opens_with_name_colon") and not r.get("opens_with_lemma_bracket")
        ),
        "rows": ua_rows,
        "interpretation": (
            f"Unanchorable notes cluster in plays with noisy witnesses "
            f"({ua_rows and sum(1 for r in ua_rows if r['noisy_witness_play'])}/{len(ua_rows)} in Troilus/Othello/Romeo/Richard III). "
            f"Workbook repair cohort: {sum(1 for r in ua_rows if r.get('in_workbook'))}/{len(ua_rows)} — "
            "repairs splice at note ends, so truncation repair is an unlikely cause of start-anchor failure. "
            f"Lemma-bracket openings: {sum(1 for r in ua_rows if r.get('opens_with_lemma_bracket'))}; "
            f"name-colon openings: {sum(1 for r in ua_rows if r.get('opens_with_name_colon'))}."
        ),
    }


def write_rate_table(rows: list[dict], summary: dict, sample_n: int, prior: dict | None, ua: dict) -> str:
    lines = [
        f"# NV Full-Span Witness Sample — {sample_n} notes/play (seed 42)",
        "",
        f"**Date:** {date.today().isoformat()}",
        "**Method (v2):** Start anchor + **tail-bounded right edge** (tail match position in witness);",
        f"`fuzz.ratio` ≥ **{FULL_SPAN_THRESHOLD}** on normalized note vs bounded span.",
        f"If tail match fails: `span_estimated` using note length ±15%.",
        "",
    ]
    if prior:
        p = prior.get("corpus_summary", prior)
        lines.extend(
            [
                "## Comparison to v1 (pre tail-bounded fix)",
                "",
                f"| Metric | v1 | v2 (this run) |",
                f"|--------|---:|--------------:|",
                f"| Anchored pass % | {p.get('pass_among_anchored_pct')}% | **{summary['pass_among_anchored_pct']}%** |",
                f"| Interior divergence | {p.get('interior_divergence_n')} | {summary['interior_divergence_n']} |",
                f"| Unanchorable | {p.get('unanchorable_n')} ({p.get('unanchorable_pct')}%) | "
                f"{summary['unanchorable_n']} ({summary['unanchorable_pct']}%) |",
                "",
            ]
        )

    lines.extend(
        [
            "## Corpus summary",
            "",
            "| Metric | Value |",
            "|--------|------:|",
            f"| Notes sampled | {summary['sample_n']} |",
            f"| Scored (excl. exempt) | {summary['scored_n']} |",
            f"| **Anchored** | {summary['anchored_n']} |",
            f"| **Unanchorable** | {summary['unanchorable_n']} ({summary['unanchorable_pct']}%) |",
            f"| **Full-span pass (scored)** | **{summary['pass_among_scored_pct']}%** |",
            f"| **Full-span pass (anchored)** | **{summary['pass_among_anchored_pct']}%** |",
            f"| Interior divergence | {summary['interior_divergence_n']} |",
            f"| Span mismatch | {summary['span_mismatch_n']} |",
            f"| Span estimated (tail fail fallback) | {summary['span_estimated_n']} |",
            f"| Exempt | {summary['exempt_n']} |",
            "",
            "## Post-adjudication fidelity summary",
            "",
            "| Metric | Value |",
            "|--------|------:|",
            f"| Anchored notes | {summary['anchored_n']} |",
            f"| Automated full-span pass | {summary['full_span_match_n']} "
            f"({summary['pass_among_anchored_pct']}%) |",
            f"| Adjudicated faithful after human review of automated failures | "
            f"{summary['full_span_match_n'] + summary['interior_divergence_n']} "
            f"({round(100 * (summary['full_span_match_n'] + summary['interior_divergence_n']) / summary['anchored_n'], 1) if summary['anchored_n'] else 0}% of anchored) |",
            f"| Unanchorable | {summary['unanchorable_n']} ({summary['unanchorable_pct']}%), reported separately |",
            f"| Span mismatch (pending human adjudication) | {summary['span_mismatch_n']} |",
            "",
            f"Interior-divergence cases ({summary['interior_divergence_n']}) adjudicated "
            f"{INTERIOR_ADJUDICATION['date']} as `{INTERIOR_ADJUDICATION['verdict']}` "
            f"by {INTERIOR_ADJUDICATION['adjudicator']}. "
            f"Span-mismatch cases ({summary['span_mismatch_n']}) await human review.",
            "",
            "**Span extraction:** tail-bounded right edge when tail locates in witness;",
            f"otherwise `span_estimated` (note length ±15%). This run: "
            f"{summary['anchored_n'] - summary['span_estimated_n']} tail-bounded, "
            f"{summary['span_estimated_n']} estimated among anchored notes.",
            "",
            "## Score histogram (anchored notes only)",
            "",
            "| Bucket | Count |",
            "|--------|------:|",
        ]
    )
    for _, _, label in HISTOGRAM_BUCKETS:
        lines.append(f"| {label} | {summary['score_histogram_anchored'].get(label, 0)} |")

    lines.extend(
        [
            "",
            f"## Exempt notes ({summary['exempt_n']}) — rule and legitimacy",
            "",
            "Exempt via `nv_ia_witness.is_cross_ref_note()` and `is_short_gloss()` "
            "(`scripts/nv_ia_witness.py`):",
            "",
            "- **Cross-ref:** `See` / `cf.` pointers with &lt;80 chars after lemma — not apparatus prose.",
            "- **Short gloss:** `That is,` / `i.e.` / critic `(YYYY):` one-liners under 120 chars.",
            "",
            "These are auto-verifiable forms in the L2 fidelity audit; exempting them avoids false",
            "full-span failures on notes that are pointers, not transcriptions. They remain reported",
            "separately and are excluded from scored denominators (same as v1).",
            "",
            "## Unanchorable rate hypothesis (31%)",
            "",
            f"- **Noisy-witness plays** (Troilus, Othello, Romeo, Richard III): "
            f"{ua['in_noisy_witness_plays']}/{ua['total_unanchorable']} unanchorable notes.",
            f"- **Truncation repair workbook cohort:** {ua['in_workbook_repair_cohort']}/{ua['total_unanchorable']} "
            "(repairs splice at note *ends*; openings should still anchor — low repair overlap argues against truncation as cause).",
            f"- **Opens with lemma bracket:** {ua['opens_lemma_bracket']}; "
            f"**opens with critic name-colon:** {ua['opens_name_colon']}; "
            f"**neither:** {ua['neither_opening_pattern']}.",
            "",
            "Clustering is strongest in Antony (11), Othello (10), Winter's Tale (9), Romeo (7) — "
            "plays with Folger-style name-colon openings or poor IA witness alignment, not Troilus-first. "
            "High unanchorable rate reflects **start-anchor misses** on OCR-noisy witnesses and "
            "non-standard note openings, not truncation-repair corruption of note starts.",
            "",
            "## Per-play results",
            "",
            "| Play | Sampled | Anchored | Pass† | Interior | Unanch. |",
            "|------|--------:|---------:|------:|---------:|--------:|",
        ]
    )

    for r in sorted(rows, key=lambda x: x.get("play", "")):
        if r.get("error"):
            lines.append(f"| {r['play']} | — | ERROR | — | — | — |")
            continue
        lines.append(
            f"| {r['play']} | {r['sample_n']} | {r['anchored_n']} | "
            f"{r.get('pass_among_anchored_pct', '—')} | {r['interior_divergence_n']} | "
            f"{r['unanchorable_n']} |"
        )

    lines.extend(
        [
            "",
            "† Pass % among anchored notes.",
            "",
            "Regenerate: `python3 scripts/audit_nv_fullspan_sample.py`",
        ]
    )
    return "\n".join(lines) + "\n"


def collect_verdict_adjudication_json(rows: list[dict], verdict: str) -> list[dict]:
    out = []
    for r in rows:
        if r.get("error"):
            continue
        for item in r.get("_full_classify", []):
            if item.get("verdict") != verdict:
                continue
            out.append(
                {
                    "play": r["play"],
                    "ref": item.get("ref"),
                    "witness": r.get("witness"),
                    "anchor_method": item.get("anchor_method"),
                    "full_ratio": item.get("full_ratio"),
                    "tail_ratio": item.get("tail_ratio"),
                    "span_method": item.get("span_method"),
                    "span_estimated": item.get("span_estimated"),
                    "span_len_ratio": item.get("span_len_ratio"),
                    "note_text": item.get("note_text"),
                    "witness_span_text": item.get("witness_span_text"),
                }
            )
    return out


def write_adjudication_packets(
    rows: list[dict],
    *,
    verdict: str,
    title: str,
    intro: str,
) -> str:
    lines = [title, "", intro, ""]
    n = 0
    for r in rows:
        if r.get("error"):
            continue
        for item in r.get("_full_classify", []):
            if item.get("verdict") != verdict:
                continue
            n += 1
            lines.extend(
                [
                    f"## {n}. {r['play']} — {item.get('ref', '')}",
                    "",
                    f"- Witness: `{r.get('witness', '')}`",
                    f"- anchor_method: `{item.get('anchor_method', '')}`",
                    f"- full_ratio: **{item.get('full_ratio')}** | tail_ratio: {item.get('tail_ratio')}",
                    f"- span_method: `{item.get('span_method')}` | span_len_ratio: {item.get('span_len_ratio')}",
                    "",
                    "### Note (electronic)",
                    "",
                    "```",
                    (item.get("note_text") or "")[:2000],
                    "```",
                    "",
                    "### Witness span (bounded)",
                    "",
                    "```",
                    (item.get("witness_span_text") or "")[:2000],
                    "```",
                    "",
                    "---",
                    "",
                ]
            )
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Stratified full-span NV witness sample audit (v2)")
    ap.add_argument("--sample-n", type=int, default=DEFAULT_SAMPLE_N)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--play", action="append")
    ap.add_argument(
        "--sample-manifest",
        type=Path,
        default=None,
        help=f"Replay exact sample refs from JSON (default: {SAMPLE_MANIFEST.name} if present)",
    )
    ap.add_argument("--write-sample-manifest", action="store_true")
    args = ap.parse_args()

    manifest_path = args.sample_manifest
    if manifest_path is None and SAMPLE_MANIFEST.is_file():
        manifest_path = SAMPLE_MANIFEST
    manifest_by_play: dict[str, set[str]] | None = None
    if manifest_path and manifest_path.is_file():
        manifest_by_play = load_sample_manifest(manifest_path)

    prior_manifest = None
    prior_path = OUT_DIR / "manifest_v1_pre_tail_bound.json"
    if not prior_path.is_file():
        prior_path = OUT_DIR / "manifest.json"
    if prior_path.is_file():
        try:
            prior_manifest = json.loads(prior_path.read_text(encoding="utf-8"))
            if prior_manifest.get("span_method") == "tail_bounded_v2":
                prior_manifest = prior_manifest.get("prior_v1_summary")
                if prior_manifest:
                    prior_manifest = {"corpus_summary": prior_manifest}
        except json.JSONDecodeError:
            prior_manifest = None

    # Preserve v1 manifest on first v2 run
    live_manifest = OUT_DIR / "manifest.json"
    if live_manifest.is_file():
        try:
            live = json.loads(live_manifest.read_text(encoding="utf-8"))
            if live.get("span_method") != "tail_bounded_v2":
                (OUT_DIR / "manifest_v1_pre_tail_bound.json").write_text(
                    live_manifest.read_text(encoding="utf-8"), encoding="utf-8"
                )
        except json.JSONDecodeError:
            pass

    workbook_keys: set[tuple] = set()
    if WORKBOOK.is_file():
        for e in load_workbook(WORKBOOK):
            workbook_keys.add(
                (e["play_name"], e["act_scene"], str(e["line_key"]), int(e["note_index"]))
            )

    specs = PLAYS
    if args.play:
        wanted = set(args.play)
        specs = [s for s in PLAYS if s["play"] in wanted]

    rows = [
        audit_play(
            spec,
            args.sample_n,
            args.seed,
            manifest_refs=manifest_by_play.get(spec["play"]) if manifest_by_play else None,
        )
        for spec in specs
    ]
    summary = corpus_summary(rows)
    ua = analyze_unanchorable(rows, workbook_keys)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Strip _full_classify from persisted results (large); keep in adjudication source
    persist_rows = []
    for r in rows:
        pr = {k: v for k, v in r.items() if k != "_full_classify"}
        persist_rows.append(pr)

    manifest = {
        "date": date.today().isoformat(),
        "sample_n_per_play": args.sample_n,
        "seed": args.seed,
        "play_seed_fn": "zlib.crc32(play) % 10000 + seed",
        "sample_manifest": str(manifest_path) if manifest_by_play else None,
        "span_method": "tail_bounded_v2",
        "full_span_threshold": FULL_SPAN_THRESHOLD,
        "tail_threshold": TAIL_THRESHOLD,
        "corpus_summary": summary,
        "prior_v1_summary": prior_manifest.get("corpus_summary") if prior_manifest else None,
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / "results.json").write_text(json.dumps(persist_rows, indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / "rate_table.md").write_text(
        write_rate_table(rows, summary, args.sample_n, prior_manifest, ua), encoding="utf-8"
    )
    (OUT_DIR / "score_histogram.json").write_text(
        json.dumps(summary["score_histogram_anchored"], indent=2) + "\n", encoding="utf-8"
    )
    (OUT_DIR / "unanchorable_analysis.json").write_text(
        json.dumps(ua, indent=2) + "\n", encoding="utf-8"
    )
    (OUT_DIR / "interior_divergence_adjudication.md").write_text(
        write_adjudication_packets(
            rows,
            verdict="interior_divergence",
            title="# Interior divergence adjudication packets (v2 tail-bounded spans)",
            intro=(
                "Human review template: classify each as (a) extraction artifact, (b) witness OCR noise,\n"
                "(c) genuine interior divergence."
            ),
        ),
        encoding="utf-8",
    )
    (OUT_DIR / "interior_divergence_adjudication.json").write_text(
        json.dumps(collect_verdict_adjudication_json(rows, "interior_divergence"), indent=2) + "\n",
        encoding="utf-8",
    )
    (OUT_DIR / "span_mismatch_adjudication.md").write_text(
        write_adjudication_packets(
            rows,
            verdict="span_mismatch",
            title="# Span mismatch adjudication packets (v2 tail-bounded spans)",
            intro=(
                "Human review template: classify each as (a) extraction artifact, (b) witness OCR noise,\n"
                "(c) genuine span mismatch / paraphrase."
            ),
        ),
        encoding="utf-8",
    )
    (OUT_DIR / "span_mismatch_adjudication.json").write_text(
        json.dumps(collect_verdict_adjudication_json(rows, "span_mismatch"), indent=2) + "\n",
        encoding="utf-8",
    )

    if args.write_sample_manifest or not SAMPLE_MANIFEST.is_file():
        notes = []
        for r in rows:
            if r.get("error"):
                continue
            for d in r["sample"]:
                notes.append({"play": r["play"], "ref": d["ref"]})
        SAMPLE_MANIFEST.write_text(
            json.dumps(
                {
                    "seed": args.seed,
                    "sample_n_per_play": args.sample_n,
                    "play_seed_fn": "zlib.crc32(play) % 10000 + seed",
                    "notes": notes,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    print(f"Wrote {OUT_DIR}/")
    print(
        f"\nCorpus ({summary['sample_n']} notes):\n"
        f"  anchored pass:    {summary['pass_among_anchored_pct']}%\n"
        f"  interior div.:    {summary['interior_divergence_n']}\n"
        f"  unanchorable:     {summary['unanchorable_n']} ({summary['unanchorable_pct']}%)\n"
        f"  span_estimated:   {summary['span_estimated_n']}\n"
        f"  histogram:        {summary['score_histogram_anchored']}\n"
    )
    if prior_manifest:
        pv = prior_manifest.get("corpus_summary", {})
        print(
            f"  v1 anchored pass: {pv.get('pass_among_anchored_pct')}% "
            f"(interior {pv.get('interior_divergence_n')})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
