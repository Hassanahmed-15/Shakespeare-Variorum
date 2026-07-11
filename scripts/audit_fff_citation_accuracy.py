#!/usr/bin/env python3
"""Audit citation accuracy (hallucination rate) for Full Fathom Five analyses.

Generates a stratified sample, calls OpenAI with the same grounding stack as
functions/shakespeare.js, server-overwrites New Variorum Analysis from local JSON,
extracts citations, and classifies each against retrieved sources.

Outputs (validation/fff_citation_audit/):
  sample_manifest.json       — stratified passage sample
  sample_raw_outputs.json    — full API responses + parsed sections
  citations_classified.json  — one row per citation with classification
  unverifiable_citations.json
  rate_table.json + rate_table.md

Usage:
  python3 scripts/audit_fff_citation_accuracy.py
  python3 scripts/audit_fff_citation_accuracy.py --profile expanded   # 27 plays × 5 = 135
  python3 scripts/audit_fff_citation_accuracy.py --profile compact    # 8-play pilot
  python3 scripts/audit_fff_citation_accuracy.py --dry-run
  python3 scripts/audit_fff_citation_accuracy.py --resume
  python3 scripts/audit_fff_citation_accuracy.py --classify-only
  python3 scripts/audit_fff_citation_accuracy.py --limit 2
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PUBLIC = ROOT / "Public" / "Data"
OUT = ROOT / "validation" / "fff_citation_audit"

# Mirrors functions/shakespeare.js playsWithoutNewVariorum (NV section excluded in FFF).
PLAYS_WITHOUT_NV = {
    "allswell", "comedyoferrors", "measureformeasure", "merrywives",
    "pericles", "taming", "troilus", "twogentlemen",
    "henryvi1", "henryvi2", "henryvi3", "henryviii",
    "richardii", "richardiii", "antony", "coriolanus",
    "henryv", "titus", "timon", "henryiv2", "midsummer",
}

# 22-play NV corpus (same set as scripts/audit_nv_fidelity_all_plays.py).
NV_CORPUS = [
    ("Romeo and Juliet", 1871, "romeo_and_juliet.json", "romeo"),
    ("Macbeth", 1873, "macbeth_notes_cleaned_play.json", "macbeth"),
    ("Hamlet", 1877, "hamlet_notes (1).json", "hamlet"),
    ("King Lear", 1880, "kinglear_notes.json", "kinglear"),
    ("Othello", 1886, "othello_notes.json", "othello"),
    ("The Merchant of Venice", 1888, "merchant_of_venice.json", "merchantofvenice"),
    ("As You Like It", 1890, "as_you_like_it.json", "asyoulikeit"),
    ("The Tempest", 1892, "the_tempest.json", "tempest"),
    ("A Midsummer Night's Dream", 1895, "midsummer_nights_dream.json", "midsummer"),
    ("The Winter's Tale", 1898, "the_winters_tale.json", "winterstale"),
    ("Much Ado About Nothing", 1899, "much_ado_about_nothing.json", "muchado"),
    ("Twelfth Night", 1901, "twelfth_night.json", "twelfthnight"),
    ("Love's Labour's Lost", 1904, "loves_labours_lost.json", "loveslabourslost"),
    ("Antony and Cleopatra", 1907, "antony_and_cleopatra.json", "antony"),
    ("Richard III", 1908, "richard_iii.json", "richardiii"),
    ("Julius Caesar", 1913, "julius_caesar.json", "juliuscaesar"),
    ("Cymbeline", 1913, "cymbeline.json", "cymbeline"),
    ("King John", 1919, "king_john.json", "kingjohn"),
    ("Coriolanus", 1928, "Coriolanus.json", "coriolanus"),
    ("Henry IV, Part 1", 1936, "henry_iv_part1.json", "henryiv1"),
    ("Henry IV, Part 2", 1940, "henry_iv_part2.json", "henryiv2"),
    ("Troilus and Cressida", 1953, "troilus_and_cressida.json", "troilus"),
]

# Non-NV contrast plays (no injected variorum section; model-only FFF).
CONTRAST_PLAYS = [
    ("Henry V", "henry_v.json", "henryv"),
    ("Titus Andronicus", "titus_andronicus.json", "titus"),
    ("Timon of Athens", "timon_of_athens.json", "timon"),
    ("Pericles", "pericles.json", "pericles"),
    ("Measure for Measure", "measure_for_measure.json", "measureformeasure"),
]

# Original 8-play pilot subset (compact profile).
COMPACT_KEYS = {
    "hamlet", "macbeth", "othello", "romeo", "tempest", "kinglear", "troilus", "antony",
}


def play_spec(display_name: str, year: int | None, filename: str, play_name: str, *, corpus: str) -> dict:
    return {
        "key": play_name,
        "display_name": display_name,
        "year": year,
        "file": filename,
        "play_name": play_name,
        "has_nv": play_name not in PLAYS_WITHOUT_NV,
        "corpus": corpus,
    }


def get_play_manifest(profile: str) -> list[dict]:
    nv = [
        play_spec(name, year, fn, slug, corpus="nv_22")
        for name, year, fn, slug in NV_CORPUS
    ]
    contrast = [
        play_spec(name, None, fn, slug, corpus="contrast_non_nv")
        for name, fn, slug in CONTRAST_PLAYS
    ]
    if profile == "compact":
        return [p for p in nv if p["key"] in COMPACT_KEYS]
    if profile == "full":
        return nv
    if profile == "expanded":
        return nv + contrast
    raise ValueError(f"Unknown profile: {profile}")


# Default manifest loaded at runtime via get_play_manifest(profile).

PASSAGE_TYPES = ("soliloquy", "dialogue", "stage_direction", "textually_contested")

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "shall", "should", "may", "might", "must", "can", "could",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her",
    "us", "them", "my", "thy", "thine", "your", "his", "its", "our", "their",
    "this", "that", "these", "those", "not", "no", "so", "if", "then", "than",
    "o", "oh", "ay", "nay", "yet", "still", "now", "here", "there", "when",
    "where", "why", "how", "all", "some", "more", "most", "such", "what",
    "nor", "let", "come", "go", "see", "say", "make", "take", "who", "whom",
}

LEMMA_OVERRIDES = {
    "doth": "do", "dost": "do", "hath": "have", "hast": "have",
    "wherefore": "wherefore", "incarnardine": "incarnadine", "fadom": "fathom",
}

MODEL_SECTIONS = [
    "Plain-Language Paraphrase",
    "Language and Rhetoric",
    "Synopsis",
    "Key Words & Glosses",
    "Historical Context",
    "Sources",
    "Literary Analysis",
    "Critical Reception",
    "Similar phrases or themes in other plays",
]

NV_SECTION = "New Variorum Analysis"

# Known retrievable source fingerprints (lowercase substrings)
KNOWN_LEXICAL = {
    "onions": "onions",
    "schmidt": "schmidt",
    "shakespeare-lexicon": "schmidt",
    "cawdrey": "leme",
    "bullokar": "leme",
    "cockeram": "leme",
    "florio": "leme",
    "cotgrave": "leme",
    "leme": "leme",
    "geneva bible": "geneva",
    "geneva": "geneva",
}

KNOWN_HISTORICAL = {
    "holinshed", "plutarch", "north", "ovid", "seneca", "montaigne",
    "bible", "geneva", "chronicles", "aristotle",
}


def load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.is_file():
        return
    raw = env_path.read_bytes()
    for enc in ("utf-8-sig", "utf-16", "utf-16-le", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        return
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def normalize_token(token: str) -> str:
    t = token.lower()
    t = re.sub(r"^['']|['']$", "", t)
    t = re.sub(r"['']s$|['']d$|['']ll$|['']ve$|['']re$", "", t)
    t = re.sub(r"[^a-z'-]", "", t)
    if t in LEMMA_OVERRIDES:
        return LEMMA_OVERRIDES[t]
    if t.endswith("eth") and len(t) > 4:
        return t[:-3] + "e"
    if t.endswith("est") and len(t) > 4:
        return t[:-3]
    if t.endswith("ed") and len(t) > 3:
        return t[:-2]
    if t.endswith("ing") and len(t) > 4:
        return t[:-3]
    return t


def extract_lookup_candidates(text: str, max_words: int = 8) -> list[str]:
    tokens = [
        normalize_token(w)
        for w in re.split(r"\s+", text)
        if normalize_token(w) and len(normalize_token(w)) > 2 and normalize_token(w) not in STOPWORDS
    ]
    seen: list[str] = []
    for t in sorted(set(tokens), key=len, reverse=True):
        if t not in seen:
            seen.append(t)
    return seen[:max_words]


def normalize_text(text: str) -> str:
    t = text.lower()
    t = t.replace("æ", "ae").replace("œ", "oe")
    t = re.sub(r"['']", "'", t)
    t = re.sub(r"[^a-z0-9'\s-]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def load_json_index(filename: str) -> dict:
    path = DATA / filename
    raw = json.loads(path.read_text(encoding="utf-8"))
    meta = raw.pop("_meta", {})
    return {"meta": meta, "entries": raw}


@dataclass
class GroundingBundle:
    onions_hits: list[dict]
    schmidt_hits: list[dict]
    leme_hits: list[dict]
    geneva_hits: list[dict]
    variorum_notes: list[str]
    onions_block: str
    schmidt_block: str
    leme_block: str
    geneva_block: str


def lookup_onions(words: list[str]) -> list[dict]:
    idx = load_json_index("onions_glossary_index.json")["entries"]
    hits = []
    for w in words:
        entry = idx.get(w) or idx.get(w.replace(" ", "-"))
        if entry:
            hits.append({"query": w, "headword": entry.get("headword", w), "text": entry.get("text", "")})
    return hits


def lookup_schmidt(words: list[str]) -> list[dict]:
    idx = load_json_index("schmidt_lexicon_index.json")["entries"]
    hits = []
    for w in words:
        entry = idx.get(w) or idx.get(w.replace(" ", "-"))
        if entry:
            hits.append({"query": w, "headword": entry.get("headword", w), "text": entry.get("text", "")})
    return hits


def lookup_leme(words: list[str], max_hits: int = 4) -> list[dict]:
    raw = load_json_index("leme_period_index.json")
    entries = raw["entries"].get("entries", raw["entries"])
    hits = []
    seen = set()
    for w in words:
        source_entries = entries.get(w)
        if not source_entries:
            continue
        for entry in source_entries:
            key = f"{entry.get('source_id')}:{entry.get('headword')}"
            if key in seen:
                continue
            seen.add(key)
            hits.append({"query": w, **entry})
            if len(hits) >= max_hits:
                return hits
    return hits


def lookup_geneva(text: str, max_hits: int = 5) -> list[dict]:
    raw = load_json_index("geneva_bible_index.json")
    verses = raw["entries"].get("verses", [])
    words = normalize_text(text).split()
    phrases: list[str] = []
    for size in (5, 4, 3):
        for i in range(max(0, len(words) - size + 1)):
            chunk = " ".join(words[i : i + size])
            if len(chunk) >= 8:
                phrases.append(chunk)
    phrases = sorted(set(phrases), key=len, reverse=True)[:12]
    hits = []
    seen = set()
    for phrase in phrases:
        for verse in verses:
            vnorm = normalize_text(verse.get("text", ""))
            if phrase in vnorm:
                ref = verse.get("ref")
                if ref in seen:
                    continue
                seen.add(ref)
                hits.append({
                    "matched_phrase": phrase,
                    "ref": ref,
                    "text": verse.get("text", ""),
                })
                if len(hits) >= max_hits:
                    return hits
    return hits


def format_onions_block(hits: list[dict]) -> str:
    if not hits:
        return "LEXICAL SOURCE (Onions, A Shakespeare Glossary, 1911/1919):\nNo matching headwords."
    lines = ["LEXICAL SOURCE (Onions, A Shakespeare Glossary, 1911/1919) — USE VERBATIM."]
    for h in hits:
        lines.append(f"▸ {h['headword']}\n  {h['text']}")
    return "\n".join(lines)


def format_schmidt_block(hits: list[dict]) -> str:
    if not hits:
        return "LEXICAL SOURCE (Schmidt, Shakespeare-Lexicon, 1902):\nNo matching headwords."
    lines = ["LEXICAL SOURCE (Schmidt, Shakespeare-Lexicon, 1902) — USE VERBATIM."]
    for h in hits:
        lines.append(f"▸ {h['headword']}\n  {h['text']}")
    return "\n".join(lines)


def format_leme_block(hits: list[dict]) -> str:
    if not hits:
        return "CONTEMPORARY PERIOD LEXICONS (LEME): No matching headwords."
    lines = ["CONTEMPORARY PERIOD LEXICONS (LEME) — USE VERBATIM."]
    for h in hits:
        lines.append(f"▸ {h.get('headword')} — {h.get('text', '')}")
    return "\n".join(lines)


def format_geneva_block(hits: list[dict]) -> str:
    if not hits:
        return "BIBLICAL SOURCE (Geneva Bible, 1599): No strong parallels found."
    lines = ["BIBLICAL SOURCE (Geneva Bible, 1599) — POSSIBLE PARALLELS ONLY."]
    for h in hits:
        lines.append(f"▸ {h['ref']} (matched: \"{h['matched_phrase']}\")\n  {h['text']}")
    return "\n".join(lines)


def build_grounding(text: str, variorum_notes: list[str]) -> GroundingBundle:
    words = extract_lookup_candidates(text, max_words=8)
    onions_hits = lookup_onions(words)
    schmidt_hits = lookup_schmidt(words)
    leme_hits = lookup_leme(words)
    geneva_hits = lookup_geneva(text)
    return GroundingBundle(
        onions_hits=onions_hits,
        schmidt_hits=schmidt_hits,
        leme_hits=leme_hits,
        geneva_hits=geneva_hits,
        variorum_notes=variorum_notes,
        onions_block=format_onions_block(onions_hits),
        schmidt_block=format_schmidt_block(schmidt_hits),
        leme_block=format_leme_block(leme_hits),
        geneva_block=format_geneva_block(geneva_hits),
    )


def load_play(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_lines(play_data: dict):
    for scene_key, scene in play_data.items():
        if str(scene_key).startswith("_") or scene_key == "DRAMATIS PERSONAE":
            continue
        if not isinstance(scene, dict):
            continue
        for line_key, line_data in scene.items():
            if str(line_key).startswith("_"):
                continue
            if isinstance(line_data, str):
                text = line_data
                notes = []
            elif isinstance(line_data, dict):
                text = (
                    line_data.get("play")
                    or line_data.get("text")
                    or line_data.get("line")
                    or ""
                )
                notes = line_data.get("notes") or []
            else:
                continue
            if not text or not str(text).strip():
                continue
            yield scene_key, str(line_key), str(text).strip(), notes


def is_stage_direction(text: str) -> bool:
    t = text.strip()
    if t.startswith("["):
        return True
    low = t.lower()
    stage_verbs = ("enter", "exit", "exeunt", "retreat", "flourish", "within", "above")
    if t.startswith("(") and any(v in low for v in stage_verbs):
        return True
    if any(v in low for v in (" exits", " exit.", " exeunt", "they enter", "enter ")):
        return True
    return False


def is_corrupted_play_line(text: str) -> bool:
    """Skip rows where dialogue was merged with apparatus text."""
    if len(text) > 220:
        return True
    if re.search(r"\]\s*(JOHNSON|STEEVENS|DYCE|MALONE)\.", text):
        return True
    if text.count("]") >= 3:
        return True
    return False


def is_speaker_line(text: str) -> bool:
    return bool(re.match(r"^[A-Z][A-Z\s'.-]{1,40}:\s", text))


def note_score(notes: list) -> int:
    if not notes:
        return 0
    return sum(len(str(n)) for n in notes) + 50 * len(notes)


def per_play_counts(n_plays: int, total_passages: int) -> list[int]:
    """Split total_passages across n_plays as evenly as possible (±1)."""
    if n_plays <= 0:
        return []
    base, rem = divmod(total_passages, n_plays)
    return [base + (1 if i < rem else 0) for i in range(n_plays)]


def build_sample(play_manifest: list[dict], per_play: int = 5, *, total_passages: int | None = None) -> list[dict]:
    sample = []
    per_play_list = per_play_counts(len(play_manifest), total_passages) if total_passages else None
    for pi, spec in enumerate(play_manifest):
        play_per_play = per_play_list[pi] if per_play_list is not None else per_play
        if play_per_play <= 0:
            continue
        path = PUBLIC / spec["file"]
        if not path.is_file():
            raise FileError(f"Missing play file: {path}")
        play_data = load_play(path)
        rows = [
            r for r in iter_lines(play_data)
            if not is_corrupted_play_line(r[2])
        ]

        soliloquy = [
            r for r in rows
            if not is_stage_direction(r[2])
            and 25 <= len(r[2]) <= 180
            and (
                not is_speaker_line(r[2])
                or (is_speaker_line(r[2]) and len(r[2].split(":", 1)[-1].strip()) > 30)
            )
        ]
        soliloquy.sort(key=lambda r: (len(r[3]), len(r[2])), reverse=True)

        stage = [r for r in rows if is_stage_direction(r[2])]

        contested = [r for r in rows if note_score(r[3]) > 400 and r[3]]
        contested.sort(key=lambda r: note_score(r[3]), reverse=True)

        dialogue_pairs = []
        by_scene: dict[str, list] = {}
        for r in rows:
            by_scene.setdefault(r[0], []).append(r)
        for _scene_key, scene_rows in by_scene.items():
            for i in range(len(scene_rows) - 1):
                a, b = scene_rows[i], scene_rows[i + 1]
                if is_stage_direction(a[2]) or is_stage_direction(b[2]):
                    continue
                if is_speaker_line(a[2]) and is_speaker_line(b[2]):
                    sp_a = a[2].split(":", 1)[0]
                    sp_b = b[2].split(":", 1)[0]
                    if sp_a != sp_b:
                        dialogue_pairs.append((a, b))
                        break
            if dialogue_pairs:
                break

        def row_key(r):
            return (r[0], r[1])

        used_keys: set[tuple] = set()
        chosen: list[dict] = []

        def add_pick(ptype: str, r, *, pair=None):
            if pair:
                a, b = pair
                keys = {row_key(a), row_key(b)}
                if keys & used_keys:
                    return False
                used_keys.update(keys)
                chosen.append({
                    "passage_type": ptype,
                    "scene": a[0],
                    "line_keys": [a[1], b[1]],
                    "text": f"{a[2]}\n{b[2]}",
                    "notes": (a[3] or []) + (b[3] or []),
                })
                return True
            rk = row_key(r)
            if rk in used_keys:
                return False
            used_keys.add(rk)
            chosen.append({
                "passage_type": ptype,
                "scene": r[0],
                "line_keys": [r[1]],
                "text": r[2],
                "notes": r[3],
            })
            return True

        for ptype, pool, is_pair in (
            ("soliloquy", soliloquy, False),
            ("dialogue", dialogue_pairs, True),
            ("stage_direction", stage, False),
            ("textually_contested", contested, False),
        ):
            if is_pair:
                for pair in pool:
                    if add_pick("dialogue", None, pair=pair):
                        break
            else:
                for r in pool:
                    if add_pick(ptype, r):
                        break

        extras: list[tuple[str, Any]] = []
        for r in contested:
            extras.append(("textually_contested", r))
        for r in soliloquy:
            extras.append(("soliloquy", r))
        for r in stage:
            extras.append(("stage_direction", r))
        for pair in dialogue_pairs:
            extras.append(("dialogue", pair))

        ei = 0
        while len(chosen) < play_per_play and ei < len(extras):
            ptype, item = extras[ei]
            ei += 1
            if ptype == "dialogue":
                add_pick(ptype, None, pair=item)
            else:
                add_pick(ptype, item)

        chosen = chosen[:play_per_play]

        for i, item in enumerate(chosen):
            sample.append({
                "sample_id": f"{spec['key']}_{item['passage_type']}_{i+1}",
                "play_key": spec["key"],
                "play_name": spec["play_name"],
                "display_name": spec.get("display_name", spec["key"]),
                "play_file": spec["file"],
                "has_nv": spec["has_nv"],
                "corpus": spec.get("corpus", "unknown"),
                **item,
            })
    return sample


AUDIT_LAYERS = ("nv", "onions", "schmidt")
LEXICON_SECTIONS = ("Language and Rhetoric", "Key Words & Glosses")

LAYER_DESCRIPTIONS = {
    "nv": (
        "New Variorum Analysis section only. Text is server-overwritten from local play JSON "
        "before citation extraction; citations are checked against injected apparatus notes."
    ),
    "onions": (
        "Onions parenthetical citations in Language and Rhetoric and Key Words & Glosses only. "
        "Checked against retrieved Onions glossary entries supplied in the prompt."
    ),
    "schmidt": (
        "Schmidt parenthetical citations in Language and Rhetoric and Key Words & Glosses only. "
        "Checked against retrieved Schmidt lexicon entries supplied in the prompt."
    ),
}


def is_onions_citation(cite: str) -> bool:
    c = cite.lower()
    return "onions" in c or "shakespeare glossary" in c


def is_schmidt_citation(cite: str) -> bool:
    c = cite.lower()
    return "schmidt" in c or "shakespeare-lexicon" in c or "shakespeare lexicon" in c


def classify_citation_layer(row: dict, grounding: GroundingBundle, section: str, layer: str) -> dict:
    cite = row["citation_text"]
    cite_low = cite.lower()
    ctx = row.get("context_snippet", "").lower()

    if layer == "nv":
        if section != NV_SECTION:
            return {**row, "classification": "unverifiable_needs_human_review", "verification_basis": "wrong_section_for_nv_layer"}
        for note in grounding.variorum_notes:
            note_str = str(note)
            if cite in note_str or cite_low in note_str.lower():
                return {**row, "classification": "verifiable_correct", "verification_basis": "variorum_injected_note"}
            if re.search(re.escape(cite.split(":")[0][:20]), note_str, re.I):
                return {**row, "classification": "verifiable_correct", "verification_basis": "variorum_injected_note"}
        if grounding.variorum_notes:
            return {**row, "classification": "real_source_wrong_details", "verification_basis": "nv_section_not_in_injected_notes"}
        return {**row, "classification": "verifiable_correct", "verification_basis": "nv_empty_placeholder"}

    if layer == "onions":
        if not is_onions_citation(cite):
            return {**row, "classification": "unverifiable_needs_human_review", "verification_basis": "not_onions_citation"}
        if grounding.onions_hits:
            return {**row, "classification": "verifiable_correct", "verification_basis": "onions_retrieved"}
        if "not in retrieved" in ctx and "onions" in ctx:
            return {**row, "classification": "verifiable_correct", "verification_basis": "explicit_miss_statement"}
        return {**row, "classification": "real_source_wrong_details", "verification_basis": "onions_cited_without_retrieval"}

    if layer == "schmidt":
        if not is_schmidt_citation(cite):
            return {**row, "classification": "unverifiable_needs_human_review", "verification_basis": "not_schmidt_citation"}
        if grounding.schmidt_hits:
            return {**row, "classification": "verifiable_correct", "verification_basis": "schmidt_retrieved"}
        if "not in retrieved" in ctx and "schmidt" in ctx:
            return {**row, "classification": "verifiable_correct", "verification_basis": "explicit_miss_statement"}
        return {**row, "classification": "real_source_wrong_details", "verification_basis": "schmidt_cited_without_retrieval"}

    raise ValueError(f"Unknown layer: {layer}")


def classify_layer_from_outputs(raw_outputs: list[dict], layer: str) -> list[dict]:
    citations: list[dict] = []
    for record in raw_outputs:
        notes = [str(n) for n in (record.get("notes") or [])]
        grounding = build_grounding(record["text"], notes)
        for sec_name, sec_text in (record.get("analysis_sections") or {}).items():
            if layer == "nv":
                if sec_name != NV_SECTION:
                    continue
            elif sec_name not in LEXICON_SECTIONS:
                continue
            for cite_row in extract_citations(sec_text, sec_name, record["sample_id"]):
                if layer == "onions" and not is_onions_citation(cite_row["citation_text"]):
                    continue
                if layer == "schmidt" and not is_schmidt_citation(cite_row["citation_text"]):
                    continue
                citations.append(classify_citation_layer(cite_row, grounding, sec_name, layer))
    return citations


def write_layer_audit_outputs(layer: str, citations: list[dict], meta: dict) -> None:
    layer_dir = OUT / "layers" / layer
    layer_dir.mkdir(parents=True, exist_ok=True)
    unver = [c for c in citations if c["classification"] == "unverifiable_needs_human_review"]

    cites_path = layer_dir / "citations_classified.json"
    cites_path.write_text(json.dumps(citations, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    unver_path = layer_dir / "unverifiable_citations.json"
    unver_path.write_text(json.dumps(unver, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    layer_meta = {**meta, "audit_layer": layer, "layer_description": LAYER_DESCRIPTIONS[layer]}
    table = rate_table(citations)
    table_path = layer_dir / "rate_table.json"
    table_path.write_text(json.dumps({"meta": layer_meta, **table}, indent=2) + "\n", encoding="utf-8")
    md_path = layer_dir / "rate_table.md"
    md_path.write_text(write_layer_md(table, layer_meta, layer), encoding="utf-8")

    print(
        f"Layer {layer}: {len(citations)} citations, "
        f"{table['overall']['rates_pct']['verifiable_correct']}% correct, "
        f"{table['overall']['rates_pct']['fabricated']}% fabricated"
    )
    print(f"  Wrote {cites_path}")
    print(f"  Wrote {unver_path}")
    print(f"  Wrote {table_path} and {md_path}")


def write_all_layer_audits(raw_outputs: list[dict], meta: dict, layers: tuple[str, ...] = AUDIT_LAYERS) -> None:
    for layer in layers:
        citations = classify_layer_from_outputs(raw_outputs, layer)
        write_layer_audit_outputs(layer, citations, meta)


def write_layer_md(table: dict, meta: dict, layer: str) -> str:
    layer_titles = {
        "nv": "New Variorum Analysis (Injected Apparatus)",
        "onions": "Onions Glossary Citations",
        "schmidt": "Schmidt Lexicon Citations",
    }
    if meta.get("passages_per_play"):
        per_play_line = str(meta["passages_per_play"])
    else:
        target = meta.get("total_passages_target", meta["total_passages"])
        per_play_line = f"{target} total ({meta['total_passages']} sampled)"
    lines = [
        f"# Full Fathom Five — {layer_titles[layer]}",
        "",
        f"- Audit layer: **{layer}**",
        f"- Plays (N): **{meta['n_plays']}**",
        f"- Total passages: **{meta['total_passages']}**",
        f"- Passages per play: **{per_play_line}**",
        f"- Model: **{meta['model']}**",
        f"- Generated: {table['generated_at']}",
        "",
        "## Method",
        "",
        meta["layer_description"],
        "",
        "Geneva Bible, LEME, and other source layers are **excluded** from this layer audit.",
        "",
        "Classifications: `verifiable_correct`, `real_source_wrong_details`, `fabricated`,",
        "`unverifiable_needs_human_review`. Rates are sample estimates, not a corpus census.",
        "",
        "## Rate table",
        "",
        "| Scope | n | Correct % | Wrong details % | Fabricated % | Unverifiable % |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    t = table["overall"]
    r = t["rates_pct"]
    lines.append(
        f"| Overall | {t['n']} | {r['verifiable_correct']} | {r['real_source_wrong_details']} | "
        f"{r['fabricated']} | {r['unverifiable_needs_human_review']} |"
    )
    return "\n".join(lines) + "\n"


def classify_from_outputs(raw_outputs: list[dict]) -> list[dict]:
    all_citations: list[dict] = []
    for record in raw_outputs:
        notes = [str(n) for n in (record.get("notes") or [])]
        grounding = build_grounding(record["text"], notes)
        for sec_name, sec_text in (record.get("analysis_sections") or {}).items():
            for cite_row in extract_citations(sec_text, sec_name, record["sample_id"]):
                all_citations.append(classify_citation(cite_row, grounding, sec_name))
    return all_citations


def load_existing_outputs(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def write_audit_outputs(raw_outputs: list[dict], meta: dict, model: str) -> None:
    all_citations = classify_from_outputs(raw_outputs)
    unver = [c for c in all_citations if c["classification"] == "unverifiable_needs_human_review"]

    raw_path = OUT / "sample_raw_outputs.json"
    raw_path.write_text(json.dumps(raw_outputs, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    cites_path = OUT / "citations_classified.json"
    cites_path.write_text(json.dumps(all_citations, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    unver_path = OUT / "unverifiable_citations.json"
    unver_path.write_text(json.dumps(unver, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    table = rate_table(all_citations)
    table_path = OUT / "rate_table.json"
    table_path.write_text(json.dumps({"meta": meta, **table}, indent=2) + "\n", encoding="utf-8")
    md_path = OUT / "rate_table.md"
    md_path.write_text(write_md(table, meta), encoding="utf-8")

    print(f"Wrote {raw_path} ({len(raw_outputs)} passages)")
    print(f"Wrote {cites_path} ({len(all_citations)} citations)")
    print(f"Wrote {unver_path} ({len(unver)} unverifiable)")
    print(f"Wrote {table_path} and {md_path}")


def build_system_prompt(play_name: str, include_nv: bool) -> str:
    nv_line = "\n**New Variorum Analysis:** (REQUIRED)" if include_nv else ""
    prompt = f"""You are an expert Shakespearean scholar providing the most comprehensive analysis possible.

IMPORTANT CONTEXT: The input text will consist of 1–3 consecutive lines selected from a Shakespearean play. Analyze those lines only and avoid referencing any surrounding text. Focus on the content and meaning of the selected text without mentioning specific scenes, acts, or play names.

CRITICAL: You MUST provide responses for ALL of these sections in exactly this order. Do not skip any sections. EVERY section must be included:

**Plain-Language Paraphrase:** (REQUIRED - FIRST SECTION)
**Language and Rhetoric:** (REQUIRED - NEW SECTION)
**Synopsis:** (REQUIRED - Focus on the content and meaning of the selected text without mentioning specific scenes)
**Key Words & Glosses:** (REQUIRED)
**Historical Context:** (REQUIRED)
**Sources:** (REQUIRED)
**Literary Analysis:** (REQUIRED)
**Critical Reception:** (REQUIRED)
**Similar phrases or themes in other plays:** (REQUIRED){nv_line}

FORMAT REQUIREMENTS:
- Start each section with the exact heading format shown above (colons are already included).
- Provide 6–12 sentences per section; use complete, scholarly style.
- Always italicize titles using <em>italics</em>, never quote them or italicize author names.
- **Key Words & Glosses**: Use format "word" means [definition] (Onions, A Shakespeare Glossary, 1911/1919) or (Schmidt, Shakespeare-Lexicon, 1902) when the supplied lexical block is Schmidt. Every gloss MUST end with its source citation.
- **Language and Rhetoric**: Include (1) archaic usage and word history from the supplied Onions or Schmidt entries, with the same parenthetical citations after each lexical point, (2) rhetorical devices, (3) meter & rhythm.

LITERARY ANALYSIS REQUIREMENTS:
- Do NOT name any specific critics or scholars — no personal names whatsoever.
- Structure the section as a series of school-based readings.
- Do not invent critic names, book titles, or publication details.

LENGTH: 800–1200 words total"""
    if include_nv:
        prompt += """

**New Variorum Analysis:**
For this section, use the historical variorum notes provided below.
- Display the EXACT notes linked to the line numbers passed in.
- Do NOT summarize, truncate, or modify the notes in any way.
- Format each entry as: [Line X] [EXACT commentary text from the provided notes]"""
    prompt += """

SOURCE GROUNDING RULES:
- Onions (1911/1919): primary Shakespeare glossary for Key Words & Glosses and archaic usage.
- Schmidt (1902): supplementary Shakespeare lexicon.
- LEME period lexicons: contemporary hard-word dictionaries.
- Geneva Bible (1599): candidate biblical parallels for Sources only.
- Use supplied source text verbatim; do not cite the Oxford English Dictionary unless a supplied entry references it.
- If no entry is supplied for a word, write "not in retrieved [source name]."
"""
    return prompt


def build_user_prompt(text: str, grounding: GroundingBundle) -> str:
    return f"""Text to analyze: "{text}"

Please provide a Full Fathom Five analysis following the exact format specified in the system prompt.

---
{grounding.onions_block}

{grounding.schmidt_block}

{grounding.leme_block}

{grounding.geneva_block}
---"""


def call_openai(system_prompt: str, user_prompt: str, model: str = "gpt-4o") -> dict:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set; cannot generate analyses.")

    body = json.dumps({
        "model": model,
        "temperature": 0.3,
        "max_tokens": 4096,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode("utf-8"))


def parse_sections(raw: str, include_nv: bool) -> dict[str, str]:
    sections = MODEL_SECTIONS.copy()
    if include_nv:
        sections.append(NV_SECTION)
    out: dict[str, str] = {}
    current = None
    buf: list[str] = []
    for line in raw.splitlines():
        trimmed = line.strip()
        matched = None
        for sec in sections:
            if trimmed.lower().startswith(f"**{sec.lower()}") or trimmed.lower().startswith(sec.lower()):
                matched = sec
                break
        if matched:
            if current and buf:
                out[current] = "\n".join(buf).strip()
            current = matched
            buf = []
        elif current and trimmed:
            buf.append(trimmed)
    if current and buf:
        out[current] = "\n".join(buf).strip()
    return out


def build_nv_section(notes: list[str], line_keys: list[str], play_lines: list[str]) -> str:
    if not notes:
        return "No historical commentary found for the selected text in the database."
    chunks = []
    for i, note in enumerate(notes):
        line_label = line_keys[i] if i < len(line_keys) else line_keys[-1]
        play_line = play_lines[i] if i < len(play_lines) else play_lines[0]
        chunks.append(f"[Line {line_label}] {play_line}\n{note}")
    return "\n\n".join(chunks)


CITATION_PATTERNS = [
    re.compile(r"\((Onions,\s*A Shakespeare Glossary,\s*1911(?:/1919)?)\)", re.I),
    re.compile(r"\((Schmidt,\s*Shakespeare-Lexicon,\s*1902)\)", re.I),
    re.compile(r"\((Cawdrey,\s*A Table Alphabeticall,\s*1604)\)", re.I),
    re.compile(r"\((Bullokar,\s*An English Expositor,\s*1616)\)", re.I),
    re.compile(r"\((Cockeram,\s*The English Dictionarie,\s*1623)\)", re.I),
    re.compile(r"\((Florio,\s*A Worlde of Wordes,\s*1598)\)", re.I),
    re.compile(r"\((Cotgrave,\s*A Dictionarie of the French and English Tongues,\s*1611)\)", re.I),
    re.compile(r"\((Geneva Bible,\s*1599)\)", re.I),
    re.compile(r"\(([^)]*\b(?:Holinshed|Plutarch|North|Ovid|Seneca|Montaigne|Bible|Geneva|Chronicles)[^)]*\d{3,4}[^)]*)\)", re.I),
    re.compile(r"\b([A-Z][A-Za-z .'-]{2,40})\s*\(\s*(1[5-9]\d{2}|20\d{2})\s*\)", re.M),
    re.compile(r"\b([A-Z][A-Z .'-]{2,30}):\]", re.M),
]


def extract_citations(section: str, section_name: str, sample_id: str) -> list[dict]:
    rows = []
    seen = set()
    for pat in CITATION_PATTERNS:
        for m in pat.finditer(section):
            cite = m.group(1).strip() if m.lastindex else m.group(0).strip()
            key = (section_name, cite.lower())
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "sample_id": sample_id,
                "section": section_name,
                "citation_text": cite,
                "context_snippet": section[max(0, m.start() - 80) : m.end() + 80].replace("\n", " "),
            })
    return rows


def grounding_text_blob(g: GroundingBundle) -> str:
    parts = [g.onions_block, g.schmidt_block, g.leme_block, g.geneva_block]
    parts.extend(g.variorum_notes)
    return "\n".join(parts).lower()


def classify_citation(row: dict, grounding: GroundingBundle, section: str) -> dict:
    cite = row["citation_text"]
    cite_low = cite.lower()
    blob = grounding_text_blob(grounding)

    # NV section after server overwrite: citations are from injected notes
    if section == NV_SECTION:
        for note in grounding.variorum_notes:
            note_str = str(note)
            if cite in note_str or cite_low in note_str.lower():
                return {**row, "classification": "verifiable_correct", "verification_basis": "variorum_injected_note"}
            # critic bracket tags
            if re.search(re.escape(cite.split(":")[0][:20]), note_str, re.I):
                return {**row, "classification": "verifiable_correct", "verification_basis": "variorum_injected_note"}
        if grounding.variorum_notes:
            return {**row, "classification": "real_source_wrong_details", "verification_basis": "nv_section_not_in_injected_notes"}
        return {**row, "classification": "verifiable_correct", "verification_basis": "nv_empty_placeholder"}

    source_family = None
    for needle, fam in KNOWN_LEXICAL.items():
        if needle in cite_low:
            source_family = fam
            break

    if source_family == "onions":
        if grounding.onions_hits:
            return {**row, "classification": "verifiable_correct", "verification_basis": "onions_retrieved"}
        if "not in retrieved" in row.get("context_snippet", "").lower():
            return {**row, "classification": "verifiable_correct", "verification_basis": "explicit_miss_statement"}
        return {**row, "classification": "real_source_wrong_details", "verification_basis": "onions_cited_without_retrieval"}

    if source_family == "schmidt":
        if grounding.schmidt_hits:
            return {**row, "classification": "verifiable_correct", "verification_basis": "schmidt_retrieved"}
        return {**row, "classification": "real_source_wrong_details", "verification_basis": "schmidt_cited_without_retrieval"}

    if source_family == "leme":
        if grounding.leme_hits:
            return {**row, "classification": "verifiable_correct", "verification_basis": "leme_retrieved"}
        return {**row, "classification": "real_source_wrong_details", "verification_basis": "leme_cited_without_retrieval"}

    if source_family == "geneva":
        if grounding.geneva_hits:
            return {**row, "classification": "verifiable_correct", "verification_basis": "geneva_retrieved"}
        return {**row, "classification": "unverifiable_needs_human_review", "verification_basis": "geneva_cited_no_retrieval"}

    if any(h in cite_low for h in KNOWN_HISTORICAL):
        if cite_low in blob or any(h in blob for h in KNOWN_HISTORICAL if h in cite_low):
            return {**row, "classification": "verifiable_correct", "verification_basis": "historical_source_in_grounding_or_notes"}
        return {**row, "classification": "unverifiable_needs_human_review", "verification_basis": "historical_source_not_in_retrieved_layer"}

    # Named critic with year — forbidden in Literary Analysis; check variorum notes
    if section == "Literary Analysis" and re.search(r"[A-Z][a-z]+", cite):
        return {**row, "classification": "fabricated", "verification_basis": "named_critic_in_forbidden_section"}

    if cite_low in blob:
        return {**row, "classification": "verifiable_correct", "verification_basis": "substring_in_grounding_blob"}

    # NV-style critic tags in model sections
    if ":]" in cite or cite.isupper():
        for note in grounding.variorum_notes:
            if cite.split(":")[0] in str(note):
                return {**row, "classification": "verifiable_correct", "verification_basis": "critic_tag_in_variorum_notes"}
        return {**row, "classification": "unverifiable_needs_human_review", "verification_basis": "critic_tag_not_in_variorum"}

    return {**row, "classification": "unverifiable_needs_human_review", "verification_basis": "not_grounded_in_retrieved_layer"}


def rate_table(rows: list[dict]) -> dict:
    def tally(subset):
        counts = {
            "verifiable_correct": 0,
            "real_source_wrong_details": 0,
            "fabricated": 0,
            "unverifiable_needs_human_review": 0,
        }
        for r in subset:
            counts[r["classification"]] += 1
        total = len(subset)
        rates = {k: round(100 * v / total, 2) if total else 0.0 for k, v in counts.items()}
        return {"n": total, "counts": counts, "rates_pct": rates}

    model_rows = [r for r in rows if r["section"] != NV_SECTION]
    nv_rows = [r for r in rows if r["section"] == NV_SECTION]
    return {
        "overall": tally(rows),
        "model_generated_sections": tally(model_rows),
        "new_variorum_analysis_section": tally(nv_rows),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def write_md(table: dict, meta: dict) -> str:
    if meta.get("passages_per_play"):
        per_play_line = str(meta["passages_per_play"])
    else:
        target = meta.get("total_passages_target", meta["total_passages"])
        per_play_line = f"{target} total ({meta['total_passages']} sampled)"
    lines = [
        "# Full Fathom Five Citation Accuracy Audit",
        "",
        f"- Plays (N): **{meta['n_plays']}**",
        f"- Profile: **{meta['profile']}**",
        f"- NV corpus plays: **{meta.get('nv_plays', '—')}** (NV section injected: **{meta.get('nv_injected_plays', '—')}**)",
        f"- Contrast (non-NV) plays: **{meta.get('contrast_plays', 0)}**",
        f"- Passages per play: **{per_play_line}**",
        f"- Total passages: **{meta['total_passages']}**",
        f"- Model: **{meta['model']}**",
        f"- Generated: {table['generated_at']}",
        "",
        "## Method",
        "",
        "Stratified sample (soliloquy, dialogue, stage direction, textually contested) × N plays.",
        "Analyses generated with the same Full Fathom Five prompt and retrieved-source grounding",
        "(Onions, Schmidt, LEME, Geneva) as `functions/shakespeare.js`. New Variorum Analysis",
        "is server-overwritten from local play JSON before citation extraction.",
        "",
        "Classifications: `verifiable_correct`, `real_source_wrong_details`, `fabricated`,",
        "`unverifiable_needs_human_review`. Rates are sample estimates, not a corpus census.",
        "",
        "## Rate table",
        "",
        "| Scope | n | Correct % | Wrong details % | Fabricated % | Unverifiable % |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for label, key in [
        ("Overall", "overall"),
        ("Model-generated sections", "model_generated_sections"),
        ("New Variorum Analysis (injected)", "new_variorum_analysis_section"),
    ]:
        t = table[key]
        r = t["rates_pct"]
        lines.append(
            f"| {label} | {t['n']} | {r['verifiable_correct']} | {r['real_source_wrong_details']} | "
            f"{r['fabricated']} | {r['unverifiable_needs_human_review']} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--profile",
        choices=("full", "expanded", "compact"),
        default="expanded",
        help="expanded=22 NV + 5 contrast (default, 135 passages); full=22 NV; compact=8-play pilot",
    )
    ap.add_argument("--per-play", type=int, default=5)
    ap.add_argument("--limit", type=int, help="Override per-play count")
    ap.add_argument(
        "--total-passages",
        type=int,
        help="Cap total passages across all plays (split evenly; overrides --per-play/--limit)",
    )
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resume", action="store_true", help="Skip passages already in sample_raw_outputs.json")
    ap.add_argument("--classify-only", action="store_true", help="Re-classify from existing raw outputs")
    ap.add_argument(
        "--classify-layers",
        nargs="*",
        choices=AUDIT_LAYERS,
        metavar="LAYER",
        help="Write per-layer audits (nv, onions, schmidt) from existing raw outputs; default: all three",
    )
    ap.add_argument("--model", default="gpt-4o")
    args = ap.parse_args()

    per_play = args.limit or args.per_play
    OUT.mkdir(parents=True, exist_ok=True)

    play_manifest = get_play_manifest(args.profile)
    sample = build_sample(
        play_manifest,
        per_play=per_play,
        total_passages=args.total_passages,
    )
    manifest_path = OUT / "sample_manifest.json"
    manifest_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile": args.profile,
        "per_play": per_play if not args.total_passages else None,
        "total_passages_target": args.total_passages,
        "n_plays": len(play_manifest),
        "total_passages": len(sample),
        "passages": sample,
    }
    manifest_path.write_text(json.dumps(manifest_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.total_passages:
        counts = per_play_counts(len(play_manifest), args.total_passages)
        per_play_desc = f"{args.total_passages} total ({min(counts)}–{max(counts)} per play)"
    else:
        per_play_desc = f"{len(play_manifest)} plays × {per_play}"
    print(f"Wrote {manifest_path} ({len(sample)} passages, {per_play_desc}, profile={args.profile})")

    meta = {
        "profile": args.profile,
        "n_plays": len(play_manifest),
        "passages_per_play": per_play if not args.total_passages else None,
        "total_passages_target": args.total_passages,
        "total_passages": len(sample),
        "nv_plays": sum(1 for p in play_manifest if p.get("corpus") == "nv_22"),
        "nv_injected_plays": sum(1 for p in play_manifest if p["has_nv"]),
        "contrast_plays": sum(1 for p in play_manifest if p.get("corpus") == "contrast_non_nv"),
        "model": args.model,
    }

    raw_path = OUT / "sample_raw_outputs.json"

    if args.classify_layers is not None or args.classify_only:
        raw_outputs = load_existing_outputs(raw_path)
        if not raw_outputs:
            print(f"No raw outputs at {raw_path}", file=sys.stderr)
            return 1
        if manifest_path.is_file():
            saved = json.loads(manifest_path.read_text(encoding="utf-8"))
            meta.update({
                "profile": saved.get("profile", meta["profile"]),
                "n_plays": saved.get("n_plays", meta["n_plays"]),
                "total_passages": saved.get("total_passages", len(raw_outputs)),
                "total_passages_target": saved.get("total_passages_target"),
                "passages_per_play": saved.get("per_play"),
            })
        meta["total_passages"] = len(raw_outputs)
        if args.classify_only:
            write_audit_outputs(raw_outputs, meta, args.model)
        layers = tuple(args.classify_layers) if args.classify_layers else AUDIT_LAYERS
        write_all_layer_audits(raw_outputs, meta, layers)
        return 0

    if args.dry_run:
        print("Dry run — sample only.")
        return 0

    load_dotenv()
    raw_outputs = load_existing_outputs(raw_path) if args.resume else []
    done_ids = {r["sample_id"] for r in raw_outputs}

    for i, item in enumerate(sample, 1):
        if item["sample_id"] in done_ids:
            print(f"[{i}/{len(sample)}] {item['sample_id']} — skipped (resume)")
            continue
        print(f"[{i}/{len(sample)}] {item['sample_id']} …")
        notes = [str(n) for n in (item.get("notes") or [])]
        grounding = build_grounding(item["text"], notes)
        include_nv = item["has_nv"] and item["play_name"] not in PLAYS_WITHOUT_NV
        system_prompt = build_system_prompt(item["play_name"], include_nv)
        user_prompt = build_user_prompt(item["text"], grounding)

        try:
            api_resp = call_openai(system_prompt, user_prompt, model=args.model)
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="replace")
            print(f"OpenAI error: {e.code} {err[:300]}", file=sys.stderr)
            return 1
        except RuntimeError as e:
            print(str(e), file=sys.stderr)
            return 1

        content = api_resp["choices"][0]["message"]["content"]
        sections = parse_sections(content, include_nv)

        if include_nv:
            sections[NV_SECTION] = build_nv_section(
                notes,
                item.get("line_keys") or [],
                item["text"].split("\n"),
            )

        record = {
            **item,
            "model": args.model,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "raw_model_output": content,
            "analysis_sections": sections,
            "grounding_summary": {
                "onions_hits": len(grounding.onions_hits),
                "schmidt_hits": len(grounding.schmidt_hits),
                "leme_hits": len(grounding.leme_hits),
                "geneva_hits": len(grounding.geneva_hits),
                "variorum_notes": len(grounding.variorum_notes),
            },
            "usage": api_resp.get("usage"),
        }
        raw_outputs.append(record)
        raw_path.write_text(json.dumps(raw_outputs, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        time.sleep(0.5)

    write_audit_outputs(raw_outputs, meta, args.model)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
