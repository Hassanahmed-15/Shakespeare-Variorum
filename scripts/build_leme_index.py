#!/usr/bin/env python3
"""Build data/leme_period_index.json from LEME plainText transcriptions (CC BY 4.0)."""

from __future__ import annotations

import json
import re
import unicodedata
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

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by",
    "from", "as", "is", "was", "are", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "shall", "should", "may", "might", "must", "can",
    "could", "that", "this", "these", "those", "not", "no", "so", "if", "then", "than",
    "also", "one", "two", "which", "who", "whom", "when", "where", "how", "all", "some",
    "more", "most", "such", "what", "any", "other", "into", "upon", "over", "under", "out",
    "up", "down", "about", "like", "very", "much", "many", "make", "made", "thing", "things",
}


def fold_accents(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def normalize_key(headword: str) -> str:
    base = fold_accents(headword.strip().lower())
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


def make_entry(headword: str, text: str, meta: dict, **extra) -> dict:
    citation = (
        f"{meta['author']}. {meta['title']} ({meta['year']}). "
        f"Transcription via {LEME_CITATION}"
    )
    entry = {
        "headword": headword,
        "text": text[:280] if len(text) > 280 else text,
        "source_id": meta["id"],
        "source_year": meta["year"],
        "citation": citation,
    }
    entry.update(extra)
    return entry


def english_gloss_terms(gloss: str, max_terms: int = 6, bilingual: bool = False) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()
    lower = fold_accents(gloss.lower())

    for match in re.finditer(r"\bto\s+([a-z][a-z'-]{2,})", lower):
        key = normalize_key(match.group(1))
        if key and len(key) >= 4 and key not in STOPWORDS and key not in seen:
            seen.add(key)
            terms.append(key)

    if bilingual:
        return terms[:max_terms]

    for clause in list(re.split(r"[,;]", gloss))[:clause_limit]:
        clause = clean_spaces(clause).lower()
        clause = re.sub(r"^(a|an|the|one|that|which|also|as)\s+", "", clause)
        match = re.match(r"([a-z][a-z'-]{2,})", clause)
        if not match:
            continue
        key = normalize_key(match.group(1))
        if key and len(key) >= 4 and key not in STOPWORDS and key not in seen:
            seen.add(key)
            terms.append(key)
        if len(terms) >= max_terms:
            break

    return terms[:max_terms]


def index_bilingual_entry(merged: dict[str, list], foreign_headword: str, gloss: str, meta: dict) -> None:
    gloss = clean_spaces(gloss)
    if not gloss or len(gloss) < 4:
        return

    gloss_short = gloss if len(gloss) <= 280 else gloss[:277] + "..."
    base = make_entry(
        foreign_headword,
        gloss_short,
        meta,
        lemma_lang=meta.get("lang"),
        match_type="english_gloss",
    )

    for term in english_gloss_terms(gloss, max_terms=3, bilingual=True):
        bucket = merged.setdefault(term, [])
        if any(e["source_id"] == meta["id"] and e["headword"] == foreign_headword for e in bucket):
            continue
        if any(e["source_id"] == meta["id"] for e in bucket):
            continue
        bucket.append(dict(base))


def parse_florio(text: str, meta: dict, merged: dict[str, list]) -> int:
    text = strip_leme_header(text)
    start = text.find("Abbandonare,")
    if start < 0:
        start = text.find("Abandonare,")
    body = text[start:] if start >= 0 else text

    head_re = re.compile(r"^([A-Z][A-Za-zàèéìòù']+),\s*(.+)$")
    cross_ref_re = re.compile(r"^as\s+[A-Za-z]", re.I)

    current_head: str | None = None
    current_gloss: list[str] = []
    count = 0

    def flush() -> None:
        nonlocal current_head, current_gloss, count
        if current_head and current_gloss:
            index_bilingual_entry(merged, current_head, " ".join(current_gloss), meta)
            count += 1
        current_head = None
        current_gloss = []

    for raw in body.splitlines():
        line = clean_spaces(raw)
        if not line:
            flush()
            continue

        match = head_re.match(line)
        if match:
            flush()
            head = match.group(1).strip()
            gloss = match.group(2).strip()
            if cross_ref_re.match(gloss) and len(gloss) < 80:
                continue
            current_head = head
            current_gloss = [gloss]
            continue

        if current_head:
            if head_re.match(line):
                continue
            current_gloss.append(line)

    flush()
    return count


def parse_cotgrave(text: str, meta: dict, merged: dict[str, list]) -> int:
    text = strip_leme_header(text)
    start = text.find("A \nA The")
    if start < 0:
        start = text.find("A DICTIONARIE")
    body = text[start:] if start >= 0 else text

    head_dot = re.compile(r"^([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' ]*?)\.\s+(.+)$")
    head_colon = re.compile(r"^([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' ]*?):\s+(.+)$")

    current_head: str | None = None
    current_gloss: list[str] = []
    count = 0

    def flush() -> None:
        nonlocal current_head, current_gloss, count
        if current_head and current_gloss:
            index_bilingual_entry(merged, current_head, " ".join(current_gloss), meta)
            count += 1
        current_head = None
        current_gloss = []

    for raw in body.splitlines():
        line = clean_spaces(raw)
        if not line or line.startswith("{") or line.startswith("TO THE"):
            flush()
            continue

        match = head_dot.match(line) or head_colon.match(line)
        if match:
            flush()
            head = clean_spaces(match.group(1))
            gloss = clean_spaces(match.group(2))
            if len(head) > 60 or head.lower() in ("a", "the"):
                continue
            current_head = head
            current_gloss = [gloss]
            continue

        if current_head and line[0].islower():
            current_gloss.append(line)

    flush()
    return count


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
    bilingual_parsers = {
        "florio": parse_florio,
        "cotgrave": parse_cotgrave,
    }

    for src in sources:
        raw_path = RAW_DIR / f"lexicon{src['lexicon_id']}.txt"
        text = download_plaintext(src["url"], raw_path)

        if src["id"] in bilingual_parsers:
            foreign_count = bilingual_parsers[src["id"]](text, src, merged)
            source_stats.append(
                {
                    "id": src["id"],
                    "foreign_entries": foreign_count,
                    "year": src["year"],
                    "lookup_mode": "english_gloss",
                }
            )
            print(f"{src['id']}: {foreign_count} foreign lemmas indexed via English gloss terms")
            continue

        if not src.get("english_lookup", True):
            print(f"Skipping {src['id']} — english_lookup disabled")
            continue

        parser = parsers.get(src["id"])
        if not parser:
            print(f"No parser for {src['id']}")
            continue

        parsed = parser(text, src)
        merge_entries(merged, parsed)
        source_stats.append({"id": src["id"], "entries": len(parsed), "year": src["year"]})
        print(f"{src['id']}: {len(parsed)} headwords")

    out = {
        "_meta": {
            "title": "LEME Period Lexicons",
            "sources": source_stats,
            "entry_count": len(merged),
            "total_source_entries": sum(len(v) for v in merged.values()),
            "license": "CC BY 4.0 (LEME transcriptions)",
            "source_url": "https://leme.library.utoronto.ca/",
            "note": (
                "English hard-word lexicons (Cawdrey 1604, Bullokar 1616, Cockeram 1623) plus "
                "bilingual Florio (1598) and Cotgrave (1611) indexed by English gloss terms "
                "extracted from Italian/French lemmas."
            ),
        },
        "entries": merged,
    }

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(merged)} headwords)")


if __name__ == "__main__":
    main()
