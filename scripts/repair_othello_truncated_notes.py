#!/usr/bin/env python3
"""Repair truncated Othello NV notes using IA witness newvariorumediti13shak."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_nv_truncation import (  # noqa: E402
    collect_notes,
    fold_apostrophe,
    is_clipped as trunc_is_clipped,
    is_hard_truncation,
    is_hyphen_artifact,
    is_mid_sentence_cut,
    is_unbalanced_parens,
    is_witness_prefix,
)
from nv_ia_witness import fetch_ia_text  # noqa: E402

JSON_PATH = ROOT / "Public/Data/othello_notes_folger.json"
MIRROR_PATH = ROOT / "Public/Data/othello_notes.json"
SITE_MIRROR = ROOT / "My Website/Public/Data/othello_notes_folger.json"
BACKUP = JSON_PATH.with_suffix(".json.pre_clip_repair.backup")
IA_ID = "newvariorumediti13shak"
IA_STREAM = f"{IA_ID}_djvu.txt"

PLAY_BLOCK = re.compile(
    r"(?:THE\s+TRAG\w*\s+OF\s+OTHELLO|THE\s+MOORE\s+OF\s+VENICE)"
    r"\s*\[?\s*act\s+[ivxlc\d]+[\s,]*sc\.?\s*[ivxlc\d]+[^\]]*\]?",
    re.I,
)
PLAY_LINE = re.compile(
    r"\b(Heauen|Appetite|pleafe|Defdemona|Caffio|Moore)\b",
    re.I,
)
SPELLING_VARIANTS = (("Bataile", "Battaile"), ("Bataille", "Battaile"))


def norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def union_signals(folded_ia: str, note: str) -> list[str]:
    signals: list[str] = []
    if trunc_is_clipped(note):
        signals.append("is_clipped")
    if is_hard_truncation(note):
        signals.append("hard_truncation")
    if is_mid_sentence_cut(note):
        signals.append("mid_sentence_cut")
    if is_hyphen_artifact(note):
        signals.append("hyphen_artifact")
    if is_unbalanced_parens(note):
        signals.append("unbalanced_parens")
    if is_witness_prefix(folded_ia, note):
        signals.append("witness_prefix")
    return signals


def count_union(data: dict, folded_ia: str) -> int:
    return sum(1 for item in collect_notes(data) if union_signals(folded_ia, item["note"]))


def skip_repair(folded_ia: str, note: str, signals: list[str]) -> bool:
    if signals == ["unbalanced_parens"] and len(note) > 1500:
        if re.search(r"—\s*Ed\.\]\s*$|\.\]\s*$", note.rstrip()):
            return True
    return False


def deinterleave_othello(text: str) -> str:
    text = PLAY_BLOCK.sub(" ||| ", text)
    parts = [p.strip() for p in text.split("|||") if p.strip()]
    if not parts:
        return norm_space(text)
    out = parts[0]
    for part in parts[1:]:
        if len(re.findall(r"\b[A-Z][a-z]+\b", part)) > 10 and len(part) > 100:
            m = re.search(
                r"(?:[a-z]{4,}[\u2018\u2019',])|(?:\u2014|—)\s*\[|(?:\u2014|—)\s*$",
                part,
                re.I,
            )
            if m:
                out += " " + part[m.start() :]
        else:
            out += " " + part
    return norm_space(out)


def note_lemma(note: str) -> str:
    if "]" not in note:
        return ""
    return note[: note.index("]") + 1]


def note_body(note: str) -> str:
    if "]" in note:
        return note[note.index("]") + 1 :].strip()
    return note.strip()


def flex_words(text: str, n: int) -> str:
    words = re.findall(r"[A-Za-z0-9\u2019']+", fold_apostrophe(text))
    return " ".join(words[:n])


def _body_anchor_score(folded_ia: str, pos: int, note: str) -> int:
    after = folded_ia[pos : pos + 160]
    rb = after.find("]")
    if rb < 0:
        return 0
    seg = after[rb + 1 : rb + 120].lower()
    words = flex_words(note_body(note), 5).split()
    if not words:
        return 1
    score = 0
    for i, w in enumerate(words[:4]):
        idx = seg.find(w.lower())
        if idx >= 0:
            score += 10 - i
            if i == 0 and idx < 25:
                score += 5
    return score


def _match_has_body(folded_ia: str, pos: int, note: str) -> bool:
    return _body_anchor_score(folded_ia, pos, note) >= 10


def find_lemma_pos(folded_ia: str, note: str) -> int:
    lemma = note_lemma(note)
    if not lemma:
        return -1
    variants = [lemma]
    for old, new in SPELLING_VARIANTS:
        if old in lemma:
            variants.append(lemma.replace(old, new))
    num_m = re.match(r"^(\d{1,3})\.\s*(.+)", lemma.strip())
    if num_m:
        variants.append(f"{num_m.group(1)}.  {num_m.group(2)}")
        variants.append(f"{num_m.group(1)}. {num_m.group(2)}")
    # IA often prefixes line numbers: "22, 23. Florentine..."
    core = re.sub(r"^\d{1,3}\.\s*", "", lemma.strip())
    if core != lemma.strip():
        variants.append(core)
    if ", . . ." in core or ",..." in core:
        stem = core.split(",")[0]
        bw = flex_words(note_body(note), 2).split()
        if len(bw) >= 2:
            pat = re.compile(
                re.escape(stem) + r".{0,40}?\]\s*" + r"\s+".join(re.escape(w) for w in bw[:2]),
                re.I,
            )
            m = pat.search(folded_ia)
            if m and _match_has_body(folded_ia, m.start(), note):
                return m.start()

    best = -1
    best_score = 0
    for variant in variants:
        v = fold_apostrophe(variant.replace("]", " ]"))
        start = 0
        while True:
            pos = folded_ia.find(v, start)
            if pos < 0:
                break
            score = _body_anchor_score(folded_ia, pos, note)
            if score > best_score:
                best_score = score
                best = pos
            start = pos + 1
        lw = flex_words(variant.replace("]", ""), 4)
        if lw:
            pat = re.compile(r"\s+".join(re.escape(w) for w in lw.split()), re.I)
            for m in pat.finditer(folded_ia):
                score = _body_anchor_score(folded_ia, m.start(), note)
                if score > best_score:
                    best_score = score
                    best = m.start()
    return best if best_score >= 10 else -1


def find_body_pos(folded_ia: str, note: str) -> int:
    body = note_body(note)
    for n in (14, 10, 8, 6):
        fw = flex_words(body, n)
        if len(fw.split()) < 4:
            continue
        pat = re.compile(r"\s+".join(re.escape(w) for w in fw.split()), re.I)
        m = pat.search(folded_ia)
        if m:
            return m.start()
    return -1


def find_note_pos(ia: str, note: str) -> int:
    folded_ia = fold_apostrophe(ia)
    pos = find_lemma_pos(folded_ia, note)
    if pos >= 0:
        return pos
    return find_body_pos(folded_ia, note)


def footnote_end(deint: str, min_len: int = 40, *, short_note: bool = False) -> int:
    """Return slice end index for a deinterleaved footnote chunk."""
    tail = deint[min_len:]
    if short_note:
        for m in re.finditer(r"[.;]\s+", tail):
            end = min_len + m.end() - 1
            rest = deint[end + 1 : end + 40].lstrip()
            if re.match(r"\d{1,3}(?:\.\s*|\s+)[A-Za-z(\[]", rest):
                return end + 1
            if re.match(r"(?:ICT|THE|ACT|More then|And I \(of)", rest, re.I):
                return end + 1
        for m in re.finditer(r"[.;]\s*$", deint):
            if m.end() > min_len:
                return m.end()
    for pat in (
        r"—\s*Ed\.\]",
        r"—\s*\[Ed\.\]",
        r"\[Ed\.\]\s*$",
        r"\.\s*—\s*Ed\.\]",
    ):
        for m in re.finditer(pat, tail):
            return min_len + m.end()
    for m in re.finditer(r"\s(\d{1,3})\.\s+([A-Z][A-Za-z .'-]+\])", tail):
        label = m.group(2)
        if not re.search(r"^[IVXLC]+\s*,\s*[ivxlc\d]", label):
            return min_len + m.start()
    for m in re.finditer(r"[.!?;]\s*$", deint):
        if m.end() > min_len:
            return m.end()
    return min(len(deint), 8000)


def extract_othello_note(ia: str, pos: int, json_note: str) -> str:
    raw = ia[pos : pos + 25000]
    lm = re.match(r"(\d{1,3}\.\s*)?[\w .'-,]+\]", raw, re.I)
    if lm:
        raw = raw[lm.start() :]
    deint = deinterleave_othello(raw)
    min_len = max(40, len(note_lemma(json_note)) + 10)
    end = footnote_end(deint, min_len=min_len, short_note=len(json_note) < 250)
    ext = deint[:end].strip()
    lemma = note_lemma(json_note)
    if lemma:
        em = re.match(r"^(\d{1,3}\.\s*)?[^\]]+\]\s*", ext)
        ext = lemma + (" " + ext[em.end() :].lstrip() if em else " " + ext)
    return norm_space(ext)


def prefix_overlap(old: str, new: str, words: int = 8) -> bool:
    ob = flex_words(note_body(old), words)
    nb = flex_words(note_body(new), words)
    if not ob or not nb:
        return fold_apostrophe(old[:80]) in fold_apostrophe(new[:200])
    ow = ob.split()
    nw = nb.split()
    shared = sum(1 for a, b in zip(ow, nw) if a.lower() == b.lower())
    return shared >= min(len(ow), len(nw), 4)


def looks_contaminated(note: str) -> bool:
    if len(note) < 800:
        if PLAY_LINE.search(note):
            return True
        if re.search(r"THE\s+MOORE\s+OF\s+VENICE", note, re.I) and re.search(
            r"\[act", note, re.I
        ):
            return True
    tail = note[-500:]
    if PLAY_LINE.search(tail):
        return True
    if len(note) < 800 and re.search(
        r"THE\s+MOORE\s+OF\s+VENICE", tail, re.I
    ) and re.search(r"\[act", tail, re.I):
        return True
    return False


def is_improvement(old: str, new: str, folded_ia: str) -> bool:
    if looks_contaminated(new):
        return False
    if not prefix_overlap(old, new):
        return False
    old_lemma = note_lemma(old)
    new_lemma = note_lemma(new)
    if old_lemma and new_lemma and fold_apostrophe(old_lemma) != fold_apostrophe(new_lemma):
        return False
    old_s = union_signals(folded_ia, old)
    new_s = union_signals(folded_ia, new)
    if len(old) < 250 and len(new) > max(350, len(old) * 8):
        return False
    if len(old) > 150 and len(new) < len(old) * 0.7:
        return False
    if not new_s:
        return True
    if len(new_s) < len(old_s):
        return True
    if "mid_sentence_cut" in old_s and "mid_sentence_cut" not in new_s:
        return True
    if "witness_prefix" in old_s and "witness_prefix" not in new_s:
        return True
    if len(new) > len(old) + 15 and len(new_s) <= len(old_s):
        return True
    return False


def repair(data: dict, ia: str, folded_ia: str, *, dry_run: bool = False) -> dict:
    stats = {
        "before": count_union(data, folded_ia),
        "repaired": 0,
        "unresolved": 0,
        "skipped": 0,
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
                signals = union_signals(folded_ia, note)
                if not signals:
                    continue
                if skip_repair(folded_ia, note, signals):
                    stats["skipped"] += 1
                    continue
                if not note_lemma(note) and not re.match(
                    r"^[A-Z][A-Za-z .'-]+:", note.strip()
                ):
                    stats["unresolved"] += 1
                    continue
                pos = find_note_pos(ia, note)
                if pos < 0:
                    stats["unresolved"] += 1
                    continue
                ext = extract_othello_note(ia, pos, note)
                if len(ext) > 20000 or len(ext) < 15:
                    stats["unresolved"] += 1
                    continue
                if not is_improvement(note, ext, folded_ia):
                    stats["unresolved"] += 1
                    continue
                if not dry_run:
                    notes[i] = ext
                stats["repaired"] += 1
                if len(stats["examples"]) < 8:
                    stats["examples"].append(
                        {
                            "before_len": len(note),
                            "after_len": len(ext),
                            "signals": signals,
                            "tail": ext[-100:],
                        }
                    )

    stats["after"] = count_union(data, folded_ia)
    return stats


def sync_mirrors(text: str) -> None:
    MIRROR_PATH.write_text(text, encoding="utf-8")
    if SITE_MIRROR.parent.is_dir():
        SITE_MIRROR.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    ia, src = fetch_ia_text(IA_ID, IA_STREAM)
    if ia is None:
        print(f"ERROR: witness unavailable ({src})", file=sys.stderr)
        return 1

    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    folded_ia = fold_apostrophe(ia)
    before = count_union(data, folded_ia)

    stats = repair(data, ia, folded_ia, dry_run=args.dry_run)
    after = stats["after"] if not args.dry_run else before

    print(f"IA witness: {IA_ID} ({src})")
    print(f"before|repaired|after|unresolved: {before}|{stats['repaired']}|{after}|{stats['unresolved']}")
    if stats.get("skipped"):
        print(f"skipped (false-positive paren): {stats['skipped']}")
    for ex in stats["examples"]:
        print(f"  + {ex['before_len']} -> {ex['after_len']} ({ex['signals']}) …{ex['tail']}")

    if args.dry_run:
        return 0

    if stats["repaired"]:
        if not BACKUP.is_file():
            shutil.copy2(JSON_PATH, BACKUP)
            print(f"Backup → {BACKUP.relative_to(ROOT)}")
        out = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        JSON_PATH.write_text(out, encoding="utf-8")
        sync_mirrors(out)
        print(f"Wrote {JSON_PATH.relative_to(ROOT)} + mirrors")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
