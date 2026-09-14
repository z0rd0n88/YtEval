#!/usr/bin/env python3
"""Self-check for check_quotes.py. Run: python3 test_check_quotes.py

Guards the two false-PASS bugs this gate has actually shipped. Both mattered
more than a crash would have: a quote checked against the wrong transcript can
be reported as verified when it is not, and transcripts are gitignored, so no
reader can ever catch it.

1. A video ID beginning with "-" was invisible to a \\b-delimited pattern, so
   attribution fell through to whichever video was named earlier in the file.
2. Several quotes on one line all inherited the line's FIRST id and timestamp,
   so the later ones were checked against the wrong video at the wrong offset.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

GATE = Path(__file__).with_name("check_quotes.py")

TRANSCRIPTS = {
    "SFh6MMe-XcM": "[12:19] tasks it burns 4x less\n[12:21] tasks it burns 4x less tokens than\n",
    "5nB8Rs4l0_M": "[00:20] and how you can use it to build 10 times\n[00:22] faster. And at the end\n",
    # Leading "-" is the default case, not an edge case: three stages of this
    # pipeline have shipped a bug on it.
    "-WBHNFAB0OE": "[24:16] running. He's got 10 threads\n[24:18] running. He's got 10 threads running at most based on his post.\n",
}


def run(report_text):
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = Path(tmp)
        (run_dir / "transcripts").mkdir()
        for vid, text in TRANSCRIPTS.items():
            (run_dir / "transcripts" / f"{vid}.md").write_text(text, encoding="utf-8")
        (run_dir / "report.md").write_text(report_text, encoding="utf-8")
        done = subprocess.run(
            [sys.executable, str(GATE), str(run_dir)], capture_output=True, text=True
        )
        return done.returncode, done.stdout + done.stderr


def check(name, report, want_ok):
    code, out = run(report)
    ok = code == 0
    if ok != want_ok:
        print(f"FAIL {name}: exit={code}\n{out}")
        return False
    print(f"ok   {name}")
    return True


def main():
    results = [
        check(
            "verbatim quote passes",
            'A: "tasks it burns 4x less tokens than" (`SFh6MMe-XcM` [12:21]).\n',
            True,
        ),
        check(
            "dash-prefixed id attributes correctly",
            'B: "running. He\'s got 10 threads running at most based on his post." (`-WBHNFAB0OE` [24:16]).\n',
            True,
        ),
        check(
            "two quotes on one line keep their own attributions",
            'C: "and how you can use it to build 10 times" (`5nB8Rs4l0_M` [00:20]); '
            '"tasks it burns 4x less tokens than" (`SFh6MMe-XcM` [12:21]).\n',
            True,
        ),
        check(
            "crossed attribution fails",
            'D: "tasks it burns 4x less tokens than" (`5nB8Rs4l0_M` [00:22]).\n',
            False,
        ),
        check(
            "fabricated quote fails",
            'E: "this sentence was never spoken by anyone" (`SFh6MMe-XcM` [12:21]).\n',
            False,
        ),
        # A report whose quotes mostly carry no timestamp used to pass while the
        # gate silently skipped them, reporting only the handful it could check.
        # An unverifiable quote looks exactly like a fabricated one.
        check(
            "mostly-untimestamped report fails on coverage",
            'F: "tasks it burns 4x less tokens than" (`SFh6MMe-XcM` [12:21]).\n'
            'He also said "the agent handles the whole workflow end to end".\n'
            'And "you never have to touch the configuration again".\n'
            'And "it saved me several hours every single day".\n',
            False,
        ),
        # The same untimestamped quotes are fine when most quotes ARE checkable:
        # reports legitimately quote documentation, which is in no transcript.
        check(
            "a minority of untimestamped quotes still passes",
            'G: "tasks it burns 4x less tokens than" (`SFh6MMe-XcM` [12:21]); '
            '"and how you can use it to build 10 times" (`5nB8Rs4l0_M` [00:20]); '
            '"running. He\'s got 10 threads running at most based on his post." '
            "(`-WBHNFAB0OE` [24:16]).\n"
            'The docs say "hooks run before the tool call".\n',
            True,
        ),
    ]
    if not all(results):
        sys.exit(1)
    print(f"\nall {len(results)} checks passed")


if __name__ == "__main__":
    main()
