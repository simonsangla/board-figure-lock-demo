---
name: interview
description: Use when a ticket is labeled waiting-simon and Simon should answer its questions, or when he says "interview me" or "pose-moi les questions", or when skill veille hands over an inbox file (grill mode). Asks the questions one at a time with clickable options, then records all answers in one place.
---
# Interview

Simon answers decisions with clicks, not long comments. You never answer for him.

## Steps
1. **Find the ticket.** Given a number, use it. Otherwise list open issues labeled `waiting-simon` (GitHub MCP) and take the oldest. Read the body and all comments: skip questions already answered in a comment.
2. **Read the rules first.** If the ticket links a rules/policy file or says some options are forbidden, read it before asking and leave forbidden options out.
3. **Extract the questions** from the body (a numbered list under an "Interview" / "Questions" heading). Keep the ticket's numbering. Sort shortest first.
4. **Ask one at a time** with `AskUserQuestion`, one question per call:
   - `header` = `#<ticket> Q<n>` (max 12 chars), `question` = the ticket's wording, shortened only if it is long.
   - 2-4 options derived from the examples in the question itself; do not invent options the ticket does not suggest. The tool adds "Other" for free text.
   - Use `multiSelect: true` when the question lists apps/tools ("which of...").
   - If the ticket gives no examples, offer `Skip for now` plus `Explain later`, so Simon can type under "Other".
5. **Post nothing between questions.** Keep the answers in memory.
6. **At the end, post ONE comment** (GitHub MCP `add_issue_comment`):
   ```
   ## Answers (via interview)
   1. <short question label>: <answer>
   ...
   Unanswered: <numbers or "none">
   ```
7. **Label.** Remove `waiting-simon` only if every question has an answer. If any is unanswered or skipped, keep the label and say which.
8. **Stop.** Do not start the follow-up work in the same run unless Simon asks.

## Rules
- Never choose, guess or infer an answer. "Skip" and "Other: later" count as unanswered.
- No routine, no polling, no retry. One pass.
- Do not edit the ticket body. Never write secrets into the comment.

## Grill mode (inbox file from skill `veille`)
Same one-question-at-a-time loop, plus rules borrowed from Matt Pocock's `grilling` skill (MIT; why: mission-os-test `decisions/2026-10-20-veille-grill-me.md`):
- **Source = the inbox file**, not a ticket: one question per proposal `P<n>` still marked `Decision: open`. `header` = `Veille P<n>`.
- **Recommended first.** Ask "Appliquer ce changement ?" so `Oui` always means apply. Option 1 is the recommended answer (`Oui (Recommended)` or `Non (Recommended)`), option 2 the other one, then `Plus tard`, plus a variant only if the proposal names one. Record the answer Simon picked, never the recommendation.
- **Facts are your job.** If a question needs a fact (does the file exist, what does the doc say), look it up before asking; never ask Simon for it.
- **Dependent proposals wait.** A proposal that depends on another still open is asked after it; drop it if its parent got "Non".
- **No question limit.** Continue until every proposal has a decision. Simon can stop with "Plus tard" on the rest.
- **Record** each answer in the inbox file (`Decision: oui` or `Decision: non`; "Plus tard" leaves `Decision: open` so the next run asks again), not as a ticket comment. Steps 6-8 above do not apply; skill `veille` applies the "oui".

## Dry run
If asked for `dry-run`: do steps 1-4 but without calling `AskUserQuestion`; print the ordered question queue with the options you would offer, and the comment skeleton with `<answer>` placeholders. Post nothing, change no label.
