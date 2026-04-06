---
name: testing
description: Creates and reviews tests for code. Use when writing unit tests, integration tests, or discussing testing strategies.
---

# Testing Skill

Guidelines for unit, integration, and E2E testing.

## Testing Pyramid
1. **Unit Tests (Many)**: Fast, test individual functions/logic.
2. **Integration Tests (Some)**: Test component interactions (DB, APIs).
3. **E2E Tests (Few)**: Test full user flows.

## Pytest Best Practices
- Use **Fixtures** for reusable setup.
- Use **Parametrization** for data-driven tests.
- **Naming**: `test_[scenario]_[condition]_[result]`.

```python
import pytest

def test_on_empty_input_returns_zero():
    assert calculate([]) == 0
```
