# Data schemas

Every agent returns JSON matching one of these and nothing else.

## Extraction output (stage 4a)

```json
{
  "video_id": "6I1wGCuFpbk",
  "title": "…",
  "channel": "…",
  "url": "https://www.youtube.com/watch?v=6I1wGCuFpbk",
  "upload_date": "20260421",
  "duration": "22:03",

  "techniques":     [{"name": "", "summary": "", "timestamp": "12:34",
                      "quote": "", "evidence": "demonstrated"}],
  "claims":         [{"text": "", "timestamp": "12:34", "quote": "",
                      "evidence": "asserted", "type": "factual",
                      "checkable": true}],
  "prompts":        [{"purpose": "", "text": "", "timestamp": "12:34"}],
  "stack":          [{"name": "", "version": "", "role": "", "timestamp": "12:34"}],
  "sources_cited":  [{"what": "", "url": "", "timestamp": "12:34"}],
  "red_flags":      [{"type": "out_of_context", "timestamp": "12:34", "quote": "",
                      "implied": "", "shown": ""}],
  "caveats_stated": [{"text": "", "timestamp": "12:34", "quote": ""}],
  "gaps":           [{"text": "", "why_it_matters": ""}]
}
```

| Field | Values |
|---|---|
| `evidence` | `demonstrated` \| `asserted` \| `cited` |
| `claims[].type` | `factual` \| `performance` \| `pricing` \| `regulatory` \| `opinion` |
| `red_flags[].type` | `unsupported` \| `out_of_context` \| `fallacy` \| `sales_pitch` \| `missing_evidence` |
| `checkable` | `false` for taste claims ("this architecture feels cleaner") |

`upload_date` comes from run state, passed in by the caller — not from the video
itself, which the transcript header does not carry.

**Every claim and technique carries a verbatim quote plus timestamp.** Verification
needs the exact assertion, not a paraphrase — and because transcripts are gitignored,
the report must carry the quote or the reader can never check it. Quotes are checked
mechanically at stage 11.

`checkable: false` excludes a claim from **both** verification tiers. Use it for taste
and preference, not for "hard to check" — hard-to-check claims are what the tiers are
for.

`evidence` is the field that produced the trading-bot report's headline observation
that no video showed a verified result. Be strict about it: `demonstrated` means the
video showed the result on screen.

`red_flags` carries `implied` vs `shown` rather than a ninth bucket, because the
sharpest case in that report was a video titled "How I Got RICH" whose best on-screen
figure was $566 — no false claim, every number real, the misrepresentation entirely in
the gap. Only that pair captures it.

## Eligibility (stage 4b)

```json
{"eligible": true,
 "reason": "Makes 14 checkable claims about library throughput and API pricing."}
```

## Reasoning analysis (stage 4c)

```json
{
  "findings": [{"type": "out_of_context", "timestamp": "19:55", "quote": "",
                "implied": "", "shown": "", "severity": "high"}],
  "justification": "Required. If findings is empty, say what was checked and why it held."
}
```

An empty `findings` with an empty `justification` is a failed output, not a clean video.
A thin analysis is obvious when it has to argue for itself.

## Verdict record (stages 6–7)

```json
{
  "claim_id": "c17",
  "text": "…",
  "attributions": [{"video_id": "…", "timestamp": "19:55", "quote": "…"}],
  "verdict": "Stale",
  "tier": "depth",
  "changed_on": "2026-06",
  "rationale": "…",
  "sources": ["https://…"],
  "votes": {"upheld": 1, "refuted": 2}
}
```

| Verdict | Meaning | Tier |
|---|---|---|
| **Verified** | checked adversarially, holds | depth |
| **False** | wrong, and was wrong at publication | depth |
| **Stale** | true at publication, not anymore — with what changed and when | depth |
| **Misleading** | literally true, framed to imply something false | depth |
| **Screened** | breadth pass found nothing suspicious; not adversarially checked | breadth |
| **Open** | couldn't determine | either |

Two properties carry weight:

**Every verdict names its tier.** A `Screened` claim and a `Verified` claim did not get
the same scrutiny, and a table that renders them identically overstates confidence. This
is what makes the cheap breadth tier safe to have at all.

**`Stale` requires `changed_on`.** "No longer true" without "changed in June 2026" is
unactionable. Staleness — not lying — is the dominant failure mode for tech tutorials:
model deprecations, API changes, pricing, library versions, retired regulations. The
FINRA pattern-day-trader finding was exactly this shape, true when the videos were made
and gone by the time it was checked. Collapsing it into `False` throws away the useful
part.

`Misleading` is where stage 4c's `out_of_context` findings land, so the reasoning
analysis reaches the verdict table instead of being stranded in an appendix.

The `False`/`Stale` boundary is decided by `upload_date`. A verifier that doesn't get it
defaults everything to `False` and the `Stale` state quietly stops working.
