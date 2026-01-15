---
name: testing
description: Creates and reviews tests for code. Use when writing unit tests, integration tests, or discussing testing strategies.
---

# Testing Skill

When creating or reviewing tests, apply these principles and patterns:

## Testing Pyramid

```
        /\
       /  \      E2E Tests (few)
      /----\
     /      \    Integration Tests (some)
    /--------\
   /          \  Unit Tests (many)
  --------------
```

## Test Types

| Type | Scope | Speed | When to Use |
|------|-------|-------|-------------|
| **Unit** | Single function/class | Fast | Business logic, utilities |
| **Integration** | Multiple components | Medium | APIs, database, services |
| **E2E** | Full system | Slow | Critical user flows |

## Python Testing with pytest

### Basic Test Structure

```python
import pytest
from mymodule import calculate_total

class TestCalculateTotal:
    """Tests for the calculate_total function."""

    def test_empty_list_returns_zero(self):
        """Empty input should return 0."""
        assert calculate_total([]) == 0

    def test_single_item(self):
        """Single item should return that item's value."""
        assert calculate_total([10]) == 10

    def test_multiple_items(self):
        """Multiple items should be summed correctly."""
        assert calculate_total([10, 20, 30]) == 60

    def test_negative_values_raises_error(self):
        """Negative values should raise ValueError."""
        with pytest.raises(ValueError, match="negative"):
            calculate_total([-5])
```

### Fixtures

```python
@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return User(name="Test User", email="test@example.com")

@pytest.fixture
def db_session():
    """Create a database session for testing."""
    session = create_test_session()
    yield session
    session.rollback()
    session.close()
```

### Parameterized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ([], 0),
    ([1], 1),
    ([1, 2, 3], 6),
    ([10, -5, 5], 10),
])
def test_calculate_total(input, expected):
    assert calculate_total(input) == expected
```

## Test Naming Convention

Use descriptive names that explain:
1. **What** is being tested
2. **Under what conditions**
3. **Expected result**

```python
# Good
def test_user_login_with_valid_credentials_succeeds():
def test_checkout_with_empty_cart_raises_error():

# Bad
def test_login():
def test_checkout():
```

## Coverage Goals

- **Unit tests**: Aim for 80%+ code coverage
- **Critical paths**: 100% coverage for payment, auth, data integrity
- Focus on testing **behavior**, not implementation details

## Mocking Best Practices

```python
from unittest.mock import Mock, patch

@patch('mymodule.external_api.fetch_data')
def test_service_handles_api_failure(mock_fetch):
    mock_fetch.side_effect = APIError("Connection failed")
    
    result = my_service.get_data()
    
    assert result.status == "error"
    assert "Connection failed" in result.message
```

## Test Checklist

- [ ] Tests are independent (no shared state)
- [ ] Tests are deterministic (no flaky tests)
- [ ] Edge cases are covered
- [ ] Error paths are tested
- [ ] Tests run fast (mock slow dependencies)
- [ ] Test names are descriptive
