---
name: python-best-practices
description: Provides Python-specific coding standards and best practices. Use when writing or reviewing Python code.
---

# Python Best Practices Skill

Core standards for maintaining a clean Python codebase.

## Formatting & Style
- **PEP 8**: Follow standard conventions.
- **Black/Ruff**: Use for consistent formatting (88 chars length).
- **Type Hints**: Always use `typing` for parameters and return types.

## Project Structure
- Use `src/` layout.
- Manage dependencies via `pyproject.toml` (recommended) or `requirements.txt`.
- Isolated environments (venv/uv).

## Anti-patterns to Avoid
- Bare `except:` blocks.
- Hardcoded sensitive data (use `.env`).
- Circular imports.
