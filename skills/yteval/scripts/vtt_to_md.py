#!/usr/bin/env python3
"""Convert a YouTube auto-caption .vtt into the repo's readable transcript .md.

Usage:
    python3 vtt_to_md.py <input.vtt> <output.md> [info.json]

The optional info.json is yt-dlp's `--write-info-json` output; when present its
title / uploader / webpage_url / duration_string populate the metadata header.

Rules (these reproduce the committed transcripts exactly):
  - keep every caption cue, in order, prefixed with [MM:SS] of its start time
  - strip inline karaoke tags (<00:00:01.234>, <c>, </c>)
  - drop empty cues
  - drop a cue whose text is identical to the previous kept cue
Rolling-caption overlap is deliberately NOT collapsed: the duplicated phrases
are what makes the timestamps line up with the video, and the house standard is
a verbatim transcript.
"""

import json
import re
import sys

TAG = re.compile(r"<[^>]+>")
CUE = re.compile(r"^(\d\d):(\d\d):(\d\d)\.\d+\s+-->")


def parse_cues(vtt_text):
    """Yield (seconds, text) for each caption cue in a WebVTT document."""
    for block in vtt_text.replace("\r\n", "\n").split("\n\n"):
        lines = block.strip().split("\n")
        if not lines:
            continue
        m = CUE.match(lines[0])
        if not m:
            continue
        h, mi, s = (int(x) for x in m.groups())
        text = TAG.sub("", " ".join(lines[1:])).strip()
        text = re.sub(r"\s+", " ", text)
        if text:
            yield h * 3600 + mi * 60 + s, text


def to_markdown(vtt_text, info=None):
    lines = []
    if info:
        lines.append(f"# {info.get('title', 'Untitled')}\n")
        lines.append(f"- **Channel:** {info.get('uploader', 'unknown')}")
        lines.append(f"- **URL:** {info.get('webpage_url', '')}")
        lines.append(f"- **Duration:** {info.get('duration_string', '')}")
        lines.append(
            "- **Transcript source:** YouTube auto-generated captions (verbatim, unedited)\n"
        )
        lines.append("---\n")

    prev = None
    for seconds, text in parse_cues(vtt_text):
        if text == prev:
            continue
        prev = text
        lines.append(f"[{seconds // 60:02d}:{seconds % 60:02d}] {text}")
    return "\n".join(lines) + "\n"


def main():
    if not 3 <= len(sys.argv) <= 4:
        sys.exit(__doc__)
    vtt_path, md_path = sys.argv[1], sys.argv[2]
    info = None
    if len(sys.argv) == 4:
        with open(sys.argv[3], encoding="utf-8") as fh:
            info = json.load(fh)

    with open(vtt_path, encoding="utf-8") as fh:
        markdown = to_markdown(fh.read(), info)
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(markdown)

    body = sum(1 for line in markdown.splitlines() if line.startswith("["))
    print(f"{md_path}: {body} caption lines")


if __name__ == "__main__":
    main()
