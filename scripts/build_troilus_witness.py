#!/usr/bin/env python3
"""Build Troilus NV witness text from the 1953 Vol. 26 PDF (image scan)."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Original download: Variorum Shakespeare Vol. 26 Troilus and Cressida 1953 (1).pdf
DEFAULT_PDF = ROOT / "data/troilus_nv_1953.pdf"
PDF_CANDIDATES = [
    DEFAULT_PDF,
    Path("/tmp/troilus_nv.pdf"),
    ROOT / "data/troilus_nv.pdf",
]
OUT = ROOT / "data/troilus_nv_witness.txt"
MIN_BYTES = 200_000


def resolve_pdf(explicit: Path | None = None) -> Path | None:
    if explicit is not None and explicit.is_file():
        return explicit
    for p in PDF_CANDIDATES:
        if p.is_file() and p.stat().st_size > 1_000_000:
            return p
    return None


def _extract_pdftotext(pdf: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["pdftotext", "-layout", str(pdf), "-"],
            check=True,
            capture_output=True,
            text=True,
        )
        return proc.stdout
    except FileNotFoundError:
        return None
    except subprocess.CalledProcessError:
        return None


def _extract_pypdf(pdf: Path) -> str | None:
    try:
        from pypdf import PdfReader  # type: ignore[import-untyped]

        reader = PdfReader(str(pdf))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return None


def _extract_rapidocr(pdf: Path, *, zoom: float = 2.0) -> str | None:
    try:
        import fitz  # type: ignore[import-untyped]
        from rapidocr_onnxruntime import RapidOCR  # type: ignore[import-untyped]
    except ImportError as exc:
        return None

    doc = fitz.open(pdf)
    ocr = RapidOCR()
    matrix = fitz.Matrix(zoom, zoom)
    parts: list[str] = []
    with tempfile.TemporaryDirectory(prefix="troilus_ocr_") as tmpdir:
        tmp = Path(tmpdir)
        for i in range(len(doc)):
            pix = doc[i].get_pixmap(matrix=matrix)
            img_path = tmp / f"p{i:04d}.png"
            pix.save(str(img_path))
            result, _ = ocr(str(img_path))
            t = "\n".join(line[1] for line in (result or []))
            parts.append(t)
            if (i + 1) % 50 == 0:
                print(f"OCR page {i + 1}/{len(doc)}", file=sys.stderr, flush=True)
    return "\n\n".join(parts)


def build_witness(
    *,
    force: bool = False,
    pdf_path: Path | None = None,
    method: str | None = None,
) -> tuple[str | None, str]:
    if OUT.is_file() and OUT.stat().st_size > MIN_BYTES and not force:
        return OUT.read_text(encoding="utf-8", errors="replace"), str(OUT)

    pdf = resolve_pdf(pdf_path)
    if pdf is None:
        return None, f"no PDF (tried {DEFAULT_PDF}, /tmp/troilus_nv.pdf, data/troilus_nv.pdf)"

    text: str | None = None
    used = "unknown"
    if method in (None, "pdftotext"):
        text = _extract_pdftotext(pdf)
        if text and len(text) >= MIN_BYTES:
            used = f"pdftotext:{pdf}"
    if (not text or len(text) < MIN_BYTES) and method in (None, "pypdf"):
        text = _extract_pypdf(pdf)
        if text and len(text) >= MIN_BYTES:
            used = f"pypdf:{pdf}"
    if not text or len(text) < MIN_BYTES:
        ocr_text = _extract_rapidocr(pdf)
        if ocr_text:
            text = ocr_text
            used = f"rapidocr+pymupdf:{pdf}"
        elif method == "rapidocr":
            return None, "rapidocr failed (install: pip install pymupdf rapidocr-onnxruntime)"

    if not text or len(text) < MIN_BYTES:
        return None, (
            f"extracted text too small ({len(text or '')} bytes); "
            "image PDF needs OCR (pdftotext/pypdf empty). "
            "Try: pip install pymupdf rapidocr-onnxruntime && "
            "python scripts/build_troilus_witness.py --force"
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    return text, used


def fetch_troilus_witness() -> tuple[str | None, str]:
    """Return cached 1953 PDF witness when available."""
    return build_witness()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true", help="Rebuild even if cache is large enough")
    ap.add_argument(
        "--pdf",
        type=Path,
        default=None,
        help="Path to 1953 Troilus NV PDF (default: data/troilus_nv_1953.pdf)",
    )
    ap.add_argument(
        "--method",
        choices=("pdftotext", "pypdf", "rapidocr"),
        default=None,
        help="Force a single extraction method",
    )
    args = ap.parse_args()
    text, src = build_witness(force=args.force, pdf_path=args.pdf, method=args.method)
    if text is None:
        print(f"ERROR: {src}", file=sys.stderr)
        return 1
    print(f"Witness: {len(text):,} chars via {src}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
