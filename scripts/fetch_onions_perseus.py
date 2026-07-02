#!/usr/bin/env python3
"""Crawl Perseus Onions (1999.03.0068) and cache keyed entry text.

Professional data entry witness: http://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.03.0068

Usage:
  python3 scripts/fetch_onions_perseus.py          # full crawl (~2h with rate limit)
  python3 scripts/fetch_onions_perseus.py --quick  # letters A-C only (smoke test)
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote, unquote

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "onions_perseus_cache.json"
DOC = "Perseus:text:1999.03.0068"
BASE = "http://www.perseus.tufts.edu/hopper/text"
LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
DELAY_SEC = 2.5


def normalize_key(headword: str) -> str:
    base = headword.strip().lower()
    base = re.sub(r"\d+$", "", base)
    base = re.sub(r"\s+(sb\.|vb\.|ppl\.|adj\.|adv\.|int\.).*$", "", base, flags=re.I)
    return re.sub(r"[^a-z'-]", "", base)


def fetch(url: str, retries: int = 4) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Shakespeare-Variorum/1.0 (lexical index build)"})
    for attempt in range(retries):
        try:
            return urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "replace")
        except urllib.error.HTTPError as err:
            if err.code == 429 and attempt < retries - 1:
                time.sleep(8 * (attempt + 1))
                continue
            raise
    raise RuntimeError(f"Failed to fetch {url}")


def slugs_from_group_html(html: str) -> list[str]:
    return sorted(set(unquote(m) for m in re.findall(r"entry%3D([a-zA-Z0-9]+)", html)))


def parse_entry_html(html: str) -> tuple[str, str] | None:
    if "unable to find" in html or "No document found" in html:
        return None
    m = re.search(r'<div class="text">(.*?)</div>', html, re.S)
    if not m:
        return None
    raw = re.sub(r"<[^>]+>", " ", m.group(1))
    raw = re.sub(r"\s+", " ", raw).strip()
    if not raw:
        return None
  # drop trailing Perseus boilerplate if present
    raw = re.sub(r"\s*A Shakespeare Glossary\..*$", "", raw).strip()
    hm = re.match(r"^([^:]{1,80}):\s*(.*)$", raw)
    if hm:
        return hm.group(1).strip(), hm.group(2).strip()
    bold = re.search(r"<b>([^<]+)</b>", m.group(1))
    if bold:
        head = bold.group(1).strip()
        rest = raw[len(head) :].lstrip(": ").strip()
        return head, rest or raw
    return raw.split()[0], raw


def discover_slugs(letters: list[str]) -> list[str]:
    slugs: set[str] = set()
    for letter in letters:
        for group in range(1, 12):
            doc = f"{DOC}:alphabetic+letter={letter}:entry+group={group}"
            url = f"{BASE}?doc={quote(doc, safe='')}"
            try:
                html = fetch(url)
            except urllib.error.HTTPError:
                break
            found = slugs_from_group_html(html)
            if not found:
                break
            slugs.update(found)
            print(f"  letter {letter} group {group}: +{len(found)} slugs ({len(slugs)} total)")
            time.sleep(0.4)
    return sorted(slugs)


def load_cache() -> dict:
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    return {"_meta": {"source": DOC, "entries": {}}, "entries": {}}


def save_cache(data: dict) -> None:
    data["_meta"]["entry_count"] = len(data.get("entries", {}))
    data["_meta"]["updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    CACHE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="Only crawl letters A-C")
    parser.add_argument("--delay", type=float, default=DELAY_SEC)
    args = parser.parse_args()

    letters = LETTERS[:3] if args.quick else LETTERS
    cache = load_cache()
    entries: dict = cache.setdefault("entries", {})

    print("Discovering Perseus entry slugs…")
    slugs = discover_slugs(letters)
    print(f"Found {len(slugs)} slugs; fetching entry bodies…")

    for i, slug in enumerate(slugs, 1):
        if slug in entries and entries[slug].get("text"):
            continue
        url = f"{BASE}?doc={quote(f'{DOC}:entry={slug}', safe='')}"
        try:
            html = fetch(url)
            parsed = parse_entry_html(html)
            if not parsed:
                continue
            head, text = parsed
            key = normalize_key(head.split()[0])
            if not key:
                continue
            entries[slug] = {
                "slug": slug,
                "headword": head,
                "key": key,
                "text": text,
            }
            if i % 25 == 0:
                save_cache(cache)
                print(f"  cached {i}/{len(slugs)} …")
        except Exception as err:
            print(f"  skip {slug}: {err}")
        time.sleep(args.delay)

    save_cache(cache)
    print(f"Wrote {CACHE} ({len(entries)} entries)")


if __name__ == "__main__":
    main()
