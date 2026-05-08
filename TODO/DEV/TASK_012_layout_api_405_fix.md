---
### TASK: Fix Layout API 405 Method Not Allowed errors
FILE: src/mkobi/api/routes/layouts.py
GOAL: Fix layout API tests returning 405 Method Not Allowed instead of expected status codes
IMPLEMENT:
* Check HTTP methods defined in layouts.py endpoints
* Verify endpoint paths match test expectations
* Check if endpoints require correct HTTP methods (POST, PUT, DELETE)
* Ensure `require_admin_role` dependency doesn't block with wrong HTTP method
LOGIC:
1. Run `uv run pytest tests/test_layouts.py -v -s` to see actual errors
2. Check `src/mkobi/api/routes/layouts.py` for:
   - Correct HTTP methods (POST for create, PUT for update, DELETE for delete)
   - Correct path parameters
   - Correct dependencies
3. Compare test expectations vs actual endpoint definitions
4. Fix routing/method mismatches
DONE:
* [ ] Endpoint definitions checked
* [ ] HTTP methods corrected
* [ ] `uv run pytest tests/test_layouts.py -v` passes
---
