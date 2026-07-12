#!/usr/bin/env python3
"""
Parse MIT/Moby Shakespeare HTML (shakespeare.mit.edu) into a linear spine,
in the same shape scripts/folger_tei/ingest_folger_tei.py's parse_folger_play()
returns, so the existing alignment code (align_scene, build_merged_play,
apply_note_overrides in scripts/folger_tei/align_nv_to_folger.py) can consume
either source unchanged.

MIT HTML structure (per-play "full.html" page):
  <H3>ACT I</h3>
  <h3>SCENE I. Venice. A street.</h3>
  <p><blockquote><i>Enter RODERIGO and IAGO</i></blockquote>
  <A NAME=speech1><b>RODERIGO</b></a>
  <blockquote>
  <A NAME=1.1.1>Tush! never tell me; I take it much unkindly</A><br>
  ...
  </blockquote>

Speech lines carry their own act.scene.line anchor (e.g. "1.1.1"). Stage
directions have no per-line anchor, so this parser synthesizes one:
SD_<act>.<scene>.<n> where n increments per stage direction within the scene,
mirroring the "SD_1.1.0" convention already used for Folger-sourced stage
directions.

License: MIT's HTML texts are placed in the public domain.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

ROMAN_ACT = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}


def _roman_to_int(s: str) -> int | None:
    s = s.strip().upper()
    if s.isdigit():
        return int(s)
    return ROMAN_ACT.get(s)


class _MITPlayParser(HTMLParser):
    """Streaming parser that walks MIT's full.html sequentially, tracking
    current act/scene/speaker and emitting spine units in document order."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.scenes: dict[str, list[dict[str, Any]]] = {}
        self._cur_scene_key: str | None = None
        self._cur_act: int | None = None
        self._cur_scene_num: int | None = None
        self._sd_counter = 0

        self._tag_stack: list[str] = []
        self._buf: list[str] = []
        self._capture: str | None = None  # "h3act" | "h3scene" | "b" | "a" | "i"
        self._cur_speaker = ""
        self._cur_anchor: str | None = None
        self._pending_units: list[dict[str, Any]] = []

    # -- helpers -----------------------------------------------------
    def _flush_text(self) -> str:
        t = "".join(self._buf).strip()
        t = re.sub(r"\s+", " ", t)
        self._buf = []
        return t

    def _add_unit(self, unit: dict[str, Any]) -> None:
        if self._cur_scene_key is None:
            return
        self.scenes.setdefault(self._cur_scene_key, []).append(unit)

    def _set_scene(self, act: int, scene: int) -> None:
        self._cur_act = act
        self._cur_scene_num = scene
        self._cur_scene_key = f"ACT {act}, SCENE {scene}"
        self._sd_counter = 0

    # -- HTMLParser hooks ---------------------------------------------
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        adict = {k.lower(): v for k, v in attrs}
        if tag == "h3":
            self._buf = []
            self._capture = "h3"
        elif tag == "b":
            self._buf = []
            self._capture = "b"
        elif tag == "i":
            self._buf = []
            self._capture = "i"
        elif tag == "a":
            name = adict.get("name") or ""
            if re.match(r"^\d+\.\d+\.\d+$", name):
                self._cur_anchor = name
                self._buf = []
                self._capture = "a"
            else:
                self._cur_anchor = None

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "h3":
            text = self._flush_text()
            m_act = re.match(r"^ACT\s+([IVX]+|\d+)\b", text, re.I)
            m_scene = re.match(r"^SCENE\s+([IVX]+|\d+)\b", text, re.I)
            if m_act:
                act_n = _roman_to_int(m_act.group(1))
                if act_n is not None:
                    self._cur_act = act_n
            elif m_scene and self._cur_act is not None:
                scene_n = _roman_to_int(m_scene.group(1))
                if scene_n is not None:
                    self._set_scene(self._cur_act, scene_n)
            self._capture = None
        elif tag == "b":
            text = self._flush_text()
            if text:
                self._cur_speaker = text.rstrip(":").strip()
            self._capture = None
        elif tag == "i":
            text = self._flush_text()
            self._capture = None
            if text and self._cur_scene_key is not None:
                self._sd_counter += 1
                anchor = f"SD_{self._cur_act}.{self._cur_scene_num}.{self._sd_counter}"
                self._add_unit(
                    {
                        "kind": "stage",
                        "anchor": anchor.replace("SD_", "SD "),
                        "text": text,
                        "play": f"[{text}]",
                    }
                )
        elif tag == "a" and self._capture == "a":
            text = self._flush_text()
            self._capture = None
            if self._cur_anchor and text:
                speaker = self._cur_speaker
                play = f"{speaker}: {text}" if speaker else text
                self._add_unit(
                    {
                        "kind": "speech",
                        "anchor": self._cur_anchor,
                        "speaker": speaker,
                        "text": text,
                        "play": play,
                    }
                )
            self._cur_anchor = None

    def handle_data(self, data: str) -> None:
        if self._capture is not None:
            self._buf.append(data)


def parse_mit_play(path: Path) -> dict[str, Any]:
    html = path.read_text(encoding="iso-8859-1", errors="replace")
    parser = _MITPlayParser()
    parser.feed(html)
    parser.close()

    title_m = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
    title = re.sub(r"\s+", " ", title_m.group(1)).strip() if title_m else path.stem

    return {
        "title": title,
        "play_id": path.stem,
        "source_file": path.name,
        "scenes": parser.scenes,
    }


def main() -> None:
    import argparse
    import json
    import sys

    ap = argparse.ArgumentParser(description="Parse MIT/Moby Shakespeare HTML to JSON spine")
    ap.add_argument("html_file", type=Path)
    ap.add_argument("-o", "--output", type=Path, required=True)
    args = ap.parse_args()
    spine = parse_mit_play(args.html_file)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(spine, ensure_ascii=False, indent=2), encoding="utf-8")
    n_units = sum(len(v) for v in spine["scenes"].values())
    print(f"Wrote {args.output} ({len(spine['scenes'])} scenes, {n_units} units)", file=sys.stderr)


if __name__ == "__main__":
    main()
