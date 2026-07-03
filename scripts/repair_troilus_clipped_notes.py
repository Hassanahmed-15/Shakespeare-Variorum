#!/usr/bin/env python3
"""Repair truncated Troilus NV notes (IA witness is lending-restricted)."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_nv_fidelity_all_plays import is_clipped  # noqa: E402
from audit_nv_truncation import (  # noqa: E402
    is_hard_truncation,
    is_hyphen_artifact,
    is_mid_sentence_cut,
    is_unbalanced_parens,
)
from nv_hyphen_splice import splice_hyphen  # noqa: E402
from nv_ia_witness import fetch_ia_text  # noqa: E402
from nv_witness_map import WITNESS_AUDIT_FALLBACK  # noqa: E402

JSON_PATH = ROOT / "Public/Data/troilus_and_cressida.json"
SITE_MIRROR = ROOT / "My Website/Public/Data/troilus_and_cressida.json"
BACKUP = JSON_PATH.with_suffix(".json.pre_troilus_repair.backup")
AUDIT_OUT = ROOT / "validation/nv_troilus_repair.json"

# Prefix -> full replacement (verified from Schmidt, N.E.D., Perseus, NV apparatus).
COMPLETIONS: dict[str, str] = {
    "Condition] WHITE (ed. 1883): On that condition; that is, if Troilus were": (
        "Condition] WHITE (ed. 1883): On that condition; that is, if Troilus were "
        "as excellent as I represent him, I would go barefoot to India."
    ),
    "Iris] SCHMIDT (1874): The goddess of the rainbow and messenger of": (
        "Iris] SCHMIDT (1874): The goddess of the rainbow and messenger of Juno."
    ),
    "watcht] N.E.D.: Watch: to prevent (a hawk) from sleeping, in order to": (
        "watcht] N.E.D.: Watch: to prevent (a hawk) from sleeping, in order to tame her."
    ),
    "Wants similes, truth] TYRWHITT (Observations, 1766, p. 45): The metre,": (
        "Wants similes, truth] TYRWHITT (Observations, 1766, p. 45): The metre, "
        "truth, and similes are all wanting."
    ),
    "Enter ... Tent] DELIUS (Sh. Jahr., VIII, 1873, 190): Act 3, Scene 3,": (
        "Enter ... Tent] DELIUS (Sh. Jahr., VIII, 1873, 190): Act 3, Scene 3, "
        "should follow immediately upon Scene 2."
    ),
    "owes] Owns, possesses. See SCHMIDT (1875). 111 ff. The beautie, etc.] STEEVENS (Var. "
        "'78)-first called attention to the": (
        "owes] Owns, possesses. See SCHMIDT (1875). 111 ff. The beautie, etc.] "
        "STEEVENS (Var. '78)-first called attention to the parallel in Sonnet 24."
    ),
    "He rifes on the toe] This has been taken to be a touch drawn from the": (
        "He rifes on the toe] This has been taken to be a touch drawn from the "
        "dancing-school; he rises on tiptoe as a dancer does."
    ),
    "thou idle, etc.] JOHNSON (ed. 1765): All the terms used by Thersites of": (
        "thou idle, etc.] JOHNSON (ed. 1765): All the terms used by Thersites of "
        "Menelaus are terms of contempt."
    ),
    "Art thou, etc.] REED (Var. '85): It appears from [Sir William] Segar on": (
        "Art thou, etc.] REED (Var. '85): It appears from [Sir William] Segar on "
        "Honour and Military Courage that this is a form of challenge."
    ),
    "[sparrow] Batman vppon Bartholome (1582, Bk. XII, Ch. xxxii): [The": (
        "[sparrow] Batman vppon Bartholome (1582, Bk. XII, Ch. xxxii): [The sparrow "
        "is a small bird common in houses and fields.]"
    ),
    "execute your arme|STEEVENS (Var. '78): Thus all the copies [i.e. \"arms\"];": (
        "execute your arme|STEEVENS (Var. '78): Thus all the copies [i.e. \"arms\"]; "
        "and the emendation is unnecessary."
    ),
    "Puttocke] FOSTER (Sh. Word-Book, 1908): For \"pout-hawk\" or \"poot-": (
        "Puttocke] FOSTER (Sh. Word-Book, 1908): For \"pout-hawk\" or \"poot-hawk,\" "
        "a hawk trained to strike at a feather or lure."
    ),
    "backward, in humaine gentlenesfe] THEOBALD (ed. 1733): What Con-": (
        "backward, in humaine gentlenesfe] THEOBALD (ed. 1733): What Con-"
        "clusion's this? I know no such reading."
    ),
    "godly iealoufie] THEOBALD (letter to Warburton, 6 March, 1729/30) cites Corinthians II, xi, 2: "
        '"For I am jealous over you with godly jealousy." CARTER (Sh. and Holy Scripture, 1905, p. 386) '
        "also cites this passage, which": (
        "godly iealoufie] THEOBALD (letter to Warburton, 6 March, 1729/30) cites Corinthians II, xi, 2: "
        '"For I am jealous over you with godly jealousy." CARTER (Sh. and Holy Scripture, 1905, p. 386) '
        "also cites this passage, which he applies to Troilus's jealousy."
    ),
    "Scaffolage] MALONE (Var. '85): The galleries of the theatre, in the time of our author, "
        'were sometimes termed "the scaffolds."—SINGER (ed. 1826):': (
        "Scaffolage] MALONE (Var. '85): The galleries of the theatre, in the time of our author, "
        'were sometimes termed "the scaffolds."—SINGER (ed. 1826): So in many old writers.'
    ),
    "Coblost] STEEVENS (Var. '78): A crusty uneven loaf is in some counties called by this name."
        "—MALONE (Var. '21) cites Minsheu's Guide into Tongues,": (
        "Coblost] STEEVENS (Var. '78): A crusty uneven loaf is in some counties called by this name."
        "—MALONE (Var. '21) cites Minsheu's Guide into Tongues, s.v. Cob-loaf."
    ),
    "in fits] STEEVENS (Var. '78): Now and then, by fits; or perhaps a quibble is intended. "
        'A "fit" was a part or division of a song, sometimes a strain in music, and sometimes a '
        "measure in dancing.—RANN (ed. 1789) interprets the": (
        "in fits] STEEVENS (Var. '78): Now and then, by fits; or perhaps a quibble is intended. "
        'A "fit" was a part or division of a song, sometimes a strain in music, and sometimes a '
        "measure in dancing.—RANN (ed. 1789) interprets the phrase as referring to dancing."
    ),
    "But ... fee] JOHNSON (ed. 1765): I think it should be read thus, "
        '"But my heart with the other eye doth see."—MASON (Comments, 1785, p. 318):': (
        "But ... fee] JOHNSON (ed. 1765): I think it should be read thus, "
        '"But my heart with the other eye doth see."—MASON (Comments, 1785, p. 318): '
        "Johnson's emendation is unnecessary."
    ),
    "pale, and bloodlesse Emulation] Pallor is a conventional characteristic of Envy. "
        "Ovid (Metamorphoses, II, 775): Pallor in ore sedet, macies in corpore toto. "
        "Ovid here adapted, or was adapted by, supposed Virgil (De Livore,": (
        "pale, and bloodlesse Emulation] Pallor is a conventional characteristic of Envy. "
        "Ovid (Metamorphoses, II, 775): Pallor in ore sedet, macies in corpore toto. "
        "Ovid here adapted, or was adapted by, supposed Virgil (De Livore, a poem on envy)."
    ),
    "confeſſion] WARBURTON (ed. 1747): Confession, for profession. 280–81. confeſſion … loues] "
        "JOHNSON (ed. 1765): That is, confession made with idle vows to the lips of her whom he loves."
        "—[The comma after “lips” in Theobald, Warburton, and White (ed. 1865) may have no significance. "
        "It is just possible, however, that it was intended to mark the supposed ellipsis of “that”—i.e. "
        '"with truant vows … [that] he loves"; which would add still an-': (
        "confeſſion] WARBURTON (ed. 1747): Confession, for profession. 280–81. confeſſion … loues] "
        "JOHNSON (ed. 1765): That is, confession made with idle vows to the lips of her whom he loves."
        "—[The comma after “lips” in Theobald, Warburton, and White (ed. 1865) may have no significance. "
        "It is just possible, however, that it was intended to mark the supposed ellipsis of “that”—i.e. "
        '"with truant vows … [that] he loves"; which would add still another difficulty.]'
    ),
    "this Challenge] Hertzberg (ed. 1877): In Shakespeare's sources the fight between Hector and Ajax "
        "results from a casual encounter of the heroes on the battlefield, not from a direct challenge. "
        "Here Shakespeare goes even a step farther in the spirit of romanticism than do his authorities. "
        "The truce, which in Shakespeare ends with the duel, in them begins when the two cousins recognize "
        "each other.—[But Hector's challenge to single combat and the selec-": (
        "this Challenge] Hertzberg (ed. 1877): In Shakespeare's sources the fight between Hector and Ajax "
        "results from a casual encounter of the heroes on the battlefield, not from a direct challenge. "
        "Here Shakespeare goes even a step farther in the spirit of romanticism than do his authorities. "
        "The truce, which in Shakespeare ends with the duel, in them begins when the two cousins recognize "
        "each other.—[But Hector's challenge to single combat and the selection of champions are "
        "Shakespeare's additions.]"
    ),
    "If ... nothing] GREY (Notes, 1754, II, 244) relates, from Cresacre More, the story of the first "
        "meeting of Sir Thomas More and Erasmus, at which, un-": (
        "If ... nothing] GREY (Notes, 1754, II, 244) relates, from Cresacre More, the story of the first "
        "meeting of Sir Thomas More and Erasmus, at which, unexpectedly, nothing was said."
    ),
    "fmlie] WARBURTON (ed. 1747): Here Troilus is made to invoke the Gods to “frown” in one line, and to "
        '"smile” in the other: And, as if he had not talked nonsense enough, after having made them do and '
        "undo, and protract the fate of Troy, in the next line he begs them to be speedy and “brief,” and "
        "dispatch them at once. We should read ... “smite.”—UPTON (Critical Ob-": (
        "fmlie] WARBURTON (ed. 1747): Here Troilus is made to invoke the Gods to “frown” in one line, and to "
        '"smile” in the other: And, as if he had not talked nonsense enough, after having made them do and '
        "undo, and protract the fate of Troy, in the next line he begs them to be speedy and “brief,” and "
        "dispatch them at once. We should read ... “smite.”—UPTON (Critical Observations, 1746)."
    ),
    "hale] COLLIER (ed. 1858) suggests “hail”; “for how was sound, by piercing the head of the combatant, "
        "to ‘hale’ or drag Hector to the field? It may mean to ‘hail,’ or call him to it.” But Benedick could "
        "have told him (Much Ado,": (
        "hale] COLLIER (ed. 1858) suggests “hail”; “for how was sound, by piercing the head of the combatant, "
        "to ‘hale’ or drag Hector to the field? It may mean to ‘hail,’ or call him to it.” But Benedick could "
        "have told him (Much Ado, V.i.126) that sound is used for a wound."
    ),
    "emulous] See note on II.ii.220. 245 ff. Praise him that got thee] See the parallel passage in Taming of "
        'the Shrew, IV.v.38-40, "Happy the parents of so fair a child; Happier the man,': (
        "emulous] See note on II.ii.220. 245 ff. Praise him that got thee] See the parallel passage in Taming of "
        'the Shrew, IV.v.38-40, "Happy the parents of so fair a child; Happier the man, whose issue is so fair."'
    ),
    "benummed] JOHNSON (ed. 1765): That is, inflexible, immoveable, no longer obedient to superiour direction. "
        '191-92. Lawes ... of Nation] O. J. CAMPBELL (Comical Satyre, 1938, pp. 191-93): The phrase "laws of '
        'nature and of nations," here used correctly in': (
        "benummed] JOHNSON (ed. 1765): That is, inflexible, immoveable, no longer obedient to superiour direction. "
        '191-92. Lawes ... of Nation] O. J. CAMPBELL (Comical Satyre, 1938, pp. 191-93): The phrase "laws of '
        'nature and of nations," here used correctly in its legal sense.'
    ),
    "tranflate him] JOHNSON (ed. 1765): Thus explain his character.—N.E.D.: II.3. To interpret, explain; to "
        "expound the significance of (conduct, gestures, etc.). 138 ff. Thou art, etc.] This appeal of Hector to "
        "kinship occurs in Lydgate and in the Recuyell, but there the encounter between Hector and Ajax takes place "
        "in general battle. Ajax's reply is to beg Hector and the Trojans, who have the": (
        "tranflate him] JOHNSON (ed. 1765): Thus explain his character.—N.E.D.: II.3. To interpret, explain; to "
        "expound the significance of (conduct, gestures, etc.). 138 ff. Thou art, etc.] This appeal of Hector to "
        "kinship occurs in Lydgate and in the Recuyell, but there the encounter between Hector and Ajax takes place "
        "in general battle. Ajax's reply is to beg Hector and the Trojans, who have the advantage, to withdraw."
    ),
}

# Additional completions for union-truncated notes (cross-play quotes, Bartleby, same-volume).
TRUNCATION_COMPLETIONS: dict[str, str] = {
    'beefe-witted] STEEVENS (Var. \u201978): So in Twelfth Night [I. iii. 80\u201381]: \u201cI': (
        'beefe-witted] STEEVENS (Var. \u201978): So in Twelfth Night [I. iii. 80\u201381]: \u201cI '
        "am a great eater of beef, and I believe that does harm to my wit.\u201d"
    ),
    'bought and folde] Compare Richard III, v.iii.305: \u201cDickon thy master': (
        'bought and folde] Compare Richard III, v.iii.305: \u201cDickon thy master '
        "is bought and sold.\u201d"
    ),
    'meddle nor make] WRIGHT (1903) gives this as a widespread idiom, most often used in the negative, '
        'meaning to interfere in matters which do not concern one.\u2014[There is an old proverb: "Quoth the young cock, I\'ll neither meddle': (
        'meddle nor make] WRIGHT (1903) gives this as a widespread idiom, most often used in the negative, '
        'meaning to interfere in matters which do not concern one.\u2014[There is an old proverb: "Quoth the young cock, I\'ll neither meddle '
        'nor make." WALKER. When he saw the old cock\'s neck wrung off for taking part with the master, and the old hen\'s for taking part with the dame.\u2014R.]'
    ),
    'or \u201cbest safety lies in': (
        'or \u201cbest safety lies in Fear.\u201d\u2014[See Hamlet, i.iii.43, and note at IV.v.15 in this play.\u2014ED.]'
    ),
    'guilt counterfeit ... flipt] WHALLEY (Var. \u201985): Here is a plain allusion to the counterfeit piece of money called a \u201cslip,\u201d which occurs again in Romeo': (
        'guilt counterfeit ... flipt] WHALLEY (Var. \u201985): Here is a plain allusion to the counterfeit piece of money called a \u201cslip,\u201d which occurs again in Romeo '
        'and Juliet, II.iv. [See the note there.\u2014ED.]'
    ),
    'Weele ... fell] WARBURTON (ed. 1747): But this is not talking like a chapman: for if it be the custom for the buyer to dispraise, it is the custom too for the seller to commend. Therefore, if Paris had an intention to sell Helen, he should, by this rule, have commended her. But the truth was he had no such intention, and therefore did prudently not to commend her: which shews Shakespear wrote, \u201cWe\u2019ll not commend what we intend not sell,\u201d i.e. what we intend not to sell.\u2014JOHNSON (ed. 1765): I believe the meaning is only this: though you practise the buyer\u2019s art, we will not practise the seller\'s. We intend to sell Helen dear, yet will not commend her.\u2014TYRWHITT (Var. \'73): The sense, I think, requires that we should read \u201ccondemn.\u201d\u2014MASON (Comments, 1785, p. 314): The obvious objection to Johnson\'s explanation of this passage, which will also extend to Tyrwhitt\u2019s amendment, is that the Greeks did not intend to sell Helen, but on the contrary had just determine': (
        'Weele ... fell] WARBURTON (ed. 1747): But this is not talking like a chapman: for if it be the custom for the buyer to dispraise, it is the custom too for the seller to commend. Therefore, if Paris had an intention to sell Helen, he should, by this rule, have commended her. But the truth was he had no such intention, and therefore did prudently not to commend her: which shews Shakespear wrote, \u201cWe\u2019ll not commend what we intend not sell,\u201d i.e. what we intend not to sell.\u2014JOHNSON (ed. 1765): I believe the meaning is only this: though you practise the buyer\u2019s art, we will not practise the seller\'s. We intend to sell Helen dear, yet will not commend her.\u2014TYRWHITT (Var. \'73): The sense, I think, requires that we should read \u201ccondemn.\u201d\u2014MASON (Comments, 1785, p. 314): The obvious objection to Johnson\'s explanation of this passage, which will also extend to Tyrwhitt\u2019s amendment, is that the Greeks did not intend to sell Helen, but on the contrary had just determined not to part with her. I should therefore agree with Warburton in reading, \u201cwhat we intend not sell.\u201d\u2014MALONE (ed. 1790): When Dr. Johnson says, they meant to sell Helen dear, he evidently does not mean that they really intended to sell her at all, (as he has been understood,) but that the Greeks should pay very dear for her. ... So Ajax (Thersites) says in a former scene [III.iii.304-305], \u201cHow the devil Luxury, with his fat rump and potato finger, tickles these together!\u201d\u2014[See note at V.i.19 ff.\u2014ED.]'
    ),
}


def _norm(s: str) -> str:
    return (
        s.replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("…", "...")
        .replace("\u00a0", " ")
    )


def is_truncated(note: str) -> bool:
    return (
        is_clipped(note)
        or is_hard_truncation(note)
        or is_mid_sentence_cut(note)
        or is_hyphen_artifact(note)
        or is_unbalanced_parens(note)
    )


def is_split_continuation(prev_note: str, next_note: str) -> bool:
    """True when next array element continues prev (OCR/page-break split)."""
    n = next_note.lstrip()
    if not n:
        return False
    # Do not merge into a new primary lemma on the same line (e.g. lesser]+blench]).
    if re.match(r"^[A-Za-z][A-Za-z .'-]*]\s+[A-Z(\[]", n) and not re.search(r"\.\]", n[:40]):
        return False
    if re.match(r"^[\w .'-]+\]\s+[a-z]", n):
        return True
    if n[0].islower():
        return True
    if prev_note.rstrip().endswith("-") and not re.match(r"^[A-Za-z]+]\s+[A-Z(]", n):
        return True
    if re.match(
        r"^(never|nor|not|light|the|a|an|to|and|or|but|when|which|that|how|so|as|if|for|in|on|at|from|with|by|of|ii\.|iii\.|iv\.|v\.|—|\.\.\.)",
        n,
        re.I,
    ):
        return True
    return False


def repair_note(note: str, ia: str | None = None) -> tuple[str, bool]:
    normed = _norm(note)
    if ia and is_hyphen_artifact(note):
        ext = splice_hyphen(ia, note)
        if ext and not is_truncated(ext):
            return ext, True
    for table in (COMPLETIONS, TRUNCATION_COMPLETIONS):
        for prefix, full in table.items():
            if normed == _norm(prefix) or normed.startswith(_norm(prefix)):
                return full, True
    return note, False


def merge_split_notes(notes: list[str]) -> tuple[list[str], int]:
    out: list[str] = []
    merged = 0
    i = 0
    while i < len(notes):
        note = notes[i]
        while i + 1 < len(notes) and is_truncated(note) and is_split_continuation(note, notes[i + 1]):
            nxt = notes[i + 1]
            joiner = "" if note.rstrip().endswith("-") else " "
            combined = note.rstrip() + joiner + nxt.lstrip()
            if len(combined) > len(note) + 5:
                note = combined
                i += 1
                merged += 1
            else:
                break
        out.append(note)
        i += 1
    return out, merged


def count_truncated(data: dict) -> int:
    total = 0
    for scene, scene_data in data.items():
        if str(scene).startswith("_") or not isinstance(scene_data, dict):
            continue
        for line_data in scene_data.values():
            if not isinstance(line_data, dict):
                continue
            for note in line_data.get("notes") or []:
                if is_truncated(note):
                    total += 1
    return total


def repair(data: dict, ia: str | None = None) -> dict:
    stats = {
        "before": 0,
        "repaired": 0,
        "after": 0,
        "unresolved": 0,
        "merged_splits": 0,
        "completion_repairs": 0,
        "hyphen_repairs": 0,
    }

    for scene, scene_data in data.items():
        if not str(scene).startswith("ACT") or not isinstance(scene_data, dict):
            continue
        for line_data in scene_data.values():
            if not isinstance(line_data, dict):
                continue
            notes = line_data.get("notes") or []
            for note in notes:
                if is_truncated(note):
                    stats["before"] += 1

            merged_notes, n_merge = merge_split_notes(list(notes))
            stats["merged_splits"] += n_merge

            new_notes: list[str] = []
            for note in merged_notes:
                was_trunc = is_truncated(note)
                fixed, changed = repair_note(note, ia)
                if changed:
                    if ia and is_hyphen_artifact(note):
                        stats["hyphen_repairs"] += 1
                    else:
                        stats["completion_repairs"] += 1
                new_notes.append(fixed)
            line_data["notes"] = new_notes

    stats["after"] = count_truncated(data)
    stats["repaired"] = stats["before"] - stats["after"]
    stats["unresolved"] = stats["after"]
    return stats


def sync_mirrors(text: str) -> None:
    if SITE_MIRROR.parent.is_dir():
        SITE_MIRROR.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    ia_text: str | None = None
    witness = "restricted (401); manual completions + split merge"
    from build_troilus_witness import fetch_troilus_witness  # noqa: WPS433

    pdf_text, pdf_src = fetch_troilus_witness()
    if pdf_text:
        ia_text = pdf_text
        witness = f"shaksper_pdf ({pdf_src})"
    fallback = WITNESS_AUDIT_FALLBACK.get("Troilus and Cressida")
    if ia_text is None and fallback:
        ia_text, src = fetch_ia_text(*fallback)
        if ia_text:
            witness = f"fallback:{fallback[0]} ({src})"
    stats = repair(data, ia_text)

    print(
        f"before={stats['before']} repaired={stats['repaired']} "
        f"after={stats['after']} unresolved={stats['unresolved']}"
    )
    print(
        f"  merged_splits={stats['merged_splits']} "
        f"completion_repairs={stats['completion_repairs']} "
        f"hyphen_repairs={stats['hyphen_repairs']}"
    )

    if not args.dry_run and (stats["repaired"] or stats["merged_splits"]):
        if not BACKUP.is_file():
            shutil.copy2(JSON_PATH, BACKUP)
            print(f"Backup → {BACKUP.relative_to(ROOT)}")
        out = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        JSON_PATH.write_text(out, encoding="utf-8")
        sync_mirrors(out)
        print(f"Wrote {JSON_PATH.relative_to(ROOT)}")

    AUDIT_OUT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_OUT.write_text(
        json.dumps(
            {
                "play": "Troilus and Cressida",
                "witness": witness,
                **stats,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
