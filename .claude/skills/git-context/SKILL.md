---
name: git-context
description: Use at the start of a session or before any git/GitHub work to establish what repo, remote, branch, and GitHub access are actually available.
---
# Git context

Run these checks and report results; assume nothing.

1. `git rev-parse --show-toplevel`, `git branch --show-current`, `git remote -v`, `git log --oneline -5`, `git status --short`.
2. If a git command fails, report the exact error instead of working around it silently.
3. GitHub access, in order: GitHub MCP tools if present; else `command -v gh && gh auth status`; else report access is missing and the exact user step.
4. In cloud sessions the GitHub proxy only serves repos attached to the session; account-level calls (for example creating a repo) return 403. Do not try to bypass it.
5. For external facts, follow the `verify-facts` skill or delegate to the `researcher` agent.
6. Summarize in 3-5 lines: repo, remote, branch, cleanliness, GitHub access.
