---
source: claude-code session, /home/alex/WeeklyWrapup
scope: install ARCH.md architecture-map tooling in YtEval
parent_session: b58f5b10-7fff-4598-a673-ad815fe8eb1a
date: 2026-09-19
---

# Install ARCH.md tooling — YtEval

## Why this exists

YtEval was promoted into the weekly-wrapup scan list on 2026-09-19 (see
[ClaudesMods#160](https://github.com/z0rd0n88/ClaudesMods/pull/160)) after Antigravity
logged 5 conversations / 567 steps against it in one week with the wrapup seeing none of
it. Promotion pulls in the `rules/common/architecture-mapping.md` obligation: owned repos
maintain a root `ARCH.md`, generated on every commit. YtEval has no `ARCH.md` and no
`.githooks/`.

## What was decided

- Install the tooling with the canonical installer rather than hand-copying:
  `bash /home/alex/.claude/scripts/arch-map/install-arch-map.sh /home/alex/YtEval`
  It is idempotent, copies `gen_arch.py` + `pre-commit` into `.githooks/`, wires
  `core.hooksPath`, and generates the first `ARCH.md`.
- Ship `gen_arch.py` and `pre-commit` **together**. The script is distributed by copy with
  no upstream link, and shipping one without the other is how three repos ended up running
  a `pre-commit` with a silent `exit 1` bug for weeks.
- Do not widen scope to the rest of the architecture-mapping rule in the same PR.

## What is still open

- **`main` is one commit behind the real work.** `main` is at `6b55ac5` "Initial release";
  the Antigravity/Gemini/Codex support lives on `feat/gemini-codex-support`. An `ARCH.md`
  generated from `main` will not describe the repo as it actually is. Decide first whether
  to land that branch, or to generate the map on top of it instead.
- **There is no root `CLAUDE.md` to point at `ARCH.md`.** The repo carries `AGENTS.md` and
  `GEMINI.md` instead. The rule's "root CLAUDE.md integration" step has nothing to hook
  into — either add the pointer to `AGENTS.md`, or skip that step deliberately and say so.
- The curated zones (`## Overview` prose, `## Key Paths`) start empty. They survive
  regeneration untouched, so an empty map is not self-correcting; someone has to write them.

## Where to look

| Path | What |
|---|---|
| `/home/alex/.claude/scripts/arch-map/install-arch-map.sh` | The installer. Read the header comment before running. |
| `/home/alex/.claude/rules/common/architecture-mapping.md` | The rule, including the operative invariants |
| `~/.claude/guides/session-discovered-gotchas.md` § "ARCH.md tooling" | Zones, install, and the incident record |
| `skills/`, `install.sh`, `.agents/` | What the map will actually cover — this repo is ~11 markdown + 3 Python files |

This repo is small enough that the generated tree will be short. The value here is the
curated `## Key Paths` block, not the file listing.

## Next step

Resolve the `main` vs `feat/gemini-codex-support` question above, then run the installer on
whichever branch wins, curate `## Overview` and `## Key Paths`, and open a PR. Do not
bypass a hook failure with `git -c core.hooksPath=/dev/null` — fix the cause.
