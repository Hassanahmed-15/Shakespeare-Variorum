#!/usr/bin/env python3
"""Build data/geneva_bible_index.json from eBible.org USFM (Geneva 1599)."""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
USFM_ZIP = ROOT / "data" / "geneva_raw" / "enggnv_usfm.zip"
USFM_DIR = ROOT / "data" / "geneva_raw"
OUT = ROOT / "data" / "geneva_bible_index.json"

BOOK_NAMES = {
    "GEN": "Genesis", "EXO": "Exodus", "LEV": "Leviticus", "NUM": "Numbers",
    "DEU": "Deuteronomy", "JOS": "Joshua", "JDG": "Judges", "RUT": "Ruth",
    "1SA": "1 Samuel", "2SA": "2 Samuel", "1KI": "1 Kings", "2KI": "2 Kings",
    "1CH": "1 Chronicles", "2CH": "2 Chronicles", "EZR": "Ezra", "NEH": "Nehemiah",
    "EST": "Esther", "JOB": "Job", "PSA": "Psalms", "PRO": "Proverbs",
    "ECC": "Ecclesiastes", "SNG": "Song of Solomon", "ISA": "Isaiah",
    "JER": "Jeremiah", "LAM": "Lamentations", "EZK": "Ezekiel", "DAN": "Daniel",
    "HOS": "Hosea", "JOL": "Joel", "AMO": "Amos", "OBA": "Obadiah",
    "JON": "Jonah", "MIC": "Micah", "NAM": "Nahum", "HAB": "Habakkuk",
    "ZEP": "Zephaniah", "HAG": "Haggai", "ZEC": "Zechariah", "MAL": "Malachi",
    "MAT": "Matthew", "MRK": "Mark", "LUK": "Luke", "JHN": "John",
    "ACT": "Acts", "ROM": "Romans", "1CO": "1 Corinthians", "2CO": "2 Corinthians",
    "GAL": "Galatians", "EPH": "Ephesians", "PHP": "Philippians", "COL": "Colossians",
    "1TH": "1 Thessalonians", "2TH": "2 Thessalonians", "1TI": "1 Timothy",
    "2TI": "2 Timothy", "TIT": "Titus", "PHM": "Philemon", "HEB": "Hebrews",
    "JAS": "James", "1PE": "1 Peter", "2PE": "2 Peter", "1JN": "1 John",
    "2JN": "2 John", "3JN": "3 John", "JUD": "Jude", "REV": "Revelation",
}


def book_code_from_filename(name: str) -> str:
    m = re.search(r"-([A-Z0-9]{3})enggnv", name)
    return m.group(1) if m else "UNK"


def parse_usfm(text: str, book_code: str) -> list[dict]:
    book = BOOK_NAMES.get(book_code, book_code)
    verses: list[dict] = []
    chapter = 0
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("\\c "):
            chapter = int(line[3:].strip())
            continue
        if line.startswith("\\v "):
            m = re.match(r"\\v\s+(\d+)\s+(.*)$", line)
            if not m:
                continue
            verse = int(m.group(1))
            body = re.sub(r"\\[a-z]+\d*\s*", "", m.group(2)).strip()
            body = re.sub(r"\s+", " ", body)
            if not body:
                continue
            ref = f"{book} {chapter}:{verse}"
            verses.append({
                "ref": ref,
                "book": book,
                "chapter": chapter,
                "verse": verse,
                "text": body,
            })
    return verses


def main() -> None:
    if USFM_ZIP.exists() and not list(USFM_DIR.glob("*.usfm")):
        with zipfile.ZipFile(USFM_ZIP) as zf:
            zf.extractall(USFM_DIR)

    all_verses: list[dict] = []
    for usfm_path in sorted(USFM_DIR.glob("*.usfm")):
        code = book_code_from_filename(usfm_path.name)
        verses = parse_usfm(usfm_path.read_text(encoding="utf-8", errors="replace"), code)
        all_verses.extend(verses)
        print(f"{usfm_path.name}: {len(verses)} verses")

    payload = {
        "_meta": {
            "title": "Geneva Bible",
            "edition": "1599",
            "source": "eBible.org (enggnv, public domain)",
            "verse_count": len(all_verses),
        },
        "verses": all_verses,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(all_verses)} verses, {OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
