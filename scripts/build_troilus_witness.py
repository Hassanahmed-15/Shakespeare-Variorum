#!/usr/bin/env python3
"""Build Troilus NV witness text from SHAKSPER PDF OCR cache."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDF_CANDIDATES = [
    Path("/tmp/troilus_nv.pdf"),
    ROOT / "data/troilus_nv.pdf",
]
OUT = ROOT / "data/troilus_nv_witness.txt"
MIN_BYTES = 200_000


def find_pdf() -> Path | None:
    for p in PDF_CANDIDATES:
        if p.is_file() and p.stat().st_size > 1_000_000:
            return p
    return None


def build_witness(*, force: bool = False) -> tuple[str | None, str]:
    if OUT.is_file() and OUT.stat().st_size > MIN_BYTES and not force:
        return OUT.read_text(encoding="utf-8", errors="replace"), str(OUT)

    pdf = find_pdf()
    if pdf is None:
        return None, "no PDF at /tmp/troilus_nv.pdf or data/troilus_nv.pdf"

    text: str | None = None
    try:
        proc = subprocess.run(
            ["pdftotext", "-layout", str(pdf), "-"],
            check=True,
            capture_output=True,
            text=True,
        )
        text = proc.stdout
    except FileNotFoundError:
        try:
            from pypdf import PdfReader  # type: ignore[import-untyped]

            reader = PdfReader(str(pdf))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:
            return None, f"PDF extract failed: {exc}"
    except subprocess.CalledProcessError as exc:
        return None, f"pdftotext failed: {exc.stderr[:200]}"

    if not text or len(text) < MIN_BYTES:
        return None, f"extracted text too small ({len(text or '')} bytes)"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    return text, str(OUT)


def fetch_troilus_witness() -> tuple[str | None, str]:
    """Return cached SHAKSPER PDF witness when available."""
    return build_witness()


def main() -> int:
    text, src = build_witness(force="--force" in sys.argv)
    if text is None:
        print(f"ERROR: {src}", file=sys.stderr)
        return 1
    print(f"Witness: {len(text):,} chars from {src}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
