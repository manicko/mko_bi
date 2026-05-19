# 02 Migration Consolidation - Research

**Researched:** 2026-05-19
**Domain:** Alembic migration squashing / consolidation
**Confidence:** HIGH

## Summary

This research investigates how to consolidate 16 Alembic migration files in `alembic/versions/` into a single initial migration. The project is pre-production with no deployed versions or real data — old migrations only reflect development churn.

After analyzing all 16 migration files, the SQLAlchemy models, the database schema docs, and the Alembic configuration, the consolidation is straightforward: use `7130ecb0388c_true_initial_migration.py` as the structural base and fold in the incremental changes that are not yet reflected in that file.

**Primary recommendation:** Create a single new migration file that creates all 5 PostgreSQL ENUM types, all 10 tables (including `registration_requests` which is missing from the base migration), all indexes (including the UPSERT unique index and the JSONB expression index), the `dashboard_filters` many-to-many table with its index, the `update_updated_at_column()` trigger function with triggers on 5 tables, the `users.email` CHECK constraint, and proper TEXT-to-VARCHAR column type changes. Then delete all 16 old files.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Alembic | >=1.18.4 | Database migrations | Project standard, already in use |
| SQLAlchemy | >=2.0.29 | ORM + DDL generation | Project standard, async with asyncpg |
| PostgreSQL | 15+ | Database | Project standard |
| asyncpg | >=0.30.0 | Async PostgreSQL driver | Required by SQLAlchemy async |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `alembic check` | Built-in | Verify no pending changes | Post-consolidation validation |
| `psql \d` | PostgreSQL CLI | Schema comparison | Manual verification against old chain |
| `op.execute()` | Alembic DDL | Raw SQL for complex DDL | ENUM creation, trigger functions, expression indexes |
| `postgresql.ENUM` | SQLAlchemy dialect | Idempotent ENUM creation | `checkfirst=True` pattern |

**Installation:** No new packages required — all tooling already installed.

## Architecture Patterns

### Recommended Project Structure

```
alembic/
├── versions/
│   ├── <new_revision>_initial_consolidated.py   # THE ONLY migration file
│   └── __pycache__/                              # (auto-generated)
├── env.py                                        # (unchanged)
├── script.py.mako                                # (unchanged)
└── alembic.ini                                   # (unchanged)
```

### Pattern 1: Consolidated Initial Migration Structure

**What:** A single migration file that creates the entire schema from scratch.
**When to use:** Pre-production cleanup of development migration history.

```python
"""Initial consolidated migration.

Creates the complete database schema as of 2026-05-19.
Replaces all 16 previous migration files which only reflected development churn.

Revision ID: <new_revision>
Revises:
Create Date: <date>

"""
from collections.abc import Sequence

from alembic import op
from sqlalchemy.dialects.postgresql import ENUM

revision: str = '<new_revision>'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create complete schema: enums, tables, indexes, triggers, constraints."""

def downgrade() -> None:
    """Drop all tables, enums, and database objects."""
```

### Pattern 2: Idempotent Raw SQL with `checkfirst=True`

**What:** Use raw SQL with `IF NOT EXISTS` / `IF EXISTS` guards via `op.execute()` for complex DDL that Alembic's high-level API cannot express.
**When to use:** ENUM types, trigger functions, expression indexes, CHECK constraints, `DROP TRIGGER IF EXISTS`.

```python
# ENUM creation (idempotent)
user_role_enum = ENUM('admin', 'editor', 'viewer', name='user_role')
user_role_enum.create(op.get_bind(), checkfirst=True)

# Trigger function (idempotent - CREATE OR REPLACE)
op.execute("""
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
""")

# Trigger creation (idempotent)
op.execute("""
    DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_trigger WHERE tgname = 'update_users_updated_at'
        ) THEN
            CREATE TRIGGER update_users_updated_at
            BEFORE UPDATE ON users
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        END IF;
    END $$;
""")

# Expression index (raw SQL required)
op.execute(
    "CREATE UNIQUE INDEX uq_aggregated_data_dashboard_graph_dims "
    "ON aggregated_data (dashboard_id, graph_id, (dims::text))"
)
```

### Pattern 3: Operation Ordering

**What:** Group operations in dependency order within `upgrade()`.
**When to use:** Always — ensures foreign key references resolve correctly.

```
1. ENUM types (no dependencies)
2. Tables without FK dependencies (users, layouts, filters)
3. Tables with FK dependencies (dashboards, graphs, dashboard_access, 
   dashboard_filters, processing_configs, processing_logs, 
   aggregated_data, registration_requests)
4. Indexes on all tables
5. CHECK constraints
6. Trigger function + triggers
```

### Anti-Patterns to Avoid

- **Don't use `op.create_table()` for the consolidated migration** — the existing migration uses raw `CREATE TABLE IF NOT EXISTS` SQL which is more explicit about column types, defaults, and constraints. Stick with the established pattern.
- **Don't forget the `registration_requests` table** — it was added by migration `a1e404502aac` and is NOT in the base `7130ecb0388c` file.
- **Don't forget the `registration_status` ENUM** — it's a 6th PostgreSQL ENUM not present in the base migration.
- **Don't forget the `update_updated_at_column()` trigger function and 5 triggers** — added by `ce58bba5d461`.
- **Don't forget the `users_email_length_check` CHECK constraint** — added by `ce58bba5d461`.
- **Don't forget the `uq_aggregated_data_dashboard_graph_dims` expression unique index** — added by `91f5436a3098` and fixed by `a2b3c4d5e6f7`.
- **Don't forget the `idx_processing_logs_dashboard_id` index** — added by `3f7a1b2c9d0e`.
- **Don't forget the `idx_aggregated_data_dashboard_graph` composite index** — added by `ce58bba5d461`.
- **Don't use `op.drop_table()` without `IF EXISTS CASCADE`** — the downgrade must handle objects that may not exist.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ENUM creation | `CREATE TYPE` raw SQL | `postgresql.ENUM.create(checkfirst=True)` | Alembic tracks ENUMs, handles dialect differences |
| Schema comparison | Custom diff logic | `alembic check` command | Built-in, compares models to DB state |
| Migration file generation | Manual file creation | `alembic revision -m "message"` | Ensures proper header format, timestamp |
| Table DDL | `op.create_table()` | Raw `CREATE TABLE IF NOT EXISTS` SQL | Matches existing pattern, more control over types |

**Key insight:** The consolidation itself is a one-time manual operation — there's no library for "squash these N migrations into one." The value is in getting the final `upgrade()` and `downgrade()` correct.

## Common Pitfalls

### Pitfall 1: Missing the `registration_requests` table and `registration_status` ENUM

**What goes wrong:** The base migration `7130ecb0388c` doesn't include the `registration_requests` table — it was added later by `a1e404502aac`. If you only use the base file, you lose this table entirely.
**Why it happens:** The base migration was created before the registration feature was added.
**How to include:** Add the `registration_status` ENUM creation and the full `registration_requests` table (with `INET` column, `UUID` FK to `users`, `VARCHAR(255)` email, etc.) to the consolidated migration.
**Warning signs:** Missing table in `\d` output, `NoReferencedTableError` for FK.

### Pitfall 2: Forgetting the `updated_at` columns on `users` and `layouts`

**What goes wrong:** The base migration creates `users` without `updated_at` and `layouts` without `updated_at`. These were added by `20260507141843` and `20260508145000` respectively.
**Why it happens:** The columns were added incrementally after the base migration.
**How to include:** Add `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()` to both `users` and `layouts` table definitions.
**Warning signs:** `updated_at` column missing in `\d users` or `\d layouts`.

### Pitfall 3: TEXT vs VARCHAR(255) column types

**What goes wrong:** The base migration uses `TEXT` for `email`, `password_hash`, `name`, and `message` columns. Later migrations (`a1e404502aac`) changed these to `VARCHAR(255)`.
**Why it happens:** The schema evolved from TEXT to VARCHAR for length-constrained fields.
**How to include:** Use `VARCHAR(255)` for: `users.email`, `users.password_hash`, `layouts.name`, `dashboards.name`, `graphs.name`, `filters.name`, `processing_logs.message`, `registration_requests.email`.
**Warning signs:** Column type mismatch when comparing `\d` output.

### Pitfall 4: Missing trigger function and triggers

**What goes wrong:** The `update_updated_at_column()` trigger function and 5 triggers (on `dashboards`, `processing_configs`, `layouts`, `graphs`, `users`) were added by `ce58bba5d461`. Without them, `updated_at` columns won't auto-update.
**Why it happens:** Triggers were a later addition for automatic timestamp management.
**How to include:** Create the trigger function with `CREATE OR REPLACE FUNCTION`, then create each trigger with `DO $$` guard blocks.
**Warning signs:** `updated_at` doesn't change on UPDATE, missing from `\df` and `\dT`.

### Pitfall 5: Missing the `users_email_length_check` CHECK constraint

**What goes wrong:** The CHECK constraint `length(email) <= 255` on `users` was added by `ce58bba5d461`.
**How to include:** Add via `op.execute()` with a `DO $$` guard block.
**Warning signs:** Missing from `\d users` constraint list.

### Pitfall 6: Missing the `idx_aggregated_data_dashboard_graph` composite index

**What goes wrong:** The composite index on `(dashboard_id, graph_id)` was added by `ce58bba5d461` and is separate from the individual column indexes.
**How to include:** Add `CREATE INDEX IF NOT EXISTS idx_aggregated_data_dashboard_graph ON aggregated_data(dashboard_id, graph_id)`.
**Warning signs:** Missing from `\d aggregated_data`.

### Pitfall 7: Missing the expression unique index for UPSERT

**What goes wrong:** The `uq_aggregated_data_dashboard_graph_dims` unique index on `(dashboard_id, graph_id, (dims::text))` is required for `ON CONFLICT` UPSERT operations. It was added by `91f5436a3098` and fixed by `a2b3c4d5e6f7`.
**How to include:** Use raw SQL: `CREATE UNIQUE INDEX uq_aggregated_data_dashboard_graph_dims ON aggregated_data (dashboard_id, graph_id, (dims::text))`.
**Warning signs:** UPSERT operations fail with "no unique or exclusion constraint matching."

### Pitfall 8: Incorrect downgrade ordering

**What goes wrong:** Dropping tables in wrong order causes FK violations. Dropping ENUMs before tables causes type errors.
**How to avoid:** Drop in reverse dependency order: triggers first, then tables (children before parents), then ENUMs last.
**Correct downgrade order:**
```
1. Drop all triggers
2. Drop trigger function
3. Drop tables: dashboard_access, dashboard_filters, filters, graphs, 
   aggregated_data, processing_configs, processing_logs, registration_requests, 
   dashboards, layouts, users
4. Drop ENUMs: user_role, dashboard_permission_level, graph_type, 
   filter_type, processing_status, registration_status
```

## Code Examples

### Complete ENUM Creation Pattern (6 ENUMs)

```python
def upgrade() -> None:
    # Create all 6 PostgreSQL ENUM types (idempotent)
    user_role_enum = ENUM('admin', 'editor', 'viewer', name='user_role')
    user_role_enum.create(op.get_bind(), checkfirst=True)

    dashboard_permission_enum = ENUM('view', 'edit', 'admin', name='dashboard_permission_level')
    dashboard_permission_enum.create(op.get_bind(), checkfirst=True)

    graph_type_enum = ENUM('bar', 'line', 'pie', 'table', name='graph_type')
    graph_type_enum.create(op.get_bind(), checkfirst=True)

    filter_type_enum = ENUM('select', 'multiselect', 'range', 'date', name='filter_type')
    filter_type_enum.create(op.get_bind(), checkfirst=True)

    processing_status_enum = ENUM(
        'started', 'uploaded', 'processing', 'success', 'failed', 'completed',
        name='processing_status'
    )
    processing_status_enum.create(op.get_bind(), checkfirst=True)

    registration_status_enum = ENUM(
        'pending', 'approved', 'rejected',
        name='registration_status'
    )
    registration_status_enum.create(op.get_bind(), checkfirst=True)
```

### Complete Downgrade Pattern

```python
def downgrade() -> None:
    # Drop triggers first
    for table_name in ['dashboards', 'processing_configs', 'layouts', 'graphs', 'users']:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table_name}_updated_at ON {table_name}")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    # Drop tables in reverse dependency order
    op.execute("DROP TABLE IF EXISTS dashboard_access CASCADE")
    op.execute("DROP TABLE IF EXISTS dashboard_filters CASCADE")
    op.execute("DROP TABLE IF EXISTS filters CASCADE")
    op.execute("DROP TABLE IF EXISTS graphs CASCADE")
    op.execute("DROP TABLE IF EXISTS aggregated_data CASCADE")
    op.execute("DROP TABLE IF EXISTS processing_configs CASCADE")
    op.execute("DROP TABLE IF EXISTS processing_logs CASCADE")
    op.execute("DROP TABLE IF EXISTS registration_requests CASCADE")
    op.execute("DROP TABLE IF EXISTS dashboards CASCADE")
    op.execute("DROP TABLE IF EXISTS layouts CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")

    # Drop all 6 ENUM types
    for enum_name in [
        'user_role', 'dashboard_permission_level', 'graph_type',
        'filter_type', 'processing_status', 'registration_status'
    ]:
        enum = ENUM(name=enum_name)
        enum.drop(op.get_bind(), checkfirst=True)
```

### Trigger Function + Triggers Pattern

```python
def upgrade() -> None:
    # ... after table creation ...

    # Create trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create triggers for all tables with updated_at
    for table_name in ['dashboards', 'processing_configs', 'layouts', 'graphs', 'users']:
        trigger_name = f"update_{table_name}_updated_at"
        op.execute(f"""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_trigger WHERE tgname = '{trigger_name}'
                ) THEN
                    CREATE TRIGGER {trigger_name}
                    BEFORE UPDATE ON {table_name}
                    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
                END IF;
            END $$;
        """)
```

### CHECK Constraint Pattern

```python
def upgrade() -> None:
    # ... after table creation ...
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'users_email_length_check'
            ) THEN
                ALTER TABLE users ADD CONSTRAINT users_email_length_check
                CHECK (length(email) <= 255);
            END IF;
        END $$;
    """)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Multiple incremental migrations | Single consolidated migration | This phase | Clean history, faster setup |
| TEXT for all string columns | VARCHAR(259) for constrained fields | During dev | Better data integrity |
| No triggers for updated_at | Trigger function + 5 triggers | During dev | Automatic timestamp updates |
| No registration_requests table | Full registration flow | During dev | Self-service user registration |
| No UPSERT support | Expression unique index on dims::text | During dev | Idempotent data writes |

**Deprecated/outdated:**
- All 16 existing migration files — will be deleted after consolidation
- `f50a4054569c_merge_heads.py` — only existed due to parallel branches, meaningless in linear history
- `e86f3c8f7324_schema_adjustments.py` — was a no-op from the start
- `57f43a5c499d_change_json_to_jsonb_for_postgresql.py` — was a no-op (base already used JSONB)

## Open Questions

1. **Revision ID naming convention**
   - What we know: Existing files use both timestamp-based IDs (`20260507141843`) and hash-based IDs (`7130ecb0388c`). The base migration uses a descriptive slug (`true_initial_migration`).
   - What's unclear: Whether to use a simple sequential ID (`001_initial`) or follow the hash+slug pattern.
   - Recommendation: Use `alembic revision -m "initial_consolidated"` to auto-generate a proper revision ID following Alembic's default scheme. This is the simplest approach and follows Alembic conventions.

2. **Whether to stamp or recreate the database for existing dev environments**
   - What we know: The validation strategy says to drop and recreate. But existing dev databases have the `alembic_version` table pointing to the old chain.
   - What's unclear: Whether the phase should include a `alembic stamp` step for existing environments.
   - Recommendation: Out of scope for the migration file itself. The planner should include a validation step that drops the DB and runs `alembic upgrade head` from scratch. For existing dev DBs, either drop or run `alembic stamp head` with the new revision ID.

## Sources

### Primary (HIGH confidence)

- All 16 migration files in `alembic/versions/` — read in full, analyzed for incremental changes
- `src/mkobi/db/models/*.py` — all 10 model files read, representing the canonical schema
- `docs/09-database/schema-core.md` — core table definitions with exact SQL
- `docs/09-database/schema-processing.md` — processing table definitions with exact SQL
- `docs/09-database/schema-access.md` — access table definitions with exact SQL
- `docs/09-database/indexes.md` — complete index reference (19 indexes total)
- `docs/09-database/enums.md` — 6 PostgreSQL ENUM types documented
- `alembic/env.py` — Alembic configuration, async engine setup
- `alembic.ini` — Alembic settings, no custom file_template
- `alembic/script.py.mako` — migration file template
- `pyproject.toml` — Alembic >=1.18.4, SQLAlchemy >=2.0.29

### Secondary (MEDIUM confidence)

- Alembic documentation (training knowledge) — `alembic revision`, `alembic check`, `alembic upgrade`, ENUM creation with `checkfirst=True`

### Tertiary (LOW confidence)

- None — all findings verified against actual source files

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — all versions confirmed from pyproject.toml
- Architecture: HIGH — patterns derived from reading all 16 migrations and the models
- Pitfalls: HIGH — each pitfall identified by tracing specific changes through the migration chain
- Final schema: HIGH — cross-referenced between SQLAlchemy models, schema docs, and migration files

**Research date:** 2026-05-19
**Valid until:** 90 days (stable domain — Alembic migration patterns don't change frequently)
