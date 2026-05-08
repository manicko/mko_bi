---
### TASK: Fix Layout API routes (405 Method Not Allowed)

FILE: src/mkobi/api/routes/layouts.py

GOAL: Add missing HTTP methods (PUT, DELETE) to Layout API routes

ERROR:
```
assert 405 == 403
assert 405 == 201
assert 405 == 200
assert 405 == 204
```

ISSUE:
The Layout API routes are missing HTTP methods for update (PUT) and delete (DELETE) operations. Tests expect these endpoints to exist but they return 405 Method Not Allowed.

Also, GET /layouts returns 404, indicating the route might not be properly registered.

IMPLEMENT:
* Add PUT /layouts/{layout_id} route for updating layouts
* Add DELETE /layouts/{layout_id} route for deleting layouts
* Verify GET /layouts and GET /layouts/{id} routes are properly registered

LOGIC:
1. Check `src/mkobi/api/routes/layouts.py` for registered routes
2. Add missing route handlers for PUT and DELETE
3. Ensure proper admin role validation
4. Verify GET routes are correctly defined

DONE:
* [ ] PUT /layouts/{id} route added
* [ ] DELETE /layouts/{id} route added
* [ ] GET /layouts returns 200
* [ ] All layout API tests pass

REFERENCE:
* `src/mkobi/api/routes/layouts.py`
* `tests/test_layouts.py`
---
