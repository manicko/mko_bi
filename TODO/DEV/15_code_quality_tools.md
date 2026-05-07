---
## CODE QUALITY TOOLS
---

### TASK: Run and Fix Code Quality Tool Issues

FILE: Entire codebase

GOAL: Ensure code passes ruff, mypy, and tests

ISSUE DESCRIPTION:

Based on the audit, we need to run:
1. **ruff** - Linting and code style
2. **mypy** - Static type checking
3. **pytest** - Unit tests

Expected issues (from previous task files):
- Syntax errors (curly quotes) - Task 09
- Missing type annotations
- Unused imports
- Type mismatches

COMMANDS TO RUN:
```bash
# From c:/py_dev/mkobi

# Ruff linting
uv run ruff check .

# Ruff auto-fix (where possible)
uv run ruff check --fix .

# Mypy type checking
uv run mypy .

# Run tests
uv run pytest tests/
```

IMPACT:
- Code quality issues
- Potential runtime errors
- Hard to maintain

IMPLEMENTATION:

1. **Run ruff and fix issues**:
   ```bash
   cd c:/py_dev/mkobi
   uv run ruff check . > ruff_issues.txt 2>&1
   # Review ruff_issues.txt and fix each issue
   ```

2. **Run mypy and fix type errors**:
   ```bash
   cd c:/py_dev/mkobi
   uv run mypy . > mypy_errors.txt 2>&1
   # Review mypy_errors.txt and fix each type error
   ```

3. **Run tests and fix failures**:
   ```bash
   cd c:/py_dev/mkobi
   uv run pytest tests/ -v > test_results.txt 2>&1
   # Review test_results.txt and fix failing tests
   ```

4. **Common fixes needed**:
   - Add type annotations to function parameters and return values
   - Fix import errors
   - Add missing `None` returns
   - Fix type mismatches

EXAMPLE FIX for common ruff issues:
```python
# Ruff might complain about:
# - Unused imports -> Remove them
# - Line too long -> Break lines
# - Missing whitespace -> Add proper spacing
# - f-string without placeholders -> Use regular string
```

EXAMPLE FIX for common mypy issues:
```python
# BEFORE:
def get_user(user_id):
    return User.get(user_id)


# AFTER:
def get_user(user_id: UUID) -> User | None:
    return User.get(user_id)
```

TESTING:
- [ ] `uv run ruff check .` passes with no errors
- [ ] `uv run mypy .` passes with no errors
- [ ] `uv run pytest tests/` passes all tests
- [ ] Code quality tools run in CI/CD pipeline

PRIORITY: High (code quality gates)

SPEC REFERENCE:
- Requirements: "Code standards", "Typing"
- Commands section in user message:
  - `uv run pytest <path>`
  - `uv run ruff check .`
  - `uv run mypy .`
