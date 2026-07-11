#!/usr/bin/env python3
"""Harvest citing works for Boros 2024 LaTeCH and Zhang 2024 DocEng seed papers."""

from __future__ import annotations

import html
import json
import re
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

OUT_DIR = Path(__file__).resolve().parent
JSON_PATH = OUT_DIR / "citing_works_catalog.json"
MD_PATH = OUT_DIR / "citing_works_catalog.md"

SEEDS = {
    "boros_2024_latech": {
        "label": "Boros et al. 2024 LaTeCH",
        "title": "Post-Correction of Historical Text Transcripts with Large Language Models: An Exploratory Study",
        "doi": "10.18653/v1/2024.latechclfl-1.14",
        "openalex_id": "W7126374621",
        "semantic_scholar_id": "57c7d33858ee424c41130888bad0a505cd61f735",
        "scholar_cites_id": "8103317005463255551",
    },
    "zhang_2024_doceng": {
        "label": "Zhang et al. 2024 DocEng",
        "title": "Post-OCR Correction with OpenAI's GPT Models on Challenging English Prosody Texts",
        "doi": "10.1145/3685650.3685669",
        "openalex_id": "W4402590041",
        "semantic_scholar_id": "866023586936381a5a2d547cee34c3d2799a2258",
        "scholar_cites_id": "18300382062689824098",
    },
}

SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
)


def normalize_title(title: str) -> str:
    if not title:
        return ""
    t = html.unescape(title)
    t = unicodedata.normalize("NFKD", t)
    t = t.lower()
    t = re.sub(r"\[[^\]]*\]", "", t)
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def invert_abstract(idx: dict[str, list[int]] | None) -> str | None:
    if not idx:
        return None
    words = [""] * (max(max(pos) for pos in idx.values()) + 1)
    for word, positions in idx.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words).strip() or None


def parse_gs_authors_line(line: str) -> tuple[list[str], int | None, str | None]:
    authors: list[str] = []
    year: int | None = None
    venue: str | None = None
    if not line:
        return authors, year, venue

    # Typical: "A Author, B Author - Venue, 2024 - publisher"
    year_match = re.search(r"\b(19|20)\d{2}\b", line)
    if year_match:
        year = int(year_match.group(0))

    parts = re.split(r"\s+-\s+", line, maxsplit=2)
    if parts:
        author_part = parts[0]
        authors = [a.strip() for a in re.split(r",|\.\.\.", author_part) if a.strip()]

    if len(parts) >= 2:
        venue_part = parts[1]
        venue = re.sub(r"\b(19|20)\d{2}\b.*", "", venue_part).strip(" ,-")
        if not venue:
            venue = venue_part.strip()

    return authors, year, venue


def extract_gs_links(result: BeautifulSoup) -> dict[str, str | None]:
    links: dict[str, str | None] = {"primary": None, "pdf": None, "doi": None}
    title_tag = result.select_one(".gs_rt a")
    if title_tag and title_tag.get("href"):
        links["primary"] = title_tag["href"]

    for a in result.select(".gs_or_ggsm a, .gs_ggs a, .gs_rt a"):
        href = a.get("href") or ""
        text = (a.get_text() or "").lower()
        if "[pdf]" in text or href.lower().endswith(".pdf"):
            links["pdf"] = href
        if "doi.org" in href:
            links["doi"] = href

    if links["primary"] and "doi.org" in links["primary"]:
        links["doi"] = links["primary"]

    return links


def harvest_google_scholar(seed_key: str, cites_id: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    meta: dict[str, Any] = {"pages_fetched": 0, "errors": [], "blocked": False}

    for start in range(0, 500, 10):
        url = (
            "https://scholar.google.com/scholar"
            f"?start={start}&hl=en&as_sdt=20000005&sciodt=0,21&cites={cites_id}&scipsc="
        )
        try:
            resp = SESSION.get(url, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as exc:
            meta["errors"].append(f"start={start}: {exc}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(" ", strip=True)
        if "can't perform the operation" in text.lower() or "unusual traffic" in text.lower():
            meta["blocked"] = True
            meta["errors"].append(f"start={start}: Scholar blocked or rate-limited")
            break

        results = soup.select(".gs_ri")
        if not results:
            break

        meta["pages_fetched"] += 1
        for item in results:
            title_tag = item.select_one(".gs_rt")
            if not title_tag:
                continue
            title = re.sub(r"\s+", " ", title_tag.get_text(" ", strip=True))
            if not title or title.lower().startswith("search within citing"):
                continue

            authors_line = item.select_one(".gs_a")
            authors, year, venue = parse_gs_authors_line(
                authors_line.get_text(" ", strip=True) if authors_line else ""
            )
            snippet_tag = item.select_one(".gs_rs")
            snippet = snippet_tag.get_text(" ", strip=True) if snippet_tag else None
            links = extract_gs_links(item)

            records.append(
                {
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "venue": venue,
                    "link": links["primary"],
                    "pdf_link": links["pdf"],
                    "doi": links["doi"],
                    "snippet": snippet,
                    "seed_papers": [seed_key],
                    "sources": ["google_scholar"],
                }
            )

        if len(results) < 10:
            break
        time.sleep(2)

    return records, meta


def harvest_openalex(seed_key: str, openalex_id: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    meta: dict[str, Any] = {"count": 0, "errors": []}
    url = (
        "https://api.openalex.org/works"
        f"?filter=cites:{openalex_id}&per_page=200"
        "&select=id,display_name,publication_year,authorships,primary_location,doi,abstract_inverted_index"
    )
    try:
        resp = SESSION.get(url, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
    except (requests.RequestException, json.JSONDecodeError) as exc:
        meta["errors"].append(str(exc))
        return records, meta

    meta["count"] = payload.get("meta", {}).get("count", 0)
    for work in payload.get("results", []):
        authors = [
            a.get("author", {}).get("display_name")
            for a in work.get("authorships", [])
            if a.get("author", {}).get("display_name")
        ]
        loc = work.get("primary_location") or {}
        source = (loc.get("source") or {}).get("display_name")
        venue = source or loc.get("landing_page_url")
        doi = work.get("doi")
        records.append(
            {
                "title": work.get("display_name"),
                "authors": authors,
                "year": work.get("publication_year"),
                "venue": venue,
                "link": loc.get("landing_page_url") or doi,
                "pdf_link": (loc.get("pdf_url") if loc else None),
                "doi": doi,
                "snippet": invert_abstract(work.get("abstract_inverted_index")),
                "seed_papers": [seed_key],
                "sources": ["openalex"],
                "openalex_id": work.get("id"),
            }
        )
    return records, meta


def harvest_semantic_scholar(seed_key: str, paper_id: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    meta: dict[str, Any] = {"returned": 0, "errors": []}
    offset = 0
    limit = 100

    while True:
        url = (
            f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/citations"
            "?fields=title,authors,year,venue,externalIds,abstract,url,isOpenAccess,openAccessPdf"
            f"&offset={offset}&limit={limit}"
        )
        try:
            resp = SESSION.get(url, timeout=30)
            if resp.status_code == 429:
                meta["errors"].append("rate limited; sleeping")
                time.sleep(3)
                continue
            resp.raise_for_status()
            payload = resp.json()
        except (requests.RequestException, json.JSONDecodeError) as exc:
            meta["errors"].append(str(exc))
            break

        batch = payload.get("data") or []
        if not batch:
            break

        meta["returned"] += len(batch)
        for entry in batch:
            paper = entry.get("citingPaper") or {}
            if not paper.get("title"):
                continue
            ext = paper.get("externalIds") or {}
            doi = ext.get("DOI")
            if doi and not doi.startswith("http"):
                doi = f"https://doi.org/{doi}"
            pdf = None
            oa = paper.get("openAccessPdf") or {}
            if oa.get("url"):
                pdf = oa["url"]
            records.append(
                {
                    "title": paper.get("title"),
                    "authors": [a.get("name") for a in (paper.get("authors") or []) if a.get("name")],
                    "year": paper.get("year"),
                    "venue": paper.get("venue"),
                    "link": paper.get("url") or doi,
                    "pdf_link": pdf,
                    "doi": doi,
                    "snippet": paper.get("abstract"),
                    "seed_papers": [seed_key],
                    "sources": ["semantic_scholar"],
                    "semantic_scholar_id": paper.get("paperId"),
                }
            )

        if len(batch) < limit:
            break
        offset += limit
        time.sleep(0.5)

    return records, meta


def merge_records(all_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}

    def key_for(rec: dict[str, Any]) -> str:
        doi = rec.get("doi") or ""
        if doi:
            doi_key = doi.lower().replace("https://doi.org/", "").strip()
            if doi_key:
                return f"doi:{doi_key}"
        return f"title:{normalize_title(rec.get('title') or '')}"

    for rec in all_records:
        k = key_for(rec)
        if not k or k == "title:":
            continue
        if k not in merged:
            merged[k] = {
                "title": rec.get("title"),
                "authors": rec.get("authors") or [],
                "year": rec.get("year"),
                "venue": rec.get("venue"),
                "link": rec.get("link"),
                "pdf_link": rec.get("pdf_link"),
                "doi": rec.get("doi"),
                "snippet": rec.get("snippet"),
                "seed_papers": list(rec.get("seed_papers") or []),
                "sources": list(rec.get("sources") or []),
                "openalex_id": rec.get("openalex_id"),
                "semantic_scholar_id": rec.get("semantic_scholar_id"),
            }
        else:
            existing = merged[k]
            for field in ("title", "year", "venue", "link", "pdf_link", "doi", "snippet", "openalex_id", "semantic_scholar_id"):
                if not existing.get(field) and rec.get(field):
                    existing[field] = rec[field]
            for author in rec.get("authors") or []:
                if author and author not in existing["authors"]:
                    existing["authors"].append(author)
            for seed in rec.get("seed_papers") or []:
                if seed not in existing["seed_papers"]:
                    existing["seed_papers"].append(seed)
            for src in rec.get("sources") or []:
                if src not in existing["sources"]:
                    existing["sources"].append(src)

    out = list(merged.values())
    out.sort(key=lambda r: (r.get("year") or 0, normalize_title(r.get("title") or "")), reverse=True)
    return out


def seed_label(seed_key: str) -> str:
    return SEEDS[seed_key]["label"]


def render_markdown(catalog: dict[str, Any]) -> str:
    lines = [
        "# Citing Works Catalog",
        "",
        f"Generated: {catalog['generated_at']}",
        "",
        "## Seed Papers",
        "",
    ]
    for key, seed in SEEDS.items():
        lines.append(f"- **{seed['label']}**: {seed['title']} (DOI: {seed['doi']})")
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- **Total unique citing works:** {catalog['total_unique_works']}",
            f"- **Citing both seeds:** {catalog['citing_both_seeds']}",
            "",
            "### Per-source harvest counts (pre-dedup)",
            "",
        ]
    )
    for src, counts in catalog["source_harvest"].items():
        lines.append(f"- **{src}**: {counts}")
    lines.extend(["", "### Fetch limitations", ""])
    for note in catalog.get("fetch_limitations", []):
        lines.append(f"- {note}")
    lines.extend(["", "## All Citing Works", ""])

    for i, work in enumerate(catalog["works"], 1):
        seeds = ", ".join(seed_label(s) for s in work.get("seed_papers", []))
        authors = ", ".join(work.get("authors") or []) or "—"
        lines.append(f"### {i}. {work.get('title')}")
        lines.append("")
        lines.append(f"- **Authors:** {authors}")
        lines.append(f"- **Year:** {work.get('year') or '—'}")
        lines.append(f"- **Venue:** {work.get('venue') or '—'}")
        lines.append(f"- **Cited by seed(s):** {seeds}")
        lines.append(f"- **Sources:** {', '.join(work.get('sources') or [])}")
        if work.get("doi"):
            lines.append(f"- **DOI:** {work['doi']}")
        if work.get("link"):
            lines.append(f"- **Link:** {work['link']}")
        if work.get("pdf_link"):
            lines.append(f"- **PDF:** {work['pdf_link']}")
        if work.get("snippet"):
            snippet = work["snippet"].replace("\n", " ")
            if len(snippet) > 500:
                snippet = snippet[:497] + "..."
            lines.append(f"- **Snippet:** {snippet}")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    all_records: list[dict[str, Any]] = []
    source_harvest: dict[str, dict[str, Any]] = {}
    fetch_limitations: list[str] = []

    for seed_key, seed in SEEDS.items():
        gs_records, gs_meta = harvest_google_scholar(seed_key, seed["scholar_cites_id"])
        all_records.extend(gs_records)
        source_harvest.setdefault("google_scholar", {})[seed_key] = len(gs_records)
        if gs_meta.get("blocked"):
            fetch_limitations.append(
                f"Google Scholar blocked or rate-limited for {seed['label']} after {gs_meta['pages_fetched']} page(s)."
            )
        if gs_meta.get("errors"):
            fetch_limitations.extend(f"Google Scholar ({seed['label']}): {e}" for e in gs_meta["errors"])

        oa_records, oa_meta = harvest_openalex(seed_key, seed["openalex_id"])
        all_records.extend(oa_records)
        source_harvest.setdefault("openalex", {})[seed_key] = oa_meta.get("count", len(oa_records))
        if oa_meta.get("errors"):
            fetch_limitations.extend(f"OpenAlex ({seed['label']}): {e}" for e in oa_meta["errors"])

        ss_records, ss_meta = harvest_semantic_scholar(seed_key, seed["semantic_scholar_id"])
        all_records.extend(ss_records)
        source_harvest.setdefault("semantic_scholar", {})[seed_key] = ss_meta.get("returned", len(ss_records))
        if ss_meta.get("errors"):
            fetch_limitations.extend(f"Semantic Scholar ({seed['label']}): {e}" for e in ss_meta["errors"])

        time.sleep(1)

    merged = merge_records(all_records)
    citing_both = sum(1 for w in merged if len(w.get("seed_papers", [])) > 1)

    catalog = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed_papers": [
            {
                "key": k,
                "label": v["label"],
                "title": v["title"],
                "doi": v["doi"],
                "openalex_id": v["openalex_id"],
                "semantic_scholar_id": v["semantic_scholar_id"],
                "google_scholar_cites_id": v["scholar_cites_id"],
            }
            for k, v in SEEDS.items()
        ],
        "total_unique_works": len(merged),
        "citing_both_seeds": citing_both,
        "source_harvest": source_harvest,
        "fetch_limitations": fetch_limitations,
        "works": merged,
    }

    JSON_PATH.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    MD_PATH.write_text(render_markdown(catalog), encoding="utf-8")

    print(json.dumps({
        "total_unique_works": len(merged),
        "citing_both_seeds": citing_both,
        "source_harvest": source_harvest,
        "json": str(JSON_PATH),
        "md": str(MD_PATH),
    }, indent=2))


if __name__ == "__main__":
    main()
