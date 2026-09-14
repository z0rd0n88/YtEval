# Triage — merge, rank, and account for everything

You receive every video's extraction output and **no transcripts**. You produce the claim
set that the two verification tiers will work from.

Everything downstream verifies only what you pass through. A claim you drop is never
checked by anything, ever, and no later stage can notice the omission. That is why this
runs on the session model and why the drop-log below is not optional.

## 1. Merge duplicates across videos

Three videos asserting the same fact become **one claim carrying three attributions**
(`video_id`, `timestamp`, `quote` for each). Verify once, report three times.

Merge on the assertion, not the wording. "Opus 5 has a 1M context window" and "you get a
million tokens of context with Opus 5" are one claim. If two claims differ in any checkable
particular — a different number, a different version, a different date — they are two
claims, however similar they read.

**A merged claim was not dropped.** Count dedupes in their own line. A log that folds them
into the drop count misrepresents its own coverage in the direction that flatters it.

## 2. Rank by load-bearing-ness

One question: **would the report's conclusions change if this claim were false?**

That is not the same as "is this interesting" or "is this likely wrong". A claim can be
central and obviously true; it still ranks high, because the report leans on it.

The top of this ranking goes to the adversarial depth tier, up to the run's
`depth_ceiling`. Everything checkable goes to the breadth screen regardless of rank.

Rank honestly rather than defensively. The promotion path exists precisely because the
surprises are never in the load-bearing set: "load-bearing" means you already knew it
mattered, so a ranking optimised to look thorough just verifies your own priors. Claims
the breadth screen doubts get promoted later, and when the ceiling binds they **outrank**
merely load-bearing claims — a claim something has doubted is a better use of an
adversarial slot than one nobody has questioned.

## 3. Emit the drop-log and the projected fan-out

Before the expensive tiers spend anything. Both to chat and into the run state.

Group drops by reason, because the groups mean different things and a blanket header would
be wrong for at least one of them:

- **not load-bearing** — still screened by the breadth tier; verdict `Screened`.
- **not checkable** — excluded from **both** tiers, never checked at all. This is the group
  the log exists to be honest about.
- **depth ceiling reached** — screened only. A budget artifact, not a judgment, and worth
  overriding. **Name the closest miss explicitly** ("ranked 16th of 15") so a reader can
  see whether the ceiling actually bit.

```
TRIAGE — 47 claims extracted across 4 videos
  → 9 deduped (asserted by more than one video, verified once)
  → 14 promoted to depth tier
  → 24 to breadth tier only
  → projected fan-out: 3 breadth + 42 depth = 45 agents

NOT ADVERSARIALLY VERIFIED (24)

  [not load-bearing · 19] — screened by the breadth tier, verdict: Screened
    ZVMTeDBmSrI [04:12]  "pandas is faster than raw loops here"

  [not checkable · 4] — excluded from BOTH tiers, never checked at all
    6I1wGCuFpbk [11:03]  "this architecture feels cleaner"

  [depth ceiling reached · 1] — screened only; budget artifact, worth overriding
    Fag2QTB2Vd8 [19:55]  "most retail traders lose money"
      ranked 16th of 15 — closest miss
```

Every extracted claim appears exactly once across the merged set and the drop-log. If the
counts do not reconcile, the log is wrong — fix it before returning.

## Output

Write the merged claim set, the ranking, and the drop-log to the output path given in your
task, then return the block above as your final message so it reaches the chat.
