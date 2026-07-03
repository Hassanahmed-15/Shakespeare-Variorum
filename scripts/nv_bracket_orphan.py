"""Recover missing [lemma] prefix for NV notes that start with ]."""

from __future__ import annotations

import re

from audit_nv_truncation import ends_nv_terminal, ends_terminal
from nv_ia_witness import fold_apostrophe


def norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def is_bracket_orphan(note: str) -> bool:
    n = note.strip()
    if not n.startswith("]"):
        return False
    tail = n.rstrip()
    return ends_terminal(tail) or ends_nv_terminal(tail)


def recover_lemma_from_ia(ia: str, note: str) -> str | None:
    """Anchor note body in IA and prepend the missing [lemma] bracket."""
    if not is_bracket_orphan(note):
        return None

    body = note.strip()[1:].strip()
    body = re.sub(r"^\d{1,3}\.\s*", "", body)
    if len(body) < 25:
        return None

    folded_ia = fold_apostrophe(ia)
    pos = -1
    for size in (120, 100, 80, 60, 45, 30):
        if len(body) < size:
            continue
        snippet = fold_apostrophe(body[:size])
        idx = folded_ia.find(snippet)
        if idx >= 0:
            pos = idx
            break
    if pos < 0:
        words = re.findall(r"[A-Za-z0-9']+", fold_apostrophe(body[:80]))
        if len(words) >= 5:
            pat = re.compile(r"\s+".join(re.escape(w) for w in words[:8]), re.I)
            m = pat.search(folded_ia)
            if m:
                pos = m.start()
    if pos >= 0:
        back = ia[max(0, pos - 250) : pos]
        lm = re.search(r"(\d{1,3}\.\s*)?[^\[\]\n]{1,100}\]\s*$", back)
        if not lm:
            lm = re.search(r"(\d{1,3}\.\s*)?[^\[\]\n]{1,100}\]\s*$", back.rstrip())
        if lm:
            lemma = lm.group(0).strip()
            if not lemma.startswith("["):
                lemma = "[" + lemma
            if lemma.endswith("]"):
                fixed = norm_space(lemma + " " + body)
                if fixed != note.strip() and fixed.startswith("["):
                    return fixed

    return fallback_bracket_orphan(note)


def fallback_bracket_orphan(note: str) -> str | None:
    """When IA lacks modern-editor layers, replace the stray leading ] with [."""
    n = note.strip()
    if not n.startswith("]"):
        return None
    rest = n[1:].lstrip()
    if not rest:
        return None
    # Editor/cross-ref commentary without recoverable line-number lemma in witness.
    if re.match(
        r"(?:See\s+[IVXLC\d]+|[A-Z][A-Za-z .'-]{1,40}\s*\(|According to|On the )",
        rest,
    ):
        fixed = norm_space("[" + rest)
        return fixed if fixed != n else None
    return None
