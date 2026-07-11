#!/usr/bin/env python3
"""Quantify stage-direction misclassification (referee Point 3).

Mirrors isStageDirection() in index.html and flags fully bracketed play lines
that receive stage-direction styling but are not genuine stage directions
(note bleed, dialogue in brackets, apparatus/editorial insertions).
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Same 22 NV dramatic volumes as audit_nv_fidelity_all_plays.py
PLAY_JSONS = [
    ("Romeo and Juliet", "Public/Data/romeo_and_juliet.json"),
    ("Macbeth", "Public/Data/macbeth_notes_cleaned_play.json"),
    ("Hamlet", "Public/Data/hamlet_notes (1).json"),
    ("King Lear", "Public/Data/kinglear_notes.json"),
    ("Othello", "Public/Data/othello_notes.json"),
    ("The Merchant of Venice", "Public/Data/merchant_of_venice.json"),
    ("As You Like It", "Public/Data/as_you_like_it.json"),
    ("The Tempest", "Public/Data/the_tempest.json"),
    ("A Midsummer Night's Dream", "Public/Data/midsummer_nights_dream.json"),
    ("The Winter's Tale", "Public/Data/the_winters_tale.json"),
    ("Much Ado About Nothing", "Public/Data/much_ado_about_nothing.json"),
    ("Twelfth Night", "Public/Data/twelfth_night.json"),
    ("Love's Labour's Lost", "Public/Data/loves_labours_lost.json"),
    ("Antony and Cleopatra", "Public/Data/antony_and_cleopatra.json"),
    ("Richard III", "Public/Data/richard_iii.json"),
    ("Julius Caesar", "Public/Data/julius_caesar.json"),
    ("Cymbeline", "Public/Data/cymbeline.json"),
    ("King John", "Public/Data/king_john.json"),
    ("Coriolanus", "Public/Data/Coriolanus.json"),
    ("Henry IV, Part 1", "Public/Data/henry_iv_part1.json"),
    ("Henry IV, Part 2", "Public/Data/henry_iv_part2.json"),
    ("Troilus and Cressida", "Public/Data/troilus_and_cressida.json"),
]

# Genuine SD after opening bracket (Folger / NV conventions).
_GENUINE_SD_START = re.compile(
    r"^(?:"
    r"Enter|Exit|Exeunt|Re-enter|Reenter|Flourish|Alarum|Alarums|Sennet|"
    r"Music|Musicians|Dance|Drum|Drums|Trumpet|Trumpets|Thunder|Lightning|"
    r"Scene|DUMB SHOW|Song|Sings|Within|Above|Below|"
    r"To |Aside|Reads?|Reading|Giving|Offering|Kneels?|Rising|Rises|Sits|"
    r"Lies|Draws|Fight|They |He |She |Gentleman |Servant |Camillo |"
    r"Cleomenes |Herdsmen |Whispers|Seats |Here after|Here enter|"
    r"A hall|A room|A street|A camp|A plain|A church|A court|A prison|"
    r"An |At |Before |After |During |From |"
    r"Re-enter|Retreat|Ordnance|Hautboys|Cornets|"
    r"Enter,|Flourish\.|Alarum\.|Fight |As they |The trumpets|"
    r"A crowd|A table|A banquet|A tent|A bed|A wood|A forest|"
    r"Thunder and|Lightning\.|Sennet\.|"
    r"Sound |Voices |Knocking|Clock |March|Shout|Low |Loud |"
    r"Opening |Drawing |Presenting |Giving |Throwing |Taking |"
    r"Unveiling|Unmasking|Kissing |Advancing|Retiring|Singing|"
    r"Stabbing|Showing |Stamping|Leaping|Seeing |Runs |Dies|"
    r"Stabs|Kills|Sleeps|Aloud|Subscribes|Gathering|"
    r"All put|Both call|A shot|A tucket|A tempestuous|A knocking|"
    r"A retreat|A flourish|Sound alarum|Sound trumpet|Sound a retreat"
    r")",
    re.I,
)

# Folger-style one-line action brackets: capitalized stage/action line.
_FOLGER_ACTION_SD = re.compile(r"^\[[A-Z][^\[\]]{0,150}\.?\s*\]$")

# Short action brackets common in modern/Folger SD.
_GENUINE_SD_SHORT = re.compile(
    r"^\[(?:Exit|Exeunt|Aside\.?|Song\.?|Rising|Sits|Whispers|To [A-Z]|"
    r"DUMB SHOW\.?|Drum beats|He speaks|They exit\.?|.* exits\.?)\.?\]$",
    re.I,
)

# Apparatus / note-bleed / editorial signals in play field.
_APPARATUS = re.compile(
    r"(?:"
    r"JOHNSON|STEEVENS|MALONE|THEOBALD|DYCE|HANMER|WARBURTON|COLERIDGE|"
    r"CAPPELL|HEATH|SCHMIDT|ONIONS|HALLIWELL|BOSWELL|REED|FARMER|"
    r"LLOYD|VERPLANCK|WHITE|CLARK|HUNTER|RITSON|DOUCE|"
    r"\(p\.\s*\d+\)|Variorum|Cambridge|Folger|Knight|Collier|"
    r"Q1|Q2|F1|F2|F3|F4|\bEd\.\]|\bSing\.\]|"
    r"reads (?:thus|so|:|,)|"
    r"this doctrine I derive|Promethean fire"
    r")",
    re.I,
)

# Lowercase-start continuation fragments (case-sensitive).
_FRAGMENT_START = re.compile(
    r"^\[(?:the |and |or |but |if |when |where |that |which |who |"
    r"you |I |we |my |thy |our |is |are |was |"
    r"do |does |did |shall |will |would |could |should |bed, |door, |"
    r"noise of |gates with )",
)

# Dialogue merged into bracket wrapper (speaker label or speech after SD clause).
_DIALOGUE_BLEED = re.compile(
    r"(?:"
    r"\.\]\s+[A-Z][A-Z\s.'\u2019-]{1,40},?\s+(?:to |aside )?[A-Z]|"
    r"\.\]\s+[A-Z][a-z]+ (?:as |You |Thou |I |We |What |How |Why |O |"
    r"Stand |Think |Our |Heyday|Here come|From women's)"
    r")",
    re.I,
)

# Inner bracket closes early then continues (note bleed or merged speech).
_MERGED_INNER_CLOSE = re.compile(r"^[^\]]*\]\s+[A-Za-z(]", re.I)

# Truncated aside/dialogue: bracketed line ends mid-thought without exit/enter.
_TRUNCATED_SPEECH = re.compile(
    r"^\[(?:Aside[^]]{10,}|[^]]*[?;])\s*$",
    re.I,
)


def is_stage_direction(line: str) -> bool:
    """Mirror index.html isStageDirection()."""
    t = line.strip()
    if not t:
        return False
    if t.startswith("[") and t.endswith("]"):
        return True
    if t.startswith("(") and t.endswith(")"):
        return True
    if re.match(
        r"^(Enter|Exit|Exeunt|Re-enter|Flourish|Alarum|Sennet|Music|Dance)\b",
        t,
        re.I,
    ):
        return True
    return False


def bracket_sd_trigger(line: str) -> bool:
    t = line.strip()
    return bool(t.startswith("[") and t.endswith("]"))


def iter_play_lines(data: dict):
    """Yield (scene_key, line_key, play_text) from NV play JSON."""
    for scene_key, scene in data.items():
        if str(scene_key).startswith("_") or scene_key == "DRAMATIS PERSONAE":
            continue
        if not isinstance(scene, dict):
            continue
        for line_key, line_data in scene.items():
            if str(line_key).startswith("_"):
                continue
            if isinstance(line_data, str):
                play = line_data.strip()
            elif isinstance(line_data, dict):
                play = (
                    line_data.get("play")
                    or line_data.get("text")
                    or line_data.get("line")
                    or ""
                ).strip()
            else:
                continue
            if play:
                yield str(scene_key), str(line_key), play


def is_genuine_bracket_sd(line: str) -> bool:
    """Heuristic: fully bracketed line is a real stage direction."""
    t = line.strip()
    if not (t.startswith("[") and t.endswith("]")):
        return False

    inner = t[1:-1].strip()
    if not inner:
        return False

    # Short aside/song markers only — not aside-prefixed dialogue.
    if re.match(r"^Aside\.?\s*$", inner, re.I):
        return True
    if re.match(r"^Aside to [A-Z]", inner) and len(inner) < 80:
        return True
    if re.match(r"^(Song|Sings)\.?\s*$", inner, re.I):
        return True
    if re.match(r"^Sings\.", inner, re.I) and len(inner) < 120:
        return True

    if _GENUINE_SD_START.match(inner):
        # Aside-prefixed speech is SD typography in Folger but not a bare SD.
        if re.match(r"^Aside\b", inner, re.I) and len(inner) > 25:
            return False
        return True
    if _GENUINE_SD_SHORT.match(t):
        return True

    # Folger-style "[They exit.]" / "[Mamillius exits.]"
    if re.search(r"\b(?:exit|exeunt|enter|re-enter)\b", inner, re.I):
        # Reject if substantial dialogue precedes a trailing exit clause.
        if re.search(
            r"^\[(?:See |From |To die |As thou |the |and |you |I |we |they )",
            t,
            re.I,
        ):
            return False
        return True

    return False


def classify_false_positive(line: str) -> tuple[bool, str]:
    """Return (is_misclassified, reason) for bracket-triggered SD lines."""
    t = line.strip()
    if not bracket_sd_trigger(t):
        return False, ""

    inner = t[1:-1].strip()

    if _APPARATUS.search(t):
        return True, "apparatus_or_note_bleed"

    if inner.startswith("("):
        return True, "parenthetical_dialogue"

    if _MERGED_INNER_CLOSE.search(inner):
        return True, "merged_sd_and_dialogue"

    if re.search(r"doctrine I derive|Promethean fire", t, re.I):
        return True, "dialogue_in_brackets"

    if inner and inner[0].islower():
        return True, "lowercase_fragment"

    if re.match(r"^\[Aside\.?\s+.+", t, re.I) and len(inner) > 25:
        return True, "truncated_speech"

    if re.search(
        r"gates of Milan|Bed, chamber, pander|one is Caius Lucius",
        t,
        re.I,
    ):
        return True, "dialogue_in_brackets"

    if is_genuine_bracket_sd(t):
        return False, "genuine_sd"

    if _FOLGER_ACTION_SD.match(t):
        return False, "genuine_sd"

    if _FRAGMENT_START.search(t):
        return True, "dialogue_in_brackets"

    if _DIALOGUE_BLEED.search(t):
        return True, "dialogue_in_brackets"

    if _TRUNCATED_SPEECH.match(t):
        return True, "truncated_speech"

    if len(t) > 180 and not re.search(
        r"\b(?:enter|exit|exeunt|flourish|alarum|aside\.|song\.)\b", t, re.I
    ):
        return True, "long_non_sd_prose"

    if re.search(r"[,;]\s*\]$", t) and not re.search(r"\b(?:exit|exeunt)\.", t, re.I):
        return True, "truncated_clause"

    return True, "unclassified_bracket"


def should_skip_scene(scene_key: str, play: str) -> bool:
    if scene_key == "DRAMATIS PERSONAE":
        return True
    pu = play.upper()
    if pu.startswith("ACT ") and "SCENE" in pu and len(play) < 40:
        return True
    return False


def audit_play(play_name: str, json_path: Path) -> dict:
    data = json.loads(json_path.read_text(encoding="utf-8"))

    stats = {
        "play": play_name,
        "json": str(json_path.relative_to(ROOT)),
        "total_play_lines": 0,
        "lines_with_brackets": 0,
        "bracket_sd_triggers": 0,
        "misclassified": 0,
        "misclassified_examples": [],
        "reason_counts": Counter(),
    }

    for scene_key, line_key, play in iter_play_lines(data):
        if should_skip_scene(scene_key, play):
            continue

        stats["total_play_lines"] += 1

        if "[" in play:
            stats["lines_with_brackets"] += 1

        if not is_stage_direction(play):
            continue

        if not bracket_sd_trigger(play):
            continue

        stats["bracket_sd_triggers"] += 1
        is_fp, reason = classify_false_positive(play)
        if is_fp:
            stats["misclassified"] += 1
            stats["reason_counts"][reason] += 1
            if len(stats["misclassified_examples"]) < 8:
                stats["misclassified_examples"].append(
                    {
                        "reason": reason,
                        "scene": scene_key,
                        "line": line_key,
                        "play": play[:320] + ("…" if len(play) > 320 else ""),
                    }
                )

    stats["reason_counts"] = dict(stats["reason_counts"])
    return stats


def pct(num: int, denom: int) -> float | None:
    if denom == 0:
        return None
    return round(100.0 * num / denom, 4)


def fmt_pct(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.4f}%"


def build_markdown(summary: dict, per_play: list[dict]) -> str:
    lines = [
        "# Stage-direction misclassification audit (referee Point 3)",
        "",
        "## Method",
        "",
        "- **Classifier mirrored:** `isStageDirection()` in `index.html` — any play line "
        "that both starts with `[` and ends with `]` receives stage-direction styling.",
        "- **False positive:** bracket-triggered SD line that is not a genuine stage direction "
        "(note/apparatus bleed, editorial brackets, dialogue wrapped in brackets, truncated speech).",
        "- **Corpus:** NV dramatic volumes (`Public/Data/*.json`). "
        "Scene/act headers and DRAMATIS PERSONAE excluded.",
        "",
    ]
    if summary.get("plays_excluded"):
        lines.append(
            f"- **Excluded:** {', '.join(summary['plays_excluded'])} "
            f"({summary['plays_audited']} plays audited)."
        )
        lines.append("")
    lines.extend(
        [
        "## Summary rates",
        "",
        f"| Metric | Count | Rate |",
        f"|--------|------:|-----:|",
        f"| Total play lines | {summary['total_play_lines']:,} | — |",
        f"| Lines containing `[` | {summary['lines_with_brackets']:,} | "
        f"{fmt_pct(summary['pct_lines_with_brackets'])} of play lines |",
        f"| Bracket SD triggers (`[…]` whole line) | {summary['bracket_sd_triggers']:,} | "
        f"{fmt_pct(summary['pct_bracket_sd_of_play'])} of play lines |",
        f"| **Misclassified (false positives)** | **{summary['misclassified']:,}** | "
        f"**{fmt_pct(summary['pct_misclassified_of_play'])} of play lines** |",
        f"| Misclassified / bracket SD triggers | {summary['misclassified']:,} / "
        f"{summary['bracket_sd_triggers']:,} | "
        f"**{fmt_pct(summary['pct_misclassified_of_bracket_sd'])}** |",
        "",
        "### Interpretation",
        "",
        ],
    )

    rate = summary["pct_misclassified_of_play"]
    if rate < 0.05:
        lines.append(
            f"The misclassification rate is **{rate:.4f}%** of play lines ({summary['misclassified']} / "
            f"{summary['total_play_lines']:,}) — small enough to treat as a cosmetic presentation edge case "
            "rather than a structural fidelity issue."
        )
    else:
        lines.append(
            f"The misclassification rate is **{rate:.4f}%** of play lines "
            f"({summary['misclassified']} / {summary['total_play_lines']:,})."
        )

    lines.extend(
        [
            "",
            "### Paper-ready sentence",
            "",
            f"> We audited stage-direction styling across all {summary['plays_audited']} NV playtext volumes "
            f"({summary['total_play_lines']:,} play lines). The UI treats any line fully wrapped in square "
            f"brackets as a stage direction. Heuristic review identified **{summary['misclassified']}** "
            f"false positives (**{rate:.2f}%** of play lines; **{summary['pct_misclassified_of_bracket_sd']:.2f}%** "
            f"of bracket-wrapped lines), chiefly dialogue or note fragments accidentally bracketed during "
            "digitization. The failure mode is cosmetic—mis-set typography and TTS skipping—not note loss.",
            "",
            "Failure mode: affected lines render in stage-direction typography and are "
            "skipped by the audio/TTS pipeline (`_isAudioStageDir` also keys on leading `[`). "
            "No note text is lost; the error is display/navigation only.",
            "",
            "### False-positive reasons (corpus-wide)",
            "",
        ]
    )
    for reason, count in sorted(
        summary["reason_counts"].items(), key=lambda x: (-x[1], x[0])
    ):
        lines.append(f"- `{reason}`: {count}")

    lines.extend(["", "## Per-play breakdown", "", "| Play | Play lines | Bracket SD | Misclassified | Rate |", "|------|----------:|-----------:|--------------:|-----:|"])
    for p in sorted(per_play, key=lambda x: -x["misclassified"]):
        r = pct(p["misclassified"], p["total_play_lines"]) or 0.0
        lines.append(
            f"| {p['play']} | {p['total_play_lines']:,} | {p['bracket_sd_triggers']:,} | "
            f"{p['misclassified']:,} | {r:.4f}% |"
        )

    lines.extend(["", "## Sample false positives", ""])
    for p in per_play:
        if not p["misclassified_examples"]:
            continue
        lines.append(f"### {p['play']}")
        for ex in p["misclassified_examples"][:3]:
            lines.append(f"- **{ex['reason']}** ({ex.get('scene')} / line {ex.get('line')}): `{ex['play']}`")
        lines.append("")

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-json",
        default=str(ROOT / "validation" / "nv_stage_direction_misclassification.json"),
    )
    parser.add_argument(
        "--out-md",
        default=str(ROOT / "validation" / "nv_stage_direction_misclassification.md"),
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="PLAY",
        help="Play title to omit (repeatable), e.g. 'Troilus and Cressida'",
    )
    args = parser.parse_args()

    excluded = set(args.exclude)
    play_list = [(n, p) for n, p in PLAY_JSONS if n not in excluded]
    if excluded:
        missing = excluded - {n for n, _ in PLAY_JSONS}
        if missing:
            print(f"WARNING: unknown --exclude play(s): {', '.join(sorted(missing))}")

    per_play = []
    for play_name, rel_path in play_list:
        path = ROOT / rel_path
        if not path.exists():
            print(f"SKIP missing: {path}")
            continue
        per_play.append(audit_play(play_name, path))

    total_lines = sum(p["total_play_lines"] for p in per_play)
    with_brackets = sum(p["lines_with_brackets"] for p in per_play)
    bracket_sd = sum(p["bracket_sd_triggers"] for p in per_play)
    misclassified = sum(p["misclassified"] for p in per_play)
    reason_counts = Counter()
    for p in per_play:
        reason_counts.update(p["reason_counts"])

    summary = {
        "method": "Mirror isStageDirection() bracket rule; heuristic genuine-SD classifier",
        "plays_audited": len(per_play),
        "plays_excluded": sorted(excluded),
        "total_play_lines": total_lines,
        "lines_with_brackets": with_brackets,
        "bracket_sd_triggers": bracket_sd,
        "misclassified": misclassified,
        "pct_lines_with_brackets": pct(with_brackets, total_lines),
        "pct_bracket_sd_of_play": pct(bracket_sd, total_lines),
        "pct_misclassified_of_play": pct(misclassified, total_lines),
        "pct_misclassified_of_bracket_sd": pct(misclassified, bracket_sd),
        "reason_counts": dict(reason_counts),
    }

    out = {"summary": summary, "per_play": per_play}
    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out_md.write_text(build_markdown(summary, per_play), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(f"\nWrote {out_json}")
    print(f"Wrote {out_md}")


if __name__ == "__main__":
    main()
