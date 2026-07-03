#!/usr/bin/env python3
"""Repair truncated King John NV notes using IA witness + truncation audit signals."""

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

from audit_nv_truncation import (  # noqa: E402
    collect_notes,
    is_clipped,
    is_hyphen_artifact,
    is_mid_sentence_cut,
    is_unbalanced_parens,
    is_witness_prefix,
)
from nv_hyphen_splice import splice_hyphen  # noqa: E402
from nv_ia_witness import fetch_ia_text, fold_apostrophe  # noqa: E402
from nv_witness_map import WITNESS_BY_PLAY  # noqa: E402

JSON_PATH = ROOT / "Public/Data/king_john.json"
SITE_MIRROR = ROOT / "My Website/Public/Data/king_john.json"
BACKUP = JSON_PATH.with_suffix(".json.pre_trunc_repair.backup")
PLAY = "King John"

_H4P2 = importlib.util.spec_from_file_location(
    "h4p2_repair", ROOT / "scripts/repair_henry_iv_part2_notes.py"
)
_h4p2 = importlib.util.module_from_spec(_H4P2)
_H4P2.loader.exec_module(_h4p2)

KJ_HDR = re.compile(
    r"(?:ACT\s+[IVXLC\d]+\s*,\s*sc\.?\s*\d+\.?\]?\s*)?"
    r"(?:OF\s+)?KING\s+JOHN\s+\d{1,3}\s+",
    re.I,
)
OCR_REF = re.compile(r"\d+\.–\w+")
SEE_NOTE_RE = re.compile(r"see note\b", re.I)
NEXT_ENTRY = re.compile(r"\s+\d+\.\s+[\w .'-]+\]\s", re.I)


def is_see_note_cross_ref(note: str) -> bool:
    n = note.strip()
    return len(n) < 160 and bool(SEE_NOTE_RE.search(n))


def complete_see_note(ia: str, note: str) -> str | None:
    if not is_see_note_cross_ref(note):
        return None
    folded_ia = fold_apostrophe(ia)
    body = note[note.index("]") + 1 :].strip() if "]" in note else note.strip()
    words = re.findall(r"[A-Za-z0-9']+", fold_apostrophe(body[:70]))
    if len(words) < 5:
        return None
    for count in (7, 6, 5):
        pat = re.compile(r"\s+".join(re.escape(w) for w in words[:count]), re.I)
        m = pat.search(folded_ia)
        if not m:
            continue
        chunk = ia[m.start() : m.start() + 220]
        end = re.search(r"\.\s*(?:\n|$|\d+\.)", chunk)
        if not end:
            continue
        ext = _h4p2.norm_space(chunk[: end.start() + 1])
        if "]" in note:
            ext = note[: note.index("]") + 1] + " " + ext.split("]", 1)[-1].lstrip()
        if len(ext) <= len(note) + 3 or is_repair_target(ext, folded_ia):
            continue
        return ext
    return None


def is_repair_target(note: str, folded_ia: str) -> bool:
    if is_see_note_cross_ref(note):
        return not note.rstrip().endswith(".")
    return bool(
        is_clipped(note)
        or is_mid_sentence_cut(note)
        or is_hyphen_artifact(note)
        or is_unbalanced_parens(note)
        or is_witness_prefix(folded_ia, note)
    )


def clean_body(body: str) -> str:
    body = OCR_REF.sub(" ", body)
    body = re.sub(r"\s+", " ", body).strip()
    return body


def collapse(s: str) -> str:
    return re.sub(r"\s+", "", fold_apostrophe(s).lower())


def collapsed_pos(ia: str, idx: int) -> int:
    ci = 0
    for i, ch in enumerate(fold_apostrophe(ia).lower()):
        if not ch.isspace():
            if ci == idx:
                return i
            ci += 1
    return -1


def find_note_pos(ia: str, note: str) -> int:
    folded_ia = fold_apostrophe(ia)
    ia_c = collapse(ia)
    pos = _h4p2.find_note_pos(ia, note)
    if pos >= 0:
        return pos

    for size in (160, 120, 100, 80, 60, 45, 30):
        if len(note) < size:
            continue
        needle = collapse(note[:size])
        if len(needle) < 25:
            continue
        idx = ia_c.find(needle)
        if idx >= 0:
            return collapsed_pos(ia, idx)

    if "]" in note:
        lemma = note[: note.index("]") + 1]
        for variant in (
            lemma,
            lemma.replace("behavior", "behaviour"),
            lemma.replace("behaviour", "behavior"),
        ):
            core = variant.rstrip("]").strip()
            words = re.findall(r"[A-Za-z0-9']+", fold_apostrophe(core))
            if len(words) >= 2:
                pat = re.compile(r"\s+".join(re.escape(w) for w in words), re.I)
                m = pat.search(folded_ia)
                if m:
                    return m.start()

    body = note[note.index("]") + 1 :].strip() if "]" in note else note.strip()
    body = clean_body(body)
    body = re.sub(r"^\d{1,3}\.\s*", "", body)

    critic = re.match(r"^([A-Za-z .'.-]+):\s*(.{20,140})", body)
    if critic:
        quote = clean_body(critic.group(2))[:90]
        words = re.findall(r"[A-Za-z0-9']+", fold_apostrophe(quote))
        for n in (12, 10, 8, 6):
            if len(words) >= n:
                pat = re.compile(r"\s+".join(re.escape(w) for w in words[:n]), re.I)
                m = pat.search(folded_ia)
                if m:
                    return m.start()

    for size in (120, 100, 80, 60, 45, 30):
        if len(body) < size:
            continue
        pat = _h4p2.flex_pattern(body[:size])
        if pat:
            m = pat.search(folded_ia)
            if m:
                return m.start()
        needle = collapse(body[:size])
        if len(needle) >= 25:
            cidx = ia_c.find(needle)
            if cidx >= 0:
                return collapsed_pos(ia, cidx)

    # Line-break artifact: search prefix before trailing hyphen.
    n = note.rstrip()
    if re.search(r"-\s*$", n):
        prefix = re.sub(r"-\s*$", "", n)
        prefix = clean_body(prefix.split("]", 1)[-1] if "]" in prefix else prefix)
        words = re.findall(r"[A-Za-z0-9']+", fold_apostrophe(prefix[-80:]))
        for count in (10, 8, 6):
            if len(words) >= count:
                pat = re.compile(r"\s+".join(re.escape(w) for w in words[-count:]), re.I)
                m = pat.search(folded_ia)
                if m:
                    return m.start()
        # hyphenated line break in IA: "personifica-\n tion"
        if words:
            hy = re.compile(
                re.escape(words[-1]) + r"-\s*" + re.escape(words[-2][:4] if len(words) > 1 else ""),
                re.I,
            )
            m = hy.search(folded_ia)
            if m:
                return m.start()

    critic = re.match(r"^[A-Za-z .'.-]+:\s*(.{25,90})", body)
    needle = clean_body(critic.group(1) if critic else body[:70])
    if len(needle) >= 25:
        idx = folded_ia.lower().find(fold_apostrophe(needle[:45]).lower())
        if idx >= 0:
            return idx

    # Mid-sentence cut: anchor on distinctive tail words before truncation.
    tail_words = re.findall(r"[A-Za-z0-9']{3,}", fold_apostrophe(note))[-14:]
    for count in (12, 10, 8, 6):
        if len(tail_words) >= count:
            pat = re.compile(r"\s+".join(re.escape(w) for w in tail_words[-count:]), re.I)
            m = pat.search(folded_ia)
            if m:
                return m.start()

    return -1


def deinterleave_kj(text: str) -> str:
    text = KJ_HDR.sub(" ||| ", text)
    parts = [p.strip() for p in text.split("|||") if p.strip()]
    if not parts:
        return _h4p2.norm_space(text)
    out = parts[0]
    for part in parts[1:]:
        if len(re.findall(r"\b[A-Z][a-z]+\b", part)) > 8 and len(part) > 120:
            m = _h4p2.RESUME.search(part)
            if m:
                out += " " + part[m.start() :]
        else:
            out += " " + part
    return _h4p2.norm_space(out)


def extract_from_ia(ia: str, pos: int, json_note: str) -> str:
    start = max(0, pos - 160)
    chunk = ia[start : start + 7000]
    rel = pos - start
    m = re.search(r"(\d{1,3}\.\s*)?[\w .'\-]+\]\s*[A-Z(‘\"]", chunk[max(0, rel - 40) :], re.I)
    if m:
        chunk = chunk[max(0, rel - 40) + m.start() :]
    else:
        back = chunk[: rel + 20]
        lm = re.search(r"[\w .'\-]+\]", back[::-1])
        if lm:
            chunk = chunk[len(back) - lm.end() :]
    ext = _h4p2.truncate_footnote(deinterleave_kj(chunk))
    if is_see_note_cross_ref(json_note) and "]" in ext:
        tail = ext.split("]", 1)[-1]
        nm = NEXT_ENTRY.search(tail)
        if nm:
            ext = ext[: ext.index("]") + 1] + tail[: nm.start()]
    if "]" in json_note:
        json_lemma = json_note[: json_note.index("]") + 1]
        em = re.match(r"^(\d{1,3}\.\s*)?[^\]]+\]\s*", ext)
        ext = json_lemma + (" " + ext[em.end() :].lstrip() if em else " " + ext)
    return _h4p2.norm_space(ext)


def looks_contaminated(note: str) -> bool:
    return bool(
        re.search(r"ACT\s+[IVXLC\d]+\s*,\s*sc\.", note, re.I)
        and re.search(r"KING\s+JOHN", note, re.I)
        and len(note) > 4000
    )


def count_truncated(data: dict, folded_ia: str) -> int:
    return sum(
        1
        for item in collect_notes(data)
        if is_repair_target(item["note"], folded_ia)
    )


def repair(data: dict, ia: str, *, dry_run: bool = False) -> dict:
    folded_ia = fold_apostrophe(ia)
    stats = {
        "before": count_truncated(data, folded_ia),
        "repaired": 0,
        "unresolved": 0,
        "after": 0,
        "examples": [],
    }
    seen: set[tuple[str, str, int]] = set()

    for item in collect_notes(data):
        scene, line_key, note_idx = item["scene"], item["line"], item["note_idx"]
        note = item["note"]
        if not is_repair_target(note, folded_ia):
            continue
        key = (scene, line_key, note_idx)
        if key in seen:
            continue
        seen.add(key)

        ext = None
        if is_hyphen_artifact(note):
            ext = splice_hyphen(ia, note, next_note_pat=NEXT_ENTRY)
            if ext and is_repair_target(ext, folded_ia):
                ext = None

        pos = find_note_pos(ia, note) if ext is None else -1
        if ext is None and pos < 0:
            ext = complete_see_note(ia, note)
            if ext is None:
                stats["unresolved"] += 1
                continue
        elif ext is None:
            ext = extract_from_ia(ia, pos, note)
            if is_see_note_cross_ref(note):
                alt = complete_see_note(ia, note)
                if alt and len(alt) < len(ext):
                    ext = alt
        if len(ext) > max(4000, len(note) * 6):
            stats["unresolved"] += 1
            continue
        if looks_contaminated(ext):
            stats["unresolved"] += 1
            continue
        if len(ext) > len(note) * 4 and len(note) < 200:
            stats["unresolved"] += 1
            continue
        if len(ext) <= len(note) + 12 or is_repair_target(ext, folded_ia):
            stats["unresolved"] += 1
            continue

        if not dry_run:
            data[scene][line_key]["notes"][note_idx] = ext
        stats["repaired"] += 1
        if len(stats["examples"]) < 8:
            stats["examples"].append(
                {
                    "ref": item["ref"],
                    "before_len": len(note),
                    "after_len": len(ext),
                    "tail": ext[-120:],
                }
            )

    stats["after"] = stats["before"] - stats["repaired"] if dry_run else count_truncated(data, folded_ia)
    return stats


def sync_mirrors(text: str) -> None:
    if SITE_MIRROR.parent.is_dir():
        SITE_MIRROR.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    ia_id, stream = WITNESS_BY_PLAY[PLAY]
    ia_text, src = fetch_ia_text(ia_id, stream)
    if ia_text is None:
        print(f"ERROR: witness unavailable: {src}", file=sys.stderr)
        return 1

    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    folded = fold_apostrophe(ia_text)
    total_repaired = 0
    all_examples: list[dict] = []
    before = count_truncated(data, folded)
    for _ in range(4):
        stats = repair(data, ia_text, dry_run=args.dry_run)
        total_repaired += stats["repaired"]
        all_examples.extend(stats["examples"])
        if stats["repaired"] == 0:
            break
    stats["before"] = before
    stats["repaired"] = total_repaired
    stats["after"] = (
        count_truncated(data, folded) if not args.dry_run else before - total_repaired
    )
    stats["unresolved"] = stats["after"]
    stats["examples"] = all_examples[:8]
    stats.update({"play": PLAY, "ia_id": ia_id, "witness": src})

    print(
        f"{PLAY}: before={stats['before']} repaired={stats['repaired']} "
        f"after={stats['after']} unresolved={stats['unresolved']}"
    )
    for ex in stats["examples"]:
        print(
            f"  {ex['ref']}: {ex['before_len']} -> {ex['after_len']} …{ex['tail']}"
        )

    if args.dry_run:
        return 0

    if stats["repaired"]:
        if not BACKUP.is_file():
            shutil.copy2(JSON_PATH, BACKUP)
            print(f"Backup → {BACKUP.relative_to(ROOT)}")
        out = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        JSON_PATH.write_text(out, encoding="utf-8")
        sync_mirrors(out)
        print(f"Wrote {JSON_PATH.relative_to(ROOT)}")
        if SITE_MIRROR.is_file():
            print(f"Synced {SITE_MIRROR.relative_to(ROOT)}")

    audit = ROOT / "validation/king_john_trunc_repair.json"
    audit.write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {audit.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
