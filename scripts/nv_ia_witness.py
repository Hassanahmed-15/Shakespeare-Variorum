"""Internet Archive NV witness fetch/cache and fuzzy note-matching utilities."""

from __future__ import annotations

import re
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IA_CACHE_DIR = ROOT / "data" / "ia_cache"
UA = "Mozilla/5.0 (compatible; nv-ia-witness/2.0; +https://github.com/)"
MIN_CACHE_BYTES = 50_000

SYNTHETIC_RE = re.compile(
    r"^(Editorial note|Annotation|Gloss|Note|Textual|Lexical|Critical note|Dramatic note|Editorial comment):",
    re.I,
)
PARAPHRASE_RE = re.compile(
    r"(notes various|discussion of|Debate among|Explanatory note|On the colloquial|and other editors note)",
    re.I,
)
CROSS_REF_RE = re.compile(
    r"(?:^|\]\s*)(?:See|cf\.|Cp\.|Compare)\s+[IVXLC\d]+[\s.,;]",
    re.I,
)
SHORT_GLOSS_RE = re.compile(
    r"^[^\]]+\]\s*(?:That is,|I\.e\.|i\.e\.|Sc\.|viz\.).{0,120}\.?\s*$",
    re.I,
)

EXACT_THRESHOLD = 0.95
HIGH_THRESHOLD = 0.75
PARTIAL_THRESHOLD = 0.45


def fold_apostrophe(s: str) -> str:
    return s.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')


def cache_path(ia_id: str, stream: str) -> Path:
    return IA_CACHE_DIR / stream


def _download_url(ia_id: str, stream: str) -> str:
    return f"https://archive.org/download/{ia_id}/{stream}"


def _fetch_via_curl(url: str, dest: Path, *, timeout: int = 120) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    subprocess.run(
        [
            "curl", "-fsSL", "-A", UA,
            "--max-time", str(timeout),
            "-o", str(tmp),
            url,
        ],
        check=True,
        capture_output=True,
    )
    if tmp.stat().st_size < MIN_CACHE_BYTES:
        size = tmp.stat().st_size
        tmp.unlink(missing_ok=True)
        raise OSError(f"download too small ({size} bytes)")
    tmp.replace(dest)


def fetch_ia_text(ia_id: str, stream: str, *, force: bool = False) -> tuple[str | None, str]:
    """Return (witness text, source label). Uses data/ia_cache when present."""
    path = cache_path(ia_id, stream)
    url = _download_url(ia_id, stream)
    if path.is_file() and path.stat().st_size > MIN_CACHE_BYTES and not force:
        return path.read_text(encoding="utf-8", errors="replace"), str(path)
    try:
        _fetch_via_curl(url, path)
        return path.read_text(encoding="utf-8", errors="replace"), url
    except Exception as curl_exc:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as resp:
                text = resp.read().decode("utf-8", errors="replace")
            if len(text) < MIN_CACHE_BYTES:
                raise OSError(f"body too small ({len(text)} bytes)")
            IA_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            return text, url
        except Exception as urllib_exc:
            if path.is_file() and path.stat().st_size > MIN_CACHE_BYTES:
                return (
                    path.read_text(encoding="utf-8", errors="replace"),
                    f"{path} (stale; fetch failed: {curl_exc}; {urllib_exc})",
                )
            return None, f"{url} ({curl_exc}; {urllib_exc})"


def is_cross_ref_note(note: str) -> bool:
    n = note.strip()
    if CROSS_REF_RE.search(n):
        tail = n.split("]")[-1].strip() if "]" in n else n
        return len(tail) < 80
    if re.search(r"\]\s*See\s+", n, re.I) and len(n) < 90:
        return True
    return False


def is_short_gloss(note: str) -> bool:
    n = note.strip()
    if len(n) > 120:
        return False
    if SHORT_GLOSS_RE.match(n):
        return True
    if "]" in n and len(n) < 70 and not SYNTHETIC_RE.match(n):
        body = n.split("]", 1)[1].strip()
        return len(body) < 55 and body.endswith(".")
    return False


def ia_match_score(ia_text: str, note: str) -> float:
    """0.0–1.0 overlap vs IA witness (flexible whitespace + word-bag fallback)."""
    if is_cross_ref_note(note) or is_short_gloss(note):
        return 1.0

    note_clean = re.sub(r"\s+", " ", note.strip())
    body = note_clean[note_clean.index("]") + 1 :].strip() if "]" in note_clean else note_clean
    folded_ia = fold_apostrophe(ia_text)

    for size in (100, 80, 60, 45, 30):
        if len(body) < size:
            continue
        words = re.findall(r"[A-Za-z0-9']+", fold_apostrophe(body[:size]))
        if len(words) < 4:
            continue
        pat = re.compile(r"\s+".join(re.escape(w) for w in words[:14]), re.I)
        if pat.search(folded_ia):
            return 1.0

    critic = re.match(r"^[A-Za-z .'-]+:\s*(.{30,120})", note_clean)
    needle = (critic.group(1) if critic else note_clean[:80]).strip(" \"'[]")
    if len(needle) >= 20 and fold_apostrophe(needle).lower() in folded_ia.lower():
        return 1.0

    words = [w for w in re.findall(r"[A-Za-z']{4,}", fold_apostrophe(body.lower())[:140])[:14]]
    if not words:
        return 0.0
    ia_low = folded_ia.lower()
    return sum(1 for w in words if w in ia_low) / len(words)


def classify_match(score: float) -> str:
    if score >= EXACT_THRESHOLD:
        return "exact"
    if score >= HIGH_THRESHOLD:
        return "high"
    if score >= PARTIAL_THRESHOLD:
        return "partial"
    return "fail"


def score_note_sample(ia_text: str, notes: list[str]) -> dict:
    buckets = {"exact": 0, "high": 0, "partial": 0, "fail": 0, "cross_ref": 0, "short_gloss": 0}
    for note in notes:
        if is_cross_ref_note(note):
            buckets["cross_ref"] += 1
            buckets["exact"] += 1
            continue
        if is_short_gloss(note):
            buckets["short_gloss"] += 1
            buckets["high"] += 1
            continue
        bucket = classify_match(ia_match_score(ia_text, note))
        buckets[bucket] += 1
    n = len(notes) or 1
    return {
        "buckets": buckets,
        "sample_n": len(notes),
        "exact_pct": round(100 * buckets["exact"] / n, 1),
        "exact_high_pct": round(100 * (buckets["exact"] + buckets["high"]) / n, 1),
        "partial_pct": round(100 * buckets["partial"] / n, 1),
        "fail_pct": round(100 * buckets["fail"] / n, 1),
    }
