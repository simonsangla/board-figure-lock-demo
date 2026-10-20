---
name: verify-facts
description: Use before stating any fact about tools, versions, docs, repos, pricing, or the state of the user's machine/accounts, and before giving the user any command to run (gh, git, snow, dbt, etc.). Reads the repo's knowledge/ base first, forces a source check instead of answering from memory, and updates the knowledge base.
---
# Verify before claiming

Never assume. Every factual claim and every command given to the user must come from a source checked in this session.

0. **Read the knowledge base first**: `knowledge/<tool>.md` (e.g. github, snowflake, dbt). If the repo has no `knowledge/` yet, create it when you first add an entry (one file per tool). An entry verified < 7 days ago can be used with its source. Older or missing: go to step 2.
1. **Classify each claim**: local machine/repo (Bash/Read), tool or product (official docs or release notes via WebFetch/WebSearch), account/remote (GitHub tools or `gh`).
2. **Check it now.** Memory, earlier turns and prior sessions are leads, not evidence.
3. **Prefer primary sources**: official docs, release notes, the repo itself. Label blogs and search summaries as secondary.
4. **Commands for the user**: check every flag against the official manual page (or `--help` of the same version), and say which folder to run it in. Put the source next to the command.
5. **Report with provenance**: mark each claim verified (source) or unverified (why).
6. **If it cannot be verified, say so.** Never fill the gap with a plausible answer.
7. **Recheck stale facts** (versions, availability, auth state) before acting on them.
8. **Update the knowledge base**: add or fix the entry in `knowledge/<tool>.md` (format in `knowledge/README.md` if it exists, else a `## <Topic>` heading, then `- **<fact or command>** — `<exact command>``, then `Source: <URL> · "<short verbatim quote>" · verified YYYY-MM-DD`) in the same push.
