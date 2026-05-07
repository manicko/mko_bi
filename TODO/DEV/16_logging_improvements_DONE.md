---
## LOGGING IMPROVEMENTS
---

### TASK: Improve Logging Practices

FILE: `src/mkobi/core/logging_config.py`, all Python files

GOAL: Ensure consistent and proper logging across the codebase

ISSUE DESCRIPTION:

1. **Inconsistent log levels**:
   - Some operations log at `info`, others at `warning` for similar events
   - Need to standardize what gets logged at each level

2. **Sensitive data in logs**:
   - `config.py` line 102: `logger.info("Пароль успешно захеширован")` - OK (not logging actual password)
   - But need to check: are passwords or tokens being logged anywhere?

3. **Missing structured logging**:
   - Using string formatting: `logger.info("User %s logged in", user_id)`
   - Could use structured logging (JSON) for better parsing

4. **Log configuration**:
   - `logging_config.py` sets up JSON logging
   - But need to verify it's applied consistently

IMPACT:
- Hard to debug issues
- Potential security issues (logging sensitive data)
- Inconsistent log analysis

FILES TO CHECK:
- `src/mkobi/core/logging_config.py` - Review configuration
- All files with `logger = logging.getLogger(__name__)` - Check usage
- `src/mkobi/config.py` - Check what gets logged

IMPLEMENTATION:

1. **Standardize log levels**:
   ```
   DEBUG: Detailed information, typically of interest only when diagnosing problems
   INFO: Confirmation that things are working as expected
   WARNING: An indication that something unexpected happened, but still operational
   ERROR: Due to a more serious problem, the software hasn't been able to perform some function
   ```

2. **Ensure no sensitive data is logged**:
   ```python
   # BAD:
   logger.info("User logged in: password=%s", password)
   
   # GOOD:
   logger.info("User logged in: user_id=%s", user_id)
   ```

3. **Use structured logging consistently**:
   ```python
   # If using JSON logging:
   logger.info("User logged in", extra={"user_id": user_id, "ip": ip_address})
   ```

4. **Review logging_config.py**:
   ```python
   # Ensure it configures:
   - Log format (JSON for production)
   - Log level from config
   - Log file path from config
   - Rotation if file logging enabled
   ```

EXAMPLE FIX:
```python
# BEFORE (inconsistent):
logger.info("Пароль успешно захеширован")  # Russian
logger.info("User authenticated: user_id=%s", user_id)  # English

# AFTER (consistent):
logger.info("Password hashed successfully", extra={"user_id": user_id})
logger.info("User authenticated", extra={"user_id": user_id})
```

TESTING:
- [ ] No passwords/tokens in log output
- [ ] Log levels used consistently
- [ ] JSON logging works in production mode
- [ ] All modules use `logger = logging.getLogger(__name__)`

PRIORITY: Medium (best practice, security)

SPEC REFERENCE:
- SPEC.md section 20: "Logging - логируются: upload, processing, errors, access events"
- Requirements: "logging"
