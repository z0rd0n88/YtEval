# Agent prompt requirements

Every agent returns JSON matching `references/schemas.md` and nothing else.

**Four roles ship as literal prompts under `prompts/` and are copied verbatim, never
composed:** extraction, triage, breadth, depth. For those, this file records only what the
individual task message must supply — the run-specific values a shipped file cannot carry.
The remaining two (stage 4b, stage 8) specify required content, not wording.

The reason four of six are shipped rather than described is that describing them failed
once, measurably: see the breadth section below.

## Extraction agent (stage 4) — no model override, `prompts/extraction.md`

Task message supplies: the transcript path, the output path, and **run-state metadata** —
`video_id`, `title`, `channel`, `url`, `upload_date`, `duration`. Paste
`references/schemas.md`'s extraction, eligibility, and reasoning blocks inline, with the
`evidence`, `type`, and `checkable` enums.

`upload_date` is the one that bites. `vtt_to_md.py`'s header carries only title, channel,
URL, and duration, so an agent that isn't given the date invents one — and that invented
date decides the `False`/`Stale` boundary two stages later, where its origin is invisible.

**Never state a target claim count or a range in the task message.** A range is read as a
quota and answered at its ceiling: "a 30-minute tutorial yields perhaps 10–20 real claims"
produced ~19 per video, and triage paid for the difference. The shipped prompt carries the
selectivity bar instead; adding a number back overrides it.

## Escalated reasoning agent (stage 4b) — no model override

Receives the extraction output plus **targeted regions only**: the title, the
highest-ranked claims, and the last ~10% of cues. Must state which regions it was given
and must not ask for more — the whole point of escalating is that it costs less than a
re-read. Same emptiness rule as above.

## Triage (stage 5) — no model override, `prompts/triage.md`

Task message supplies: every extraction output (**no transcripts**), the run's
`depth_ceiling`, and the output path.

Runs as one call on the session model. Everything downstream verifies only what triage
passes through, and no later stage can detect a claim that never arrived — which is why
this one does not get a cheaper model.

## Breadth verifier (stage 6) — fast/cost-effective tier (Claude Code: `model: "sonnet"`, Gemini: `model: "flash"`, Codex: default)

**Do not compose this prompt. Copy `prompts/breadth.md` into the run directory
verbatim.** When invoking a subagent, you must explicitly read this file and pass its entire contents into the API's `Prompt` parameter, or the subagent will spawn starved of instructions. ~10 claims per agent, one vote each.

The shipped file is the source of truth, and the reason it is shipped rather than
described is that describing it failed. A session working from prose guidance wrote *"you
may use web search, but you do not have to for claims you can assess from knowledge"* and
produced a **66% false-positive rate** on the 2026-09-05 batch: 19 of 29 `false`/`stale`
flags collapsed under a sourced re-check, and all 3 flags that reached the depth tier were
wrong. Any summary of the rule invites the same paraphrase, so this file no longer carries
one.

Corpus-specific context (dates spanned, subject matter, what repetition to expect) belongs
in each agent's individual task message, never in an edit to the copied prompt.

## Depth verifier (stage 7) — adversarial tier (Claude Code: `model: "sonnet"`, Gemini: `model: "pro"`, Codex: default), `prompts/depth.md`

Task message supplies: one claim with its verbatim quote and attributions, the
`upload_date` **from run state**, and the output path. When invoking a subagent, explicitly read `prompts/depth.md` and pass its entire contents into the API's `Prompt` parameter. Three agents per claim, dispatched
independently; 2 of 3 refutations sink it.

Pass `upload_date` from run state, not from the extraction agent's echoed copy. A
hallucinated date that survives extraction would otherwise decide the `False`/`Stale`
boundary here, and this tier is the last thing that checks anything.

## Synthesis (stage 8) — no model override

Receives verdicts, extraction outputs, the drop-log, and the failure list. **Never
receives transcripts** — that is the whole reason the extraction agents exist.

Must produce the section set in `references/output-format.md`, resolve cross-video
contradictions in the body rather than deferring them to a later section, and name every
downgraded and failed video. It also proposes the `<slug>` — just the slug; the date and
`yteval` marker are generated.

**Every quote taken from a video carries its `[MM:SS]` on the same line.** No exception for
a three-word fragment mid-sentence. The stage 11 gate can only check a quote it can pair
with a timestamp, so an untimestamped video quote is unverifiable — indistinguishable from
a fabricated one, in the one document whose sources the reader cannot open. Quoting a
version string, a config key, or a line of vendor documentation needs no timestamp; those
are not transcript quotes. A run where the untimestamped quotes outnumber the timestamped
ones now fails the gate.

## Tool failures: quote them or don't claim them (every role)

**Write files with the `Write` tool. If any tool call fails, paste the tool's exact error
string and stop. Do not substitute a different mechanism, and never describe a failure you
cannot quote.**

An agent may not report a tool refusal, permission denial, or guard in its own words. Give
the verbatim string or report nothing.

The guard below is why this rule earns its place, and the history is worth stating straight
because it cuts both ways.

On the 2026-09-05 run the synthesis agent wrote its files with shell heredocs and reported
that `Write` had refused them. The session that investigated concluded the guard did not
exist and the agent had fabricated it — because a probe agent wrote `probe-report.md`
successfully, and the string appeared in no hook, setting, or plugin. **That conclusion was
wrong.** On the 2026-09-07 run a second agent hit the same guard, quoted it verbatim, and
stopped; a six-filename probe then pinned it down. The first agent had been telling the
truth, and the investigation had tested a near-miss filename instead of the exact one.

Both halves of the rule survive that correction. The verbatim quote is what made the
guard reproducible on the second encounter — a paraphrase would have failed the same way
again. And the earlier agent's *silent* fallback to heredocs is what let a real blocker
travel as an unverified anecdote for two days.

## The guard: blocked filenames for subagents

A subagent's `Write` is refused on certain filenames with:

```
Subagents should return findings as text, not write report files. Include this content in your final response instead.
```

Observed behaviour, 32 filenames tested across three probes (2026-09-07, 2026-09-10):

| Refused | Accepted |
|---|---|
| `report.md`, `report.draft.md`, `report-draft.md`, `report_draft.md`, `reporting.md`, `Report.md`, `REPORT.MD`, `subdir/report.md`, `report-` + 68 `a`s + `.md`, `findings.md`, `findings-summary.md`, `summary.md`, `summary-report.md`, `analysis.md`, `analysis2.md`, `analysis-notes.md` | `synthesis.md`, `writeup.md`, `onepager.md`, `my-report.md`, `draft-report.md`, `probe-report.md`, `report.txt`, `probe-a.md`, `probe1.md`, `results.md`, `notes.md`, `summaries.md`, `finding.md`, `report.markdown`, `my-findings.md`, `breakdown.md` |

The 2026-09-10 pass added a fourth blocked prefix (`analysis`, not predicted by the
2026-09-07 theory — found because `analysis.md` was refused with no `report`/`findings`/
`summary` in it, then reproduced on a second, independent agent run before being trusted)
and two case variants (`Report.md`, `REPORT.MD`, both refused — the prefix match is
case-insensitive, at least for `report`). `report.markdown` (extension not `.md`) and
`subdir/report.md` (nested path) were also tested: extension must be exactly `.md`;
directory depth doesn't matter, only the final path segment does.

Consistent with all of it: `.md` files whose basename *starts with* `report`, `findings`,
`summary`, or `analysis`, case-insensitively. That is an inference from the table, not a
documented rule — the table is the evidence, so extend it rather than trusting the
generalisation. A fifth blocked word is exactly as plausible as `analysis` was before
2026-09-10 — this table is not closed.

An earlier version of this file asserted an exact-name blocklist of `report.md` and
`findings.md` from six observations, and prescribed `report.draft.md` as the workaround —
which the next run proved is itself blocked. Two wrong mechanism claims in one afternoon
is the argument for recording observations and picking a verified-passing name.

**Stage 8 writes `synthesis.md`; the main session renames it to `report.md`.** Both names in
that sentence are confirmed by direct probe. `onepager.md` needs no workaround. Do not
"solve" this by having the agent
return a 300-line report as chat text; that is the failure the file-based handoff exists to
avoid.
