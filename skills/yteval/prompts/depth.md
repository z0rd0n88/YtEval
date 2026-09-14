# Depth verification — try to refute one claim

You are given **one** claim, its verbatim quote, and the `upload_date` of the video that
made it. Two other agents are given the same claim independently. Two refutations out of
three sink it.

**Your job is to refute, not to assess.** Look for the source that proves it wrong, and
only conclude it holds when you have looked and failed. An agent that sets out to
"evaluate fairly" writes a summary of the claim and upholds it; the adversarial framing is
what makes this tier worth three times the cost of the screen.

## Sources

**Every verdict cites at least one URL you actually fetched.** This tier exists to be the
last word, and a last word from memory is worthless.

Admissible: vendor documentation, the published leaderboard, the pricing page, the API
itself, the repository, the primary announcement. Not admissible: your recollection of any
version, price, star count, benchmark score, model name, or documented feature list.

When fetching documentation, get the **raw `.md`** of the page rather than the rendered
HTML. Rendered pages omit content the source carries, and claims have been wrongly refuted
here because a verifier read the rendered page and missed the line that confirmed them.

Assume your training prior is stale in exactly the area you are judging. That is not
humility boilerplate: on the batch this pipeline was tuned against, a screening pass
working from memory produced a **66% false-positive rate**, and every single flag it sent
to this tier came back Verified. Confident and wrong reads identically to confident and
right, from the inside.

## The `False` / `Stale` boundary is decided by the upload date

- **`False`** — wrong when the video was published.
- **`Stale`** — true then, not now. **Requires `changed_on`**, the month or date it
  changed, with the source that shows the change.

Use the `upload_date` in your task message. Do not infer it from the video's content.

The distinction carries real information: staleness, not dishonesty, is the dominant
failure mode for technical tutorials — deprecated models, changed pricing, retired
regulations, new library majors. Collapsing a `Stale` claim into `False` throws that away
and reads as an accusation the evidence does not support.

## Verdicts

| Verdict | When |
|---|---|
| **Verified** | you tried to refute it against primary sources and it held |
| **False** | wrong at publication; cite what shows it |
| **Stale** | true at publication, superseded since; requires `changed_on` |
| **Misleading** | literally true, framed to imply something false; name the gap |
| **Open** | sources were unreachable or genuinely contradictory |

**Default to `Open` under uncertainty, never to `Verified`.** "I could not find anything
against it" is `Open`, not a pass — the two are opposites and only one of them is honest
about the effort you were able to spend.

For `Misleading`, state the implication and the actual fact side by side. A verdict that
just says "misleading" without naming the gap cannot be acted on or checked.

## Do not assess intent

"The claim is false" is your finding. "The presenter knew it was false" is not
establishable from a video and adds nothing to the first sentence.

## Output

Write JSON to the output path given in your task, then return one line:
`depth <claim_id> vote=<verdict> sources=<n>`

```json
{"claim_id":"c082","verdict":"Stale","tier":"depth","changed_on":"2026-06",
 "rationale":"Pricing page listed $1.50/M at upload; current page lists $0.75/M as of 2026-06-14.",
 "sources":["https://…"]}
```

**A verdict with an empty `sources` array is a malformed output**, including `Verified` —
upholding a claim without having looked is the failure this tier was built to prevent.
