#!/usr/bin/env python3
"""Download and cache Internet Archive djvu.txt witnesses for all 22 NV plays."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_nv_fidelity_all_plays import PLAYS  # noqa: E402
from nv_ia_witness import fetch_ia_text  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true", help="Re-download even if cached")
    args = ap.parse_args()

    ok = fail = 0
    for spec in PLAYS:
        text, src = fetch_ia_text(spec["ia"], spec["ia_stream"], force=args.force)
        if text:
            ok += 1
            print(f"OK  {spec['play']:<32} {len(text):>9,} chars  {src}")
        else:
            fail += 1
            print(f"FAIL {spec['play']:<32} {src}")
    print(f"\nCached {ok}/{len(PLAYS)} witnesses under data/ia_cache/")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
