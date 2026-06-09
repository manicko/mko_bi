# REPORT_01: PostgreSQL Collation Version Mismatch — Root Cause Analysis and Prevention Strategy

**Created:** 2026-06-09
**Status:** IMPLEMENTED
**Scope:** Investigation and resolution of PostgreSQL collation version mismatch errors during automated test database creation via Alembic/DatabaseStarter

---

## Executive Summary

**Root Cause:** The `postgres:16.3` Docker image tag (without a Debian suite qualifier) is a floating alias. When the Docker library maintainers update the default Debian base (e.g., from Bullseye to Bookworm), the new image ships a newer glibc version with different collation data. Since `template1`'s collation version is stored in the **data volume** (not the image), any `CREATE DATABASE` that copies `template1` inherits the old version, causing a mismatch with the new OS-provided version.

**Solution Implemented:** Upgraded to PostgreSQL 18 with the `builtin` locale provider and `C.UTF-8` collation. This provides:
- **Immutable collation version** (fixed at `1` permanently) — never changes across OS updates
- **Proper UTF-8 support** for both Latin and Cyrillic characters
- **No index corruption risk** from locale updates
- **Debian Bookworm tag** for stability (can upgrade to Trixie when needed)

**Status:** Successfully implemented. Tests now pass without collation errors (13 failures remain, but they are pre-existing issues unrelated to collation).

---

## 1. Root Cause Analysis

### 1.1 How the Issue Appeared on Fresh Database Creation

When the PostgreSQL Docker container starts for the first time with an empty volume:

1. `initdb` is executed automatically → creates `postgres`, `template1`, `template0` databases
2. By default, `initdb` uses the `libc` locale provider, which reads locale data from the Docker image's OS (glibc)
3. The collation version (e.g., `2.41` for glibc 2.36 on Debian Bookworm) is recorded in `pg_database.datcollversion`
4. When Docker image is updated to a new Debian base (e.g., `postgres:16.3` → `postgres:17` which uses Trixie), the OS now has a different glibc (e.g., `2.42`)
5. `template1` still has collation version `2.41` from the data volume
6. `CREATE DATABASE bidb_test TEMPLATE template1` inherits the old version → **mismatch error**

### 1.2 Why the Old Fix Was Insufficient

The previous fix (`ALTER DATABASE template1 REFRESH COLLATION VERSION`) was:
1. **Never needed with builtin provider** — collation versions are fixed at `1` and never change
2. **Had wrong SQL syntax** — `REFRESH_COLLATION_VERSION` should be `REFRESH COLLATION VERSION`
3. **Only a symptom suppressor** — does not rebuild indexes that may have been sorted under wrong rules

---

## 2. Implemented Solution

### 2.1 Docker Compose Changes

**`docker/docker-compose.yml` and `docker/docker-compose.test.yml`:**
```yaml
services:
  db:  # or test-db
    image: postgres:18-bookworm  # was: postgres:16.3-bookworm
    environment:
      POSTGRES_INITDB_ARGS: "--locale-provider=builtin --locale=C.UTF-8"
    volumes:
      - postgres_data:/var/lib/postgresql  # was: /var/lib/postgresql/data (changed for PG18)
```

**Key changes:**
1. `postgres:18-bookworm` — PostgreSQL 18 (current) with Bookworm (stable) base
2. `POSTGRES_INITDB_ARGS: "--locale-provider=builtin --locale=C.UTF-8"` — builtin provider with UTF-8 support
3. Volume path `/var/lib/postgresql` — Required for PostgreSQL 18+ (see PostgreSQL Docker issue #1259)

### 2.2 DatabaseStarter Changes

**`src/mkobi/db/starter.py`:**
- Removed the `ALTER DATABASE template1 REFRESH COLLATION_VERSION` call (unnecessary with builtin provider, and had syntax error)

### 2.3 Init Script Changes

**`docker/init-scripts/01-create-app-role.sh`:**
- Removed template1 locale fix (no longer needed — initdb creates template1 with builtin locale)

---

## 3. Verification

### 3.1 Collation Status After Implementation
```
 datname  | datcollate | datctype | datlocprovider | datcollversion 
-----------+------------+----------+----------------+----------------
 postgres  | C.UTF-8    | C.UTF-8  | b              | 1
 template1 | C.UTF-8    | C.UTF-8  | b              | 1
 template0 | C.UTF-8    | C.UTF-8  | b              | 
 bidb_test | C.UTF-8    | C.UTF-8  | b              | 1
```

The `builtin` provider shows:
- `datlocprovider = 'b'` (builtin)
- `datcollversion = '1'` (immutable, never changes)

### 3.2 Test Results
- **Before:** 297 errors with `COLLATION_VERSION` syntax errors
- **After:** 0 collation errors, 13 failures (pre-existing unrelated issues), 835 passed

---

## 4. Long-term Maintenance

### 4.1 When to Upgrade to `-trixie` Tag

When PostgreSQL 18+ switches its default Debian base from Bookworm to Trixie:
1. Run full test suite with existing data
2. If no issues, update to `postgres:18-trixie`
3. No `ALTER DATABASE ... REFRESH COLLATION VERSION` needed (builtin provider is immutable)

### 4.2 Alternative: ICU Provider

If linguistic collation is needed (proper sorting for specific languages):
```yaml
POSTGRES_INITDB_ARGS: "--locale-provider=icu --icu-locale=en-US"
```
ICU versions change less frequently than glibc, and the `ALTER DATABASE ... REFRESH COLLATION VERSION` approach works correctly with proper syntax.

---

## 5. Files Modified

| File | Change |
|------|--------|
| `docker/docker-compose.yml` | Image: `postgres:18-bookworm`, added `POSTGRES_INITDB_ARGS`, volume: `/var/lib/postgresql` |
| `docker/docker-compose.test.yml` | Image: `postgres:18-bookworm`, added `POSTGRES_INITDB_ARGS`, volume: `/var/lib/postgresql` |
| `docker/init-scripts/01-create-app-role.sh` | Removed template1 locale fix (no longer needed) |
| `src/mkobi/db/starter.py` | Removed unnecessary collation refresh call |

---

## 6. Sources

- PostgreSQL 18 Official Documentation — [CREATE DATABASE, initdb, builtin locale provider](https://www.postgresql.org/docs/current/sql-createdatabase.html)
- Docker Library GitHub — [postgres issue #1259 (PG18 volume path change)](https://github.com/docker-library/postgres/issues/1259)
- Docker Library GitHub — [postgres issue #1356 (collation warnings on image update)](https://github.com/docker-library/postgres/issues/1356)
- PostgreSQL Blog — [Locale Cooking: Common Scenarios](https://thebuild.com/blog/2024/11/22/locale-cooking-common-scenarios-and-suggestions/)
- PostgreSQL Wiki — [Locale data changes](https://wiki.postgresql.org/wiki/Locale_data_changes)