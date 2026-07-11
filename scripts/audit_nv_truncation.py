#!/usr/bin/env python3
"""Exhaustive NV note truncation audit across all 22 dramatic volumes."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_nv_fidelity_all_plays import PLAYS, is_clipped  # noqa: E402
from nv_ia_witness import fetch_ia_text, fold_apostrophe  # noqa: E402
from nv_witness_map import WITNESS_AUDIT_FALLBACK  # noqa: E402

OUT = ROOT / "validation" / "nv_truncation_audit.json"

TERMINAL = set('.!?]"\'\u2014\u2019\u201d)')

# Common NV scholarly closers treated as complete endings.
NV_TERMINAL_RE = re.compile(
    r"(?:"
    r"—\s*Ed\.\]|—\s*ED\.\]|—\s*\[Ed\.\]|\[Ed\.\]|\[ED\.\]"
    r"|ff\.\]|pp\.\]|p\.\s*\d+\]|vol\.\s*[IVXLC\d]+\]"
    r"|\.—|\.\]|\.\"|\.'|\.\)|\.\}|\.»"
    r")\s*$",
    re.I,
)


def norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def last_alnum_token(note: str) -> str:
    tokens = re.findall(r"[A-Za-z0-9\u2019']+", note.rstrip())
    return tokens[-1] if tokens else ""


def ends_terminal(note: str) -> bool:
    n = note.rstrip()
    if not n:
        return True
    return n[-1] in TERMINAL


def ends_nv_terminal(note: str) -> bool:
    """True when note ends with a typical NV citation or editorial closer."""
    n = note.rstrip()
    if not n:
        return True
    if ends_terminal(n):
        return True
    return bool(NV_TERMINAL_RE.search(n))


def is_hard_truncation(note: str) -> bool:
    n = note.strip()
    if not n:
        return False
    # Bracket-orphan: missing leading `[` but otherwise complete (Twelfth Night logic).
    if n.startswith("]") and ends_nv_terminal(n.rstrip()):
        return False
    if ends_nv_terminal(n):
        return False
    last = last_alnum_token(n)
    if last and len(last) < 4 and re.search(r"[A-Za-z]", last):
        return True
    return not ends_terminal(n)


def is_mid_sentence_cut(note: str) -> bool:
    n = note.rstrip()
    if not n:
        return False
    if ends_nv_terminal(n):
        return False
    return bool(re.search(r"[a-z]\s*$", n))


def is_hyphen_artifact(note: str) -> bool:
    return bool(re.search(r"-\s*$", note.strip()))


def is_unbalanced_parens(note: str) -> bool:
    n = note.strip()
    if not n:
        return False
    if n.count("(") <= n.count(")"):
        return False
    # Long scholarly notes often nest unclosed parenthetical citations.
    if ends_nv_terminal(n) and len(n) >= 500:
        return False
    return True


def is_union_truncated(note: str, folded_ia: str | None = None) -> bool:
    """Any truncation signal (optionally including witness_prefix)."""
    if is_clipped(note):
        return True
    if is_hard_truncation(note):
        return True
    if is_mid_sentence_cut(note):
        return True
    if is_hyphen_artifact(note):
        return True
    if is_unbalanced_parens(note):
        return True
    if folded_ia is not None and is_witness_prefix(folded_ia, note):
        return True
    return False


def is_witness_prefix(folded_ia: str, note: str) -> bool:
    """True when IA witness continues with prose after the note ends."""
    body = note[note.index("]") + 1 :].strip() if "]" in note else note.strip()
    if len(body) < 50:
        return False
    words = re.findall(r"[A-Za-z0-9']+", fold_apostrophe(body))
    if len(words) < 8:
        return False

    start_pat = re.compile(r"\s+".join(re.escape(w) for w in words[:8]), re.I)
    sm = start_pat.search(folded_ia)
    if not sm:
        return False

    end_words = words[-8:]
    end_pat = re.compile(r"\s+".join(re.escape(w) for w in end_words), re.I)
    search_end = sm.start() + max(len(note) * 2, 800)
    em = end_pat.search(folded_ia, sm.start(), search_end)
    if not em:
        return False

    rest = folded_ia[em.end() : em.end() + 100].lstrip()
    if len(rest) < 10:
        return False
    if not re.match(r"[a-zA-Z(\[\u2018\"']", rest):
        return False
    cont_words = re.findall(r"[A-Za-z']{3,}", rest[:80])
    return len(cont_words) >= 2


def collect_notes(data: dict) -> list[dict]:
    items: list[dict] = []
    for scene, scene_data in data.items():
        if str(scene).startswith("_") or not isinstance(scene_data, dict):
            continue
        for line_num, obj in scene_data.items():
            if not isinstance(obj, dict):
                continue
            for note_idx, note in enumerate(obj.get("notes") or []):
                if not isinstance(note, str) or not note.strip():
                    continue
                items.append(
                    {
                        "scene": scene,
                        "line": str(line_num),
                        "note_idx": note_idx,
                        "note": note,
                        "ref": f"{scene} / line {line_num} / note {note_idx}",
                    }
                )
    return items


def tail_preview(note: str, n: int = 90) -> str:
    t = note.rstrip()
    if len(t) <= n:
        return t
    return "…" + t[-n:]


def audit_play(spec: dict) -> dict:
    path = ROOT / spec["json"]
    if not path.is_file():
        return {"play": spec["play"], "error": f"missing {spec['json']}"}

    data = json.loads(path.read_text(encoding="utf-8"))
    notes = collect_notes(data)

    ia_text: str | None = None
    folded_ia: str | None = None
    ia_id, stream = spec["ia"], spec["ia_stream"]
    ia_text, ia_src = fetch_ia_text(ia_id, stream)
    if ia_text is not None:
        ia_status = "ok"
        folded_ia = fold_apostrophe(ia_text)
    else:
        fallback = WITNESS_AUDIT_FALLBACK.get(spec["play"])
        if fallback:
            fb_id, fb_stream = fallback
            ia_text, ia_src = fetch_ia_text(fb_id, fb_stream)
            if ia_text is not None:
                ia_status = f"fallback:{fb_id}"
                folded_ia = fold_apostrophe(ia_text)
                ia_id = fb_id
            else:
                ia_status = f"unavailable: {ia_src}; fallback:{fb_id}:{ia_src}"
        else:
            ia_status = f"unavailable: {ia_src}"

    counts = {
        "total_notes": len(notes),
        "is_clipped": 0,
        "hard_truncation": 0,
        "mid_sentence_cut": 0,
        "hyphen_artifact": 0,
        "unbalanced_parens": 0,
        "witness_prefix": 0,
        "union_truncated": 0,
    }
    flagged: list[dict] = []

    for item in notes:
        note = item["note"]
        signals: list[str] = []
        if is_clipped(note):
            counts["is_clipped"] += 1
            signals.append("is_clipped")
        if is_hard_truncation(note):
            counts["hard_truncation"] += 1
            signals.append("hard_truncation")
        if is_mid_sentence_cut(note):
            counts["mid_sentence_cut"] += 1
            signals.append("mid_sentence_cut")
        if is_hyphen_artifact(note):
            counts["hyphen_artifact"] += 1
            signals.append("hyphen_artifact")
        if is_unbalanced_parens(note):
            counts["unbalanced_parens"] += 1
            signals.append("unbalanced_parens")
        if folded_ia is not None and is_witness_prefix(folded_ia, note):
            counts["witness_prefix"] += 1
            signals.append("witness_prefix")

        if signals:
            counts["union_truncated"] += 1
            flagged.append({**item, "signals": signals, "tail": tail_preview(note)})

    total = counts["total_notes"] or 1
    pct = round(100 * counts["union_truncated"] / total, 2)
    old_pct = round(100 * counts["is_clipped"] / total, 2)

    examples = []
    for ex in flagged[:5]:
        examples.append(
            {
                "ref": ex["ref"],
                "signals": ex["signals"],
                "tail": ex["tail"],
            }
        )

    return {
        "play": spec["play"],
        "year": spec["year"],
        "json_file": spec["json"],
        "ia_id": ia_id,
        "ia_status": ia_status,
        **counts,
        "union_pct": pct,
        "is_clipped_pct": old_pct,
        "examples": examples[:3],
    }


def print_table(rows: list[dict], play_count: int) -> None:
    hdr = (
        f"{'Play':<32} {'Notes':>6} {'Old':>6} {'Hard':>6} {'Mid':>6} "
        f"{'Hyphen':>6} {'Paren':>6} {'IApfx':>6} {'UNION':>6} {'Union%':>7}"
    )
    print(hdr)
    print("-" * len(hdr))
    totals = {k: 0 for k in (
        "total_notes", "is_clipped", "hard_truncation", "mid_sentence_cut",
        "hyphen_artifact", "unbalanced_parens", "witness_prefix", "union_truncated",
    )}
    for r in rows:
        if r.get("error"):
            print(f"{r['play']:<32} ERROR: {r['error']}")
            continue
        for k in totals:
            totals[k] += r[k]
        print(
            f"{r['play']:<32} {r['total_notes']:>6} {r['is_clipped']:>6} "
            f"{r['hard_truncation']:>6} {r['mid_sentence_cut']:>6} "
            f"{r['hyphen_artifact']:>6} {r['unbalanced_parens']:>6} "
            f"{r['witness_prefix']:>6} {r['union_truncated']:>6} {r['union_pct']:>6.2f}%"
        )
    t = totals["total_notes"] or 1
    print("-" * len(hdr))
    print(
        f"{f'TOTAL ({play_count} plays)':<32} {totals['total_notes']:>6} {totals['is_clipped']:>6} "
        f"{totals['hard_truncation']:>6} {totals['mid_sentence_cut']:>6} "
        f"{totals['hyphen_artifact']:>6} {totals['unbalanced_parens']:>6} "
        f"{totals['witness_prefix']:>6} {totals['union_truncated']:>6} "
        f"{100 * totals['union_truncated'] / t:>6.2f}%"
    )


def _exclude_slug(excluded: set[str]) -> str:
    known = {
        frozenset({"Troilus and Cressida"}): "_no_troilus",
    }
    key = frozenset(excluded)
    if key in known:
        return known[key]
    slug = "_".join(
        sorted(
            p.lower().replace("'", "").replace(",", "").replace(" ", "_")[:16]
            for p in excluded
        )
    )[:48]
    return f"_no_{slug}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Play title(s) to omit (repeatable), e.g. 'Troilus and Cressida'",
    )
    ap.add_argument(
        "--out-suffix",
        default=None,
        help="Output filename suffix (default: _no_<slug> when --exclude is set)",
    )
    args = ap.parse_args()
    excluded = {name.strip() for name in args.exclude if name.strip()}
    plays = [spec for spec in PLAYS if spec["play"] not in excluded]
    if not plays:
        print("No plays left after exclusions.", file=sys.stderr)
        return 1

    suffix = args.out_suffix
    if suffix is None and excluded:
        suffix = _exclude_slug(excluded)

    out_path = OUT
    if suffix:
        stem = suffix if suffix.startswith("_") else f"_{suffix}"
        out_path = OUT.with_name(f"{OUT.stem}{stem}{OUT.suffix}")

    rows = []
    n = len(plays)
    for i, spec in enumerate(plays, 1):
        print(f"[{i}/{n}] {spec['play']}...", flush=True)
        rows.append(audit_play(spec))
    payload = {
        "excluded_plays": sorted(excluded) if excluded else [],
        "methodology": {
            "is_clipped": "Existing audit heuristic (length thresholds on stop-word/hyphen/paren endings)",
            "hard_truncation": "Missing terminal punctuation / mid-word fragment; bracket-orphans with NV closers excluded",
            "mid_sentence_cut": "Ends with lowercase letter and no NV terminal punctuation",
            "hyphen_artifact": "Ends with hyphen (line-break artifact)",
            "unbalanced_parens": "More ( than ) unless note ends with NV terminal and len>=500",
            "witness_prefix": "Note anchor found in IA witness and prose continues after note end",
            "union_truncated": "Any of the above signals",
        },
        "plays": rows,
        "totals": {},
    }
    ok_rows = [r for r in rows if not r.get("error")]
    t_notes = sum(r["total_notes"] for r in ok_rows)
    t_union = sum(r["union_truncated"] for r in ok_rows)
    t_old = sum(r["is_clipped"] for r in ok_rows)
    payload["totals"] = {
        "plays": len(ok_rows),
        "total_notes": t_notes,
        "is_clipped": t_old,
        "union_truncated": t_union,
        "is_clipped_pct": round(100 * t_old / t_notes, 2) if t_notes else 0,
        "union_pct": round(100 * t_union / t_notes, 2) if t_notes else 0,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")
    if excluded:
        print(f"Excluded: {', '.join(sorted(excluded))} ({n} plays audited)\n")
    else:
        print()
    print_table(ok_rows, n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
