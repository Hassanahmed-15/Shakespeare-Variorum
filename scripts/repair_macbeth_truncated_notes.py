#!/usr/bin/env python3
"""Repair truncated Macbeth NV notes using IA witness newvariorumediti10shak."""

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
    fold_apostrophe,
    is_clipped as trunc_is_clipped,
    is_hard_truncation,
    is_hyphen_artifact,
    is_mid_sentence_cut,
    is_unbalanced_parens,
    is_witness_prefix,
)
from nv_ia_witness import fetch_ia_text  # noqa: E402
from nv_witness_map import WITNESS_BY_PLAY  # noqa: E402

JSON_PATH = ROOT / "Public/Data/macbeth_notes_cleaned_play.json"
SITE_MIRROR = ROOT / "My Website/Public/Data/macbeth_notes_cleaned_play.json"
BACKUP = JSON_PATH.with_suffix(".json.pre_clip_repair.backup")
PLAY = "Macbeth"
IA_ID, IA_STREAM = WITNESS_BY_PLAY[PLAY]

_H4P2 = importlib.util.spec_from_file_location(
    "h4p2", ROOT / "scripts/repair_henry_iv_part2_notes.py"
)
_h4p2 = importlib.util.module_from_spec(_H4P2)
_H4P2.loader.exec_module(_h4p2)

PLAY_BLOCK = re.compile(
    r"(?:THE\s+TRAGEDIE\s+OF\s+MACBETH|MACBETH)"
    r"\s*\[?\s*act\s+[ivxlc\d]+[\s,]*sc\.?\s*[ivxlc\d]+[^\]]*\]?",
    re.I,
)
PAGE_HDR = re.compile(r"(?:THE\s+TRAGEDIE\s+OF\s+)?MACBETH\s+\d{1,3}\s+", re.I)


def norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def fold_text(s: str) -> str:
    s = fold_apostrophe(s)
    s = re.sub(r"'\s+s\b", "'s", s, flags=re.I)
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


def skip_repair(note: str, signals: list[str]) -> bool:
    if signals == ["unbalanced_parens"] and len(note) > 1500:
        if re.search(r"—\s*Ed\.\]\s*$|\.\]\s*$", note.rstrip()):
            return True
    return False


def deinterleave_macbeth(text: str) -> str:
    text = PLAY_BLOCK.sub(" ||| ", text)
    text = PAGE_HDR.sub(" ||| ", text)
    parts = [p.strip() for p in text.split("|||") if p.strip()]
    if not parts:
        return norm_space(text)
    out = parts[0]
    for part in parts[1:]:
        if len(re.findall(r"\b[A-Z][a-z]+\b", part)) > 8 and len(part) > 120:
            m = _h4p2.RESUME.search(part)
            if m:
                out += " " + part[m.start() :]
        else:
            out += " " + part
    return norm_space(out)


def note_lemma(note: str) -> str:
    m = re.match(r"^(\d{1,3}\.\s*)?[^\]]{1,120}\]", note)
    return m.group(0) if m else ""


def note_body(note: str) -> str:
    lemma = note_lemma(note)
    if lemma:
        return note[len(lemma) :].strip()
    return note.strip()


def match_words(words: list[str]) -> str:
    parts = []
    for w in words:
        core = w.rstrip(".,;:!?")
        if not core:
            continue
        if core.endswith("'s"):
            base = re.escape(core[:-2])
            parts.append(base + r"['\u2019]?\s*s")
        else:
            parts.append(re.escape(core) + r"[.,;:!?]?")
    return r"\s+".join(parts)


def flex_words(text: str, n: int) -> str:
    words = re.findall(r"[A-Za-z0-9\u2019']+", fold_apostrophe(text))
    return " ".join(words[:n])


def lemma_variants(lemma: str) -> list[str]:
    variants = [lemma, lemma.replace("]", " ]")]
    num_m = re.match(r"^(\d{1,3})\.\s*(.+)", lemma.strip())
    if num_m:
        variants.append(f"{num_m.group(1)}.  {num_m.group(2)}")
        variants.append(f"{num_m.group(1)}. {num_m.group(2)}")
    core = lemma.strip().rstrip("]").strip()
    core = re.sub(r"\.{2,}|…", " ", core)
    core = re.sub(r"\s+", " ", core).strip()
    if core and core not in variants:
        variants.append(core + "]")
        variants.append(core)
    return variants


def find_lemma_pos(folded_ia: str, note: str) -> int:
    lemma = note_lemma(note)
    if not lemma:
        return -1
    for variant in lemma_variants(lemma):
        pos = folded_ia.find(fold_apostrophe(variant))
        if pos >= 0:
            return pos
        lw = flex_words(variant.replace("]", ""), 4)
        if lw:
            pat = re.compile(r"\s+".join(re.escape(w) for w in lw.split()), re.I)
            m = pat.search(folded_ia)
            if m:
                return m.start()
        words = re.findall(r"[A-Za-z0-9\u2019']+", fold_apostrophe(variant))
        if len(words) >= 3:
            pat = re.compile(
                r"\s+".join(re.escape(w) for w in words[:2])
                + r".{0,40}"
                + re.escape(words[-1]),
                re.I,
            )
            m = pat.search(folded_ia)
            if m:
                return m.start()
    return -1


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


def find_body_pos(folded_ia: str, note: str, ia: str | None = None) -> int:
    body = note_body(note)
    for n in (14, 10, 8, 6):
        fw = flex_words(body, n)
        if len(fw.split()) < 4:
            continue
        pat = re.compile(r"\s+".join(re.escape(w) for w in fw.split()), re.I)
        m = pat.search(folded_ia)
        if m:
            return m.start()
    if ia is not None:
        ia_c = collapse(ia)
        for size in (100, 80, 60, 45, 30):
            if len(body) < size:
                continue
            needle = collapse(body[:size])
            if len(needle) < 25:
                continue
            idx = ia_c.find(needle)
            if idx >= 0:
                pos = collapsed_pos(ia, idx)
                if pos >= 0:
                    return pos
    return -1


def find_tail_anchor(folded_ia: str, note: str) -> int:
    body = fold_text(note_body(note))
    words = body.split()
    for n in range(min(15, len(words)), 4, -1):
        ew = words[-n:]
        if ew[-1].endswith("'s"):
            ew = ew[:-1]
        if len(ew) < 4:
            continue
        pat = re.compile(r" ".join(re.escape(w) for w in ew), re.I)
        m = pat.search(folded_ia)
        if m:
            return max(0, m.start() - 200)
    return -1


def find_note_pos(ia: str, note: str) -> int:
    folded_ia = fold_apostrophe(ia)
    lemma_pos = find_lemma_pos(folded_ia, note)
    if lemma_pos >= 0:
        return lemma_pos
    for finder in (
        lambda f, n: find_body_pos(f, n, ia),
        find_tail_anchor,
    ):
        pos = finder(folded_ia, note)
        if pos >= 0:
            return pos
    return _h4p2.find_note_pos(ia, note)


def footnote_end(deint: str, min_len: int = 40) -> int:
    for pat in (
        r"—\s*Ed\.\]",
        r"—\s*\[Ed\.\]",
        r"\[Ed\.\]\s*$",
        r"\.\s*—\s*Ed\.\]",
    ):
        for m in re.finditer(pat, deint):
            if m.end() > min_len:
                return m.end()
    for m in re.finditer(r"\s(\d{1,3})\.\s+([A-Z][A-Za-z .'-]+\])", deint[min_len:]):
        label = m.group(2)
        if not re.search(r"^[IVXLC]+\s*,\s*[ivxlc\d]", label):
            return min_len + m.start()
    for m in re.finditer(r"[.!?;]\s*$", deint):
        if m.end() > min_len:
            return m.end()
    return min(len(deint), 12000)


def extract_macbeth_note(ia: str, pos: int, json_note: str) -> str:
    start = max(0, pos - 80)
    raw = ia[start : start + 30000]
    m = re.search(r"(\d{1,3}\.\s*)?[\w .'-]+\]\s*[A-Z(\[\"']", raw, re.I)
    if m and m.start() <= (pos - start) + 40:
        raw = raw[m.start() :]
    deint = deinterleave_macbeth(raw)
    end = footnote_end(deint, min_len=max(30, len(note_lemma(json_note))))
    ext = deint[:end].strip()
    lemma = note_lemma(json_note)
    if lemma:
        em = re.match(r"^(\d{1,3}\.\s*)?[^\]]+\]\s*", ext)
        ext = lemma + (" " + ext[em.end() :].lstrip() if em else " " + ext)
    return norm_space(ext)


def complete_mid_sentence(ia: str, note: str, folded_ia: str) -> str | None:
    body = fold_text(note_body(note))
    words = body.split()
    lemma_pos = find_lemma_pos(folded_ia, note)
    body_pos = find_body_pos(folded_ia, note, ia)
    anchor = lemma_pos if lemma_pos >= 0 else body_pos
    best: str | None = None
    for n in range(min(20, len(words)), 4, -1):
        ew = words[-n:]
        if ew[-1].endswith("'s"):
            ew = ew[:-1]
        if len(ew) < 4:
            continue
        pat = re.compile(match_words(ew), re.I)
        for m in pat.finditer(folded_ia):
            if anchor >= 0 and abs(m.start() - anchor) > max(len(note) * 3, 12000):
                continue
            tail_raw = ia[m.end() : m.end() + 8000]
            tail = deinterleave_macbeth(tail_raw)
            end = footnote_end(tail, min_len=20)
            tail = tail[:end].strip()
            if not tail:
                continue
            merged = norm_space(note.rstrip() + " " + tail)
            if len(merged) > len(note) + 10 and (
                best is None or len(merged) > len(best)
            ):
                best = merged
    return best


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
    return bool(
        re.search(r"THE\s+TRAGEDIE\s+OF\s+MACBETH", note, re.I)
        and re.search(r"\[act\s+[ivxlc\d]+", note, re.I)
    )


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
    if len(old) < 250 and len(new) > max(600, len(old) * 4):
        return False
    if len(old) > 800 and len(new) < len(old) * 0.45:
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
                if skip_repair(note, signals):
                    stats["skipped"] += 1
                    continue

                ext: str | None = None
                if "mid_sentence_cut" in signals:
                    ext = complete_mid_sentence(ia, note, folded_ia)
                if ext is None:
                    pos = find_note_pos(ia, note)
                    if pos >= 0:
                        candidate = extract_macbeth_note(ia, pos, note)
                        if candidate and (
                            "mid_sentence_cut" not in signals
                            or len(candidate) <= max(20000, len(note) * 4)
                        ):
                            ext = candidate
                if ext is None and "mid_sentence_cut" in signals:
                    pos = find_body_pos(folded_ia, note, ia)
                    if pos >= 0:
                        ext = complete_mid_sentence(ia, note, folded_ia)

                if ext is None or len(ext) > max(20000, len(note) * 6) or len(ext) < 15:
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
    after = stats["after"] if not args.dry_run else before - stats["repaired"]

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
        print(f"Wrote {JSON_PATH.relative_to(ROOT)} + mirror")

    audit = ROOT / "validation/macbeth_truncation_repair.json"
    audit.write_text(
        json.dumps(
            {"play": PLAY, "ia_id": IA_ID, "witness": src, **stats},
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
