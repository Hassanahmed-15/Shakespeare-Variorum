#!/usr/bin/env python3
"""Repair truncated Henry IV Part 1 variorum notes from IA editi21 witness."""

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
    is_hard_truncation,
    is_hyphen_artifact,
    is_mid_sentence_cut,
    is_unbalanced_parens,
    is_witness_prefix,
)
from nv_ia_witness import fetch_ia_text, fold_apostrophe  # noqa: E402
from nv_witness_map import WITNESS_BY_PLAY  # noqa: E402

JSON_PATH = ROOT / "Public/Data/henry_iv_part1.json"
BACKUP = JSON_PATH.with_suffix(".json.pre_clip_repair.backup")
SITE_MIRROR = ROOT / "My Website/Public/Data/henry_iv_part1.json"
IA_ID, IA_STREAM = WITNESS_BY_PLAY["Henry IV, Part 1"]

_H4P2 = importlib.util.spec_from_file_location(
    "h4p2_repair", ROOT / "scripts/repair_henry_iv_part2_notes.py"
)
_h4p2 = importlib.util.module_from_spec(_H4P2)
_H4P2.loader.exec_module(_h4p2)

ACT_BLOCK = re.compile(
    r"\[?\s*ACT\s+[IVXLC\d]+\s*,?\s*(?:SC\.?|SCENE)\.?\s*[ivxlc\d]+\.?\]?\s*",
    re.I,
)
PAGE_HDR = re.compile(
    r"HENRY\s+THE\s+FOURTH(?:\s*,\s*PART\s+I)?(?:\s+\d{1,3})?\s*",
    re.I,
)
NEXT_NOTE = re.compile(r"\s(\d{1,3}\.\s+[\w .'\-\u2018\u2019]+\])", re.I)
FOOTNOTE_START = re.compile(r"(\d{1,3}\.\s*)?[\w .'\-\u2018\u2019]+\]\s*", re.I)
VERSE_LINE = re.compile(
    r"^[A-Z\u2018\u201c][a-z].{10,100}[.!?]?\s*$"
)
COLLATION = re.compile(r"^\d{1,3}\.\s+\w.+\]\s+\w", re.M)


def union_signals(note: str, folded_ia: str) -> list[str]:
    sig: list[str] = []
    if is_clipped(note):
        sig.append("is_clipped")
    if is_hard_truncation(note):
        sig.append("hard_truncation")
    if is_mid_sentence_cut(note):
        sig.append("mid_sentence_cut")
    if is_hyphen_artifact(note):
        sig.append("hyphen_artifact")
    if is_unbalanced_parens(note):
        sig.append("unbalanced_parens")
    if is_witness_prefix(folded_ia, note):
        sig.append("witness_prefix")
    return sig


def should_attempt(sig: list[str], note: str) -> bool:
    if not sig:
        return False
    if sig == ["hard_truncation"]:
        n = note.rstrip()
        if re.search(r"(?:Ed\.|\]|—|\d+\.)$", n) and len(n) > 40:
            return False
        if n.endswith(".") and len(n) < 100:
            return False
    return True


def _lemma_words(lemma: str) -> list[str]:
    """Tokenize a note lemma, preserving ellipsis gaps."""
    core = re.sub(r"\s*\.\s*\.\s*\.\s*", " <ELL> ", lemma)
    raw = re.findall(r"[A-Za-z0-9\u2019']+|<ELL>", _h4p2.fold_apostrophe(core))
    out: list[str] = []
    for w in raw:
        if w == "<ELL>":
            out.append("<ELL>")
        else:
            out.append(w)
    return out


def _flex(words: list[str]) -> re.Pattern[str] | None:
    if not words:
        return None
    parts: list[str] = []
    for w in words:
        if w == "<ELL>":
            parts.append(r"(?:\.\s*){2,3}")
        else:
            parts.append(re.escape(w))
    return re.compile(r"\s+".join(parts), re.I)


def find_lemma_pos(ia: str, note: str) -> int:
    folded = _h4p2.fold_apostrophe(ia)
    if "]" not in note:
        return _h4p2.find_note_pos(ia, note)

    lemma = note[: note.index("]") + 1]
    body = re.sub(r"^\d{1,3}\.\s*", "", note[note.index("]") + 1 :].strip())
    body_words = re.findall(r"[A-Za-z0-9\u2019']+", _h4p2.fold_apostrophe(body))

    for n in (12, 10, 8, 6, 4):
        if len(body_words) < n:
            continue
        anchor = _lemma_words(lemma) + body_words[:n]
        pat = _flex(anchor)
        if pat:
            m = pat.search(folded)
            if m:
                return m.start()

    lemma_words = _lemma_words(lemma.replace("]", " ]"))
    pat = _flex(lemma_words)
    if pat:
        best = -1
        best_score = -1
        for m in pat.finditer(folded):
            tail = folded[m.end() : m.end() + 120]
            score = sum(
                1
                for w in body_words[:6]
                if re.search(r"\b" + re.escape(w.lower()) + r"\b", tail.lower())
            )
            if score > best_score:
                best_score = score
                best = m.start()
        if best_score >= 2:
            return best

    return _h4p2.find_note_pos(ia, note)


CONTINUATION = re.compile(
    r"^(?:sometimes|So,|See |N\.\s*E\.\s*D)",
)


def is_prose_continuation(ln: str) -> bool:
    if CONTINUATION.match(ln):
        return True
    if ln[0:1].islower() or ln[0:1] in "\u2018\u2019(":
        return is_scholarly_line(ln) or bool(
            re.search(r"\(ed\.\s*\d{4}\)|—\s*[A-Z(]", ln)
        )
    return False
COLLATION_LINE = re.compile(r"^\d{1,3}\.\s+[\w .'-]+\]\s+\S", re.I)


def is_variant_collation(ln: str) -> bool:
    if re.match(r"^(?:by|in|et)\s+MS\.", ln, re.I):
        return True
    if re.match(r"^[\w .'-]+\]\s+(?:Q[0-9qFf]|soldier|soldiour|lead|leuy|wombs)", ln, re.I):
        return True
    return bool(
        re.search(
            r"\]\s*(?:Q[0-9qFf]|His\.|Thirlby|Var\.|MS\.|soldiour|leauy|mothers|wombe)",
            ln,
            re.I,
        )
    )


def is_scholarly_line(ln: str) -> bool:
    if COLLATION_LINE.match(ln) or is_variant_collation(ln):
        return False
    return bool(re.search(r"\(ed\.\s*\d{4}\)|—\s*[A-Z(]|—\s*Ed\.", ln))


def deinterleave_h4p1(text: str) -> str:
    text = ACT_BLOCK.sub("\x00", text)
    text = PAGE_HDR.sub("\x00", text)
    parts = [p.strip() for p in text.split("\x00") if p.strip()]
    if not parts:
        return _h4p2.norm_space(text)

    out = parts[0]
    for part in parts[1:]:
        lines = [ln.strip() for ln in part.split("\n") if ln.strip()]
        if not lines:
            continue

        start = 0
        for j, ln in enumerate(lines):
            if COLLATION_LINE.match(ln) or is_variant_collation(ln):
                continue
            if VERSE_LINE.match(ln) and not is_scholarly_line(ln):
                continue
            if CONTINUATION.match(ln) or is_prose_continuation(ln):
                start = j
                break
        else:
            continue

        fragment = " ".join(lines[start:])
        if fragment:
            out += " " + fragment

    return _h4p2.norm_space(out)


def truncate_h4p1(text: str, min_len: int = 40) -> str:
    text = text.strip()
    m0 = FOOTNOTE_START.match(text)
    body_start = m0.end() if m0 else 0

    for pat in (
        r"—\s*Ed\.\]",
        r"—\s*\[Ed\.\]",
        r"\[Ed\.\]\s*$",
        r"\.\s*—\s*Ed\.\]",
    ):
        for m in re.finditer(pat, text):
            if m.end() > min_len:
                candidate = text[: m.end()].strip()
                nm = NEXT_NOTE.search(candidate[body_start + 20 :])
                if nm and nm.start() < len(candidate) - 30:
                    candidate = candidate[: body_start + 20 + nm.start()].strip()
                return candidate

    for m in re.finditer(r"\.\s*—\s*(?=[A-Z\[\"'\u2018(]|$)", text):
        if min_len < m.end() < 2500:
            candidate = text[: m.end()].strip()
            nm = NEXT_NOTE.search(candidate[body_start + 20 :])
            if nm and nm.start() < len(candidate) - 30:
                candidate = candidate[: body_start + 20 + nm.start()].strip()
            return candidate

    nm = NEXT_NOTE.search(text, body_start + min_len)
    if nm:
        return text[: nm.start()].strip()

    return _h4p2.truncate_footnote(text, min_len)


def norm_key(s: str) -> str:
    return re.sub(r"\s+", " ", _h4p2.fold_apostrophe(s)).strip().lower()


def extract_from_ia(ia: str, pos: int, json_note: str) -> str:
    start = max(0, pos - 100)
    chunk = ia[start : start + 7000]
    m = FOOTNOTE_START.search(chunk)
    if m and m.start() <= (pos - start) + 15:
        chunk = chunk[m.start() :]

    ext = truncate_h4p1(deinterleave_h4p1(chunk))
    if "]" in json_note:
        json_lemma = json_note[: json_note.index("]") + 1]
        em = re.match(r"^(\d{1,3}\.\s*)?[^\]]+\]\s*", ext)
        ext = json_lemma + (" " + ext[em.end() :].lstrip() if em else " " + ext)

    return _h4p2.norm_space(ext)


def looks_bad(note: str) -> bool:
    if _h4p2.looks_contaminated(note):
        return True
    if re.search(
        r"(Againft|fheathed|maifler|Chrift|foldiour|leauy|wombe|chafe|pagans|"
        r"Exeunt|Enter the prince|THE HISTORIE OF|rob them and bind)",
        note,
        re.I,
    ):
        return True
    if re.search(r"\bQ[1-9q]\b.*Var\.", note) and len(note) < 500:
        # Collation-only grab without apparatus prose
        if not re.search(r"\(ed\.\s*\d{4}\)|— [A-Z]", note):
            return True
    return False


def is_valid_repair(old: str, new: str) -> bool:
    if len(new) <= len(old):
        return False
    if len(new) > max(3500, len(old) * 6):
        return False
    if looks_bad(new):
        return False
    if not norm_key(old)[: min(60, len(old))] in norm_key(new):
        return False
    if is_clipped(new):
        return False
    gain = len(new) - len(old)
    if gain <= 8 and not re.search(r"[.!?]\s*$", new) and gain < 3:
        return False
    return True


def count_union(data: dict, folded_ia: str) -> int:
    return sum(
        1 for item in collect_notes(data) if union_signals(item["note"], folded_ia)
    )


def repair(data: dict, ia: str, folded_ia: str, *, dry_run: bool = False) -> dict:
    stats = {"repaired": 0, "unresolved": 0, "attempted": 0, "examples": []}

    for scene, scene_data in data.items():
        if not str(scene).startswith("ACT") or not isinstance(scene_data, dict):
            continue
        for line_key, line_data in scene_data.items():
            if not isinstance(line_data, dict):
                continue
            notes = line_data.get("notes") or []
            for i, note in enumerate(notes):
                sig = union_signals(note, folded_ia)
                if not should_attempt(sig, note):
                    continue
                stats["attempted"] += 1

                pos = find_lemma_pos(ia, note)
                if pos < 0:
                    stats["unresolved"] += 1
                    continue

                ext = extract_from_ia(ia, pos, note)
                if is_valid_repair(note, ext):
                    if not dry_run:
                        notes[i] = ext
                    stats["repaired"] += 1
                    if len(stats["examples"]) < 6:
                        stats["examples"].append(
                            {
                                "ref": f"{scene} / line {line_key} / note {i}",
                                "before_len": len(note),
                                "after_len": len(ext),
                                "tail": ext[-100:],
                            }
                        )
                else:
                    stats["unresolved"] += 1

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
    folded = fold_apostrophe(ia)
    before = count_union(data, folded)
    stats = repair(data, ia, folded, dry_run=args.dry_run)
    after = count_union(data, folded) if args.dry_run else before

    if not args.dry_run:
        after = count_union(data, folded)
        if stats["repaired"]:
            if not BACKUP.is_file():
                shutil.copy2(JSON_PATH, BACKUP)
            out = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
            JSON_PATH.write_text(out, encoding="utf-8")
            sync_mirrors(out)

    audit = {
        "play": "Henry IV, Part 1",
        "json_file": str(JSON_PATH.relative_to(ROOT)),
        "ia_id": IA_ID,
        "witness": src,
        "before": before,
        "repaired": stats["repaired"],
        "after": after,
        "unresolved": stats["unresolved"],
        "attempted": stats["attempted"],
        "examples": stats["examples"],
    }
    audit_path = ROOT / "validation/henry_iv_part1_repair.json"
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(
        f"before|{before}|repaired|{stats['repaired']}|after|{after}|"
        f"unresolved|{stats['unresolved']}"
    )
    print(f"Wrote {audit_path.relative_to(ROOT)}")
    print(f"witness: {IA_ID} ({src})")
    for ex in stats["examples"]:
        print(
            f"  + {ex['ref']}: {ex['before_len']} -> {ex['after_len']} …{ex['tail']}"
        )
    if not args.dry_run and stats["repaired"]:
        print(f"Wrote {JSON_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
