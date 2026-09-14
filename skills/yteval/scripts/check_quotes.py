#!/usr/bin/env python3
"""Quote-fidelity gate: every quote in a writeup must exist in its transcript.

Usage:
    python3 check_quotes.py <run-dir> [--window N]

<run-dir> is a report directory containing report.md / onepager.md and a
transcripts/ subdirectory of <ID>.md files produced by vtt_to_md.py.

Why this check exists
---------------------
Transcripts are gitignored, so the quotes in report.md are the only evidence a
reader will ever see. A fabricated `[12:34] "..."` is invisible to every other
check in the pipeline, and invisible to the reader forever. Every other
acceptance criterion can be satisfied by a well-formed empty report; this is the
one that can't.

What counts as a quote
----------------------
A double-quoted span on a line that also carries a [MM:SS] or [HH:MM:SS]
timestamp, and can be attributed to a video. Attribution comes from an <ID> on
the same line, or failing that from the nearest preceding line naming one.

Quotes with no timestamp cannot be checked, and the count of those is reported
alongside the verified count. It used to be silent, which was the worst possible
behaviour for this particular gate: a 633-line report carrying 93 quoted spans
passed as "19 quotes verified", and nothing said the other 74 had been skipped.
An unverifiable quote is exactly what a fabricated one looks like, so the two
must never be reported as one number.

Not every unchecked quote is a defect — a report may legitimately quote vendor
documentation, which is not in any transcript. That is why a high skip count
fails rather than every skip: the run needs a human to look, not a rule that
cries wolf.

Matching is deliberately forgiving about presentation and strict about words:
case, whitespace, and typographic quotes/dashes are normalised away; the word
sequence must then appear verbatim in the transcript.

Rolling captions mean a quote often spans several cues, so the transcript is
searched as one normalised stream restricted to a window of cues around the
cited timestamp (default +/-3).

Exit status
-----------
0  every quote verified, and most quotes were checkable
1  at least one quote failed, or more quotes were unchecked than verified
2  bad usage, or the run directory is missing transcripts
"""

import re
import sys
import unicodedata
from pathlib import Path

TS = re.compile(r"\[(?:(\d+):)?(\d{1,2}):(\d{2})\]")
QUOTE = re.compile(r"[\"“]([^\"“”]{12,})[\"”]")
# Not \b-delimited: a YouTube ID may start or end with "-", and \b never matches
# between a backtick and a hyphen, so `-WBHNFAB0OE` would be missed entirely and the
# quote silently checked against whichever video was named on an earlier line. That
# misattribution can produce a false PASS as easily as a false failure.
VIDEO_ID = re.compile(r"(?<![A-Za-z0-9_-])([A-Za-z0-9_-]{11})(?![A-Za-z0-9_-])")
CUE = re.compile(r"^\[(\d{2,}):(\d{2})\]\s*(.*)$")

# Quotes shorter than this many characters are skipped: short fragments match
# by coincidence and would make the gate noisy without making it stronger.
MIN_QUOTE_CHARS = 12


def normalise(text):
    """Collapse presentation differences, keep the word sequence."""
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("—", "-").replace("–", "-")
    text = re.sub(r"[^\w\s']", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def load_transcript(path):
    """Return a list of (seconds, normalised_text) cues."""
    cues = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = CUE.match(line)
        if m:
            minutes, seconds = int(m.group(1)), int(m.group(2))
            cues.append((minutes * 60 + seconds, normalise(m.group(3))))
    return cues


def seconds_of(match):
    hours, minutes, seconds = match.groups()
    total = int(minutes) * 60 + int(seconds)
    return total + int(hours) * 3600 if hours else total


def find_quotes(doc_path, known_ids):
    """Yield (video_id | None, seconds | None, quote_text) per quote.

    seconds is None when the quote carries no timestamp. Those are unverifiable
    rather than wrong, so they are yielded to be counted, never dropped.
    """
    current = None
    for line in doc_path.read_text(encoding="utf-8").splitlines():
        ids = [i for i in VIDEO_ID.findall(line) if i in known_ids]
        if ids:
            current = ids[0]

        # A line often carries several quotes, each with its own attribution
        # trailing it: "...a..." (`ID1` [00:22]); "...b..." (`ID2` [12:21]).
        # Taking the line's first ID and first timestamp for every quote on it
        # checks the later quotes against the wrong video at the wrong offset —
        # which can pass a misattributed quote as easily as it can fail a good
        # one. Pair each quote with the attribution that follows it instead.
        quotes = list(QUOTE.finditer(line))
        for i, q in enumerate(quotes):
            text = q.group(1).strip()
            if len(text) < MIN_QUOTE_CHARS:
                continue
            tail = line[
                q.end() : quotes[i + 1].start() if i + 1 < len(quotes) else len(line)
            ]
            ts = TS.search(tail) or TS.search(line)
            if not ts:
                yield None, None, text
                continue
            near = [v for v in VIDEO_ID.findall(tail) if v in known_ids]
            yield (near[0] if near else current), seconds_of(ts), text


def verify(quote, cues, at_seconds, window):
    """True if the quote's words appear in the cue window around at_seconds."""
    target = normalise(quote)
    if not target:
        return True

    idx = min(
        range(len(cues)),
        key=lambda i: abs(cues[i][0] - at_seconds),
        default=None,
    )
    if idx is None:
        return False

    lo, hi = max(0, idx - window), min(len(cues), idx + window + 1)
    # Rolling captions repeat the previous cue's tail, so a quote can straddle
    # cue boundaries. Joining the window into one stream is what makes those
    # quotes verifiable at all.
    stream = " ".join(text for _, text in cues[lo:hi])
    if target in stream:
        return True

    # Fall back to the whole transcript before failing: a correct quote with a
    # slightly-off timestamp is a citation defect, not a fabrication, and the
    # two deserve different words in the failure report.
    whole = " ".join(text for _, text in cues)
    if target in whole:
        return "TIMESTAMP"
    return False


def main():
    argv = sys.argv[1:]
    window = 3
    if "--window" in argv:
        i = argv.index("--window")
        window = int(argv[i + 1])
        del argv[i : i + 2]
    args = [a for a in argv if not a.startswith("--")]

    if len(args) != 1:
        sys.exit(__doc__)

    run_dir = Path(args[0])
    tdir = run_dir / "transcripts"
    if not tdir.is_dir():
        sys.exit(f"no transcripts/ directory under {run_dir}")

    transcripts = {p.stem: load_transcript(p) for p in sorted(tdir.glob("*.md"))}
    if not transcripts:
        sys.exit(f"no transcript .md files in {tdir}")

    failures, unchecked, checked = [], [], 0
    for name in ("report.md", "onepager.md"):
        doc = run_dir / name
        if not doc.exists():
            continue
        for vid, seconds, quote in find_quotes(doc, set(transcripts)):
            if seconds is None:
                unchecked.append((name, quote))
                continue
            checked += 1
            if vid is None:
                failures.append((name, "?", seconds, quote, "unattributed"))
                continue
            result = verify(quote, transcripts[vid], seconds, window)
            if result == "TIMESTAMP":
                failures.append((name, vid, seconds, quote, "wrong timestamp"))
            elif not result:
                failures.append((name, vid, seconds, quote, "not in transcript"))

    coverage = f"{checked} verified, {len(unchecked)} unchecked (no timestamp)"

    if failures:
        print(
            f"QUOTE FIDELITY FAILED — {len(failures)} of {checked} checkable quotes\n"
        )
        for doc, vid, seconds, quote, why in failures:
            stamp = f"[{seconds // 60:02d}:{seconds % 60:02d}]"
            print(f"  {doc}  {vid} {stamp}  {why}")
            print(f'    "{quote[:100]}"')
        print(f"\ncoverage: {coverage}")
        print("The transcripts are gitignored, so these quotes are the only")
        print("evidence a reader gets. Fix them before finalising.")
        return 1

    if len(unchecked) > checked:
        print(f"QUOTE COVERAGE TOO LOW — {coverage}\n")
        for doc, quote in unchecked[:10]:
            print(f'  {doc}  "{quote[:90]}"')
        if len(unchecked) > 10:
            print(f"  … and {len(unchecked) - 10} more")
        print(
            "\nEvery quote that passed was genuine, but most were never checked.\n"
            "Give video quotes a [MM:SS] so the gate can see them. Quotes from\n"
            "documentation or other non-transcript sources are fine to leave —\n"
            "confirm that is what these are before overriding."
        )
        return 1

    print(f"quote fidelity OK — {coverage}, across {len(transcripts)} transcripts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
