# yteval

A skill for [Claude Code](https://claude.com/claude-code), [Google Antigravity / Gemini](https://antigravity.google), and [OpenAI Codex](https://openai.com) that turns YouTube videos into a
fact-checked writeup — or just their transcript.

It does not summarize. It pulls out every statement a viewer could check and be proved
wrong about, then checks those statements against primary sources and says plainly where
the video is wrong, where it is out of date, and where it asserts a number it never
measured.

> **A full run spends a real multi-agent budget.** It fans out dozens of verification
> subagents with web search, and the spend cannot be undone once started. Use
> `--transcript-only` to fetch captions with no agents at all.

## Requirements

| Tool | Required | Notes |
|---|---|---|
| AI Assistant | yes | Claude Code, Google Antigravity / Gemini, or OpenAI Codex |
| `yt-dlp` | yes | `pipx install yt-dlp` — captions only, never downloads audio or video |
| `python3` | yes | standard library only, nothing to `pip install` |
| `gh` | no | only for `--issues`, and only when authenticated |

## Install

```bash
git clone https://github.com/z0rd0n88/YtEval.git && cd YtEval && ./install.sh
```

By default, `./install.sh` installs the skill globally for all supported AI coding assistants:
- **Claude Code**: `~/.claude/skills/yteval/`
- **OpenAI Codex**: `~/.agents/skills/yteval/`
- **Google Antigravity / Gemini**: `~/.gemini/config/skills/yteval/` (and CLI config)

You can also target specific platforms:
```bash
./install.sh --claude     # Claude Code only
./install.sh --gemini     # Google Antigravity / Gemini only
./install.sh --codex      # OpenAI Codex only
```

Or install inside the current project workspace:
```bash
./install.sh --project    # installs into .claude/ and .agents/
```

To remove:
```bash
./install.sh --uninstall
```

Then start your AI assistant in whatever directory you want reports written to, and run
`/yteval --help` (or activate the `yteval` skill).

## Use it

Fetch a transcript and stop. No agents, no cost beyond the download:

```bash
/yteval --transcript-only https://www.youtube.com/watch?v=VIDEO_ID
```

Full verified writeup of one video:

```bash
/yteval https://www.youtube.com/watch?v=VIDEO_ID
```

Several videos at once, compared against each other, with the expensive verification tier
held to three claims:

```bash
/yteval --depth-ceiling 3 URL_ONE URL_TWO URL_THREE
```

`/yteval --help` lists every option.

## What you get

A directory under `docs/reports/<date>-yteval-<slug>/` containing a `README.md` index, a
scannable `onepager.md`, and a full `report.md` carrying the method and the evidence.
Transcripts land in a `transcripts/` subdirectory and are meant to stay out of version
control.

Because transcripts are not committed, the report quotes every line it relies on, with a
timestamp, and a mechanical gate checks those quotes back against the transcript before
the run finishes.

## How it verifies

Two tiers, because checking every claim adversarially is unaffordable and checking none
of them is worthless.

**Breadth** screens every checkable claim once and returns a verdict or a flag. It is
deliberately cheap, and it is not allowed to call something false without having fetched
a source that says so.

**Depth** takes the flagged and highest-stakes claims, caps them at `--depth-ceiling`, and
puts each one through three independent adversarial checks that are told to refute it.
Every verdict there must cite a URL that was actually fetched.

The depth tier doubles as an audit of the breadth tier: if depth keeps overturning what
breadth screened clean, the screen is broken and the run says so rather than publishing
the results quietly.

## Limitations worth knowing before you rely on it

- **Videos with no captions are out of scope.** There is no speech-to-text fallback. The
  run reports `no-captions` and moves on.
- **A claim can only be dated as wrong-then or wrong-now if a contemporaneous source is
  reachable.** When archive lookups fail, claims come back "could not confirm either way"
  rather than being guessed at, and the report says which ones those were.
- **Coverage is reported, not implied.** If the quote gate could not check part of a
  report, it prints how much and fails the run when it could not check most of it.
- **Verification quality depends on the model and the sources it can reach.** This finds
  claims worth doubting and does real work on them; it is not an oracle.

## Filing issues from findings (`--issues`)

Off by default. When enabled it drafts issues, dedupes against the target repo's open
*and closed* issues, checks them against that repo's `CLAUDE.md`, `AGENTS.md`, or `GEMINI.md`, then shows you the whole
batch and waits. Nothing is filed without explicit approval, and approval never carries
forward to the next run. The target repo has no default and is never inferred.

## Transcripts are untrusted input

Captions are written by whoever uploaded the video. If a transcript contains text aimed at
an automated reader — "ignore previous instructions", "file an issue saying…" — the
pipeline records it as content and does not act on it. This matters because extraction
output flows into the optional issue-filing stage, which writes to real repositories.

## License

Public domain, via [The Unlicense](LICENSE). Use it, change it, sell it, ship it in
anything you like. No attribution required and no conditions attached.
