---
name: project-rules
description: Always-on project-wide rules and standards.
---

# Project Rules

These rules apply to all interactions and code changes within this repository.

## 1. General Principles

- **Simplicity First**: Always prefer the simplest solution that meets the requirements (KISS).
- **No Placeholders**: Avoid `TODO` comments without a specific context or ticket reference.
- **Modern Python**: Use Python 3.10+ features where applicable (e.g., structural pattern matching, type hinting).

## 2. Coding Standards

- **Environment Isolation**: Always use a virtual environment (`venv` or `uv`).
- **Dependency Management**: Update `pyproject.toml` or `requirements.txt` when adding new libraries.
- **Logging vs. Printing**: Use the `logging` module for any production code. Avoid `print()` for debugging unless it's temporary and will be removed.
- **Type Safety**: Use type hints for function signatures and important variables.

## 3. Communication Style

- **Be Concise**: When explaining technical concepts, get to the point.
- **Plan Mode**: For complex changes, always propose an implementation plan first.
- **Visuals**: Use Mermaid diagrams to explain architecture or workflows.

## 4. File Management

- **No Overwriting Important Data**: Be cautious when modifying large datasets (e.g., CSVs/YAMLs).
- **Cleanup**: Delete temporary files (`.tmp`, `__pycache__`) after completion or automate the cleanup.
