---
name: verification-loop
description: Ensure agent-written code actually works via automated verification. TRIGER when: implementation is "done" but not yet verified. DO NOT TRIGGER when: user says "just skip verification".
origin: ECC
---

# Verification Loop

The goal is to ensure the code works as intended before claiming completion.

## When to Use

- Implementation is "complete" and ready for handoff
- A bug was fixed and needs confirmation
- A refactor was done and needs regression check
- New tests were added and need to pass

## Workflow

1. **Verify State** — run relevant tests or build commands.
2. **Analyze Failure** — if tests fail, identify the root cause.
3. **Fix and Repeat** — modify code and re-run verification until green.
4. **Final Confirmation** — run full suite if applicable.

## Non-Negotiable Rules

- Never claim "done" without evidence (test output, build log).
- If no tests exist, suggest creating them or perform manual verification via shell/scripts.
- Call out if verification is impossible (e.g. requires UI interaction not available to the agent).

## Output

A summary of verification results:
- Tests run
- Pass/Fail count
- Evidence (snippets of logs)
- Remaining risks
