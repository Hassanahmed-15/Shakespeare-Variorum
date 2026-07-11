"""Canonical Internet Archive witnesses for the 22 NV dramatic volumes.

Never infer witness IDs from editi## numbering — those identifiers are not
sequential by play. Use resolve_nv_witnesses.py to validate candidates.
"""

from __future__ import annotations

from pathlib import Path as _Path

_ROOT = _Path(__file__).resolve().parents[1]

# On-disk NV witness when IA text is restricted or wrong edition (play title -> path under repo root).
LOCAL_WITNESS_BY_PLAY: dict[str, _Path] = {
    "Troilus and Cressida": _ROOT / "data" / "troilus_nv_witness.txt",
}

WITNESS_BY_PLAY: dict[str, tuple[str, str]] = {
    "Romeo and Juliet": (
        "newvariorumediti01shak",
        "newvariorumediti01shak_djvu.txt",
    ),
    "Macbeth": (
        "newvariorumediti10shak",
        "newvariorumediti10shak_djvu.txt",
    ),
    # Furness Hamlet apparatus (line-by-line commentary, Acts I–V). Do not use
    # newvariorumediti11shak — that IA item is introductory/critical essays, not the play text.
    "Hamlet": (
        "anewvariorumedi07furngoog",
        "anewvariorumedi07furngoog_djvu.txt",
    ),
    "King Lear": (
        "newvariorumediti05shak",
        "newvariorumediti05shak_djvu.txt",
    ),
    "Othello": (
        "newvariorumediti13shak",
        "newvariorumediti13shak_djvu.txt",
    ),
    "The Merchant of Venice": (
        "newvariorumediti0000unse_h5u1",
        "newvariorumediti0000unse_h5u1_djvu.txt",
    ),
    "As You Like It": (
        "newvariorumediti0000unse_v0h0",
        "newvariorumediti0000unse_v0h0_djvu.txt",
    ),
    "The Tempest": (
        "tempestnewvarior0009unse",
        "tempestnewvarior0009unse_djvu.txt",
    ),
    "A Midsummer Night's Dream": (
        "amidsommernight01furngoog",
        "amidsommernight01furngoog_djvu.txt",
    ),
    "The Winter's Tale": (
        "winterstale0007unse",
        "winterstale0007unse_djvu.txt",
    ),
    "Much Ado About Nothing": (
        "in.ernet.dli.2015.94001",
        "2015.94001.A-New-Variorum-Edition-Of-Shakespearemuch-Adoe-About-Nothingvol12ed2_djvu.txt",
    ),
    "Twelfth Night": (
        "twelfenightorwha0000hora",
        "twelfenightorwha0000hora_djvu.txt",
    ),
    "Love's Labour's Lost": (
        "in.ernet.dli.2015.94000",
        "2015.94000.A-New-Variorum-Edition-Of-Shakespeareloues-Labours-Lostvol14_djvu.txt",
    ),
    "Antony and Cleopatra": (
        "newvariorumediti15shak",
        "newvariorumediti15shak_djvu.txt",
    ),
    "Richard III": (
        "newvariorumediti16shak",
        "newvariorumediti16shak_djvu.txt",
    ),
    "Julius Caesar": (
        "in.ernet.dli.2015.94007",
        "2015.94007.A-New-Variorum-Edition-Of-Shakespearethe-Tragedie-Of-Ivlivs-Caesar_djvu.txt",
    ),
    "Cymbeline": (
        "unset0000unse_m8h0",
        "unset0000unse_m8h0_djvu.txt",
    ),
    "King John": (
        "in.ernet.dli.2015.93998",
        "2015.93998.A-New-Variorum-Edition-Of-Shakespeare_djvu.txt",
    ),
    "Coriolanus": (
        "tragedieofcoriol0002edit",
        "tragedieofcoriol0002edit_djvu.txt",
    ),
    "Henry IV, Part 1": (
        "newvariorumediti21shak",
        "newvariorumediti21shak_djvu.txt",
    ),
    "Henry IV, Part 2": (
        "newvariorumediti23shak",
        "newvariorumediti23shak_djvu.txt",
    ),
    # Canonical Vol. XXV (Hillebrand/Baldwin, 1953). IA djvu is lending-restricted (401);
    # Canonical text: data/troilus_nv_1953.pdf -> data/troilus_nv_witness.txt (1953 scan OCR).
    "Troilus and Cressida": (
        "newvariorumediti0000unse",
        "newvariorumediti0000unse_djvu.txt",
    ),
}

# Audit-time fallback when canonical witness is unavailable (401, missing cache).
# Repair scripts should still use WITNESS_BY_PLAY; only truncation audit uses these.
WITNESS_AUDIT_FALLBACK: dict[str, tuple[str, str]] = {
    # Vol. XXII (1917 ed. Furness lineage); ~85% note match vs 1953 volume; cached locally.
    "Troilus and Cressida": (
        "newvariorumediti22shak",
        "newvariorumediti22shak_djvu.txt",
    ),
}

# Extra candidates tested by resolve_nv_witnesses.py when verifying a play.
WITNESS_CANDIDATES: dict[str, list[tuple[str, str]]] = {
    "Hamlet": [
        ("anewvariorumedi07furngoog", "anewvariorumedi07furngoog_djvu.txt"),
        ("in.ernet.dli.2015.94022", "2015.94022.A-Variorum-Edition-Of-Shakespearehamletvol2ed12_djvu.txt"),
        ("newvariorumediti12shak", "newvariorumediti12shak_djvu.txt"),
        ("newvariorumediti02shak", "newvariorumediti02shak_djvu.txt"),
        # Legacy mis-map: critical essays about Hamlet, not line apparatus.
        ("newvariorumediti11shak", "newvariorumediti11shak_djvu.txt"),
    ],
    "King Lear": [
        ("newvariorumediti05shak", "newvariorumediti05shak_djvu.txt"),
        ("kinglearthenewva0005shak", "kinglearthenewva0005shak_djvu.txt"),
    ],
    "As You Like It": [
        ("newvariorumediti0000unse_v0h0", "newvariorumediti0000unse_v0h0_djvu.txt"),
        ("bwb_W8-AJR-935", "bwb_W8-AJR-935_djvu.txt"),
        ("in.ernet.dli.2015.226430", "2015.226430.A-New_djvu.txt"),
        ("anewvariorumedi06furngoog", "anewvariorumedi06furngoog_djvu.txt"),
    ],
    "A Midsummer Night's Dream": [
        ("amidsommernight01furngoog", "amidsommernight01furngoog_djvu.txt"),
        ("anewvariorumedi08furngoog", "anewvariorumedi08furngoog_djvu.txt"),
        ("anewvariorumedi03furngoog", "anewvariorumedi03furngoog_djvu.txt"),
        ("anewvariorumedi07furngoog", "anewvariorumedi07furngoog_djvu.txt"),
        ("newvariorumediti07shak", "newvariorumediti07shak_djvu.txt"),
        ("bwb_C0-BNX-214", "bwb_C0-BNX-214_djvu.txt"),
    ],
    "Troilus and Cressida": [
        ("anewvariorumedi16furngoog", "anewvariorumedi16furngoog_djvu.txt"),
        ("anewvariorumedi19furngoog", "anewvariorumedi19furngoog_djvu.txt"),
        ("newvariorumediti22shak", "newvariorumediti22shak_djvu.txt"),
    ],
    "Julius Caesar": [
        ("in.ernet.dli.2015.94007", "2015.94007.A-New-Variorum-Edition-Of-Shakespearethe-Tragedie-Of-Ivlivs-Caesar_djvu.txt"),
        ("tragedieofjulius0018hora", "tragedieofjulius0018hora_djvu.txt"),
    ],
}
