---
name: prove-it
description: Use after creating or changing anything (skill, plugin, agent, script, workflow, repo, config). Test it immediately and report real evidence, never "should work".
---
# Prove it

Nothing you create is done until a check has run and you have shown its output.

1. **Pick the check for the artifact**:
   - skill/agent file: frontmatter parses, then a headless run (`claude -p`) shows it is listed
   - plugin or marketplace: `claude plugin validate <path>`, then add the marketplace and `claude plugin list`
   - script: run it on a real input and a bad input
   - GitHub workflow: YAML parses, then trigger it and read the run result
   - repo or config: clone or reload it fresh and confirm it behaves the same
2. **Run it now**, not at the end. Prefer a throwaway target (test repo, temp dir).
3. **Report evidence**: command, exit code, key output. Mark anything not testable as unverified and say why.
4. **If the check fails**, fix the cause and rerun. Do not suppress the error.
5. **Keep the check reusable**: if the same test will recur, save it as a script in the repo.
