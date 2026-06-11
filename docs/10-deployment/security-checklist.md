---
id: security-checklist
domain: deployment
tags:
  - security
  - deployment
  - production
  - checklist
related:
  - deployment
  - security-overview
  - configuration
---

## Purpose

This document provides a production security checklist for deploying the mkobi BI Dashboard system. Use this checklist to verify all security-critical configurations before going to production.

## Main Concepts

- Rate limiting is a critical defense layer that must be configured correctly for production
- Fail-closed mode prevents attackers from exploiting Redis outages to bypass rate limits
- All secrets must be explicitly configured with no defaults in production

## Rate Limiting Security Configuration

### Fail-Closed Rate Limiting

The rate limiter is Redis-based and has configurable fail-open/fail-closed behavior:

| Setting | Development Default | Production Default | Recommendation |
| --- | --- | --- | --- |
| `RATE_LIMITER_FAIL_CLOSED` | `false` (fail-open) | `true` (fail-closed) | Always `true` in production |

#### Behavior

- **Fail-open** (`RATE_LIMITER_FAIL_CLOSED=false`): Requests are allowed through when Redis is unavailable. Use only for development and availability-first deployments.
- **Fail-closed** (`RATE_LIMITER_FAIL_CLOSED=true`): Requests are rejected with HTTP 429 when the rate limiter cannot connect to Redis. This is the secure default for production.

#### Log Messages

When Redis is unavailable:

| Mode | Log Level | Message |
| --- | --- | --- |
| Fail-open | WARNING | "Rate limiter fail-open: allowing request for key X (Redis unavailable)" |
| Fail-closed | CRITICAL | "Rate limiter FAIL-CLOSED: rejecting request for key X (Redis unavailable)" |

## Required Production Variables

The following environment variables **must** be set explicitly in production. Docker Compose will fail to start if unset:

| Variable | Description | Required In Production |
| --- | --- | --- |
| `DATABASE__PASSWORD` | Database password for `mkobi_app` role | Yes |
| `JWT__SECRET_KEY` | JWT signing secret (256-bit random) | Yes |
| `RATE_LIMITER_FAIL_CLOSED` | Rate limiter failure mode | Yes (set to `true`) |
| `CORS_ORIGINS` | Allowed CORS origins (JSON array) | Yes |

## Optional Security Hardening

| Variable | Default | Production Recommendation |
| --- | --- | --- |
| `LOGGING__LEVEL` | `INFO` | Set to `WARNING` to reduce log verbosity |
| `ADMIN_USERNAME` | `admin` | Must be explicitly set (non-default) |
| `ADMIN_PASSWORD` | `admin` | Must be explicitly set (non-default) |

## Docker Compose Production Check

Run this command to verify your production configuration:

```bash
docker compose -f docker/docker-compose.yml config --services
```

Verify the `app` service includes:

```yaml
environment:
  RATE_LIMITER_FAIL_CLOSED: ${RATE_LIMITER_FAIL_CLOSED:-true}
```

## Security Verification Steps

1. **Rate Limiter Test**: Verify Redis connectivity is required for requests to succeed when `RATE_LIMITER_FAIL_CLOSED=true`
2. **File Upload Limits**: Confirm `UPLOAD__MAX_FILE_SIZE_MB` is appropriate for your data
3. **CORS Validation**: Ensure `CORS_ORIGINS` contains only your production domain(s)
4. **JWT Secret**: Verify `JWT__SECRET_KEY` is at least 32 bytes of random data
5. **Admin Credentials**: Confirm `ADMIN_USERNAME` and `ADMIN_PASSWORD` are not default values

## Test Port Exposure in CI/CD

The test compose file (`docker/docker-compose.test.yml`) exposes database and application ports to the host for convenient local test execution. In CI/CD environments, avoid exposing these ports for security:

```bash
# Instead of relying on exposed ports, use:
docker compose -f docker/docker-compose.test.yml exec app uv run pytest tests/

# Or run tests inside the container network:
docker compose -f docker/docker-compose.test.yml exec test-app /app/.venv/bin/pytest tests/
```

**Rationale:** While port exposure is acceptable for local development (security risk is LOW — test databases contain no production data), CI/CD environments may have different network security boundaries. Running tests inside the container via `docker compose exec` keeps ports isolated within the Docker network.

## Cross-References

- [Deployment](deployment.md) — Production deployment procedures
- [Security Overview](../08-security/security-overview.md) — Rate limiting implementation details
- [Configuration](../06-backend/configuration.md) — Environment variables reference