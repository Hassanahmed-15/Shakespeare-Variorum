#!/usr/bin/env python3
"""Prep (and eventually run) true Stage-1 Tesseract vs deployed ablation.

Revision-round scaffold: anchors sample notes in IA witness, estimates pages,
emits fetch URLs. Full OCR + segmentation is --pilot / --run (requires tesseract
or rapidocr + network).

See validation/nv_true_ocr_ablation_recipe.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_nv_fidelity_all_plays import PLAYS  # noqa: E402
from audit_nv_witness_sample import find_start, iter_note_records, locate_note  # noqa: E402
from audit_nv_stage_ablation import (  # noqa: E402
    categorize_edit,
    summarize_verification,
    tail_verify_note,
)
from audit_nv_fullspan_sample import classify_note  # noqa: E402
from nv_ia_witness import fold_apostrophe  # noqa: E402
from nv_witness_map import WITNESS_BY_PLAY  # noqa: E402
from verify_all_notes import build_chunks, get_witness, norm  # noqa: E402

MANIFEST = ROOT / "validation" / "nv_stage_ablation_manifest.json"
OUT_DIR = ROOT / "validation"
PAGE_CACHE = ROOT / "data" / "page_cache"


def load_manifest() -> list[dict]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return data["notes"]


def play_spec(play_name: str) -> dict:
    for spec in PLAYS:
        if spec["play"] == play_name:
            return spec
    raise KeyError(play_name)


def note_row(play_name: str, ref: str) -> dict | None:
    spec = play_spec(play_name)
    data = json.loads((ROOT / spec["json"]).read_text(encoding="utf-8"))
    for row in iter_note_records(data):
        if row["ref"] == ref:
            return row
    return None


def ia_page_image_url(ia_id: str, leaf: int) -> str:
    jp2 = f"{ia_id}_{leaf:04d}.jp2"
    return (
        f"https://archive.org/download/{ia_id}/{ia_id}_jp2/{jp2}"
    )


def estimate_leaf(char_offset: int, witness_len: int, leaf_count: int = 600) -> int:
    """Rough leaf estimate when scandata not loaded. Replace in --run with scandata.xml."""
    if witness_len <= 0:
        return 1
    leaf = int((char_offset / witness_len) * leaf_count) + 1
    return max(1, min(leaf, leaf_count))


def prep_row(entry: dict) -> dict:
    play = entry["play"]
    ref = entry["ref"]
    row = note_row(play, ref)
    if row is None:
        return {"play": play, "ref": ref, "error": "note_not_in_deployed_json"}

    note = row["note"]
    spec = play_spec(play)
    witness_text, witness_src = get_witness(play)
    if witness_text is None:
        return {"play": play, "ref": ref, "error": f"witness_unavailable: {witness_src}"}

    folded = fold_apostrophe(witness_text)
    located = locate_note(folded, note)
    start = find_start(folded, note)
    char_offset = located if located is not None else (start.start() if start else None)

    ia_id, _stream = WITNESS_BY_PLAY.get(play, ("", ""))
    leaf = estimate_leaf(char_offset or 0, len(folded)) if char_offset is not None else None

    return {
        "play": play,
        "ref": ref,
        "json": spec["json"],
        "deployed_note_len": len(note),
        "deployed_opening": note[:120],
        "witness_src": witness_src,
        "witness_char_offset": char_offset,
        "anchor_found": char_offset is not None,
        "ia_id": ia_id or None,
        "estimated_leaf": leaf,
        "page_image_url": ia_page_image_url(ia_id, leaf) if ia_id and leaf else None,
        "stage2_note": note,
        "status": "prepared",
    }


def extract_segment_from_page_ocr(page_ocr: str, deployed_note: str) -> tuple[str, str, float]:
    """Witness-anchored fuzzy slice from full-page OCR (segmentation v0)."""
    from rapidfuzz import fuzz

    body = deployed_note
    if "]" in body[:80]:
        body = body.split("]", 1)[1].strip()
    probe = body[:60].strip()
    if len(probe) < 15:
        probe = deployed_note[:60]

    best_score = 0.0
    best_idx = -1
    folded_page = fold_apostrophe(page_ocr)
    probe_fold = fold_apostrophe(probe)
    for i in range(0, max(1, len(folded_page) - len(probe_fold)), 8):
        window = folded_page[i : i + len(probe_fold) + 40]
        score = fuzz.partial_ratio(probe_fold.lower(), window.lower())
        if score > best_score:
            best_score = score
            best_idx = i

    if best_idx < 0 or best_score < 80:
        return "", "opening_not_found", best_score

    end = min(len(page_ocr), best_idx + int(len(deployed_note) * 1.2) + 80)
    segment = page_ocr[best_idx:end].strip()
    # Trim at next critic/line-number boundary
    tail = page_ocr[best_idx:end]
    m = re.search(
        r"\n\s*\d+\.\s+[A-Z]|\n\s*[A-Z][A-Z .'-]{2,28}:\]|\n\s*[A-Z][A-Z .'-]{2,28}:",
        tail[len(probe) :],
    )
    if m:
        segment = tail[: len(probe) + m.start()].strip()
    return segment, "opening_fuzzy_match", best_score


def ocr_page_image(image_path: Path) -> str:
    """Try tesseract, then rapidocr."""
    import subprocess

    try:
        proc = subprocess.run(
            ["tesseract", str(image_path), "stdout", "--oem", "1", "--psm", "4", "-l", "eng"],
            check=True,
            capture_output=True,
            text=True,
        )
        return proc.stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    try:
        from rapidocr_onnxruntime import RapidOCR  # type: ignore

        ocr = RapidOCR()
        result, _ = ocr(str(image_path))
        return "\n".join(line[1] for line in (result or []))
    except ImportError as exc:
        raise RuntimeError("Install tesseract or rapidocr-onnxruntime") from exc


def fetch_page(url: str, dest: Path) -> bool:
    import urllib.request

    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "nv-true-ocr-ablation/1.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            dest.write_bytes(resp.read())
        return dest.is_file() and dest.stat().st_size > 1000
    except Exception:
        return False


def run_pilot(prepared: list[dict], n: int) -> list[dict]:
    """Fetch + OCR + segment for first N anchored rows."""
    out = []
    for row in prepared:
        if len(out) >= n:
            break
        if row.get("error") or not row.get("page_image_url"):
            continue
        ia_id = row["ia_id"]
        leaf = row["estimated_leaf"]
        cache_img = PAGE_CACHE / ia_id / f"{leaf:04d}.jpg"
        url = row["page_image_url"].replace(".jp2", "")  # try jp2 direct first
        if not cache_img.is_file():
            ok = fetch_page(row["page_image_url"], cache_img.with_suffix(".jp2"))
            if not ok:
                # IIIF JPEG fallback
                iiif = (
                    f"https://iiif.archive.org/iiif/{ia_id}%2F{ia_id}_jp2%2F{ia_id}_{leaf:04d}.jp2"
                    f"/full/full/0/default.jpg"
                )
                ok = fetch_page(iiif, cache_img)
            if not ok:
                row["pilot_error"] = "page_fetch_failed"
                out.append(row)
                continue

        img = cache_img if cache_img.is_file() else cache_img.with_suffix(".jp2")
        try:
            page_ocr = ocr_page_image(img)
        except RuntimeError as exc:
            row["pilot_error"] = str(exc)
            out.append(row)
            continue

        segment, method, conf = extract_segment_from_page_ocr(page_ocr, row["stage2_note"])
        row["stage1_segment"] = segment
        row["segment_method"] = method
        row["segment_confidence"] = conf
        row["stage1_segment_len"] = len(segment)
        out.append(row)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="Anchor + page URLs only")
    ap.add_argument("--pilot", type=int, default=0, help="OCR+segment N notes (network)")
    ap.add_argument("--manifest", type=Path, default=MANIFEST)
    args = ap.parse_args()

    entries = json.loads(args.manifest.read_text(encoding="utf-8"))["notes"]
    prepared = [prep_row(e) for e in entries]
    anchored = sum(1 for r in prepared if r.get("anchor_found"))

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest": str(args.manifest),
        "sample_n": len(entries),
        "anchored_n": anchored,
        "recipe": "validation/nv_true_ocr_ablation_recipe.md",
        "rows": prepared,
    }

    out_path = OUT_DIR / "nv_true_ocr_ablation_page_map.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {out_path} ({len(entries)} notes, {anchored} anchored)")

    if args.dry_run and not args.pilot:
        print("Dry run complete. See recipe for --pilot / --run.")
        return 0

    if args.pilot:
        pilot_rows = run_pilot(prepared, args.pilot)
        pilot_path = OUT_DIR / "nv_true_ocr_ablation_pilot.json"
        pilot_path.write_text(json.dumps(pilot_rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        ok = sum(1 for r in pilot_rows if r.get("stage1_segment"))
        print(f"Pilot: {ok}/{len(pilot_rows)} segments extracted → {pilot_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
