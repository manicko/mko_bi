---
id: configuration
domain: backend
tags:
  - configuration
  - pydantic-settings
  - secrets
  - environment-variables
  - docker-secrets
  - production-security
related:
  - backend-architecture
  - logging
  - security-overview
  - deployment
---

# Configuration

## Overview

The application uses **pydantic-settings** for configuration management with a multi-source priority system. All configuration is loaded into a singleton `Settings` instance via `get_config()`.

**Implementation:** `src/mkobi/config.py`

See [Backend Architecture](architecture.md) for the startup lifecycle and how configuration is loaded during initialization. See [Deployment](../10-deployment/deployment.md) for Docker secrets and production environment setup.

## Config Source Priority

Settings are loaded from multiple sources. The first matching value wins:

| Priority | Source                                      | Description                                    |
| -------- | ------------------------------------------- | ---------------------------------------------- |
| 1 (highest) | **Environment variables**                | `DATABASE__PASSWORD`, `JWT__SECRET_KEY`, etc.  |
| 2        | **Docker secrets files** (`_FILE` suffix)   | `DATABASE__PASSWORD_FILE=/run/secrets/db_password` |
| 3        | **`.env` file**                             | Development convenience via pydantic-settings  |
| 4        | **`app.yaml`**                              | Non-sensitive defaults (hosts, ports, paths)   |
| 5 (lowest) | **Code defaults**                         | Field defaults in `Settings` class             |

This is implemented via `Settings.settings_customise_sources()` which returns sources in priority order.

## Environment Variables

All environment variables use the double-underscore (`__`) delimiter for nesting:

| Variable                      | Nested Path              | Default        | Description                     |
| ----------------------------- | ------------------------ | -------------- | ------------------------------- |
| `ENV`                         | `environment`            | `development`  | Application environment         |
| `DATABASE__HOST`              | `database.host`          | `localhost`    | PostgreSQL host                 |
| `DATABASE__PORT`              | `database.port`          | `5432`         | PostgreSQL port                 |
| `DATABASE__DBNAME`            | `database.dbname`        | `bidb`         | Main database name              |
| `DATABASE__USER`              | `database.user`          | `mkobi_app`    | Database user                   |
| `DATABASE__PASSWORD`          | `database.password`      | `None`         | Database password (secret)      |
| `DATABASE__TEST_DBNAME`       | `database.test_dbname`   | `bidb_test`    | Test database name              |
| `JWT__SECRET_KEY`             | `jwt.secret_key`         | `None`         | JWT signing key (secret)        |
| `JWT__ALGORITHM`              | `jwt.algorithm`          | `HS256`        | JWT signing algorithm           |
| `JWT__ACCESS_TOKEN_EXPIRE_MINUTES` | `jwt.access_token_expire_minutes` | `15` | Token TTL      |
| `REDIS__HOST`                 | `redis.host`             | `localhost`    | Redis host                      |
| `REDIS__PORT`                 | `redis.port`             | `6379`         | Redis port                      |
| `ADMIN_USERNAME`              | `admin_username`         | `admin`        | Admin user email                |
| `ADMIN_PASSWORD`              | `admin_password`         | `admin`        | Admin user password (secret)    |
| `AUTO_MIGRATE`                | `auto_migrate`           | `false`        | Auto-apply Alembic migrations   |
| `RECREATE_TEST_DB`            | `recreate_test_db`       | `false`        | Recreate test DB on startup. Set to `true` in test environment for automatic test database recreation. |
| `STALE_FILE_THRESHOLD_HOURS`  | `stale_file_threshold_hours` | `24`      | Temp file cleanup threshold     |
| `RATE_LIMITER_FAIL_CLOSED`    | `rate_limiter_fail_closed` | `true`      | Fail-closed on Redis outage     |
| `CORS_ORIGINS`                | `cors_origins`           | `[]`           | Allowed CORS origins            |
| `TEMP_PASSWORD_TTL_SECONDS`   | `temp_password_ttl_seconds` | `86400`     | Temp password Redis TTL (min 60s) |

## Secrets Management

### Docker Secrets Support

The application supports Docker secrets through the `_FILE` suffix pattern:

```bash
# Instead of passing the secret directly:
DATABASE__PASSWORD=supersecret

# Point to a file containing the secret:
DATABASE__PASSWORD_FILE=/run/secrets/db_password
```

The custom `SecretsFileSource` class scans all environment variables ending with `_FILE`, reads the referenced file, and injects the value under the base variable name (e.g., `DATABASE__PASSWORD`).

### Secrets in Code

- Secrets are **never logged** — the `_log_initialization()` method logs only non-sensitive settings
- Secrets are **never stored in `app.yaml`** — the YAML file contains only non-sensitive configuration
- The `extra="ignore"` model config prevents unknown fields from being stored

## Production Credential Enforcement

The application **refuses to start in production** if default credentials are detected:

### Database Password

- `DATABASE__PASSWORD` must be explicitly set in production
- In development, placeholder passwords (e.g., `postgres`) are permitted but not recommended
- The placeholder validation runs only in production mode, allowing easier development setup

### Admin Credentials

```python
# In production, this raises ValueError:
# "Default admin credentials are not allowed in production."
if environment == "production" and (admin_username == "admin" or admin_password == "admin"):
    raise ValueError(...)
```

**Required in production:**
- `ADMIN_USERNAME` must be explicitly set (not `admin`)
- `ADMIN_PASSWORD` must be explicitly set (not `admin`)

In development, default credentials are permitted but a warning is logged.

### JWT Secret Key

- `JWT__SECRET_KEY` must be explicitly set in production
- The Docker Compose production config uses `${JWT__SECRET_KEY:?...}` syntax to fail on startup if unset

### Database Password

- `DATABASE__PASSWORD` must be explicitly set in production
- Same fail-if-unset pattern in Docker Compose via `${DATABASE__PASSWORD:?...}`

### CORS Origins

- `CORS_ORIGINS` must be explicitly configured in production
- The application validates CORS configuration at startup and raises an error if origins are not set in production mode

### Temp Password TTL

- `TEMP_PASSWORD_TTL_SECONDS` controls the Redis TTL for temporarily stored passwords (default: `86400` = 24 hours)
- A Pydantic `field_validator` enforces a minimum value of `60` seconds
- Passwords are stored in Redis via `TempPasswordStore` and automatically expire after the configured TTL
- This setting affects both admin password reset and registration approval flows
- Passwords are also deleted immediately upon retrieval (single-use pattern)

## YAML Configuration

The `app.yaml` file (at `src/mkobi/settings/app.yaml`) contains only non-sensitive settings:

- Hosts and ports
- File paths
- Feature flags
- Default values

It is loaded via pydantic-settings `YamlConfigSettingsSource` and has lower priority than environment variables, Docker secrets, and `.env` files.

## Settings Singleton

Configuration is accessed through a module-level singleton:

```python
from mkobi.config import get_config

config = get_config()
```

The `get_config()` function uses a cached global `_settings` instance, ensuring a single configuration source throughout the application.

## Key Properties

The `Settings` class exposes convenient properties that map to nested config values:

| Property              | Source Path                   | Description                    |
| --------------------- | ----------------------------- | ------------------------------ |
| `DATABASE_URL`        | `database.database_url`       | Full asyncpg connection URL    |
| `TEST_DATABASE_URL`   | `database.test_database_url`  | Test database connection URL   |
| `jwt_secret_key`      | `jwt.secret_key`              | JWT signing key                |
| `upload_temp_dir`     | `upload.temp_dir`             | Temp file directory            |
| `max_file_size`       | `upload.max_file_size_mb`     | Max upload size in bytes       |
| `allowed_file_types`  | `upload.allowed_extensions`   | Allowed file extensions        |
| `allowed_mime_types`  | `upload.allowed_mime_types`   | Allowed MIME types             |
| `log_level`           | `logging.level`               | Logging level                  |

## Cross-References

- [Backend Architecture](architecture.md) — System architecture and startup lifecycle
- [Logging](logging.md) — Logging configuration and standards
- [Security](../08-security/) — Security configuration details
- [Deployment](../10-deployment/deployment.md) — Production deployment and Docker Compose
- [Security Overview](../08-security/security-overview.md) — Production credential enforcement and secrets management
