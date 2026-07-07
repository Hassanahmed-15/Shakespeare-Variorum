"""Shared NV note repair library — anchor, extract, deinterleave, accept/reject."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from audit_nv_truncation import (
    ends_nv_terminal,
    is_clipped,
    is_hard_truncation,
    is_hyphen_artifact,
    is_mid_sentence_cut,
    is_unbalanced_parens,
    is_witness_prefix,
)
from nv_hyphen_splice import splice_hyphen, splice_page_break
from nv_ia_witness import fold_apostrophe

# --- text normalization -------------------------------------------------------

RESUME = re.compile(
    r"(it must be|nausea|[a-z]{4,}[\u2018\u2019',])|(?:\u2014|—)\s*\[|(?:\u2014|—)\s*$",
    re.I,
)

PLAY_BLOCK_H4P2 = re.compile(
    r"ACT\s+[IVXLC\d]+\s*,\s*sc\.?\s*\d+\.?\]?\s*(?:HENRY\s+THE\s+FOURTH)?\s*\d*\s*",
    re.I,
)
PAGE_HDR_H4P2 = re.compile(r"HENRY\s+THE\s+FOURTH\s+\d{1,3}\s+", re.I)

ENTRY_BOUNDARY = re.compile(r"\d+\.\s+[^\]]+\]")
UNNUMBERED_LEMMA = re.compile(r"(?<=\])\s*([A-Za-z][\w .'\-]{1,60}\])")
PAGE_NUM_TAIL = re.compile(r"(?:\s+\d{1,3}\s*|\s+ACT\s+[IVXLC\d]+.*)$", re.I)
NEXT_ENTRY = re.compile(r"\s+\d+\.\s+[\w .'\-\u2019]+\]\s", re.I)


def norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def collapse(s: str) -> str:
    return re.sub(r"\s+", "", fold_apostrophe(s).lower())


def collapsed_pos(ia: str, idx: int) -> int:
    ci = 0
    for i, ch in enumerate(fold_apostrophe(ia).lower()):
        if not ch.isspace():
            if ci == idx:
                return i
            ci += 1
    return -1


def flex_pattern(text: str, max_words: int = 14) -> re.Pattern[str] | None:
    words = re.findall(r"[A-Za-z0-9\u2019']+", fold_apostrophe(text))
    if len(words) < 4:
        return None
    words = words[:max_words]
    return re.compile(r"\s+".join(re.escape(w) for w in words), re.I)


# --- deinterleave (default + play hooks) --------------------------------------

Deinterleaver = Callable[[str], str]

# Generic page-furniture skipper, run before any play-specific deinterleaver.
#
# NV apparatus pages interleave a footnote's true continuation with running
# headers, bare page numbers, the next footnote's bracketed lemma marker, and
# reproduced play-text/verse lines (which carry trailing line numbers). These
# blocks are visually separated by blank lines in the OCR text. This walks
# blank-line-delimited blocks and drops any block matching one of those
# "page furniture" shapes, keeping the first block (already-anchored text)
# and any block that reads as continuing scholarly prose.
_ACT_SC_MARK = re.compile(r"\bACT\b|\bSC\.?\s*[IVXLC\d]|\bDRAMATIS\b", re.I)
_LEMMA_MARKER = re.compile(r"^\s*\[?[o0-9]{1,4}[a-z]?\.\s*[^\]\n]{1,60}\]", re.I)
_BRACKET_LEMMA = re.compile(r"^\s*\[[^\]\n]{1,80}\]")
_VERSE_LINE_NUM = re.compile(r"\s\d{1,4}\s*$")


def _looks_like_running_header(block: str) -> bool:
    """Short page-furniture line: a running head, page number, or scene tag.

    OCR renders these in wildly different forms across plays/pages (word
    order, spacing, garbled letters), so rather than enumerate every exact
    wording this uses shape: short, and either carries an ACT/SC/DRAMATIS
    marker or is mostly capitalized words (title-case running heads).
    """
    b = block.strip()
    if not b or len(b) > 55:
        return False
    if re.fullmatch(r"\d{1,4}", b):
        return True
    if _ACT_SC_MARK.search(b):
        return True
    words = re.findall(r"[A-Za-z]+", b)
    if not words:
        return True
    cap_words = sum(1 for w in words if w.isupper() or w[0].isupper())
    return cap_words / len(words) >= 0.6


def _is_page_furniture(block: str) -> bool:
    b = block.strip()
    if not b:
        return True
    if _looks_like_running_header(b):
        return True
    if _BRACKET_LEMMA.match(b) and len(b) < 90:
        return True
    if _VERSE_LINE_NUM.search(b) and len(b) < 120 and not re.search(r"[.!?]\s*$", b):
        return True
    return False


def _strip_leading_lemma(block: str) -> str:
    """Drop a leading lemma marker (e.g. '[94. word]' or '94. word]') from a
    block, keeping any real prose that follows it on the same block.

    A short textual-variants entry (e.g. '61. intend] intended Rowe ii.') is
    a complete apparatus item in its own right, not a lemma introducing more
    prose -- drop the whole block in that case rather than exposing its
    trailing fragment as if it continued the current note.
    """
    m = _LEMMA_MARKER.match(block)
    if not m:
        return block
    rest = block[m.end() :].lstrip()
    if len(rest) < 60:
        return ""
    return rest


def skip_page_furniture(text: str) -> str:
    blocks = re.split(r"\n\s*\n+", text)
    out_blocks: list[str] = []
    for blk in blocks:
        if not blk.strip():
            continue
        candidate = _strip_leading_lemma(blk)
        if _is_page_furniture(candidate):
            continue
        out_blocks.append(candidate)
    if not out_blocks:
        return text
    return "\n\n".join(out_blocks)


def deinterleave_default(text: str) -> str:
    text = skip_page_furniture(text)
    text = PLAY_BLOCK_H4P2.sub(" ||| ", text)
    text = PAGE_HDR_H4P2.sub(" ||| ", text)
    parts = [p.strip() for p in text.split("|||") if p.strip()]
    if not parts:
        return norm_space(text)
    out = parts[0]
    for part in parts[1:]:
        if len(re.findall(r"\b[A-Z][a-z]+\b", part)) > 8 and len(part) > 120:
            m = RESUME.search(part)
            if m:
                out += " " + part[m.start() :]
        else:
            out += " " + part
    return norm_space(out)


# Coriolanus
_COR_PLAY = re.compile(r"ACT\s+[IVXLC\d]+\s*,\s*sc\.?\s*[ivxlc\d]+\.?\]?\s*", re.I)
_COR_HDR = re.compile(r"CORIOLANUS\s+\d{1,3}\s+", re.I)
_COR_SCENE = re.compile(r"\[ACT\s+[IVXLC\d]+,\s*sc\.\s*[ivxlc\d]+\.", re.I)
_COR_PAGE = re.compile(r"^\s*\d{1,3}\s*$")
_COR_SPEAKER = re.compile(r"^[A-Za-z]{2,5}[,.]\s+[A-Z\u017f]", re.M)
_COR_RESUME = re.compile(
    r"(?:^|\s)(?:to|of|the|and|that|which|many|it must be|nausea|"
    r"[a-z]{4,}[\u2018\u2019',])|(?:\u2014|—)\s*\[|(?:\u2014|—)\s*$",
    re.I,
)


def deinterleave_cor(text: str) -> str:
    text = skip_page_furniture(text)
    text = _COR_PLAY.sub(" ||| ", text)
    text = _COR_HDR.sub(" ||| ", text)
    text = _COR_SCENE.sub(" ||| ", text)
    parts = [p.strip() for p in text.split("|||") if p.strip()]
    if not parts:
        return norm_space(text)
    out = parts[0]
    for part in parts[1:]:
        lines = [ln.strip() for ln in part.splitlines() if ln.strip()]
        if lines and all(_COR_PAGE.match(ln) for ln in lines):
            continue
        if len(part) < 100 and _COR_SPEAKER.search(part):
            continue
        if len(re.findall(r"\b[A-Z][a-z]+\b", part)) > 10 and len(part) > 150:
            m = _COR_RESUME.search(part)
            if m:
                out += " " + part[m.start() :]
                continue
        if part and (
            part[0].islower()
            or part.lstrip().startswith(("to ", "of ", "the ", "and ", "that ", "which "))
        ):
            out += " " + part
        elif re.search(r"[A-Za-z .'-]+:\s", part) or "—" in part or "Ed." in part:
            out += " " + part
    return norm_space(text) if not out else norm_space(out)


# King John
_KJ_HDR = re.compile(
    r"(?:ACT\s+[IVXLC\d]+\s*,\s*sc\.?\s*\d+\.?\]?\s*)?"
    r"(?:OF\s+)?KING\s+JOHN\s+\d{1,3}\s+",
    re.I,
)


def deinterleave_kj(text: str) -> str:
    text = skip_page_furniture(text)
    text = _KJ_HDR.sub(" ||| ", text)
    parts = [p.strip() for p in text.split("|||") if p.strip()]
    if not parts:
        return norm_space(text)
    out = parts[0]
    for part in parts[1:]:
        if len(re.findall(r"\b[A-Z][a-z]+\b", part)) > 8 and len(part) > 120:
            m = RESUME.search(part)
            if m:
                out += " " + part[m.start() :]
        else:
            out += " " + part
    return norm_space(out)


# Antony
_ANT_ACT = re.compile(r"Act\s+[IVXLC\d]+\s*,?\s*(?:sc\.?\s*\d+\.?)?\s*\]?\s*", re.I)
_ANT_LINE = re.compile(r"\n\s*\d{1,3}\.\s+[A-Za-z\u2018\u2019\"'\(\[]", re.I)


def deinterleave_antony(text: str) -> str:
    text = skip_page_furniture(text)
    text = _ANT_ACT.sub(" ||| ", text)
    text = _ANT_LINE.sub(lambda m: " ||| " + m.group(0).lstrip(), text)
    parts = [p.strip() for p in text.split("|||") if p.strip()]
    if not parts:
        return norm_space(text)
    out = parts[0]
    for part in parts[1:]:
        if len(part) > 120 and len(re.findall(r"\b[A-Z][a-z]+\b", part)) > 8:
            m = RESUME.search(part)
            out += " " + (part[m.start() :] if m else part)
        else:
            out += " " + part
    return norm_space(out)


# Cymbeline
_CYMB_PLAY = re.compile(r"ACT\s+[IVXLC\d]+\s*,\s*SC\.?\s*[IVXLC\divxlc]+\.?\]?\s*", re.I)
_CYMB_HDR = re.compile(r"(?:THE\s+TRAGED(?:IE|ILZ|Y)\s+OF|CYMBELINE)\s*(?:\[ACT|\d{1,3})", re.I)
_CYMB_SCENE = re.compile(r"\[ACT\s+[^\]]+\]", re.I)
_CYMB_PAGE = re.compile(r"^\s*\d{1,3}\s*$")
_CYMB_RESUME = re.compile(
    r"(?:^|\s)(?:to|of|the|and|many|in|on|at|his|her|this|that|"
    r"[a-z]{4,}[\u2018\u2019',])|(?:\u2014|—)\s*\[|(?:\u2014|—)\s*$",
    re.I,
)


def deinterleave_cymb(text: str) -> str:
    text = skip_page_furniture(text)
    text = _CYMB_PLAY.sub(" ||| ", text)
    text = _CYMB_HDR.sub(" ||| ", text)
    text = _CYMB_SCENE.sub(" ||| ", text)
    parts = [p.strip() for p in text.split("|||") if p.strip()]
    if not parts:
        return norm_space(text)
    out = parts[0]
    for part in parts[1:]:
        lines = [ln.strip() for ln in part.splitlines() if ln.strip()]
        if lines and all(_CYMB_PAGE.match(ln) for ln in lines):
            continue
        if len(re.findall(r"\b[A-Z][a-z]+\b", part)) > 10 and len(part) > 150:
            m = _CYMB_RESUME.search(part)
            if m:
                out += " " + part[m.start() :]
                continue
        if part and (part[0].islower() or part.lstrip().startswith(("to ", "of ", "the ", "and "))):
            out += " " + part
        elif re.search(r"[A-Za-z .'-]+:\s", part) or "—" in part or "Ed." in part:
            out += " " + part
    return norm_space(out)


# Julius Caesar
_JC_PLAY = re.compile(r"ACT\s+[IVXLC\d]+\s*,\s*sc\.?\s*\d+\.?\]?\s*", re.I)
_JC_HDR = re.compile(r"(?:THE\s+TRAGED(?:IE|Y)\s+OF\s+)?(?:JULIUS\s+)?CAESAR\s+\d{1,3}\s+", re.I)


def deinterleave_jc(text: str) -> str:
    text = skip_page_furniture(text)
    text = _JC_PLAY.sub(" ||| ", text)
    text = _JC_HDR.sub(" ||| ", text)
    parts = [p.strip() for p in text.split("|||") if p.strip()]
    if not parts:
        return norm_space(text)
    out = parts[0]
    for part in parts[1:]:
        if len(re.findall(r"\b[A-Z][a-z]+\b", part)) > 8 and len(part) > 120:
            m = RESUME.search(part)
            if m:
                out += " " + part[m.start() :]
        else:
            out += " " + part
    return norm_space(out)


# Love's Labour's Lost
_LLL_PLAY = re.compile(r"ACT\s+[IVXLC\d]+\s*,\s*SC\.?\s*[IVXLC\d]*\.?\]?\s*", re.I)
_LLL_HDR = re.compile(r"LOU?ES\s+LAB(?:OU|OR)U?R'?S?\s+LOST", re.I)
_LLL_SCENE = re.compile(r"\[act\s+[IVXLC\d]+,\s*sc\.\s*[ivxlc\d]+\.", re.I)


def deinterleave_lll(text: str) -> str:
    text = skip_page_furniture(text)
    text = _LLL_PLAY.sub(" ||| ", text)
    text = _LLL_HDR.sub(" ||| ", text)
    text = _LLL_SCENE.sub(" ||| ", text)
    parts = [p.strip() for p in text.split("|||") if p.strip()]
    if not parts:
        return norm_space(text)
    out = parts[0]
    for part in parts[1:]:
        if len(re.findall(r"\b[A-Z][a-z]+\b", part)) > 8 and len(part) > 120:
            m = RESUME.search(part)
            if m:
                out += " " + part[m.start() :]
        else:
            out += " " + part
    return norm_space(out)


# Macbeth
_MAC_PLAY = re.compile(
    r"(?:THE\s+TRAGEDIE\s+OF\s+MACBETH|MACBETH)"
    r"\s*\[?\s*act\s+[ivxlc\d]+[\s,]*sc\.?\s*[ivxlc\d]+[^\]]*\]?",
    re.I,
)
_MAC_HDR = re.compile(r"(?:THE\s+TRAGEDIE\s+OF\s+)?MACBETH\s+\d{1,3}\s+", re.I)


def deinterleave_mac(text: str) -> str:
    text = skip_page_furniture(text)
    text = _MAC_PLAY.sub(" ||| ", text)
    text = _MAC_HDR.sub(" ||| ", text)
    parts = [p.strip() for p in text.split("|||") if p.strip()]
    if not parts:
        return norm_space(text)
    out = parts[0]
    for part in parts[1:]:
        if len(re.findall(r"\b[A-Z][a-z]+\b", part)) > 8 and len(part) > 120:
            m = RESUME.search(part)
            if m:
                out += " " + part[m.start() :]
        else:
            out += " " + part
    return norm_space(out)


# The Merchant of Venice
_MOV_PLAY = re.compile(r"\[ACT\s+[IVXLC\d]+,\s*SC\.?\s*[ivxlc\d]+\.?\]?", re.I)
_MOV_HDR = re.compile(r"THE\s+MERCHANT\s+OF\s+VENICE\s*(?:\[ACT\s+[IVXLC\d]+,\s*SC\.?\s*[ivxlc\d]+\.?)?", re.I)


def deinterleave_mov(text: str) -> str:
    text = skip_page_furniture(text)
    text = _MOV_HDR.sub(" ||| ", text)
    text = _MOV_PLAY.sub(" ||| ", text)
    parts = [p.strip() for p in text.split("|||") if p.strip()]
    if not parts:
        return norm_space(text)
    out = parts[0]
    for part in parts[1:]:
        if len(re.findall(r"\b[A-Z][a-z]+\b", part)) > 8 and len(part) > 120:
            m = RESUME.search(part)
            if m:
                out += " " + part[m.start() :]
        else:
            out += " " + part
    return norm_space(out)


# Othello
_OTH_PLAY = re.compile(
    r"THE\s+TR\s*A?\s*C?G?E?D?\s*I?E?\s+OF\s+OTHELLO\s*\[act\s+[ivxlc\d]+,\s*sc\.?\s*[ivxlc\d]+\.?\]?",
    re.I,
)
_OTH_HDR = re.compile(r"THE\s+TR[A-Z]*\s+OF\s+OTHELLO\s+\[act\s+[ivxlc\d]+,?\s*sc\.?\s*[ivxlc\d]+\.?\]?", re.I)


def deinterleave_oth(text: str) -> str:
    text = skip_page_furniture(text)
    text = _OTH_HDR.sub(" ||| ", text)
    parts = [p.strip() for p in text.split("|||") if p.strip()]
    if not parts:
        return norm_space(text)
    out = parts[0]
    for part in parts[1:]:
        if len(re.findall(r"\b[A-Z][a-z]+\b", part)) > 8 and len(part) > 120:
            m = RESUME.search(part)
            if m:
                out += " " + part[m.start() :]
        else:
            out += " " + part
    return norm_space(out)


# Twelfth Night
_TN_PLAY_BLOCK = re.compile(
    r"\[?ACT\s+[IVXLC\d]+,?\s*\)?SC\.?\.?,?\s*[ivxlc\d]*\.?\]?",
    re.I,
)
_TN_PAGE_HDR = re.compile(r"(?:\d+\s+)?TWELFE\s+NIGHT\s+\[ACT\s+", re.I)


def deinterleave_tn(text: str) -> str:
    text = skip_page_furniture(text)
    text = _TN_PAGE_HDR.sub(" ||| ", text)
    text = _TN_PLAY_BLOCK.sub(" ||| ", text)
    parts = [p.strip() for p in text.split("|||") if p.strip()]
    if not parts:
        return norm_space(text)
    out = parts[0]
    for part in parts[1:]:
        if len(re.findall(r"\b[A-Z][a-z]+\b", part)) > 8 and len(part) > 120:
            m = RESUME.search(part)
            if m:
                out += " " + part[m.start() :]
        else:
            out += " " + part
    return norm_space(out)


# Romeo and Juliet
_ROM_HDR = re.compile(r"ROMEO\s+AND\s+JULIET\.?\s*\[act\s+[ivxlc\d]+,\s*sc\.?\s*[ivxlc\d]+\.?\]?", re.I)


def deinterleave_rom(text: str) -> str:
    text = skip_page_furniture(text)
    text = _ROM_HDR.sub(" ||| ", text)
    parts = [p.strip() for p in text.split("|||") if p.strip()]
    if not parts:
        return norm_space(text)
    out = parts[0]
    for part in parts[1:]:
        if len(re.findall(r"\b[A-Z][a-z]+\b", part)) > 8 and len(part) > 120:
            m = RESUME.search(part)
            if m:
                out += " " + part[m.start() :]
        else:
            out += " " + part
    return norm_space(out)


DEINTERLEAVERS: dict[str, Deinterleaver] = {
    "Henry IV, Part 2": deinterleave_default,
    "Coriolanus": deinterleave_cor,
    "King John": deinterleave_kj,
    "Antony and Cleopatra": deinterleave_antony,
    "Cymbeline": deinterleave_cymb,
    "Julius Caesar": deinterleave_jc,
    "Love's Labour's Lost": deinterleave_lll,
    "Macbeth": deinterleave_mac,
    "The Merchant of Venice": deinterleave_mov,
    "Othello": deinterleave_oth,
    "Twelfth Night": deinterleave_tn,
    "Romeo and Juliet": deinterleave_rom,
}


def get_deinterleaver(play: str | None) -> Deinterleaver:
    if play and play in DEINTERLEAVERS:
        return DEINTERLEAVERS[play]
    return deinterleave_default


# --- truncate / anchor / extract ----------------------------------------------

def truncate_footnote(text: str, min_len: int = 40) -> str:
    if len(text) <= min_len:
        return text.strip()
    for pat in (
        r"—\s*Ed\.\]",
        r"—\s*\[Ed\.\]",
        r"\[Ed\.\]\s*$",
        r"\.\s*—\s*Ed\.\]",
    ):
        m = re.search(pat, text)
        if m and m.end() > min_len:
            return text[: m.end()].strip()
    for m in re.finditer(r"—\s*$", text):
        if min_len < m.end() < 2800:
            return text[: m.end()].strip()
    for m in re.finditer(r"\.\s*—\s*(?=[A-Z\[\"'\u2018(]|$)", text):
        if min_len < m.end() < 2800:
            return text[: m.end()].strip()
    m = re.search(r"\s(\d{1,3})\.\s+(?:[A-Za-z(\[]|\w+\]|\w+\.)", text[min_len:])
    if m:
        return text[: min_len + m.start()].strip()
    nm = NEXT_ENTRY.search(text[min_len:])
    if nm:
        return text[: min_len + nm.start()].strip()
    if len(text) > 2800:
        cut = text[:2800]
        m = re.search(r"[.!?]\s*—?\s*$", cut)
        if m:
            return cut[: m.end()].strip()
    return text.strip()


def find_note_pos(ia: str, note: str, *, play: str | None = None) -> int:
    folded_ia = fold_apostrophe(ia)
    if "]" in note:
        lemma = note[: note.index("]") + 1]
        pat = flex_pattern(lemma.replace("]", " ]").replace("  ", " "), max_words=8)
        if pat is None:
            words = re.findall(r"[A-Za-z0-9\u2019']+", fold_apostrophe(lemma))
            if len(words) >= 2:
                pat = flex_pattern(" ".join(words[:6]), 6)
        if pat:
            m = pat.search(folded_ia)
            if m:
                return m.start()

    body = note[note.index("]") + 1 :].strip() if "]" in note else note.strip()
    body = re.sub(r"^\d{1,3}\.\s*", "", body)
    for size in (100, 80, 60, 45, 30):
        if len(body) < size:
            continue
        pat = flex_pattern(body[:size])
        if pat:
            m = pat.search(folded_ia)
            if m:
                return m.start()
    critic = re.match(r"^[A-Za-z .'.-]+:\s*(.{20,120})", body)
    if critic:
        pat = flex_pattern(critic.group(1)[:70])
        if pat:
            m = pat.search(folded_ia)
            if m:
                return m.start()
    words = re.findall(r"[A-Za-z0-9\u2019']+", fold_apostrophe(body))
    for n in (10, 8, 6):
        if len(words) >= n:
            pat = flex_pattern(" ".join(words[:n]), n)
            if pat:
                m = pat.search(folded_ia)
                if m:
                    return m.start()

    ia_c = collapse(ia)
    for size in (160, 120, 100, 80, 60, 45, 30):
        if len(note) < size:
            continue
        needle = collapse(note[:size])
        if len(needle) >= 25:
            idx = ia_c.find(needle)
            if idx >= 0:
                return collapsed_pos(ia, idx)

    for n in (12, 10, 8, 6):
        if len(words) >= n:
            tail = " ".join(words[-n:])
            pat = flex_pattern(tail, n)
            if pat:
                m = pat.search(folded_ia)
                if m:
                    return max(0, m.start() - 200)
    return -1


def extract_from_ia(
    ia: str,
    pos: int,
    json_note: str,
    *,
    play: str | None = None,
    chunk_size: int = 7000,
) -> str:
    deinterleave = get_deinterleaver(play)
    start = max(0, pos - 160)
    chunk = ia[start : start + chunk_size]
    rel = pos - start
    m = re.search(r"(\d{1,3}\.\s*)?[\w .'\"-]+\]\s*[A-Z(‘\"]", chunk[max(0, rel - 40) :], re.I)
    if m:
        chunk = chunk[max(0, rel - 40) + m.start() :]
    else:
        back = chunk[: rel + 20]
        lm = re.search(r"[\w .'\-]+\]", back[::-1])
        if lm:
            chunk = chunk[len(back) - lm.end() :]
    ext = truncate_footnote(deinterleave(chunk))
    if "]" in json_note:
        json_lemma = json_note[: json_note.index("]") + 1]
        em = re.match(r"^(\d{1,3}\.\s*)?[^\]]+\]\s*", ext)
        ext = json_lemma + (" " + ext[em.end() :].lstrip() if em else " " + ext)
    return norm_space(ext)


# --- acceptance / contamination -----------------------------------------------

def needs_extension(note: str) -> bool:
    """True when note should be considered for witness continuation repair."""
    n = note.strip()
    if not n:
        return False
    if n.startswith("]") and ends_nv_terminal(n):
        return False
    if ends_nv_terminal(n) and not is_hyphen_artifact(n):
        if not is_unbalanced_parens(n):
            return False
    return True


def looks_contaminated(note: str, *, play: str | None = None) -> bool:
    if re.search(r"ACT\s+[IVXLC\d]+\s*,\s*sc\.", note, re.I) and re.search(
        r"(?:HENRY\s+THE\s+FOURTH|KING\s+JOHN|CORIOLANUS)", note, re.I
    ):
        return True
    if play == "King John" and PAGE_NUM_TAIL.search(note.rstrip()):
        if re.search(r"\b(?:JOHNSON|STEEVENS|MALONE|WARBURTON)\b", note, re.I):
            pass
        elif re.search(r"\s+\d{1,3}\s*$", note):
            return True
    if play == "Antony and Cleopatra":
        if re.search(r"\b(?:Enob|Men)\.\s+[A-Z]", note, re.I):
            return True
        if re.search(r"\bANTHONY\s+AND\s+CLEOPATRA\s+\d", note, re.I):
            return True
    if play == "Coriolanus":
        if _COR_SPEAKER.search(note) and len(note) < 200:
            return True
        if re.search(r"(?:^|[.!?]\s+)(?:Cor|Men|Com)\.\s+[A-Z]", note):
            return True
    return False


def is_union_truncated(note: str, folded_ia: str | None = None) -> bool:
    if is_clipped(note):
        return True
    if is_hard_truncation(note):
        return True
    if is_mid_sentence_cut(note):
        return True
    if is_hyphen_artifact(note):
        return True
    if is_unbalanced_parens(note):
        return True
    if folded_ia is not None and is_witness_prefix(folded_ia, note):
        return True
    return False


def repair_acceptable(
    note: str,
    ext: str,
    folded_ia: str | None = None,
    *,
    play: str | None = None,
    min_gain: int = 8,
    require_fixed: bool = True,
) -> bool:
    if len(ext) <= len(note) + min_gain:
        return False
    if len(ext) > max(4000, len(note) * 8):
        return False
    if looks_contaminated(ext, play=play):
        return False
    if PAGE_NUM_TAIL.search(ext) and play == "King John":
        return False
    if require_fixed and folded_ia is not None:
        if is_union_truncated(ext, folded_ia):
            if not (is_clipped(note) and not is_clipped(ext)):
                if is_hard_truncation(ext) or is_mid_sentence_cut(ext):
                    return False
    elif require_fixed:
        if is_clipped(ext) and is_clipped(note):
            return False
        if is_hard_truncation(ext) and is_hard_truncation(note):
            return False
    return True


def try_hyphen_repair(
    ia: str,
    note: str,
    folded_ia: str | None = None,
    *,
    next_note_pat: re.Pattern[str] | None = None,
    play: str | None = None,
) -> str | None:
    if not is_hyphen_artifact(note):
        ext = splice_page_break(ia, note, next_note_pat=next_note_pat)
        if ext and repair_acceptable(note, ext, folded_ia, play=play, min_gain=5):
            return ext
        return None
    ext = splice_hyphen(ia, note, next_note_pat=next_note_pat)
    if ext and repair_acceptable(note, ext, folded_ia, play=play, min_gain=5):
        return ext
    ext = splice_page_break(ia, note, next_note_pat=next_note_pat)
    if ext and repair_acceptable(note, ext, folded_ia, play=play, min_gain=5):
        return ext
    return None


def try_witness_repair(
    ia: str,
    note: str,
    folded_ia: str | None = None,
    *,
    play: str | None = None,
    next_note_pat: re.Pattern[str] | None = None,
) -> str | None:
    if not needs_extension(note) and not is_union_truncated(note, folded_ia):
        return None
    ext = try_hyphen_repair(ia, note, folded_ia, next_note_pat=next_note_pat, play=play)
    if ext:
        return ext
    pos = find_note_pos(ia, note, play=play)
    if pos < 0:
        return None
    ext = extract_from_ia(ia, pos, note, play=play)
    if repair_acceptable(note, ext, folded_ia, play=play):
        return ext
    if len(ext) > len(note) + 8 and not is_clipped(ext) and not looks_contaminated(ext, play=play):
        if not is_hard_truncation(ext) and not is_mid_sentence_cut(ext):
            return ext
    return None


# --- mega-note splitter -------------------------------------------------------

def split_mega_note(note: str, *, min_brackets: int = 4) -> list[str]:
    """Split merged apparatus entries when note has min_brackets+ `]` markers."""
    if note.count("]") < min_brackets:
        return [note]

    splits: list[int] = []
    for m in ENTRY_BOUNDARY.finditer(note):
        pos = m.start()
        if pos < 8 and not note[:pos].strip():
            continue
        if note[:pos].count("]") >= 1:
            splits.append(pos)

    if len(splits) < 2:
        for m in UNNUMBERED_LEMMA.finditer(note):
            pos = m.start(1)
            seg = note[pos : m.end(1)]
            if re.match(r"^[A-Za-z][\w .'-]{1,60}\]$", seg) and pos > 40:
                if note[:pos].count("]") >= 1:
                    splits.append(pos)

    if not splits:
        return [note]

    splits = sorted(set(splits))
    segments: list[str] = []
    prev = 0
    for sp in splits:
        seg = norm_space(note[prev:sp])
        if seg and seg.count("]") >= 1:
            segments.append(seg)
        prev = sp
    tail = norm_space(note[prev:])
    if tail and tail.count("]") >= 1:
        segments.append(tail)

    if len(segments) <= 1:
        return [note]
    return segments


def split_mega_notes_in_data(
    data: dict,
    *,
    min_brackets: int = 4,
) -> dict[str, Any]:
    stats = {"mega_before": 0, "split_events": 0, "notes_added": 0, "examples": []}
    for scene, scene_data in data.items():
        if str(scene).startswith("_") or not isinstance(scene_data, dict):
            continue
        for line_key, line_data in scene_data.items():
            if not isinstance(line_data, dict):
                continue
            notes = line_data.get("notes") or []
            new_notes: list[str] = []
            changed = False
            for note in notes:
                if note.count("]") >= min_brackets:
                    stats["mega_before"] += 1
                    parts = split_mega_note(note, min_brackets=min_brackets)
                    if len(parts) > 1:
                        stats["split_events"] += 1
                        stats["notes_added"] += len(parts) - 1
                        changed = True
                        if len(stats["examples"]) < 5:
                            stats["examples"].append(
                                {"before_brackets": note.count("]"), "parts": len(parts), "head": parts[0][:80]}
                            )
                        new_notes.extend(parts)
                    else:
                        new_notes.append(note)
                else:
                    new_notes.append(note)
            if changed:
                line_data["notes"] = new_notes
    return stats


def repair_pass(
    data: dict,
    ia: str,
    *,
    play: str | None = None,
    folded_ia: str | None = None,
    dry_run: bool = False,
    max_passes: int = 4,
    next_note_pat: re.Pattern[str] | None = None,
) -> dict[str, Any]:
    if folded_ia is None:
        folded_ia = fold_apostrophe(ia)
    before = sum(
        1
        for scene, sd in data.items()
        if not str(scene).startswith("_") and isinstance(sd, dict)
        for ld in sd.values()
        if isinstance(ld, dict)
        for n in (ld.get("notes") or [])
        if is_union_truncated(n, folded_ia)
    )
    total_repaired = 0
    examples: list[dict] = []

    for _ in range(max_passes):
        pass_repaired = 0
        for scene, scene_data in data.items():
            if str(scene).startswith("_") or not isinstance(scene_data, dict):
                continue
            for line_data in scene_data.values():
                if not isinstance(line_data, dict):
                    continue
                notes = line_data.get("notes") or []
                for i, note in enumerate(notes):
                    if not is_union_truncated(note, folded_ia):
                        continue
                    ext = try_witness_repair(
                        ia, note, folded_ia, play=play, next_note_pat=next_note_pat
                    )
                    if ext:
                        if not dry_run:
                            notes[i] = ext
                        pass_repaired += 1
                        if len(examples) < 8:
                            examples.append(
                                {"before_len": len(note), "after_len": len(ext), "tail": ext[-100:]}
                            )
        total_repaired += pass_repaired
        if pass_repaired == 0:
            break

    after = before - total_repaired if dry_run else sum(
        1
        for scene, sd in data.items()
        if not str(scene).startswith("_") and isinstance(sd, dict)
        for ld in sd.values()
        if isinstance(ld, dict)
        for n in (ld.get("notes") or [])
        if is_union_truncated(n, folded_ia)
    )
    return {
        "before": before,
        "repaired": total_repaired,
        "after": after,
        "unresolved": after,
        "examples": examples,
    }
