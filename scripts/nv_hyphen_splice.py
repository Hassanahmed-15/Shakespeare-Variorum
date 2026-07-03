"""Shared hyphen line-break and page-break splice for NV note repair scripts."""

from __future__ import annotations

import re

from nv_ia_witness import fold_apostrophe

DEFAULT_NEXT_NOTE = re.compile(
    r"\n\s*\d{1,3}\.\s+[\w .'\-\u2019]+\]\s*[A-Z(\[]|\n\s*ACT\s+[IVXLC]",
    re.I,
)
PAGE_BREAK = re.compile(r"\s+\d{1,3}\s+(?=[a-z])", re.I)


def norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _apply_lemma(note: str, new: str) -> str:
    if "]" not in note:
        return norm_space(new)
    lemma = note[: note.index("]") + 1]
    if new.startswith(lemma):
        body = new[len(lemma) :].strip()
    elif "]" in new:
        body = new[new.index("]") + 1 :].strip()
    else:
        body = new
    return norm_space(lemma + " " + body)


def _continuation(
    tail: str,
    *,
    next_note_pat: re.Pattern[str] | None,
    cont_limit: int,
) -> str:
    pat = next_note_pat or DEFAULT_NEXT_NOTE
    endm = pat.search(tail)
    cont = tail[: endm.start()] if endm else tail[:cont_limit]
    return norm_space(cont)


def splice_hyphen(
    ia: str,
    note: str,
    *,
    next_note_pat: re.Pattern[str] | None = None,
    search_window: int = 6000,
    cont_limit: int = 2500,
) -> str | None:
    """Rejoin a note truncated at a line-break hyphen using IA witness text."""
    n = note.rstrip()
    if not re.search(r"-\s*$", n):
        return None

    ctx = re.sub(r"-\s*$", "", n).rstrip()
    fia = fold_apostrophe(ia)

    for size in (120, 100, 80, 60, 45, 30):
        if len(ctx) < size:
            continue
        snippet = fold_apostrophe(ctx[-size:])
        idx = fia.find(snippet)
        if idx < 0:
            continue
        pos = idx + len(snippet)
        rest = ia[pos : pos + search_window]
        hm = re.match(r"-\s*(\w+)", rest)
        if not hm:
            continue
        cont = _continuation(rest[hm.end() :], next_note_pat=next_note_pat, cont_limit=cont_limit)
        new = norm_space(ctx + hm.group(1) + " " + cont)
        new = _apply_lemma(note, new)
        if len(new) > len(note) + 5:
            return new
    return None


def splice_page_break(
    ia: str,
    note: str,
    *,
    next_note_pat: re.Pattern[str] | None = None,
    search_window: int = 6000,
    cont_limit: int = 2500,
) -> str | None:
    """Stitch continuation across page-break numerals or soft wraps (no trailing hyphen)."""
    n = note.rstrip()
    if re.search(r"-\s*$", n):
        return None
    fia = fold_apostrophe(ia)

    for size in (140, 120, 100, 80, 60, 45):
        if len(n) < size:
            continue
        snippet = fold_apostrophe(n[-size:])
        idx = fia.find(snippet)
        if idx < 0:
            continue
        pos = idx + len(snippet)
        rest = ia[pos : pos + search_window]
        # Skip page number + optional whitespace before lowercase continuation.
        pm = re.match(r"\s*\d{1,3}\s*", rest)
        if pm:
            rest = rest[pm.end() :]
        elif not re.match(r"[a-z(\[\u2018\"']", rest.lstrip()):
            continue
        cont = _continuation(rest, next_note_pat=next_note_pat, cont_limit=cont_limit)
        if len(cont) < 8:
            continue
        new = norm_space(n + " " + cont)
        new = _apply_lemma(note, new)
        if len(new) > len(note) + 12:
            return new

    # Mid-word page break: "personifica 113 tion"
    body = n[n.index("]") + 1 :].strip() if "]" in n else n
    words = re.findall(r"[A-Za-z0-9']+", fold_apostrophe(body))
    if len(words) >= 3:
        tail = " ".join(words[-4:])
        idx = fia.find(fold_apostrophe(tail))
        if idx >= 0:
            pos = idx + len(fold_apostrophe(tail))
            rest = ia[pos : pos + search_window]
            pm = re.match(r"\s*\d{1,3}\s+([a-z]{2,})", rest)
            if pm:
                cont = _continuation(
                    rest[pm.end() - len(pm.group(1)) :],
                    next_note_pat=next_note_pat,
                    cont_limit=cont_limit,
                )
                new = norm_space(n + pm.group(1) + " " + cont)
                new = _apply_lemma(note, new)
                if len(new) > len(note) + 12:
                    return new
    return None
