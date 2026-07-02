#!/usr/bin/env python3
"""Build data/onions_glossary_index.json from Internet Archive OCR."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OCR = ROOT / "data" / "onions_ocr.txt"
OUT = ROOT / "data" / "onions_glossary_index.json"

COLON_ENTRY_RE = re.compile(r"^([a-z][a-z' -]{0,55}?)\s*:\s*(.*)$", re.I)
PAREN_ENTRY_RE = re.compile(r"^([a-z][a-z' -]{0,55}?)\s+\((.+)$", re.I)
SENSE_LINE_RE = re.compile(r"^\d+\s+")
SKIP_PREFIXES = ("http", "<", ".", "/*", "@media", "display:", "content:")


def normalize_key(headword: str) -> str:
    base = headword.strip().lower()
    base = re.sub(r"\s+(sb\.|vb\.|ppl\.|adj\.|adv\.|int\.).*$", "", base, flags=re.I)
    return re.sub(r"[^a-z'-]", "", base)


def clean_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def try_new_entry(line: str, current_key: str | None) -> tuple[str, str] | None:
    m = COLON_ENTRY_RE.match(line)
    if m:
        key = normalize_key(m.group(1))
        if key:
            return key, clean_spaces(m.group(2))

    m = PAREN_ENTRY_RE.match(line)
    if m:
        key = normalize_key(m.group(1))
        if key and key != current_key:
            return key, clean_spaces(m.group(2))

    return None


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
            if line.startswith("abandon ") or line.startswith("abate "):
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

            current_key = key
            head_raw = COLON_ENTRY_RE.match(line) or PAREN_ENTRY_RE.match(line)
            head_label = head_raw.group(1).strip() if head_raw else key
            entries[current_key] = {
                "headword": head_label.split()[0],
                "forms": head_label if " " in head_label else None,
                "text": rest,
            }
            buffer = [rest] if rest else []
            continue

        if current_key:
            buffer.append(line)

    if current_key and buffer:
        entries[current_key]["text"] = clean_spaces(" ".join(buffer))

    return {k: v for k, v in entries.items() if len(k) > 1 and len(v.get("text", "")) > 3}


def main() -> None:
    if not OCR.exists():
        raise SystemExit(f"Missing OCR file: {OCR}")

    entries = parse_onions_ocr(OCR.read_text(encoding="utf-8", errors="replace"))
    payload = {
        "_meta": {
            "title": "A Shakespeare Glossary",
            "author": "C. T. Onions",
            "publisher": "Clarendon Press, Oxford",
            "first_edition": 1911,
            "second_edition_revised": 1919,
            "cover_title": "The Oxford Shakespeare Glossary",
            "entry_count": len(entries),
            "source_url": "https://archive.org/details/shakespearegloss00oniouoft",
        },
        **entries,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(entries)} headwords, {OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
