#!/usr/bin/env python3
"""Repair truncated Antony and Cleopatra NV notes from IA editi15 witness."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_nv_fidelity_all_plays import is_clipped as audit_clipped  # noqa: E402
from audit_nv_truncation import collect_notes, is_hyphen_artifact, is_witness_prefix  # noqa: E402
from nv_hyphen_splice import splice_hyphen  # noqa: E402
from nv_ia_witness import fetch_ia_text, fold_apostrophe  # noqa: E402
from nv_repair import extract_from_ia as _extract_from_ia  # noqa: E402
from nv_witness_map import WITNESS_BY_PLAY  # noqa: E402

JSON_PATH = ROOT / "Public/Data/antony_and_cleopatra.json"
SITE_MIRROR = ROOT / "My Website/Public/Data/antony_and_cleopatra.json"
BACKUP = JSON_PATH.with_suffix(".json.pre_clip_repair.backup")
PLAY = "Antony and Cleopatra"

_H4P2 = importlib.util.spec_from_file_location(
    "h4p2_repair", ROOT / "scripts/repair_henry_iv_part2_notes.py"
)
_h4p2 = importlib.util.module_from_spec(_H4P2)
_H4P2.loader.exec_module(_h4p2)

ACT_BLOCK = re.compile(
    r"Act\s+[IVXLC\d]+\s*,?\s*(?:sc\.?\s*\d+\.?)?\s*\]?\s*",
    re.I,
)
LINE_HDR = re.compile(r"\n\s*\d{1,3}\.\s+[A-Za-z\u2018\u2019\"'\(\[]", re.I)
PAGE_HDR = re.compile(
    r"(?:"
    r"\bTHE\s+TR\s*AG(?:ED|E)\s+IE\s+OF\b"
    r"|\bTHE\s+TRAGEDIE\s+OF\b"
    r"|\bANTHONY\s+AND\s+CLEOPATRA\s+\d"
    r")",
    re.I,
)
PLAY_TEXT_RE = re.compile(
    r"(?:"
    r"\b(?:Enob|Men|Ant|Char|Cleo|Caes|Proculeius|Dolabella|Scarus|Decretas|"
    r"Dercetas|Diomed|Soothsayer|Mardian|Seleucus|Alexas|Iras|Charmian)\.\s+[A-Z\u2018\u2019\"']"
    r"|\b(?:fir|fhe|fhall|fpeak|fuch|felf|fweet|fword|fay|fucce)\b"
    r"|\bTHE\s+TR\s*AG(?:ED|E)\s+IE\s+OF\b"
    r"|\bTHE\s+TRAGEDIE\s+OF\b"
    r"|\bANTHONY\s+AND\s+CLEOPATRA\s+\d"
    r")",
    re.I,
)
PAGE_INTRUSION = re.compile(
    r"(?:"
    r"\bTHE\s+TR\s*AG(?:ED|E)\s+IE\s+OF\b"
    r"|\bTHE\s+TRAGEDIE\s+OF\b"
    r"|\bANTHONY\s+AND\s+CLEOPATRA\s+\d"
    r"|\n\s*\d{1,3}\.\s+[A-Za-z\u2018\u2019\"'.-]+\]\s"
    r")",
    re.I,
)


def deinterleave_antony(text: str) -> str:
    text = ACT_BLOCK.sub(" ||| ", text)
    text = LINE_HDR.sub(lambda m: " ||| " + m.group(0).lstrip(), text)
    parts = [p.strip() for p in text.split("|||") if p.strip()]
    if not parts:
        return _h4p2.norm_space(text)
    out = parts[0]
    for part in parts[1:]:
        if len(part) > 120 and len(re.findall(r"\b[A-Z][a-z]+\b", part)) > 8:
            m = _h4p2.RESUME.search(part)
            out += " " + (part[m.start() :] if m else part)
        else:
            out += " " + part
    return _h4p2.norm_space(out)


def tail_anchor(folded_ia: str, words: list[str]) -> re.Match[str] | None:
    for n in range(min(len(words), 16), 5, -1):
        pat = re.compile(r"\s+".join(re.escape(w) for w in words[-n:]), re.I)
        m = pat.search(folded_ia)
        if m:
            return m
    return None


DIALOGUE_RE = re.compile(r"\b(?:Enob|Men)\.\s+[A-Z\u2018\u2019\"']", re.I)


def looks_contaminated(note: str, *, suffix: bool = False) -> bool:
    if _h4p2.looks_contaminated(note):
        return True
    if DIALOGUE_RE.search(note) or PAGE_HDR.search(note):
        return True
    if suffix and PLAY_TEXT_RE.search(note):
        return True
    return False


def ends_well(note: str) -> bool:
    n = note.rstrip()
    if re.search(r"—\s*Ed\.?\]?\s*$", n):
        return True
    if re.search(r"\[[^\]]+\]\s*—\s*Ed\.?\]?\s*$", n):
        return True
    if re.search(r"—\s*Ed\b", n[-40:]):
        return True
    return False


def extract_from_ia(ia: str, pos: int, json_note: str) -> str:
    return _extract_from_ia(ia, pos, json_note, play=PLAY)


def complete_note(note: str, ia: str) -> str | None:
    body = note[note.index("]") + 1 :].strip() if "]" in note else note.strip()
    body = re.sub(r"^\d{1,3}\.\s*", "", body)
    words = re.findall(r"[A-Za-z0-9\u2019']+", _h4p2.fold_apostrophe(body))
    if len(words) < 6:
        return None
    tm = tail_anchor(_h4p2.fold_apostrophe(ia), words)
    if not tm:
        return None
    chunk = PAGE_INTRUSION.split(ia[tm.end() : tm.end() + 5000], maxsplit=1)[0]
    suffix = _h4p2.truncate_footnote(deinterleave_antony(chunk))
    suffix = _h4p2.norm_space(suffix)
    if not suffix or len(suffix) < 8:
        return None
    return _h4p2.norm_space(note.rstrip() + suffix)


def is_improved(note: str, ext: str, *, suffix_mode: bool = False) -> bool:
    if len(ext) <= len(note) + 12:
        return False
    if _h4p2.is_clipped(ext) or audit_clipped(ext):
        return False
    if looks_contaminated(ext, suffix=suffix_mode):
        return False
    if not ends_well(ext):
        return False
    if len(ext) > max(3500, len(note) * 6):
        return False
    if suffix_mode:
        return ext.startswith(note.rstrip())
    body_n = note[note.index("]") + 1 :].strip() if "]" in note else note.strip()
    return body_n[:40] in ext


def repair_note(note: str, ia: str) -> str | None:
    if is_hyphen_artifact(note):
        ext = splice_hyphen(ia, note)
        if ext and is_improved(note, ext, suffix_mode=True):
            return ext

    pos = _h4p2.find_note_pos(ia, note)
    if pos >= 0:
        ext = extract_from_ia(ia, pos, note)
        if (
            len(ext) > len(note) + 12
            and not _h4p2.is_clipped(ext)
            and not audit_clipped(ext)
            and ends_well(ext)
            and not looks_contaminated(ext, suffix=False)
            and len(ext) <= max(3500, len(note) * 6)
        ):
            return ext

    ext = complete_note(note, ia)
    if ext and is_improved(note, ext, suffix_mode=True):
        return ext
    return None


def needs_repair(note: str, folded_ia: str) -> bool:
    return (
        audit_clipped(note)
        or _h4p2.is_clipped(note)
        or is_witness_prefix(folded_ia, note)
    )


def union_truncated_count(data: dict, folded_ia: str) -> int:
    from audit_nv_truncation import (  # noqa: WPS433
        is_hard_truncation,
        is_hyphen_artifact,
        is_mid_sentence_cut,
        is_unbalanced_parens,
    )

    n = 0
    for item in collect_notes(data):
        note = item["note"]
        if (
            audit_clipped(note)
            or _h4p2.is_clipped(note)
            or is_hard_truncation(note)
            or is_mid_sentence_cut(note)
            or is_hyphen_artifact(note)
            or is_unbalanced_parens(note)
            or is_witness_prefix(folded_ia, note)
        ):
            n += 1
    return n


def repair_targets_count(data: dict, folded_ia: str) -> int:
    return sum(1 for item in collect_notes(data) if needs_repair(item["note"], folded_ia))


def repair(data: dict, ia: str, folded_ia: str, *, dry_run: bool = False) -> dict:
    stats = {
        "before": repair_targets_count(data, folded_ia),
        "union_before": union_truncated_count(data, folded_ia),
        "repaired": 0,
        "unresolved": 0,
        "after": 0,
        "union_after": 0,
        "examples": [],
    }

    for scene, scene_data in data.items():
        if not str(scene).startswith("ACT") or not isinstance(scene_data, dict):
            continue
        for line_data in scene_data.values():
            if not isinstance(line_data, dict):
                continue
            notes = line_data.get("notes") or []
            for i, note in enumerate(notes):
                if not needs_repair(note, folded_ia):
                    continue
                ext = repair_note(note, ia)
                if ext is None:
                    stats["unresolved"] += 1
                    continue
                if not dry_run:
                    notes[i] = ext
                stats["repaired"] += 1
                if len(stats["examples"]) < 6:
                    stats["examples"].append(
                        {
                            "before_len": len(note),
                            "after_len": len(ext),
                            "tail": ext[-100:],
                        }
                    )

    stats["after"] = repair_targets_count(data, folded_ia)
    stats["union_after"] = union_truncated_count(data, folded_ia)
    return stats


def sync_mirrors(text: str) -> None:
    if SITE_MIRROR.parent.is_dir():
        SITE_MIRROR.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not JSON_PATH.is_file():
        print(f"ERROR: missing {JSON_PATH}", file=sys.stderr)
        return 1

    ia_id, stream = WITNESS_BY_PLAY[PLAY]
    ia_text, src = fetch_ia_text(ia_id, stream)
    if ia_text is None:
        print(f"ERROR: witness unavailable: {src}", file=sys.stderr)
        return 1

    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    folded = fold_apostrophe(ia_text)
    stats = repair(data, ia_text, folded, dry_run=args.dry_run)
    stats.update({"play": PLAY, "ia_id": ia_id, "witness": src})

    print(
        f"{stats['before']}|{stats['repaired']}|{stats['after']}|{stats['unresolved']}"
    )
    print(
        f"union_truncated {stats['union_before']} -> {stats['union_after']}  "
        f"ia={ia_id}"
    )
    for ex in stats["examples"]:
        print(f"  + {ex['before_len']} -> {ex['after_len']} …{ex['tail']}")

    if args.dry_run:
        return 0

    if stats["repaired"]:
        if not BACKUP.is_file():
            shutil.copy2(JSON_PATH, BACKUP)
            print(f"Backup -> {BACKUP.relative_to(ROOT)}")
        out = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        JSON_PATH.write_text(out, encoding="utf-8")
        sync_mirrors(out)
        print(f"Wrote {JSON_PATH.relative_to(ROOT)}")
        if SITE_MIRROR.is_file():
            print(f"Mirror -> {SITE_MIRROR.relative_to(ROOT)}")

    audit_out = ROOT / "validation" / "nv_antony_clip_repair.json"
    audit_out.write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
