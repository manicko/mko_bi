---
## TASK: Fix test messages to use English
---

### PROBLEM

Some test assertions and error messages are in Russian, but the project requirements specify that all comments and logs should be in English.

Error observed:
```
AssertionError: Regex pattern did not match.
  Expected regex: 'dims должен быть словарём'
  Actual message: 'dims должен быть dict'
```

### ROOT CAUSE

Test files contain Russian language messages instead of English, which:
1. Violates the project requirement: "комментарии и логи на английском" (comments and logs in English)
2. Creates inconsistency between test messages

### FILES TO CHECK

- `tests/test_storage_manager.py` - Contains Russian messages
- All other test files for similar issues

### SOLUTION

1. Update test files to use English messages
2. Update regex patterns to match English messages
3. Ensure all new code uses English only

### EXAMPLES

Before:
```python
assert "dims должен быть словарём" in str(exc_info.value)
```

After:
```python
assert "dims must be a dictionary" in str(exc_info.value)
```

### VERIFICATION

1. Run `uv run pytest tests/ -v`
2. Check that all tests pass
3. Search for Russian text: `Select-String -Path tests/*.py -Pattern "[а-яА-Я]"` (or manually review)

### PRIORITY

Low - code quality improvement

### STATUS

- [ ] Issue identified
- [ ] All test messages updated to English
- [ ] Tests pass

---
