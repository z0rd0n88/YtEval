# Output format

## Directory

```
docs/reports/<YYYY-MM-DD>-yteval-<slug>/
├── README.md
├── report.md
├── onepager.md
└── transcripts/          # gitignored
    ├── <ID>.en.vtt
    └── <ID>.md
```

Transients the run creates and stage 11 deletes: `<ID>.info.json`, `<ID>.fetch.log`,
`.verdicts.json`, `*.pre-trim.md.bak`.

Keep generated output in its own directory, separate from hand-written docs. Dated,
re-runnable output is a different class of thing, and mixing the two makes it impossible
to tell at a glance which files a re-run is allowed to overwrite.

## `README.md`

Four parts, in order:

1. **One-line verdict** — what the batch concluded.
2. **File index** — `./onepager.md` (scannable) and `./report.md` (full), each with one
   line on when to read it. Relative filenames; the directory already carries the date.
3. **Source table** — `| Title (linked) | Channel | Duration | Uploaded | Status |`,
   where Status is `covered`, `downgraded (reason)`, or `failed (reason)`. **Every input
   video appears**, including failures — a partial report that reads as complete is the
   failure mode this table prevents.
4. **Run provenance** — the manifest as given, the date, agent counts per stage, and the
   models used. Enough to re-run it, or to explain a cost line a month later.

## `report.md`

Technical register. Section order, following the house pattern in
`docs/trading-bot-videos/report.md`:

```
# <Title>
## Executive summary
## Contents
## Method                     ← includes "Attempted but not covered: N videos (reason)"
## Per-video verdicts
## Verified claims            ← the verdict table
## Synthesis / blueprint
## What to ignore
## Red-flags appendix
## Claims considered but not verified   ← the triage drop-log
## Sources
```

Two requirements beyond the shape:

**Every verdict-table row names its tier.** A `Screened` row and a `Verified` row did not
get the same scrutiny; rendering them identically overstates confidence.

**A breadth flag rate is never a finding.** "39% of claims were flagged" is a statement
about the screen, not about the videos, and it reads as the opposite. Report counts the
reader can audit: how many `false`/`stale` verdicts carry a cited source, and how many
`unsupported`/`misleading` verdicts were judged from the claim's own text. If the
screen's overturn rate blew past the stage 6–7 thresholds, the Method section says so and
gives the number — a report whose own instrument failed and doesn't mention it is the
worst output this pipeline can produce.

**The drop-log appendix is not optional** whenever anything was dropped. Version
controlled, travelling with the conclusions it qualifies, it is what makes the report
honest about its own coverage.

## `onepager.md`

Fully plain language — no jargon, short sentences, the same facts. It is the file
someone reads instead of the report, not a teaser for it.

## The triage drop-log

Printed to chat at stage 5 **and** written into `report.md` as the appendix above.

Group by reason, because the groups mean different things: *not load-bearing* and *not
checkable* drops are usually correct and boring, while **depth ceiling reached** is a
budget artifact worth overriding. Name the closest miss explicitly so it is visible
whether the ceiling actually bit.

Each group states its own coverage. A blanket "screened, not adversarially verified"
header would be wrong for `not checkable` claims, which were excluded from both tiers and
never checked at all — and that is precisely the group the log exists to be honest about.

```
TRIAGE — 47 claims extracted across 4 videos
  → 9 deduped (asserted by more than one video, verified once)
  → 14 promoted to depth tier
  → 24 to breadth tier only
  → projected fan-out: 3 breadth + 42 depth = 45 agents

NOT ADVERSARIALLY VERIFIED (24)

  [not load-bearing · 19] — screened by the breadth tier, verdict: Screened
    ZVMTeDBmSrI [04:12]  "pandas is faster than raw loops here"
    y_bsjZThP0o [22:40]  "I use VS Code for this part"

  [not checkable · 4] — excluded from BOTH tiers, never checked at all
    6I1wGCuFpbk [11:03]  "this architecture feels cleaner"

  [depth ceiling reached · 1] — screened only; budget artifact, worth overriding
    Fag2QTB2Vd8 [19:55]  "most retail traders lose money"
      ranked 16th of 15 — closest miss
```

Rows are illustrative. Dedupes are counted separately from drops: a claim verified once
on behalf of three videos was not dropped.
