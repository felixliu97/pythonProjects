---
name: ai-regression-testing
description: Maintaining long-term project health with regression checks. Use when making changes to core logic.
origin: ECC
---

# AI Regression Testing

Ensure that new AI-generated changes do not break existing functionality.

## Principles

1. **Baseline First** — always know the state before your change.
2. **Targeted Regressions** — focus on code paths affected by the change.
3. **Automated Comparison** — use diffs and test deltas to measure impact.

## Workflow

1. **Identify Critical Paths** — what must not break?
2. **Execute Baseline Tests** — capture current behaviour.
3. **Apply Changes**.
4. **Execute Regression Tests** — compare against baseline.
5. **Report Deltas** — explicitly call out any changed behaviour, even if tests still pass.

## Success Criteria

- Zero regression in high-priority paths.
- All existing tests remain passing.
- Performance remains within acceptable bounds.
- No new lint/style regressions.
