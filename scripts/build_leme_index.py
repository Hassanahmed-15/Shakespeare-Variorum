#!/usr/bin/env python3
"""Build data/leme_period_index.json from LEME plainText transcriptions (CC BY 4.0)."""

from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "leme_raw"
SOURCES = ROOT / "scripts" / "leme_sources.json"
OUT = ROOT / "data" / "leme_period_index.json"

LEME_CITATION = (
    "Lexicons of Early Modern English (LEME), University of Toronto. "
    "CC BY 4.0. https://leme.library.utoronto.ca/"
)


def normalize_key(headword: str) -> str:
    base = headword.strip().lower()
    base = base.replace("æ", "ae").replace("œ", "oe")
    base = re.sub(r"[^a-z'-]", "", base)
    return base


def clean_spaces(text: str) -> str:
    text = text.replace("\u00ad", "")
    return re.sub(r"\s+", " ", text).strip()


def strip_leme_header(text: str) -> str:
    text = text.replace("\u00ad", "")
    # Drop spaced-out LEME banner lines
    lines = []
    for line in text.splitlines():
        compact = re.sub(r"\s+", "", line)
        if compact.startswith("leme.library.utoronto.ca"):
            continue
        if re.fullmatch(r"stc\d+", compact, re.I):
            continue
        if re.fullmatch(r"ver\.\d+\.\d+\(\d+\)", compact, re.I):
            continue
        lines.append(line)
    return "\n".join(lines)


def parse_cawdrey(text: str, meta: dict) -> dict[str, dict]:
    text = strip_leme_header(text)
    # Dictionary body begins after editorial preface markers
    start = text.find("§ ABandon")
    if start < 0:
        start = text.find("Abandon,")
    if start < 0:
        start = 0
    body = text[start:]

    entries: dict[str, dict] = {}
    entry_re = re.compile(r"^(?:§\s*)?([A-Za-z][A-Za-z'-]*)\s*,\s*(.+)$")

    for line in body.splitlines():
        line = clean_spaces(line)
        if not line or len(line) < 4:
            continue
        m = entry_re.match(line)
        if not m:
            continue
        head = m.group(1).strip()
        gloss = clean_spaces(m.group(2))
        if not gloss or len(head) > 40:
            continue
        key = normalize_key(head)
        if not key:
            continue
        entries[key] = make_entry(head, gloss, meta)
    return entries


def parse_bullokar(text: str, meta: dict) -> dict[str, dict]:
    text = strip_leme_header(text)
    start = text.lower().find("an exposition of the hardest words")
    body = text[start:] if start >= 0 else text

    entries: dict[str, dict] = {}
    entry_re = re.compile(r"^([A-Za-z][A-Za-z'-]*)\s*,\s*(.+?)\.?\s*$")

    for block in re.split(r"\n\s*\n", body):
        for line in block.splitlines():
            line = clean_spaces(line)
            if not line or line.startswith("Not found in OED"):
                continue
            m = entry_re.match(line)
            if not m:
                continue
            head = m.group(1).strip()
            gloss = clean_spaces(m.group(2).rstrip("."))
            if not gloss or head.lower() in ("a", "an", "the"):
                continue
            key = normalize_key(head)
            if not key:
                continue
            entries[key] = make_entry(head, gloss, meta)
    return entries


def parse_cockeram(text: str, meta: dict) -> dict[str, dict]:
    text = strip_leme_header(text)
    start = text.find("THE ENGLISH DICTIONARIE")
    if start < 0:
        start = text.find("Abandon.")
    body = text[start:] if start >= 0 else text

    entries: dict[str, dict] = {}
    current_key: str | None = None
    current_head: str | None = None
    buffer: list[str] = []

    head_re = re.compile(r"^([A-Z][A-Za-z'-]+)\.\s*(.*)$")

    def flush() -> None:
        nonlocal current_key, current_head, buffer
        if current_key and buffer:
            entries[current_key] = make_entry(current_head or current_key, clean_spaces(" ".join(buffer)), meta)
        buffer = []

    for raw in body.splitlines():
        line = clean_spaces(raw)
        if not line:
            flush()
            current_key = None
            current_head = None
            continue

        m = head_re.match(line)
        if m:
            flush()
            current_head = m.group(1).strip()
            current_key = normalize_key(current_head)
            rest = clean_spaces(m.group(2))
            buffer = [rest] if rest else []
            continue

        if current_key:
            if head_re.match(line):
                continue
            buffer.append(line)

    flush()
    return entries


def make_entry(headword: str, text: str, meta: dict) -> dict:
    citation = (
        f"{meta['author']}. {meta['title']} ({meta['year']}). "
        f"Transcription via {LEME_CITATION}"
    )
    return {
        "headword": headword,
        "text": text,
        "source_id": meta["id"],
        "source_author": meta["author"],
        "source_title": meta["title"],
        "source_year": meta["year"],
        "citation": citation,
    }


def download_plaintext(url: str, dest: Path) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists() or dest.stat().st_size < 100:
        print(f"Downloading {url} ...")
        with urllib.request.urlopen(url, timeout=120) as resp:
            dest.write_bytes(resp.read())
    return dest.read_text(encoding="utf-8", errors="ignore")


def merge_entries(index: dict[str, list], new: dict[str, dict]) -> None:
    for key, entry in new.items():
        index.setdefault(key, []).append(entry)


def main() -> None:
    sources = json.loads(SOURCES.read_text())
    merged: dict[str, list] = {}
    source_stats = []

    parsers = {
        "cawdrey": parse_cawdrey,
        "bullokar": parse_bullokar,
        "cockeram": parse_cockeram,
    }

    for src in sources:
        if not src.get("english_lookup", True) and src["type"] != "english_hard_word":
            print(f"Skipping {src['id']} ({src['type']}) — not indexed for English headword lookup in v1")
            continue
        parser = parsers.get(src["id"])
        if not parser:
            print(f"No parser for {src['id']}")
            continue

        raw_path = RAW_DIR / f"lexicon{src['lexicon_id']}.txt"
        text = download_plaintext(src["url"], raw_path)
        parsed = parser(text, src)
        merge_entries(merged, parsed)
        source_stats.append({"id": src["id"], "entries": len(parsed), "year": src["year"]})
        print(f"{src['id']}: {len(parsed)} headwords")

    out = {
        "_meta": {
            "title": "LEME Period Lexicons (English hard-word subset)",
            "sources": source_stats,
            "entry_count": len(merged),
            "total_source_entries": sum(len(v) for v in merged.values()),
            "license": "CC BY 4.0 (LEME transcriptions)",
            "source_url": "https://leme.library.utoronto.ca/",
            "note": (
                "Contemporary period dictionaries (Cawdrey 1604, Bullokar 1616, Cockeram 1623). "
                "Florio (1598) and Cotgrave (1611) are in leme_sources.json but omitted from this "
                "English headword index because they are bilingual works keyed to Italian/French lemmas."
            ),
        },
        "entries": merged,
    }

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(merged)} headwords)")


if __name__ == "__main__":
    main()
