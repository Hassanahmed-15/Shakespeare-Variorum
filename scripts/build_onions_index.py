#!/usr/bin/env python3
"""Build data/onions_glossary_index.json from Perseus keyed text + OCR fallback."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OCR = ROOT / "data" / "onions_ocr.txt"
PERSEUS_CACHE = ROOT / "data" / "onions_perseus_cache.json"
OUT = ROOT / "data" / "onions_glossary_index.json"

COLON_ENTRY_RE = re.compile(r"^([a-z][a-z' -]{0,55}?)\s*:\s*(.*)$", re.I)
POS_PAREN_RE = re.compile(
    r"^([a-z][a-z' -]{0,55}?)\s+\((sb\.|vb\.|adj\.|ppl\.|adv\.|int\.|cf\.|obs\.|var\.|q\.)",
    re.I,
)
HEADWORD_PAREN_RE = re.compile(r"^([a-z][a-z' -]{0,55}?)\s+\((.+)$", re.I)
FALSE_PAREN_RE = re.compile(r"^([a-z][a-z' -]{0,55}?)\s+\((.+)$", re.I)
PLAY_REF_IN_PAREN = re.compile(r"^(Ff|F\d|Qq|Q\d|Fi\b|later|earlier|mod\.|Ed\.)", re.I)
SENSE_LINE_RE = re.compile(r"^\d+\s+")
SKIP_PREFIXES = ("http", "<", ".", "/*", "@media", "display:", "content:")


def normalize_key(headword: str) -> str:
    base = headword.strip().lower()
    base = re.sub(r"\d+$", "", base)
    base = re.sub(r"\s+(sb\.|vb\.|ppl\.|adj\.|adv\.|int\.).*$", "", base, flags=re.I)
    return re.sub(r"[^a-z'-]", "", base)


def clean_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def is_false_headword_paren(line: str) -> bool:
    m = FALSE_PAREN_RE.match(line)
    if not m:
        return False
    inner = m.group(2).strip()
    return bool(PLAY_REF_IN_PAREN.match(inner))


def try_new_entry(line: str, current_key: str | None) -> tuple[str, str] | None:
    if is_false_headword_paren(line):
        return None

    m = COLON_ENTRY_RE.match(line)
    if m:
        key = normalize_key(m.group(1))
        if key:
            return key, clean_spaces(m.group(2))

    m = HEADWORD_PAREN_RE.match(line)
    if m:
        key = normalize_key(m.group(1))
        if key:
            return key, clean_spaces(m.group(2))

    return None


def is_fragmentary_text(text: str) -> bool:
    t = clean_spaces(text)
    if len(t) < 4:
        return True
    if t[0] in "),.]":
        return True
    if re.match(r"^Ff\s", t):
        return True
    return False


def parse_onions_ocr(text: str) -> dict[str, dict]:
    entries: dict[str, dict] = {}
    current_key: str | None = None
    buffer: list[str] = []
    in_glossary = False

    for raw_line in text.splitlines():
        line = clean_spaces(raw_line)
        if not line or any(line.startswith(p) for p in SKIP_PREFIXES):
            continue

        if not in_glossary:
            if re.match(r"^(abandon|abandoned|abase|abate)\b", line):
                in_glossary = True
            else:
                continue

        if SENSE_LINE_RE.match(line):
            if current_key:
                buffer.append(line)
            continue

        new_entry = try_new_entry(line, current_key)
        if new_entry:
            key, rest = new_entry
            if current_key and buffer:
                entries[current_key]["text"] = clean_spaces(" ".join(buffer))

            head_raw = COLON_ENTRY_RE.match(line) or HEADWORD_PAREN_RE.match(line)
            head_label = head_raw.group(1).strip() if head_raw else key
            entries[key] = {
                "headword": head_label.split()[0],
                "forms": head_label if " " in head_label else None,
                "text": rest,
                "source": "ocr",
            }
            current_key = key
            buffer = [rest] if rest else []
            continue

        if current_key:
            buffer.append(line)

    if current_key and buffer:
        entries[current_key]["text"] = clean_spaces(" ".join(buffer))

    return {
        k: v
        for k, v in entries.items()
        if len(k) > 1 and len(v.get("text", "")) > 3 and not is_fragmentary_text(v["text"])
    }


def load_perseus_entries() -> dict[str, dict]:
    if not PERSEUS_CACHE.exists():
        return {}
    raw = json.loads(PERSEUS_CACHE.read_text(encoding="utf-8"))
    by_key: dict[str, dict] = {}
    for slug_entry in raw.get("entries", {}).values():
        key = slug_entry.get("key") or normalize_key(slug_entry.get("headword", ""))
        text = clean_spaces(slug_entry.get("text", ""))
        if not key or not text:
            continue
        headword = slug_entry.get("headword", key).split()[0]
        candidate = {
            "headword": headword,
            "forms": slug_entry.get("headword") if " " in slug_entry.get("headword", "") else None,
            "text": text,
            "source": "perseus",
            "perseus_slug": slug_entry.get("slug"),
        }
        existing = by_key.get(key)
        if not existing or len(text) > len(existing.get("text", "")):
            by_key[key] = candidate
    return by_key


def merge_entries(ocr_entries: dict[str, dict], perseus_entries: dict[str, dict]) -> dict[str, dict]:
    merged = dict(ocr_entries)
    for key, pentry in perseus_entries.items():
        oentry = merged.get(key)
        if not oentry:
            merged[key] = {k: v for k, v in pentry.items() if k != "perseus_slug"}
            continue
        ocr_text = oentry.get("text", "")
        elif is_fragmentary_text(ocr_text):
            merged[key] = {
                "headword": pentry.get("headword") or oentry.get("headword", key),
                "forms": pentry.get("forms") or oentry.get("forms"),
                "text": pentry["text"],
                "source": "perseus",
            }
        elif len(pentry["text"]) > len(ocr_text) * 1.2:
            merged[key] = {
                "headword": pentry.get("headword") or oentry.get("headword", key),
                "forms": pentry.get("forms") or oentry.get("forms"),
                "text": pentry["text"],
                "source": "perseus",
            }
    return merged


def main() -> None:
    if not OCR.exists():
        raise SystemExit(f"Missing OCR fallback file: {OCR}")

    ocr_entries = parse_onions_ocr(OCR.read_text(encoding="utf-8", errors="replace"))
    perseus_entries = load_perseus_entries()
    entries = merge_entries(ocr_entries, perseus_entries)

    perseus_count = sum(1 for e in entries.values() if e.get("source") == "perseus")
    payload = {
        "_meta": {
            "title": "A Shakespeare Glossary",
            "author": "C. T. Onions",
            "publisher": "Clarendon Press, Oxford",
            "first_edition": 1911,
            "second_edition_revised": 1919,
            "cover_title": "The Oxford Shakespeare Glossary",
            "entry_count": len(entries),
            "perseus_entries": perseus_count,
            "ocr_entries": len(entries) - perseus_count,
            "primary_source": "Perseus Digital Library (1999.03.0068) with Internet Archive OCR fallback",
            "perseus_url": "http://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.03.0068",
            "ocr_source_url": "https://archive.org/details/shakespearegloss00oniouoft",
        },
        **{k: {kk: vv for kk, vv in v.items() if kk != "source"} for k, v in entries.items()},
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Wrote {OUT} ({len(entries)} headwords, {perseus_count} Perseus, "
        f"{OUT.stat().st_size // 1024} KB)"
    )


if __name__ == "__main__":
    main()
