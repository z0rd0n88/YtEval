# GEMINI.md — YtEval

Guidance for Google Antigravity and Gemini working inside this repository.

See [AGENTS.md](./AGENTS.md) for architecture, invariants, and pipeline specifications.

## Gemini / Antigravity Skill Integration

- **Skill discovery**: Configured via `.agents/skills.json` pointing to `skills/` and `.agents/skills/yteval`.
- **Subagent mapping**:
  - Breadth verification (Stage 6): use `invoke_subagent` with `TypeName: "self"` and `model: "flash"` or `model: "inherit"`.
  - Adversarial depth verification (Stage 7): use `invoke_subagent` with `TypeName: "self"` and `model: "pro"`.
- **Testing**: Run `python3 skills/yteval/scripts/test_check_quotes.py` to verify quote verification logic before committing changes.
