#!/usr/bin/env python3
"""Apply contractor-completed NV note text from workbook into Public/Data/*.json."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from rapidfuzz import fuzz  # noqa: E402

from audit_nv_fidelity_all_plays import PLAYS  # noqa: E402
from audit_nv_truncation import (  # noqa: E402
    collect_notes,
    ends_nv_terminal,
    is_union_truncated,
)
from nv_ia_witness import fetch_ia_text, fold_apostrophe  # noqa: E402
from nv_witness_map import (  # noqa: E402
    LOCAL_WITNESS_BY_PLAY,
    WITNESS_AUDIT_FALLBACK,
    WITNESS_BY_PLAY,
)

FUZZY_MATCH_THRESHOLD = 78  # rapidfuzz partial_ratio; tolerates OCR noise, catches fabrication

DEFAULT_WORKBOOK = ROOT / "validation" / "contractor_truncation_workbook.json"


def load_workbook(path: Path) -> list[dict]:
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        for row in rows:
            sig = row.get("truncation_signals") or ""
            row["truncation_signals"] = [s for s in sig.split(";") if s]
            row["note_index"] = int(row["note_index"])
            row["char_count_before"] = int(row.get("char_count_before") or 0)
            row["char_count_after"] = int(row.get("char_count_after") or 0)
        return rows

    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "entries" in payload:
        return payload["entries"]
    if isinstance(payload, list):
        return payload
    raise ValueError(f"Unrecognized workbook format: {path}")


def play_json_path(play_file: str) -> Path:
    return ROOT / "Public" / "Data" / f"{play_file}.json"


def validate_completion(entry: dict, completed: str) -> list[str]:
    issues: list[str] = []
    original = entry["current_note_text"]
    status = (entry.get("status") or "").strip().lower()

    if status == "no_change_needed":
        if completed and completed != original:
            issues.append("no_change_needed but completed_note_text differs from original")
        return issues

    if status != "complete":
        issues.append(f"status is {entry.get('status')!r}, expected 'complete' or 'no_change_needed'")

    if not completed.strip():
        issues.append("completed_note_text is empty")
        return issues

    if len(completed) < len(original):
        issues.append(
            f"completed text shorter than original ({len(completed)} < {len(original)})"
        )

    if completed == original:
        issues.append("completed_note_text identical to current_note_text")

    if not ends_nv_terminal(completed.rstrip()):
        issues.append("completed text lacks NV terminal punctuation / scholarly closer")

    # Prefix continuity: first 80 chars of original should appear near start of
    # completed. Uses the same OCR/typography-tolerant normalization as the
    # witness check (curly vs straight quotes, long-s, whitespace) so a
    # legitimate cosmetic correction (e.g. fixing an OCR-garbled character in
    # the note's own opening) doesn't get flagged as a lost prefix, while a
    # genuinely different note (wrong lemma/critic entirely) still fails.
    prefix = original[:80].strip()
    if prefix:
        norm_prefix = _norm(prefix)
        norm_window = _norm(completed[: max(len(original), 120)])
        if norm_prefix in norm_window:
            pass  # exact (normalized) match, definitely fine
        else:
            # Short NV apparatus fragments (e.g. "86. Vlug.] F:F" -> "86. Vlug.] F1F2.")
            # commonly involve a legitimate one-token OCR correction (misread folio
            # sigla, a garbled ampersand, etc.) that a strict substring check can
            # never pass. Use token-based fuzzy matching so a short but mostly-
            # identical prefix still passes, while a genuinely unrelated note
            # (wrong lemma/critic) still fails.
            score = fuzz.token_sort_ratio(norm_prefix, norm_window[: len(norm_prefix) + 20])
            if score < 55:
                issues.append("completed text does not preserve original opening prefix")

    return issues


def _norm(s: str) -> str:
    s = re.sub(r"\s+", " ", s)
    s = fold_apostrophe(s)
    s = s.replace("ſ", "f")  # long-s
    s = s.replace("œ", "oe").replace("æ", "ae")
    s = s.replace("—", "-").replace("–", "-")
    s = re.sub(r"[^a-z0-9 ]", "", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def _get_witness_text(play_name: str) -> str | None:
    """Resolve the correct witness for a play, preferring a local override
    (e.g. Troilus and Cressida's lending-restricted IA volume) before
    falling back to the IA witness map / audit fallback."""
    local = LOCAL_WITNESS_BY_PLAY.get(play_name)
    if local is not None and local.is_file():
        return local.read_text(encoding="utf-8")
    wit = WITNESS_BY_PLAY.get(play_name)
    if wit is None:
        return None
    ia_text, _src = fetch_ia_text(*wit)
    if ia_text is None:
        fallback = WITNESS_AUDIT_FALLBACK.get(play_name)
        if fallback:
            ia_text, _src = fetch_ia_text(*fallback)
    return ia_text


_WITNESS_CACHE: dict[str, str | None] = {}


def witness_prefix_ok(play_name: str, completed: str) -> bool | None:
    """Fuzzy-match the completed note's body against the play's witness text.

    Tolerant of OCR noise (misread characters/words) via rapidfuzz partial_ratio,
    and of the lemma-header appearing before or after an inline line-number
    (e.g. 'lemma] 41. CRITIC:' vs '41. lemma] CRITIC:'), unlike a literal
    substring check. Still rejects genuinely absent/fabricated content, since
    OCR noise degrades a handful of characters, not the whole passage.
    """
    if play_name not in _WITNESS_CACHE:
        _WITNESS_CACHE[play_name] = _get_witness_text(play_name)
    ia_text = _WITNESS_CACHE[play_name]
    if ia_text is None:
        return None

    body = completed[completed.index("]") + 1 :].strip() if "]" in completed else completed.strip()
    # Strip a relocated line-number that may follow the lemma bracket, e.g.
    # "Claudio] 41. THEOBALD:" -> "THEOBALD:"
    m = re.match(r"^\d+[a-z]?[.,]?\s+", body)
    if m:
        body = body[m.end() :]
    if len(body) < 40:
        return None

    if len(body) < 20:
        return None

    if not hasattr(witness_prefix_ok, "_norm_cache"):
        witness_prefix_ok._norm_cache = {}
    norm_cache = witness_prefix_ok._norm_cache
    if play_name not in norm_cache:
        norm_cache[play_name] = _norm(ia_text)
    folded = norm_cache[play_name]

    def probe_score(probe: str) -> float:
        if len(probe) < 20:
            return 0.0
        if probe in folded:
            return 100.0
        win = len(probe) + 20
        step = 25
        best = 0.0
        for start in range(0, max(1, len(folded) - win), step):
            chunk = folded[start : start + win]
            score = fuzz.partial_ratio(probe, chunk)
            if score > best:
                best = score
                if best >= 100:
                    break
        return best

    # Primary probe: the note's own opening (first 80 chars of the body).
    primary = _norm(body[:80])
    if probe_score(primary) >= FUZZY_MATCH_THRESHOLD:
        return True

    # NV witness OCR frequently interleaves an act/scene header and a block
    # of Folio verse text directly into the middle of continuous prose
    # commentary (a well-known artifact of this corpus — see repair
    # methodology notes). A note whose opening lands right before such a
    # block will genuinely be present in the witness, just not contiguous
    # with the note's first 80 characters. Try a secondary probe from
    # further into the note body before concluding the passage is absent:
    # a real note will still match somewhere; fabricated text will not
    # match at any offset.
    if len(body) >= 100:
        mid_start = len(body) // 3
        secondary = _norm(body[mid_start : mid_start + 80])
        if probe_score(secondary) >= FUZZY_MATCH_THRESHOLD:
            return True
        # For shorter bodies the /3 offset may itself still sit inside (or
        # right after) an interleaved block; also try starting from the
        # midpoint as a second fallback.
        if len(body) < 250:
            mid_start2 = len(body) // 2
            tertiary = _norm(body[mid_start2 : mid_start2 + 60])
            if probe_score(tertiary) >= FUZZY_MATCH_THRESHOLD:
                return True

    return False


def apply_entry(data: dict, entry: dict, completed: str) -> None:
    scene = entry["act_scene"]
    line_key = str(entry["line_key"])
    note_index = int(entry["note_index"])
    scene_data = data.get(scene)
    if not isinstance(scene_data, dict):
        raise KeyError(f"scene not found: {scene}")
    line_obj = scene_data.get(line_key)
    if not isinstance(line_obj, dict):
        raise KeyError(f"line not found: {scene} / {line_key}")
    notes = line_obj.get("notes")
    status = (entry.get("status") or "").strip().lower()
    if not isinstance(notes, list) or note_index >= len(notes):
        if status == "no_change_needed" and not completed.strip():
            # Note entry was intentionally removed during manual repair
            # (e.g. a duplicate/merged fragment); nothing to write.
            return
        raise IndexError(f"note index out of range: {note_index}")
    notes[note_index] = completed


def count_union_truncated_for_play(play_name: str, json_rel: str) -> int:
    path = ROOT / json_rel
    data = json.loads(path.read_text(encoding="utf-8"))
    ia_text = _get_witness_text(play_name)
    folded_ia = fold_apostrophe(ia_text) if ia_text else None
    count = 0
    for item in collect_notes(data):
        if is_union_truncated(item["note"], folded_ia):
            count += 1
    return count


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--workbook",
        type=Path,
        default=DEFAULT_WORKBOOK,
        help="Workbook JSON or CSV (default: validation/contractor_truncation_workbook.json)",
    )
    ap.add_argument("--dry-run", action="store_true", help="Validate only; do not write play JSON")
    ap.add_argument("--strict-witness", action="store_true", help="Reject if witness prefix check fails")
    ap.add_argument("--regenerate-workbook", action="store_true", help="Rebuild workbook from current data")
    args = ap.parse_args()

    if args.regenerate_workbook:
        from generate_contractor_workbook import main as gen_main

        return gen_main()

    entries = load_workbook(args.workbook)
    actionable = [
        e
        for e in entries
        if (e.get("status") or "").strip().lower() in ("complete", "no_change_needed")
    ]

    applied = 0
    skipped = 0
    rejected: list[dict] = []
    touched_files: dict[str, dict] = {}

    for entry in actionable:
        status = (entry.get("status") or "").strip().lower()
        completed = (
            entry.get("current_note_text", "")
            if status == "no_change_needed"
            else (entry.get("completed_note_text") or "")
        )
        issues = validate_completion(entry, completed)
        if not issues and status == "complete":
            witness_ok = witness_prefix_ok(entry["play_name"], completed)
            if witness_ok is False:
                issues.append("completed text anchor not found in IA witness (prefix mismatch)")
            if args.strict_witness and witness_ok is False:
                issues.append("strict witness check failed")

        if issues:
            rejected.append({"entry": entry, "issues": issues})
            continue

        play_file = entry["play_file"]
        path = play_json_path(play_file)
        if play_file not in touched_files:
            touched_files[play_file] = json.loads(path.read_text(encoding="utf-8"))
        try:
            apply_entry(touched_files[play_file], entry, completed)
            applied += 1
        except (KeyError, IndexError) as exc:
            rejected.append({"entry": entry, "issues": [str(exc)]})

    for play_file, data in touched_files.items():
        path = play_json_path(play_file)
        if args.dry_run:
            print(f"[dry-run] would write {path.relative_to(ROOT)}")
            continue
        backup = path.with_suffix(path.suffix + ".pre_contractor_repair.backup")
        if not backup.is_file():
            shutil.copy2(path, backup)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {path.relative_to(ROOT)}")

    skipped = len(entries) - len(actionable)

    print(f"\nApplied: {applied}")
    print(f"Skipped (pending/other status): {skipped}")
    print(f"Rejected: {len(rejected)}")
    if rejected:
        for item in rejected[:10]:
            ref = f"{item['entry']['play_name']} / {item['entry']['act_scene']} / line {item['entry']['line_key']} / note {item['entry']['note_index']}"
            print(f"  - {ref}: {', '.join(item['issues'])}")
        if len(rejected) > 10:
            print(f"  ... and {len(rejected) - 10} more")

    if not args.dry_run and touched_files:
        print("\nRemaining union-truncated notes after apply:")
        play_by_file = {Path(s["json"]).stem: s for s in PLAYS}
        total_remaining = 0
        for play_file in sorted(touched_files):
            spec = play_by_file.get(play_file)
            if not spec:
                continue
            remaining = count_union_truncated_for_play(spec["play"], spec["json"])
            total_remaining += remaining
            print(f"  {spec['play']:<32} {remaining:>4}")
        print(f"  {'TOTAL (touched plays)':<32} {total_remaining:>4}")

    return 1 if rejected else 0


if __name__ == "__main__":
    raise SystemExit(main())
