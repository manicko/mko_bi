---
name: 04-security
description: Security audit covering authentication, authorization, credential handling, input validation, and trust boundaries
agent: audit-executor
alwaysApply: false
---

# Phase 04 Audit — Security

**Executor:** audit-executor
**Status:** {pending|in-progress|complete}
**Validated:** {yes|no}

---

## Discovery Stage

Before performing audit checks, discover the project's security architecture:

1. **Trust Boundary Discovery**
   - Identify entry points (HTTP endpoints, file upload, message queues)
   - Map authentication mechanism(s)
   - Discover authorization model (RBAC, ABAC, or custom)
   - Locate sensitive data storage and transmission paths

2. **Credential Discovery**
   - Identify secret storage mechanism
   - Map credential injection paths (env vars, secret files, config)
   - Discover password/session/token handling
   - Find encryption/cryptography usage

3. **Input Validation Discovery**
   - Identify validation entry points
   - Map validation to trust boundaries
   - Discover sanitization patterns
   - Find file upload processing flows

4. **Runtime Security Model**
   - Rate limiting and abuse prevention
   - Error handling for security events
   - Audit logging for security-relevant actions
   - Security headers and CORS configuration

---

## Audit Dimensions

### 1. Authentication Invariants

Verify identity verification is robust:

| Check | Status | Evidence |
|-------|--------|----------|
| Authentication required on protected endpoints | | |
| Token validation at every trust boundary | | |
| Token expiration enforced | | |
| Invalid/missing tokens return 401 Unauthorized | | |
| Credentials never stored in plaintext | | |
| Credential comparison uses constant-time algorithm | | |
| Authentication state managed securely | | |

---

### 2. Authorization Invariants

Verify access control is correctly enforced:

| Check | Status | Evidence |
|-------|--------|----------|
| Authorization checked on every protected resource | | |
| Role-based restrictions enforced | | |
| Direct object access prevented (no IDOR) | | |
| Admin privileges follow least-privilege principle | | |
| Existence vs access distinction (404 vs 403) | | |
| Authorization decisions centralized | | |

---

### 3. Credential & Secret Management

Verify secrets are handled securely:

| Check | Status | Evidence |
|-------|--------|----------|
| No hardcoded secrets in source code | | |
| Secrets derived from environment variables | | |
| Secret injection supports file-based secrets (e.g., _FILE suffix) | | |
| Production refuses defaults or test credentials | | |
| JWT signing key is cryptographically strong | | |
| Algorithm explicitly configured (not default) | | |

---

### 4. Input Validation & Sanitization

Verify boundary defenses:

| Check | Status | Evidence |
|-------|--------|----------|
| All external input validated before processing | | |
| File uploads validated (MIME type, size, path traversal) | | |
| SQL injection prevented (parameterized queries) | | |
| Invalid input produces clear error messages | | |
| Error messages don't leak sensitive information | | |
| Validation happens at trust boundary | | |

---

### 5. Rate Limiting & Abuse Prevention

Verify resource protection:

| Check | Status | Evidence |
|-------|--------|----------|
| Rate limiting on authentication endpoints | | |
| Rate limiting on write operations (upload) | | |
| Throttling configurable by environment | | |
| Fail-closed in production, fail-open in development | | |
| Rate limit bypass not exploitable | | |

---

### 6. Password Security Invariants

Verify password handling is secure:

| Check | Status | Evidence |
|-------|--------|----------|
| Passwords hashed with secure algorithm (bcrypt, scrypt, argon2) | | |
| Password hashes never logged | | |
| Minimum password length enforced | | |
| Temporary passwords are cryptographically random | | |
| Password change requires current password verification | | |

---

### 7. Security Header & CORS

Verify transport security:

| Check | Status | Evidence |
|-------|--------|----------|
| CORS origins explicitly configured (no wildcards) | | |
| CORS validated at startup in production | | |
| Security headers on responses (CSP, X-Frame-Options, etc.) | | |
| HTTPS enforced or enforced by infrastructure | | |

---

## Report Output

Write findings to: `.ai/audit/04-security/findings.md` using template `.ai/audit/templates/audit-findings.md`.

Use prefix `SEC-` for finding IDs.