---
## DATA PROCESSING
---

### TASK: Standardize Logging

FILE: src/mkobi/**/*.py

GOAL: Ensure all log messages are in English and use proper logging

IMPLEMENT:

* Replace any `print()` statements with `logger` calls
* Ensure all log messages are in English (not Russian)
* Verify proper logger initialization:
  ```python
  import logging
  logger = logging.getLogger(__name__)
  ```
* Check log levels are appropriate:
  - INFO: normal operations (upload, processing, auth)
  - WARNING: potential issues
  - ERROR: actual errors with stack traces
  - DEBUG: only for development
* Verify logging_config.py is properly configured
* Check logs go to both file and stdout (for Docker)

LOGIC:

1. Search for `print(` in Python files: `grep -r "print(" src/mkobi/`
2. Replace all print() with logger calls
3. Search for Russian text in log messages
4. Translate to English
5. Verify logging_config.py sets up handlers correctly
6. Test: run app and check log output

DONE:

* [ ] No print() statements in production code
* [ ] All log messages in English
* [ ] Logger properly initialized in all files
* [ ] Log levels appropriate
* [ ] Logging works in Docker environment

---

### TASK: Add Missing Log Points

FILE: src/mkobi/api/routes/*.py, src/mkobi/services/*.py, src/mkobi/data/**/*.py

GOAL: Add logging for key business events

IMPLEMENT:

* Add logging for:
  - Upload events (start, complete, failure)
  - Processing events (start, steps, complete, failure)
  - Auth events (login success/failure)
  - Errors with context (not just "Error occurred")
* Ensure log context includes:
  - User ID where applicable
  - Dashboard ID where applicable
  - Task ID for background tasks
  - File names for uploads
* Add structured logging where helpful

LOGIC:

1. Review all API routes for logging coverage
2. Review all services for logging coverage
3. Review data processing pipeline for logging
4. Add missing log points
5. Test: trigger operations and verify logs

DONE:

* [ ] Upload events logged
* [ ] Processing events logged
* [ ] Auth events logged
* [ ] Errors logged with context
* [ ] Log messages are informative

---
