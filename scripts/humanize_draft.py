#!/usr/bin/env python3
"""Iteratively revise a draft until Pangram classifies it as high-confidence human.

Workflow (each round):
  1. Write the current draft to draft.md in the workspace.
  2. Call check_pangram(path="draft.md") for AI fraction, label, and flagged segments.
  3. Revise draft.md to lower the AI score while keeping content complete and tone intact.
  4. Repeat until the draft passes the human threshold, then write the final output.

Requires:
  - PANGRAM_API_KEY
  - OPENAI_API_KEY

Usage:
  python scripts/humanize_draft.py path/to/input.md
  python scripts/humanize_draft.py uploads/my_essay.docx
  python scripts/humanize_draft.py uploads/my_paper.pdf
  python scripts/humanize_draft.py path/to/input.md --output polished.md --max-rounds 20
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKSPACE = ROOT / "validation" / "humanize_workspace"
DEFAULT_UPLOADS = ROOT / "uploads"
DEFAULT_MAX_FRACTION_AI = 0.05
DEFAULT_MAX_ROUNDS = 20
DEFAULT_MODEL = "gpt-4o"


@dataclass
class PangramVerdict:
    fraction_ai: float
    fraction_ai_assisted: float
    fraction_human: float
    label: str
    headline: str
    prediction: str
    flagged_segments: list[dict]
    full_result: dict

    @property
    def fraction_ai_percent(self) -> float:
        return round(self.fraction_ai * 100, 2)


def load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.is_file():
        return
    raw = env_path.read_bytes()
    for enc in ("utf-8-sig", "utf-16", "utf-16-le", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        return
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_document_text(input_path: Path) -> str:
    """Extract plain text from .txt, .md, .docx, or .pdf files."""
    suffix = input_path.suffix.lower()

    if suffix in {".txt", ".md", ".markdown", ".text"}:
        return input_path.read_text(encoding="utf-8")

    if suffix == ".docx":
        try:
            from docx import Document
        except ImportError as exc:
            raise RuntimeError(
                "python-docx is not installed. Run: pip3 install -r requirements_humanize.txt"
            ) from exc
        doc = Document(str(input_path))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        if not paragraphs:
            raise RuntimeError(f"No readable text found in Word file: {input_path}")
        return "\n\n".join(paragraphs)

    if suffix == ".pdf":
        try:
            import pdfplumber
        except ImportError as exc:
            raise RuntimeError(
                "pdfplumber is not installed. Run: pip3 install -r requirements_humanize.txt"
            ) from exc
        pages: list[str] = []
        with pdfplumber.open(str(input_path)) as pdf:
            for page in pdf.pages:
                text = (page.extract_text() or "").strip()
                if text:
                    pages.append(text)
        if not pages:
            raise RuntimeError(
                f"No readable text found in PDF: {input_path}. "
                "Scanned/image PDFs may need OCR first."
            )
        return "\n\n".join(pages)

    raise RuntimeError(
        f"Unsupported file type '{suffix}'. Use .txt, .md, .docx, or .pdf."
    )


def check_pangram(file_path: str | Path, *, timeout: float = 120.0) -> PangramVerdict:
    """Classify text with Pangram and return a normalized verdict."""
    try:
        from pangram import Pangram
    except ImportError as exc:
        raise RuntimeError(
            "pangram-sdk is not installed. Run: pip install -r requirements_humanize.txt"
        ) from exc

    api_key = os.environ.get("PANGRAM_API_KEY")
    if not api_key:
        raise RuntimeError("PANGRAM_API_KEY is not set.")

    text = Path(file_path).read_text(encoding="utf-8")
    client = Pangram(api_key=api_key)
    try:
        result = client.predict(text=text, public_dashboard_link=False, timeout=timeout)
    except TypeError:
        result = client.predict(text=text, public_dashboard_link=False)
    if not isinstance(result, dict):
        result = dict(result)

    windows = result.get("windows") or []
    flagged = []
    for window in windows:
        score = float(window.get("ai_assistance_score") or 0.0)
        label = str(window.get("label") or "")
        confidence = str(window.get("confidence") or "")
        label_lower = label.lower()
        looks_ai = score >= 0.35 or ("ai" in label_lower and "human" not in label_lower)
        if looks_ai:
            flagged.append(
                {
                    "text": window.get("text") or "",
                    "label": label,
                    "confidence": confidence,
                    "ai_assistance_score": score,
                    "start_index": window.get("start_index"),
                    "end_index": window.get("end_index"),
                }
            )

    flagged.sort(key=lambda item: item["ai_assistance_score"], reverse=True)

    return PangramVerdict(
        fraction_ai=float(result.get("fraction_ai") or 0.0),
        fraction_ai_assisted=float(result.get("fraction_ai_assisted") or 0.0),
        fraction_human=float(result.get("fraction_human") or 0.0),
        label=str(result.get("prediction_short") or result.get("label") or ""),
        headline=str(result.get("headline") or ""),
        prediction=str(result.get("prediction") or ""),
        flagged_segments=flagged,
        full_result=result,
    )


def is_high_confidence_human(
    verdict: PangramVerdict,
    *,
    max_fraction_ai: float = DEFAULT_MAX_FRACTION_AI,
) -> bool:
    """Return True when Pangram reports high-confidence human classification."""
    if verdict.label != "Human":
        return False
    if verdict.fraction_ai > max_fraction_ai:
        return False

    headline = verdict.headline.lower()
    if "fully human" not in headline and "human written" not in headline:
        return False

    for segment in verdict.flagged_segments:
        if segment.get("confidence") != "High":
            continue
        score = float(segment.get("ai_assistance_score") or 0.0)
        label = str(segment.get("label") or "").lower()
        if score >= 0.35 and "human" not in label:
            return False

    return True


def format_flagged_segments(segments: list[dict], *, limit: int = 12) -> str:
    if not segments:
        return "(none flagged)"
    lines = []
    for idx, segment in enumerate(segments[:limit], start=1):
        snippet = " ".join(str(segment.get("text") or "").split())
        if len(snippet) > 320:
            snippet = snippet[:317] + "..."
        lines.append(
            f"{idx}. score={segment.get('ai_assistance_score'):.2f}, "
            f"confidence={segment.get('confidence')}, label={segment.get('label')}\n"
            f"   \"{snippet}\""
        )
    if len(segments) > limit:
        lines.append(f"... and {len(segments) - limit} more flagged segments")
    return "\n".join(lines)


def call_openai(system_prompt: str, user_prompt: str, *, model: str = DEFAULT_MODEL) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    body = json.dumps(
        {
            "model": model,
            "temperature": 0.7,
            "max_tokens": 8192,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API error {exc.code}: {detail}") from exc

    choices = payload.get("choices") or []
    if not choices:
        raise RuntimeError("OpenAI API returned no choices.")
    content = choices[0].get("message", {}).get("content", "")
    if not content.strip():
        raise RuntimeError("OpenAI API returned empty content.")
    return content.strip()


REVISION_SYSTEM_PROMPT = """You are a careful human editor revising prose so it reads naturally.

Rules:
- Preserve ALL factual content, claims, examples, and structure from the draft.
- Keep the tone, register, and voice as close as possible to the original.
- Do not add new arguments, remove sections, or shorten the piece materially.
- Focus rewrites on passages that sound generic, formulaic, or machine-polished.
- Prefer concrete wording, varied sentence rhythm, and natural transitions.
- Return ONLY the full revised document. No commentary, no markdown fences."""


def revise_draft(
    draft_text: str,
    verdict: PangramVerdict,
    *,
    model: str = DEFAULT_MODEL,
) -> str:
    user_prompt = textwrap.dedent(
        f"""\
        Pangram AI detector results for the current draft:
        - Overall label: {verdict.label}
        - Headline: {verdict.headline}
        - AI fraction: {verdict.fraction_ai_percent:.1f}%
        - AI-assisted fraction: {verdict.fraction_ai_assisted * 100:.1f}%
        - Human fraction: {verdict.fraction_human * 100:.1f}%

        Flagged segments (edit these first, but keep the whole piece coherent):
        {format_flagged_segments(verdict.flagged_segments)}

        Full draft to revise:
        ---
        {draft_text}
        ---
        """
    )
    revised = call_openai(REVISION_SYSTEM_PROMPT, user_prompt, model=model)
    if revised.startswith("```"):
        revised = revised.strip("`")
        if revised.lower().startswith("markdown"):
            revised = revised[8:].lstrip()
        revised = revised.strip()
        if revised.endswith("```"):
            revised = revised[:-3].rstrip()
    return revised


def finish(
    *,
    workspace: Path,
    output_path: Path,
    verdict: PangramVerdict,
    rounds: int,
    summary_path: Path | None = None,
) -> dict:
    draft_path = workspace / "draft.md"
    final_text = draft_path.read_text(encoding="utf-8")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(final_text, encoding="utf-8")

    summary = {
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "rounds": rounds,
        "output_path": str(output_path),
        "draft_path": str(draft_path),
        "verdict": {
            "label": verdict.label,
            "headline": verdict.headline,
            "fraction_ai_percent": verdict.fraction_ai_percent,
            "fraction_ai_assisted_percent": round(verdict.fraction_ai_assisted * 100, 2),
            "fraction_human_percent": round(verdict.fraction_human * 100, 2),
            "flagged_segment_count": len(verdict.flagged_segments),
        },
    }
    if summary_path:
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def run_humanize_loop(
    input_path: Path,
    *,
    output_path: Path,
    workspace: Path,
    max_rounds: int,
    max_fraction_ai: float,
    model: str,
) -> dict:
    workspace.mkdir(parents=True, exist_ok=True)
    draft_path = workspace / "draft.md"
    log_path = workspace / "rounds.jsonl"

    original = load_document_text(input_path)
    draft_path.write_text(original, encoding="utf-8")

    verdict = check_pangram(draft_path)
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(
            json.dumps(
                {
                    "round": 0,
                    "phase": "initial",
                    "verdict": asdict(verdict),
                },
                default=str,
            )
            + "\n"
        )

    print(f"Initial Pangram: {verdict.label} ({verdict.headline})")
    print(f"  AI fraction: {verdict.fraction_ai_percent:.1f}%")
    print(f"  Flagged segments: {len(verdict.flagged_segments)}")

    if is_high_confidence_human(verdict, max_fraction_ai=max_fraction_ai):
        print("Draft already passes as high-confidence human.")
        return finish(
            workspace=workspace,
            output_path=output_path,
            verdict=verdict,
            rounds=0,
            summary_path=workspace / "summary.json",
        )

    for round_num in range(1, max_rounds + 1):
        print(f"\nRound {round_num}/{max_rounds}: revising flagged segments...")
        current = draft_path.read_text(encoding="utf-8")
        revised = revise_draft(current, verdict, model=model)
        if revised.strip() == current.strip():
            print("Revision returned unchanged text; stopping early.")
            break

        draft_path.write_text(revised, encoding="utf-8")
        verdict = check_pangram(draft_path)
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(
                json.dumps(
                    {
                        "round": round_num,
                        "phase": "post_revision",
                        "verdict": asdict(verdict),
                    },
                    default=str,
                )
                + "\n"
            )

        print(f"  Pangram: {verdict.label} ({verdict.headline})")
        print(f"  AI fraction: {verdict.fraction_ai_percent:.1f}%")
        print(f"  Flagged segments: {len(verdict.flagged_segments)}")

        if is_high_confidence_human(verdict, max_fraction_ai=max_fraction_ai):
            print("\nTarget reached: high-confidence human classification.")
            return finish(
                workspace=workspace,
                output_path=output_path,
                verdict=verdict,
                rounds=round_num,
                summary_path=workspace / "summary.json",
            )

    print(f"\nStopped after {max_rounds} rounds without reaching the target.")
    return finish(
        workspace=workspace,
        output_path=output_path,
        verdict=verdict,
        rounds=max_rounds,
        summary_path=workspace / "summary.json",
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Revise a document until Pangram classifies it as high-confidence human."
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to the uploaded draft (.txt, .md, .docx, or .pdf)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Final output path (default: <input_stem>.humanized<suffix> next to input)",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=DEFAULT_WORKSPACE,
        help=f"Working directory for draft.md and logs (default: {DEFAULT_WORKSPACE})",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=DEFAULT_MAX_ROUNDS,
        help=f"Maximum revision rounds (default: {DEFAULT_MAX_ROUNDS})",
    )
    parser.add_argument(
        "--max-fraction-ai",
        type=float,
        default=DEFAULT_MAX_FRACTION_AI,
        help=f"Maximum allowed AI fraction, 0-1 (default: {DEFAULT_MAX_FRACTION_AI})",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"OpenAI model for revisions (default: {DEFAULT_MODEL})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    args = parse_args(argv)

    input_path = args.input.expanduser().resolve()
    if not input_path.is_file():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    output_path = args.output
    if output_path is None:
        if input_path.suffix.lower() in {".docx", ".pdf"}:
            output_path = input_path.with_name(f"{input_path.stem}.humanized.txt")
        else:
            output_path = input_path.with_name(f"{input_path.stem}.humanized{input_path.suffix}")
    else:
        output_path = output_path.expanduser().resolve()

    try:
        summary = run_humanize_loop(
            input_path,
            output_path=output_path,
            workspace=args.workspace.expanduser().resolve(),
            max_rounds=args.max_rounds,
            max_fraction_ai=args.max_fraction_ai,
            model=args.model,
        )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print("\nDone.")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
