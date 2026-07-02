#!/usr/bin/env python3
"""Build data/schmidt_lexicon_index.json from Internet Archive OCR (Sarrazin rev.)."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "schmidt_lexicon_index.json"
CORRECTIONS = ROOT / "data" / "schmidt_corrections.json"
OCR_FILES = [
    ROOT / "data" / "schmidt_vol1_ocr.txt",
    ROOT / "data" / "schmidt_ocr.txt",
]

ENTRY_RE = re.compile(r"^([A-Z][A-Za-z' -]{1,55}?)(?:,\s*|\s{2,})(.+)$")
SKIP_PREFIXES = ("http", "<", "Usage", "Google", "Preface", "THE ", "CHAPTER")


def normalize_key(headword: str) -> str:
    base = headword.strip().lower()
    base = re.sub(r"\s+or\s+.*$", "", base)
    return re.sub(r"[^a-z'-]", "", base)


def clean_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_schmidt_ocr(text: str) -> dict[str, dict]:
    entries: dict[str, dict] = {}
    current_key: str | None = None
    buffer: list[str] = []
    in_lexicon = False

    for raw_line in text.splitlines():
        line = clean_spaces(raw_line)
        if not line or any(line.startswith(p) for p in SKIP_PREFIXES):
            continue
        if line.isdigit() and len(line) <= 4:
            continue

        if not in_lexicon:
            if ENTRY_RE.match(line) and len(line) < 120:
                in_lexicon = True
            else:
                continue

        if re.match(r"^\d+\s+", line):
            if current_key:
                buffer.append(line)
            continue

        m = ENTRY_RE.match(line)
        if m and len(m.group(1)) < 40:
            head_raw = m.group(1).strip()
            rest = m.group(2).strip()
            key = normalize_key(head_raw)
            if not key or len(key) < 2:
                continue

            if current_key and buffer:
                entries[current_key]["text"] = clean_spaces(" ".join(buffer))

            if key not in entries:
                entries[key] = {
                    "headword": head_raw.split(" or ")[0].strip(),
                    "forms": head_raw if " or " in head_raw else None,
                    "text": rest,
                }
                current_key = key
                buffer = [rest] if rest else []
            else:
                entries[key]["text"] = clean_spaces(entries[key]["text"] + " " + rest)
                current_key = key
                buffer = [entries[key]["text"]]
            continue

        if current_key:
            buffer.append(line)

    if current_key and buffer:
        entries[current_key]["text"] = clean_spaces(" ".join(buffer))

    return {k: v for k, v in entries.items() if len(v.get("text", "")) > 5}


def apply_corrections(entries: dict[str, dict]) -> dict[str, dict]:
    if not CORRECTIONS.exists():
        return entries
    spec = json.loads(CORRECTIONS.read_text(encoding="utf-8"))
    for pattern, repl in spec.get("global_replacements", []):
        for entry in entries.values():
            entry["text"] = re.sub(pattern, repl, entry["text"])
    for key, override in spec.get("entries", {}).items():
        if key not in entries:
            continue
        text = override.get("text")
        if text:
            entries[key]["text"] = text
    return entries


def main() -> None:
    merged: dict[str, dict] = {}
    for ocr_path in OCR_FILES:
        if not ocr_path.exists():
            print(f"Skip missing {ocr_path}")
            continue
        part = parse_schmidt_ocr(ocr_path.read_text(encoding="utf-8", errors="replace"))
        for key, entry in part.items():
            if key not in merged or len(entry["text"]) > len(merged[key]["text"]):
                merged[key] = entry
        print(f"Parsed {ocr_path.name}: {len(part)} entries")

    merged = apply_corrections(merged)

    payload = {
        "_meta": {
            "title": "Shakespeare-Lexicon",
            "author": "Alexander Schmidt",
            "editor": "Gregor Sarrazin (rev.)",
            "edition": "3rd edition, 1902",
            "entry_count": len(merged),
            "source_url": "https://archive.org/details/shakespearelexi02sarrgoog",
        },
        **merged,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(merged)} headwords, {OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
