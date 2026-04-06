---
name: code-review
description: Reviews code changes for bugs, style issues, and best practices. Use when reviewing PRs or checking code quality.
---

# Code Review Skill

Use this checklist during PR reviews or when auditing local code.

## 1. Correctness & Logic
- Does the code achieve the intended functional Goal?
- Are edge cases (nulls, empty lists, timeouts) handled?
- Are there any off-by-one errors or logical fallacies?

## 2. Style & Readability
- Follows PEP 8 (Python) or project-specific style guides.
- Naming is descriptive, not cryptic (e.g., `user_id` vs `uid`).
- Complex logic is explained via comments, not over-abstracted.

## 3. Performance & Security
- No redundant database queries or API calls inside loops.
- Input is sanitized before use in commands or queries.
- Sensitive data is NOT logged or printed.

## Feedback Etiquette
- Be **constructive**: "Consider using X here because..."
- **Praise** good implementations.
- Distinguish between **Blocking** issues and **Nitpicks**.
