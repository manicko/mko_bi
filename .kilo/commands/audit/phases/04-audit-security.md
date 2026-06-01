---
name: 04-security
description: Security audit covering authentication, authorization, credential handling, input validation, and trust boundaries
agent: audit-executor
alwaysApply: false
problems-only: true
---

# Phase 04 Audit — Security

## Output Mode

`problems-only: true` — **only problems, bugs, and deviations are documented.**

- **Do NOT** write sections that say "X is correct" or "no issues found in Y".
- **Do NOT** include checklist rows where the check passes — omit them entirely.
- If a dimension has zero findings after investigation, **omit the dimension entirely**.
- Every finding must be actionable: it describes a real problem, its evidence (code/logs/output), and its impact.
- If `problems-only: false` were set, you would produce a full report with compliance statements. But it is `true`, so the report is exclusively findings.
- If you need to start or stop docker environment to check functional or run test you should run it following the documantation instruction in dev mode BUT you mast return it to the same status as before - running or stopped
---

## Discovery Stage

Before performing audit checks, discover the project's security architecture:

1. **Trust Boundary Discovery** — Identify entry points, map authentication mechanisms, discover authorization model, locate sensitive data paths.
2. **Credential Discovery** — Identify secret storage, map credential injection paths, discover password/session/token handling, find cryptography usage.
3. **Validation Discovery** — Identify validation entry points, map validation to trust boundaries, discover sanitization patterns, find file upload flows.
4. **Runtime Security Model** — Rate limiting, security error handling, audit logging, security headers and CORS.

---

## Mandatory Runtime Verification

**Before evaluating any checklist item, you MUST complete these steps. Skip only if a step is impossible — document why.**

### Step R1 — Credential Leak Search

Search the entire codebase for hardcoded secrets: passwords, API keys, tokens, private keys, and secrets.

- For each match, determine if it is: a hardcoded value (CRITICAL), an environment variable reference (OK), a placeholder/default that might be used in production (finding), or a test fixture (verify it's not the same value used in production).
- Check `.env*` files: if committed to the repo with real values, that is CRITICAL.
- Check Dockerfiles and docker-compose files for secrets baked into images via ARG/ENV.

### Step R2 — Token Generation and Validation Analysis

Read the authentication code end-to-end:

- Locate where tokens are created: verify signing algorithm is NOT `none` or weak. Verify key strength.
- Locate where tokens are validated: verify signature check is actually performed.
- Check token expiration: verify `exp` is set AND enforced at validation.
- Check for token revocation: if a user is deactivated, are their existing tokens still valid? If yes, that is a finding.

### Step R3 — Route-by-Route Access Control Verification

**For every route in the application:**

Read each route definition and verify:
1. Is authentication required? (Is there an auth dependency or middleware?)
2. If not, is it intentionally public? (e.g., login, health check)
3. Is authorization/permission checked? (Is the user's role/permission checked before the action?)
4. Is resource-level access control applied? (Can user A access user B's data via ID manipulation?)

- Every protected route without auth is CRITICAL.
- Every route without resource-level ACL where the URL contains a resource ID is HIGH.

### Step R4 — Password Handling Verification

Read the entire password lifecycle:

1. **Creation**: What algorithm? What cost factor?
2. **Storage**: Is the hash stored? Is plaintext ever logged, serialized, or stored?
3. **Verification**: Is comparison constant-time? (library function, not `==`)
4. **Reset**: Is the reset token cryptographically random? Does it expire?

For each step, provide file:line evidence.

### Step R5 — Input Attack Surface Analysis

Review each input processing path for injection vulnerabilities:

- **File upload**: Verify MIME type checking, file size limit, filename sanitization (path traversal), content validation before processing.
- **SQL injection**: Search for raw SQL with string interpolation. Any user input in SQL is CRITICAL.
- **Path traversal**: Search for user-supplied paths used in file operations. Each instance needs sanitization evidence.

### Step R6 — Rate Limiting Verification

- Read the rate limiting configuration.
- Is it applied to ALL authentication endpoints? Missing rate limiting on login = CRITICAL.
- Is it applied to upload endpoints? Missing rate limiting on upload = HIGH.
- Is the rate limit backing store shared (if multi-worker) or per-process? Per-process rate limiting in multi-worker deployment is insufficient.

### Step R7 — CORS and Security Headers

- Read the CORS configuration. Wildcard origins in production = CRITICAL.
- Check for security headers middleware: `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`, `Content-Security-Policy`.
- Verify CORS origins are validated at startup in production mode (fail-fast).

---

## Audit Scope

Authentication, authorization, credential management, input validation, rate limiting, password security, transport security.

---

## Audit Dimensions

### 1. Authentication Invariants

| Check | Description |
|-------|-------------|
| Authentication required on protected endpoints | Every non-public route has auth middleware. |
| Token validation at every trust boundary | Every entry point validates the token. |
| Token expiration enforced | Expired tokens are rejected. |
| Invalid/missing tokens return 401 | Correct HTTP status for auth failures. |
| Credentials never stored in plaintext | Only hashes stored. |
| Credential comparison uses constant-time algorithm | Timing attack prevention. |
| Authentication state managed securely | No session fixation or hijacking risks. |

**Evidence required:** Step R3 route-by-route analysis. Step R2 token analysis. Step R4 for credential handling.

### 2. Authorization Invariants

| Check | Description |
|-------|-------------|
| Authorization checked on every protected resource | Every resource access is authorized. |
| Role-based restrictions enforced | Roles are enforced, not just decorative. |
| Direct object access prevented (no IDOR) | Users cannot access other users' data via ID manipulation. |
| Admin privileges follow least-privilege principle | Admin has only necessary permissions. |
| Existence vs access distinction (404 vs 403) | Correct status codes for not-found vs forbidden. |
| Authorization decisions centralized | Single authorization logic, not scattered. |

**Evidence required:** Step R3 resource-level ACL analysis. For IDOR: read the code that fetches resources by ID and verify ownership/access check before returning data.

### 3. Credential & Secret Management

| Check | Description |
|-------|-------------|
| No hardcoded secrets in source code | All secrets from environment/config. |
| Secrets derived from environment variables | No hardcoded fallback secrets. |
| Secret injection supports file-based secrets | `_FILE` suffix or equivalent pattern. |
| Production refuses defaults or test credentials | App fails to start with insecure config. |
| JWT signing key is cryptographically strong | Key length and algorithm are secure. |
| Algorithm explicitly configured | Not relying on library defaults. |

**Evidence required:** Step R1 credential leak search results. Read the config module: verify production mode refuses to start with default/empty secrets.

### 4. Input Validation & Sanitization

| Check | Description |
|-------|-------------|
| All external input validated before processing | Every input is validated. |
| File uploads validated (MIME, size, path traversal) | Upload handler is secure. |
| SQL injection prevented | Parameterized queries only. |
| Invalid input produces clear error messages | User-friendly validation errors. |
| Error messages don't leak sensitive information | No stack traces, DB schema, or file paths in errors. |
| Validation happens at trust boundary | Input is validated at entry, not deep in logic. |

**Evidence required:** Step R5 attack surface analysis. For error messages: check the response body of error paths. Stack traces or DB details in errors = finding.

### 5. Rate Limiting & Abuse Prevention

| Check | Description |
|-------|-------------|
| Rate limiting on authentication endpoints | Login, register, reset are rate-limited. |
| Rate limiting on write operations (upload) | Upload endpoints are rate-limited. |
| Throttling configurable by environment | Different limits per environment. |
| Fail-closed in production | Rate limit errors are proper 429 responses. |
| Rate limit bypass not exploitable | No header or parameter to bypass. |

**Evidence required:** Step R6 analysis. Check the rate limit error response is a proper 429, not an unhandled exception.

### 6. Password Security Invariants

| Check | Description |
|-------|-------------|
| Passwords hashed with secure algorithm | bcrypt, scrypt, or argon2. |
| Password hashes never logged | No log statements with password or hash. |
| Minimum password length enforced | Validation rejects short passwords. |
| Temporary passwords are cryptographically random | Not predictable. |
| Password change requires current password verification | Re-auth on sensitive change. |

**Evidence required:** Step R4 full lifecycle analysis. Search for `logger` calls near password handling code.

### 7. Security Headers & CORS

| Check | Description |
|-------|-------------|
| CORS origins explicitly configured (no wildcards) | Specific origins only in production. |
| CORS validated at startup in production | Fail-fast on misconfiguration. |
| Security headers on responses | CSP, X-Frame-Options, etc. |
| HTTPS enforced | At app or infrastructure level. |

**Evidence required:** Step R7 analysis. If the app doesn't set headers, verify whether the reverse proxy does. Document the gap either way.

---

## Report Output

Write findings to: `.ai/audit/04-security/findings.md` using template `.ai/audit/templates/audit-findings.md`.

Use prefix `SEC-` for finding IDs.

**`problems-only: true` rules:**
- The report contains **only findings** — real problems discovered during investigation.
- Do NOT include sections, dimensions, or checklist rows where everything is correct.
- If after completing all Runtime Verification steps and all Audit Dimensions, no problems were found, write a single line: `No problems found in this phase.`
- Every finding MUST include:
  1. **Runtime evidence** — grep results, file:line code analysis, route-by-route table, token analysis output.
  2. **Severity justified by exploitability:** A hardcoded secret in production config is CRITICAL. A missing rate limit on login is CRITICAL.
