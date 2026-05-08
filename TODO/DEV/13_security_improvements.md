---
## DATA PROCESSING
---

### TASK: Security Audit & Fixes

FILE: src/mkobi/core/security.py, src/mkobi/api/routes/auth.py, src/mkobi/api/routes/upload.py

GOAL: Ensure all security best practices are followed

IMPLEMENT:

* **JWT Security** (src/mkobi/core/security.py):
  - Token expiration validation
  - Invalid token handling (401 Unauthorized)
  - Missing token handling (401 Unauthorized)
  - Secret key from env (JWT__SECRET_KEY)
  - Algorithm explicitly specified (not default)

* **Password Security**:
  - bcrypt usage (not md5, SHA, plaintext)
  - Password hash stored in DB (not plaintext)
  - No password logging
 

* **Upload Security** (src/mkobi/api/routes/upload.py):
  - Path traversal protection (../../file.csv)
  - Unsafe filenames handling (use secure_filename)
  - Oversized files handling (limit via config)
  - MIME-type validation (client + server side)
  - Rate limiting (protection from spam upload)

* **SQL Safety** (src/mkobi/db/repositories/*.py):
  - No raw unsafe SQL
  - Parameterized queries (SQLAlchemy ORM/Core)
  - No string interpolation for SQL (f-strings, +)
  - ORM used for all operations

* **Secrets/Config** (src/mkobi/config.py):
  - No hardcoded secrets
  - Env-based configuration (pydantic-settings)
  - Docker secrets support (_FILE suffix)
  - Nested env vars (DATABASE__HOST, DATABASE__PORT)
  - `.env` file only for development

LOGIC:

1. Review security.py for JWT best practices
2. Verify password hashing uses bcrypt
3. Check upload.py for path traversal, filename issues
4. Search for raw SQL: `grep -r "execute(" src/mkobi/db/`
5. Verify no hardcoded secrets in code
6. Test: try path traversal attack, oversized file upload
7. Test: JWT expiration, invalid token handling

DONE:

* [ ] JWT properly configured and validated
* [ ] Passwords securely hashed
* [ ] Upload security checks in place
* [ ] No raw SQL or string interpolation
* [ ] No hardcoded secrets
* [ ] Docker secrets supported
* [ ] Security tests pass

---

### TASK: Access Control Verification

FILE: src/mkobi/core/permissions.py, src/mkobi/api/deps.py

GOAL: Ensure proper access control throughout application

IMPLEMENT:

* Verify dashboard access check on every dashboard request
* Check editor/viewer/admin restrictions work
* Verify direct object access vulnerabilities fixed:
  - User cannot access other's dashboard
* Admin has full access
* Use StrEnum for role checks (not strings):
  - Good: `if user.role == UserRole.ADMIN:`
  - Bad: `if user.role == "admin":`

LOGIC:

1. Review permissions.py for access control logic
2. Check all API routes use proper dependency injection:
   - `require_dashboard_read_access`
   - `require_dashboard_write_access`
   - `require_dashboard_admin_access`
3. Verify StrEnum usage in permission checks
4. Test: viewer cannot edit, editor cannot admin
5. Test: user cannot access other's dashboard
6. Test: admin can access all dashboards

DONE:

* [ ] Dashboard access checked on every request
* [ ] Role-based permissions work correctly
* [ ] No direct object access vulnerabilities
* [ ] StrEnum used for all role checks
* [ ] Access control tests pass

---
