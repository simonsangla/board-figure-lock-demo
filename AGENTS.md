# Project instructions

Read by every agent; `CLAUDE.md` is exactly `@AGENTS.md` so Claude loads it too. Keep this file short (< 60 lines; CI fails at 200).

## Start here
1. Read this file, then the newest plan in `docs/plans/` and `git log --oneline -10`.
2. Run skill `git-context` before any git/GitHub work.

## Rules
- Verify every fact before stating it; cite the source (skill `verify-facts`).
- Prove every artifact with a real check and show the output (skills `prove-it`, `verification-before-completion`).
- New work: `brainstorming` -> `writing-plans` (plan in `docs/plans/YYYY-MM-DD-<topic>.md`, checkbox to-dos) -> `executing-plans` or `subagent-driven-development`.
- Run safe tests autonomously. Stop only for credentials, sudo, destructive actions, or anything outside the user's own repos.
- Give ready-to-run commands, not vague suggestions.
- Never write tokens or secrets into any file. Secrets live in GitHub Actions secrets.
- Remember across sessions: when the user says "souviens-toi" / "remember", or states a lasting preference, add one dated line to `memory/MEMORY.md` and commit it on your branch (format in that file). Cloud sessions have no built-in auto memory; this file is loaded in every session:
@memory/MEMORY.md
- Run `bin/check` before every push (valid JSON, SKILL.md frontmatter, `make test` if a Makefile exists, `CLAUDE.md` = `@AGENTS.md`). The pre-commit hook runs it: cloud sessions set `core.hooksPath` themselves, on a Mac run once `git config core.hooksPath .githooks`. `.github/workflows/ci.yml` only calls `bin/check` and runs by hand (Actions tab -> ci -> Run workflow), so pushes spend no Actions minutes.
