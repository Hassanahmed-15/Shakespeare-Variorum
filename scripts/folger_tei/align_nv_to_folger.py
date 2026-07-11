#!/usr/bin/env python3
"""
Align legacy Variorum line objects (integer-string keys, old spelling) to Folger TEI spine units.

Uses difflib.SequenceMatcher on per-line normalized text within each scene.
Unmatched NV lines with notes are listed for manual review.

Does not delete notes: attaches to the best Folger anchor or leaves in review.
"""
from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


def normalize_for_match(play: str) -> str:
    """Strip speaker tag, brackets, collapse whitespace, lowercase, drop most punctuation."""
    s = (play or "").strip()
    s = re.sub(r"^\[[^\]]+\]\s*", "", s)
    s = re.sub(r"^[A-Za-z0-9 .'\[\]]+:\s*", "", s, count=1)
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s']+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _rom_to_int(s: str) -> int:
    s = s.strip().upper()
    if s.isdigit():
        return int(s)
    return {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7}.get(s, 0)


# Variorum JSON sometimes merges two Folger scenes. Values are ordered Folger scene keys.
# Keys are Folger publication ids (e.g. idno in TEI), so mappings do not leak across plays.
LEGACY_TO_FOLGER_SCENE_SEGMENTS: dict[str, dict[str, tuple[str, ...]]] = {
    "Oth": {
        # Herald (2.2) + Cyprus guard / drinking scene (2.3) appear under one legacy heading.
        "ACT 2, SCENE 2": ("ACT 2, SCENE 2", "ACT 2, SCENE 3"),
    },
}


def scene_key_normalize(key: str) -> str:
    """Match index.html normalizeSceneKey: ACT N, SCENE M (Arabic)."""
    n = key.strip()
    n = re.sub(r"ACT\s+(\d+)\s+SCENE\s+(\d+)", r"ACT \1, SCENE \2", n, flags=re.I)
    n = re.sub(r"ACT\s+I(?!I|V|X)\b", "ACT 1", n, flags=re.I)
    n = re.sub(r"ACT\s+II\b", "ACT 2", n, flags=re.I)
    n = re.sub(r"ACT\s+III\b", "ACT 3", n, flags=re.I)
    n = re.sub(r"ACT\s+IV\b", "ACT 4", n, flags=re.I)
    n = re.sub(r"ACT\s+V(?!I)\b", "ACT 5", n, flags=re.I)
    n = re.sub(r"SCENE\s+I(?!I|V|X)\b", "SCENE 1", n, flags=re.I)
    n = re.sub(r"SCENE\s+II\b", "SCENE 2", n, flags=re.I)
    n = re.sub(r"SCENE\s+III\b", "SCENE 3", n, flags=re.I)
    n = re.sub(r"SCENE\s+IV\b", "SCENE 4", n, flags=re.I)
    n = re.sub(r"SCENE\s+V(?!I)\b", "SCENE 5", n, flags=re.I)
    m = re.search(r"ACT\s+(\d+)\s*,\s*SCENE\s+(\d+)", n, re.I)
    if m:
        return f"ACT {int(m.group(1))}, SCENE {int(m.group(2))}"
    return key


def _ratio_score(a: str, b: str) -> float:
    """Blend character sequence similarity with token-sorted similarity (word-order drift)."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    r1 = SequenceMatcher(None, a, b).ratio()
    ta = " ".join(sorted(a.split()))
    tb = " ".join(sorted(b.split()))
    r2 = SequenceMatcher(None, ta, tb).ratio()
    score = max(r1, r2)
    # Short NV fragments often live inside a merged target line (e.g. MIT/Moby spine).
    if len(a) >= 4 and a in b:
        score = max(score, 0.92)
    elif len(b) >= 4 and b in a:
        score = max(score, 0.85)
    return score


def _best_fol_match(
    nv_norm: str,
    fn: list[str],
    search_indices: list[int],
    *,
    widen_to: list[int] | None = None,
    min_wide_ratio: float = 0.28,
) -> tuple[int, float]:
    """Pick the best Folger/MIT unit for one NV line; many NV lines may share one target."""
    best_j, best_r = -1, 0.0
    for fj in search_indices:
        r = _ratio_score(nv_norm, fn[fj])
        if r > best_r:
            best_r, best_j = r, fj
    if best_r < min_wide_ratio and widen_to:
        for fj in widen_to:
            if fj in search_indices:
                continue
            r = _ratio_score(nv_norm, fn[fj])
            if r > best_r:
                best_r, best_j = r, fj
    return best_j, best_r


def _folger_units_for_legacy_scene(
    spine_scenes: dict[str, list[dict[str, Any]]],
    norm_scene: str,
    play_id: str = "",
) -> tuple[list[dict[str, Any]], tuple[str, ...]]:
    """Return concatenated Folger units and which scene keys were used."""
    per_play = LEGACY_TO_FOLGER_SCENE_SEGMENTS.get(play_id, {})
    segs = per_play.get(norm_scene, (norm_scene,))
    units: list[dict[str, Any]] = []
    for sk in segs:
        units.extend(spine_scenes[sk])
    return units, segs


def align_scene(
    nv_lines: list[tuple[str, str, list[Any]]],
    fol_units: list[dict[str, Any]],
) -> tuple[dict[str, list[Any]], list[dict[str, Any]]]:
    """
    nv_lines: [(old_key, play_text, notes), ...]
    fol_units: spine units with 'play', 'anchor', 'kind'

    Returns (anchor -> merged notes list, review rows)
    """
    notes_by_anchor: dict[str, list[Any]] = {}
    review: list[dict[str, Any]] = []

    fol_plays = [u.get("play") or "" for u in fol_units]
    fol_anchors = []
    for u in fol_units:
        a = u.get("anchor") or ""
        if a.startswith("SD"):
            a = a.replace(" ", "_")
        fol_anchors.append(a)

    nv_keys = [x[0] for x in nv_lines]
    nv_plays = [x[1] for x in nv_lines]
    nv_notes = [x[2] for x in nv_lines]

    fn = [normalize_for_match(p) for p in fol_plays]
    vn = [normalize_for_match(p) for p in nv_plays]

    sm = SequenceMatcher(a=vn, b=fn, autojunk=False)
    matched_nv: set[int] = set()

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                ni, fj = i1 + k, j1 + k
                matched_nv.add(ni)
                anc = fol_anchors[fj]
                if nv_notes[ni]:
                    notes_by_anchor.setdefault(anc, []).extend(nv_notes[ni])
        elif tag == "replace":
            # Folger and MIT/Moby often disagree on line granularity inside a block.
            # Match each NV row to its best target (many NV -> one Folger/MIT is allowed).
            nv_block = list(range(i1, i2))
            fol_block = list(range(j1, j2))
            all_fol = list(range(len(fn)))
            for ni in nv_block:
                fnx = normalize_for_match(nv_plays[ni])
                if not fnx:
                    # Notes-only rows: keep local order inside the replace block.
                    pos = ni - nv_block[0]
                    best_j = fol_block[min(pos, len(fol_block) - 1)] if fol_block else -1
                    best_r = 0.4 if best_j >= 0 else 0.0
                else:
                    best_j, best_r = _best_fol_match(fnx, fn, fol_block, widen_to=all_fol)
                min_r = 0.22
                if len(fnx) < 12 and fnx:
                    min_r = 0.18
                if not fnx:
                    min_r = 0.0
                if best_j >= 0 and best_r >= min_r:
                    matched_nv.add(ni)
                    if nv_notes[ni]:
                        notes_by_anchor.setdefault(fol_anchors[best_j], []).extend(nv_notes[ni])
                elif nv_notes[ni]:
                    review.append(
                        {
                            "reason": "replace_block_unmatched_nv",
                            "nv_key": nv_keys[ni],
                            "notes": nv_notes[ni],
                            "best_ratio": round(best_r, 3),
                        }
                    )

    unmatched_idx = [i for i in range(len(nv_lines)) if i not in matched_nv and nv_notes[i]]
    n_nv = len(nv_lines)
    n_fol = len(fol_plays)

    for i in unmatched_idx:
        fn = normalize_for_match(nv_plays[i])
        best_j = -1
        best_r = 0.0
        for j, fp in enumerate(fol_plays):
            r = _ratio_score(fn, normalize_for_match(fp))
            if r > best_r:
                best_r, best_j = r, j

        min_r = 0.32
        if len(fn) < 12:
            min_r = 0.18
        if not fn:
            # Notes-only rows (no speech text): map by position in scene list
            if n_fol > 0 and n_nv > 0:
                best_j = min(n_fol - 1, round(i * (n_fol - 1) / max(n_nv - 1, 1)))
                best_r = 0.4
                min_r = 0.0

        if best_j >= 0 and best_r >= min_r:
            notes_by_anchor.setdefault(fol_anchors[best_j], []).extend(nv_notes[i])
        else:
            reason = "unmatched_nv_line_short" if len(fn) < 12 else "unmatched_nv_line"
            row = {
                "reason": reason,
                "nv_key": nv_keys[i],
                "play": nv_plays[i][:200],
                "notes": nv_notes[i],
                "best_ratio": round(best_r, 3),
            }
            review.append(row)

    return notes_by_anchor, review


def build_merged_play(
    spine: dict[str, Any],
    legacy: dict[str, Any],
    notes_by_anchor: dict[str, list[Any]],
) -> dict[str, Any]:
    """Build full JSON: DRAMATIS from legacy + Folger scenes with notes."""
    out: dict[str, Any] = {}
    if "DRAMATIS PERSONAE" in legacy:
        out["DRAMATIS PERSONAE"] = legacy["DRAMATIS PERSONAE"]

    for scene_key, units in spine["scenes"].items():
        scene_obj: dict[str, Any] = {}
        for u in units:
            anchor = u.get("anchor") or ""
            line_key = anchor.replace(" ", "_") if anchor.startswith("SD") else anchor
            play = u.get("play") or ""
            lookup = line_key if anchor.startswith("SD") else anchor
            notes = list(notes_by_anchor.get(lookup, []))
            scene_obj[line_key] = {
                "play": play,
                "notes": notes,
                "folgerAnchor": anchor,
                "kind": u.get("kind", "speech"),
            }
        out[scene_key] = scene_obj

    out["_meta"] = {
        "textSource": "Folger Digital Texts TEI (CC BY-NC)",
        "playId": spine.get("play_id"),
        "alignment": "nv_notes_mapped_by_scene_text_similarity",
        "legacySceneSegments": LEGACY_TO_FOLGER_SCENE_SEGMENTS.get(spine.get("play_id") or "", {}),
    }
    return out


def apply_note_overrides(merged: dict[str, Any], overrides: dict[str, Any] | None) -> None:
    """Apply optional JSON moves (e.g. Public/Data/othello_note_overrides.json)."""
    if not overrides:
        return
    raw = overrides.get("moves") or []
    if not raw:
        return
    meta = merged.setdefault("_meta", {})
    applied: list[dict[str, str]] = []

    for m in raw:
        scene = m.get("scene")
        from_k = m.get("fromLineKey")
        to_k = m.get("toLineKey")
        needle = (m.get("noteContains") or "").strip()
        reason = (m.get("reason") or "").strip()
        if not scene or not from_k or not to_k or not needle:
            continue
        sc = merged.get(scene)
        if not isinstance(sc, dict) or from_k not in sc or to_k not in sc:
            continue
        kept: list[Any] = []
        moved: list[Any] = []
        for n in sc[from_k].get("notes") or []:
            (moved if needle in str(n) else kept).append(n)
        if not moved:
            continue
        sc[from_k]["notes"] = kept
        sc[to_k].setdefault("notes", []).extend(moved)
        applied.append(
            {
                "from": f"{scene} / {from_k}",
                "to": f"{scene} / {to_k}",
                "matchedBy": needle[:120],
                "reason": reason,
            }
        )

    if applied:
        meta["noteOverridesApplied"] = applied
        meta["noteOverridesVersion"] = overrides.get("version")


def run_align(
    tei_path: Path,
    legacy_path: Path,
    out_path: Path,
    review_path: Path,
    overrides_path: Path | None = None,
) -> None:
    from scripts.folger_tei.ingest_folger_tei import parse_folger_play  # noqa: WPS433

    spine = parse_folger_play(tei_path)
    legacy = json.loads(legacy_path.read_text(encoding="utf-8"))

    notes_by_anchor: dict[str, list[Any]] = {}
    all_review: list[dict[str, Any]] = []
    play_id = spine.get("play_id") or ""

    for raw_key, scene_data in legacy.items():
        if raw_key == "DRAMATIS PERSONAE" or raw_key.startswith("_"):
            continue
        if not isinstance(scene_data, dict):
            continue
        norm = scene_key_normalize(raw_key)
        per_play = LEGACY_TO_FOLGER_SCENE_SEGMENTS.get(play_id, {})
        segs = per_play.get(norm, (norm,))
        missing = [s for s in segs if s not in spine["scenes"]]
        if missing:
            all_review.append(
                {
                    "reason": "legacy_scene_not_in_folger_spine",
                    "scene": raw_key,
                    "normalized": norm,
                    "missing_segments": missing,
                }
            )
            continue

        nv_lines: list[tuple[str, str, list[Any]]] = []
        for lk in sorted(scene_data.keys(), key=lambda x: int(x) if str(x).isdigit() else 9999):
            ent = scene_data[lk]
            if not isinstance(ent, dict):
                continue
            play = ent.get("play") or ""
            notes = ent.get("notes") or []
            if not play and not notes:
                continue
            nv_lines.append((str(lk), play, notes))

        fol_units, _seg_keys = _folger_units_for_legacy_scene(spine["scenes"], norm, play_id)
        merged_notes, review = align_scene(nv_lines, fol_units)
        for anc, lst in merged_notes.items():
            notes_by_anchor.setdefault(anc, []).extend(lst)
        for r in review:
            r["scene"] = norm
            if "folger_segments" not in r:
                r["folger_segments"] = list(segs)
        all_review.extend(review)

    merged = build_merged_play(spine, legacy, notes_by_anchor)

    overrides_data: dict[str, Any] | None = None
    if overrides_path is not None and overrides_path.is_file():
        overrides_data = json.loads(overrides_path.read_text(encoding="utf-8"))
        op = overrides_path.resolve()
        try:
            idx = op.parts.index("Public")
            rel = "/".join(op.parts[idx:])
        except ValueError:
            rel = str(overrides_path)
        merged.setdefault("_meta", {})["noteOverridesFile"] = rel
    apply_note_overrides(merged, overrides_data)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(merged, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    review_path.write_text(json.dumps(all_review, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path} and {review_path}")


def run_othello(
    tei_path: Path,
    legacy_path: Path,
    out_path: Path,
    review_path: Path,
    overrides_path: Path | None = None,
) -> None:
    """Backward-compatible name for run_align."""
    run_align(tei_path, legacy_path, out_path, review_path, overrides_path=overrides_path)


def main() -> None:
    import argparse
    import sys
    from pathlib import Path as P

    root = P(__file__).resolve().parents[2]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    default_overrides = root / "Public/Data/othello_note_overrides.json"

    ap = argparse.ArgumentParser(
        description="Align legacy Variorum JSON line notes to Folger TEI anchors and emit merged play JSON."
    )
    ap.add_argument("--tei", type=Path, required=True, help="Folger TEI XML for the play")
    ap.add_argument("--legacy", type=Path, required=True, help="Legacy Variorum JSON (integer line keys)")
    ap.add_argument("--out", type=Path, required=True, help="Output merged JSON path")
    ap.add_argument("--review", type=Path, required=True, help="Alignment review JSON path")
    ap.add_argument(
        "--overrides",
        type=Path,
        default=None,
        help=f"Note moves JSON (defaults to {default_overrides} when that file exists)",
    )
    ap.add_argument(
        "--no-overrides",
        action="store_true",
        help="Do not load or apply note overrides",
    )
    args = ap.parse_args()

    ov: Path | None = None
    if not args.no_overrides:
        path = args.overrides if args.overrides is not None else default_overrides
        if path.is_file():
            ov = path

    run_align(args.tei, args.legacy, args.out, args.review, overrides_path=ov)


if __name__ == "__main__":
    main()
