---
name: python-best-practices
description: Provides Python-specific coding standards and best practices. Use when writing or reviewing Python code.
---

# Python Best Practices Skill

When writing or reviewing Python code, apply these standards:

## Code Style

- Follow **PEP 8** style guidelines
- Use **type hints** for function parameters and return values
- Use **docstrings** for modules, classes, and functions (Google style or NumPy style)
- Maximum line length: 88 characters (Black formatter default)

## Project Structure

```
project/
├── src/
│   └── package_name/
│       ├── __init__.py
│       └── module.py
├── tests/
│   └── test_module.py
├── pyproject.toml
└── README.md
```

## Best Practices

1. **Virtual Environments**: Always use `venv` or `uv` for dependency isolation
2. **Dependencies**: Use `pyproject.toml` for modern Python packaging
3. **Testing**: Write tests using `pytest`
4. **Linting**: Use `ruff` or `flake8` for linting
5. **Formatting**: Use `black` or `ruff format` for consistent formatting
6. **Type Checking**: Use `mypy` for static type checking

## Error Handling

```python
# Good - specific exception handling
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise

# Bad - bare except
try:
    result = risky_operation()
except:  # Never do this!
    pass
```

## Async Python

- Use `async/await` for I/O-bound operations
- Use `asyncio.gather()` for concurrent tasks
- Always handle cancellation properly
