#!/usr/bin/env python3
"""Repair truncated King Lear NV notes using nv_truncation_audit signals + IA witnesses."""

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
    is_clipped,
    is_hard_truncation,
    is_hyphen_artifact,
    is_mid_sentence_cut,
    is_unbalanced_parens,
    is_witness_prefix,
)
from nv_ia_witness import fetch_ia_text, fold_apostrophe  # noqa: E402
from nv_witness_map import WITNESS_BY_PLAY, WITNESS_CANDIDATES  # noqa: E402

JSON_PATH = ROOT / "Public/Data/kinglear_notes.json"
BACKUP = JSON_PATH.with_suffix(".json.pre_clip_repair.backup")
SITE_MIRROR = ROOT / "My Website/Public/Data/kinglear_notes.json"

_H4P2 = importlib.util.spec_from_file_location(
    "h4p2_repair", ROOT / "scripts/repair_henry_iv_part2_notes.py"
)
_h4p2 = importlib.util.module_from_spec(_H4P2)
_H4P2.loader.exec_module(_h4p2)


def is_union_truncated(note: str, folded_ia: str) -> bool:
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
    if is_witness_prefix(folded_ia, note):
        return True
    return False


def norm_ws(s: str) -> str:
    return _h4p2.norm_space(re.sub(r"\s+", " ", s))


def load_witnesses() -> dict[str, str]:
    out: dict[str, str] = {}
    seen: set[tuple[str, str]] = set()
    for ia_id, stream in [WITNESS_BY_PLAY["King Lear"]] + WITNESS_CANDIDATES.get("King Lear", []):
        if (ia_id, stream) in seen:
            continue
        seen.add((ia_id, stream))
        text, _ = fetch_ia_text(ia_id, stream)
        if text:
            out[ia_id] = text
    return out


def extract_note(ref: str, note: str, witnesses: dict[str, str]) -> str | None:
    e5 = witnesses.get("newvariorumediti05shak", "")
    kv = witnesses.get("kinglearthenewva0005shak", "")

    if ref == "ACT 1 SCENE 1 / line 61 / note 0":
        if note.count("(") > note.count(")"):
            fixed = note.replace(
                "(quoted by contention or challenge",
                "(quoted by NARES, 'ed. 1768' DYCE.) Contention or challenge",
            )
            if fixed.count("(") == fixed.count(")"):
                return fixed
        return None

    if ref == "ACT 1 SCENE 1 / line 138 / note 0":
        if note.rstrip().endswith("Lex. s. v"):
            return note.rstrip() + ".]"
        return None

    if ref == "ACT 2 SCENE 4 / line 240 / note 0":
        m = re.search(
            r"less\s+advancement\]\s*Percy:.*?undisguised\s+sneer\.?",
            kv or e5,
            re.I | re.S,
        )
        if m:
            body = norm_ws(m.group())
            body = body.replace("] Percy:", "] PERCY:").replace(".Schmidt", ". SCHMIDT")
            body = body.replace("situation /", "situation;").replace("situation/", "situation;")
            if not body.endswith("."):
                body += "."
            return body
        if note.rstrip().endswith("sneer"):
            return note.rstrip() + "."
        return None

    if ref == "ACT 3 SCENE 4 / line 128 / note 0":
        m = re.search(
            r"walks at first cock\].*?for this time",
            kv,
            re.I | re.S,
        )
        if m:
            text = norm_ws(m.group())
            text = text.replace("Scnmipr:", "SCHMIDT:").replace("'to walk? 1s", "'to walk' is")
            text = text.replace("equivalent ¢o", "equivalent to").replace("Jm- oge.", "Imogen.")
            return text + "."
        return None

    if ref == "ACT 3 SCENE 7 / line 66 / note 0":
        if not note.startswith("Capell:"):
            return None
        m = re.search(
            r"it is not worth\s+denying, however,.*?it must be from a different cause\.",
            kv,
            re.I | re.S,
        )
        if m:
            return norm_ws(note.rstrip() + " " + m.group())
        return None

    if ref == "ACT 3 SCENE 7 / line 78 / note 0":
        if note.count("(") > note.count(")"):
            fixed = note.replace("\u2018stick.\u2019—Note", "\u2018stick.\u2019).—Note")
            if fixed.count("(") == fixed.count(")"):
                return fixed
        return None

    if ref == "ACT 4 SCENE 3 / line 37 / note 0":
        i2 = e5.find("outcries  were  accompanied  with  tears", e5.find("clamour  moisten"))
        if i2 < 0:
            return None
        chunk = e5[i2 - 20 : i2 + 2400]
        end = chunk.find("present  passage  cited)")
        if end < 0:
            return None
        tail = chunk[: end + len("present  passage cited)")]
        tail = re.sub(r"^her,'\s*", "her,' ", tail)
        tail = norm_ws(tail.replace("\u2019", "'"))
        if not tail.rstrip().endswith((")", ".", "]", "!", "?")):
            tail = tail.rstrip() + ")."
        lemma = note[: note.index("]") + 1]
        body = note[note.index("]") + 1 :].rstrip()
        if not body.endswith(("moistened", "moisten'd", "moistened'")):
            body = body
        merged = norm_ws(lemma + " " + body + " " + tail)
        return merged

    if ref == "ACT 4 SCENE 6 / line 94 / note 0":
        h = e5.find("73.  clearest]  Theobald:")
        t = e5.find("Schmidt  says \nthat  bright,  pure,  glorious")
        if h < 0 or t < 0:
            return None
        head = e5[h:t]
        tail = e5[t : e5.find("\n\n74.", t)]
        mid_start = e5.find("evil.  Capell  :  It  may  have  the  sense of  clear-sighted", h)
        parts = [head]
        if mid_start > h:
            mid = e5[mid_start:t]
            parts.append(mid)
        parts.append(tail)
        merged = norm_ws("".join(parts))
        merged = re.sub(r"^\d{1,3}\.\s*clearest\]\s*", "", merged, flags=re.I)
        merged = merged.replace("fimon", "Timon")
        lemma = note[: note.index("]") + 1]
        if not merged.endswith((".", "!", "?", "]", "'")):
            merged += "."
        merged = merged.replace("*  clear.'", "'clear.'").replace("* clear.'", "'clear.'")
        return lemma + " " + merged

    if ref == "ACT 4 SCENE 7 / line 50 / note 0":
        if note.rstrip().endswith("proof"):
            return note.rstrip() + "."
        return None

    if ref == "ACT 5 SCENE 3 / line 101 / note 0":
        m = re.search(
            r"Whether he shall not or shall, depends not on your\s+choice\..*?prevent the match\.'\s*\[Ritson\]",
            kv,
            re.I | re.S,
        )
        if m:
            lemma = note[: note.index("]") + 1]
            body = norm_ws(m.group())
            body = body.replace("means to.tell", "means to tell")
            return lemma + " " + body
        if note.rstrip().endswith("[Ritson"):
            return note.rstrip() + "]"
        return None

    if ref == "ACT 5 SCENE 3 / line 347 / note 0":
        h = e5.find("263.  stone]  Collier")
        t = e5.find("might  be  confounded  by  the  old  printer")
        end = e5.find("respectively.]", t)
        if h < 0 or t < 0 or end < 0:
            return None
        merged = norm_ws(e5[h : end + len("respectively.]")])
        merged = re.sub(r"^\d{1,3}\.\s*stone\]\s*", "", merged, flags=re.I)
        merged = merged.replace("appear¬", "appearance").replace("*  Stone  '", "'Stone'")
        lemma = note[: note.index("]") + 1]
        return lemma + " " + merged.split("]", 1)[-1].lstrip()

    return None


def still_truncated(note: str, folded_ia: str) -> bool:
    return is_union_truncated(note, folded_ia)


def repair(data: dict, witnesses: dict[str, str], *, dry_run: bool = False) -> dict:
    folded = fold_apostrophe(witnesses.get("newvariorumediti05shak", ""))
    stats = {
        "truncated_before": 0,
        "truncated_after": 0,
        "repaired": 0,
        "unresolved": 0,
        "examples": [],
        "unresolved_refs": [],
    }

    for scene, scene_data in data.items():
        if not str(scene).startswith("ACT") or not isinstance(scene_data, dict):
            continue
        for line_num, line_data in scene_data.items():
            if not isinstance(line_data, dict):
                continue
            notes = line_data.get("notes") or []
            for i, note in enumerate(notes):
                if not is_union_truncated(note, folded):
                    continue
                stats["truncated_before"] += 1
                ref = f"{scene} / line {line_num} / note {i}"
                ext = extract_note(ref, note, witnesses)
                if ext and ext != note and not still_truncated(ext, folded):
                    if not dry_run:
                        notes[i] = ext
                    stats["repaired"] += 1
                    if len(stats["examples"]) < 12:
                        stats["examples"].append(
                            {
                                "ref": ref,
                                "before_len": len(note),
                                "after_len": len(ext),
                                "tail": ext[-120:],
                            }
                        )
                elif ext and ext != note and len(ext) > len(note) + 8:
                    # Accept meaningful extension even if one soft signal remains.
                    if not dry_run:
                        notes[i] = ext
                    stats["repaired"] += 1
                    if len(stats["examples"]) < 12:
                        stats["examples"].append(
                            {
                                "ref": ref,
                                "before_len": len(note),
                                "after_len": len(ext),
                                "tail": ext[-120:],
                            }
                        )
                else:
                    stats["unresolved"] += 1
                    stats["unresolved_refs"].append(ref)

    for scene, scene_data in data.items():
        if not str(scene).startswith("ACT") or not isinstance(scene_data, dict):
            continue
        for line_data in scene_data.values():
            if not isinstance(line_data, dict):
                continue
            for note in line_data.get("notes") or []:
                if is_union_truncated(note, folded):
                    stats["truncated_after"] += 1
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

    witnesses = load_witnesses()
    if not witnesses:
        print("ERROR: no IA witnesses available", file=sys.stderr)
        return 1

    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    stats = repair(data, witnesses, dry_run=args.dry_run)

    print(
        f"King Lear  before {stats['truncated_before']:>3}  "
        f"repaired {stats['repaired']:>3}  "
        f"after {stats['truncated_after']:>3}  "
        f"unresolved {stats['unresolved']:>3}"
    )
    for ex in stats["examples"]:
        print(f"  {ex['ref']}: {ex['before_len']}->{ex['after_len']} …{ex['tail']}")
    if stats["unresolved_refs"]:
        print("Unresolved:")
        for ref in stats["unresolved_refs"]:
            print(f"  {ref}")

    out = ROOT / "validation" / "kinglear_clip_repair.json"
    out.write_text(
        json.dumps(
            {
                "play": "King Lear",
                "json_file": str(JSON_PATH.relative_to(ROOT)),
                "witnesses": list(witnesses.keys()),
                **stats,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    if not args.dry_run and stats["repaired"]:
        if not BACKUP.is_file():
            shutil.copy2(JSON_PATH, BACKUP)
            print(f"Backup → {BACKUP.relative_to(ROOT)}")
        out_text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        JSON_PATH.write_text(out_text, encoding="utf-8")
        sync_mirrors(out_text)
        print(f"Wrote {JSON_PATH.relative_to(ROOT)}")
        if SITE_MIRROR.parent.is_dir():
            print(f"Mirror → {SITE_MIRROR.relative_to(ROOT)}")

    print(f"Wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
