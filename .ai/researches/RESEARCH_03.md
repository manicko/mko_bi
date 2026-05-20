# 03 Admin Dashboard Creation - Research

**Researched:** 2026-05-20
**Domain:** Full-stack form implementation — FastAPI backend + React/MUI/Zod frontend
**Confidence:** HIGH

## Summary

This phase completes the "Create Dashboard" functionality in the admin panel. The frontend modal already exists with Name + Description fields, and the backend already has a `POST /dashboards/` endpoint, a `DashboardService.create_dashboard()` method, and a `DashboardRepository.create()` method. **The root cause of the "Failed to create" error is a schema mismatch**: the frontend sends `{name, description}` but the backend's `DashboardCreate` model requires `config: DashboardConfig` (which requires `graph_types`). Additionally, the `DashboardService.create_dashboard()` has a transaction management issue — when `db` is passed from the endpoint (which already has a transaction via FastAPI's dependency injection), the service tries to `db.commit()` on an already-managed session, causing `"A transaction is already begun on this Session"` errors (visible in historical logs).

The fix involves: (1) making `config` optional in `DashboardCreate` with a sensible default, (2) fixing the service-layer transaction handling, (3) wiring the frontend form with Zod v4 validation matching the specified rules, (4) adding the layout dropdown, description character counter, and inline error display per the phase decisions.

**Primary recommendation:** The backend mostly exists — fix the `DashboardCreate` model to make `config` optional with a default, fix the service transaction pattern, then update the frontend form with proper Zod validation, layout dropdown, error handling, and character counter.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | (existing) | REST API framework | Already in use, Pydantic integration |
| Pydantic v2 | (existing) | Request/response validation | Already in use, `model_config = ConfigDict(...)` pattern |
| SQLAlchemy 2.0 async | (existing) | ORM + async DB operations | Already in use, `AsyncSession` pattern |
| React 18 + TypeScript | (existing) | UI framework | Already in use |
| MUI (Material UI) | (existing) | Component library (Dialog, TextField, DataGrid) | Already in use throughout admin panel |
| TanStack Query | (existing) | Server state management | Already in use for admin CRUD |
| Zod v4 | (existing) | Frontend form validation | Already in use (`formSchemas.ts` uses `z.email()` v4 API) |
| React Hook Form | (existing) | Form state management | Listed in SPEC.md, already installed |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @mui/material Select/MenuItem | (existing) | Layout type dropdown | For the layout dropdown in create dialog |
| @hookform/resolvers | (existing) | Zod + React Hook Form integration | If form uses RHF (check existing pattern) |
| react-hot-toast | (existing) | Toast notifications | Already in use, but phase says NO toast for create success |

**Installation:** No new packages needed. All required libraries are already in the project.

## Architecture Patterns

### Recommended Project Structure

```
Backend changes:
├── src/mkobi/models/dashboard.py     — Make config optional in DashboardCreate
├── src/mkobi/services/dashboard_service.py — Fix transaction handling
├── src/mkobi/api/routes/dashboards.py — Minor: pass description to service
└── tests/test_dashboards_api.py      — Update test payloads

Frontend changes:
├── frontend/src/features/admin/ui/DashboardManagement.tsx — Main changes
├── frontend/src/shared/types/formSchemas.ts — Update Zod schema
└── frontend/src/shared/types/api.types.ts — Add layout to CreateDashboardRequest
```

### Pattern 1: Backend — Optional Config with Default

**What:** The `DashboardCreate` model currently requires `config: DashboardConfig` which requires `graph_types`. For the admin create-dashboard flow, the user only provides name/description/layout. The config should be optional with a default.

**When to use:** When the frontend doesn't provide a full config at creation time.

**Example:**
```python
# src/mkobi/models/dashboard.py
class DashboardCreate(BaseModel):
    name: str
    description: str | None = None
    config: DashboardConfig = DashboardConfig(graph_types=["bar"])  # Default config
    layout_id: UUID | None = None
```

**Source:** Existing pattern in `_dashboard_to_read` at `dashboard_service.py:550-553` already uses `DashboardConfig(graph_types=["bar"])` as default when config is empty.

### Pattern 2: Backend — Transaction Management in Service Layer

**What:** The `DashboardService.create_dashboard()` currently calls `db.commit()` when `db` is passed in. But when called from the FastAPI endpoint, the session is managed by the dependency injection (`get_db_dependency` yields a session within a context manager). The service should NOT commit when it receives an externally-managed session — the endpoint (or the DI context manager) handles commit/rollback.

**Root cause:** The `get_db_dependency` in `deps.py:89-104` uses `async with get_session() as db: yield db`. The session context manager handles cleanup. When the service also calls `db.commit()`, it conflicts with the already-active transaction.

**Fix approach:** Remove the `db.commit()` from `create_dashboard()` when `db` is provided externally. The endpoint should commit after the service call succeeds. Alternatively, follow the pattern used by `update_dashboard()` and `delete_dashboard()` which call `db.commit()` — but ensure the endpoint doesn't double-commit.

**Current problematic code** (`dashboard_service.py:116`):
```python
await db.commit()  # This causes "transaction already begun" when db is from DI
```

**Recommended fix:** The endpoint should commit after the service returns. The service should only commit when it creates its own session (the `db is None` branch). When `db` is passed in, the caller is responsible for commit.

```python
# In dashboard_service.py create_dashboard():
# Remove db.commit() — let the endpoint handle it
# Keep only flush/refresh in the service

# In dashboards.py endpoint:
result = await dashboard_service.create_dashboard(...)
await db.commit()  # Endpoint commits
return result
```

### Pattern 3: Frontend — Zod v4 Schema for Dashboard Form

**What:** Update the `createDashboardSchema` in `formSchemas.ts` to match the phase decisions: name required 3-100 chars alphanumeric+spaces+hyphens, description optional max 200 chars.

**Example:**
```typescript
// frontend/src/shared/types/formSchemas.ts
export const createDashboardSchema = z.object({
  name: z.string()
    .min(3, { error: 'Name must be at least 3 characters' })
    .max(100, { error: 'Name must be at most 100 characters' })
    .regex(/^[a-zA-Z0-9\s-]+$/, { error: 'Name can only contain letters, numbers, spaces, and hyphens' }),
  description: z.string()
    .max(200, { error: 'Description must be at most 200 characters' })
    .optional(),
  layout: z.enum(['single-column', 'two-columns', 'grid']).optional(),
})
```

**Source:** Context7 Zod v4 docs confirm `z.string().min().max().regex()` chaining works. The existing `formSchemas.ts` already uses Zod v4 API (`z.email()`, `z.uuid()`).

### Pattern 4: Frontend — Inline Error Display in Modal

**What:** Per phase decisions, errors should display inline inside the modal below form fields. The modal stays open on error. User input is preserved. No toast for errors.

**Implementation approach:** Replace the generic `toast.error('Failed to create dashboard')` with an error state variable that renders an MUI `Alert` or `Typography` with the error message inside the `DialogContent`, below the form fields.

```tsx
const [error, setError] = useState<string | null>(null)

// In mutation:
onError: (err) => {
  setError(err instanceof Error ? err.message : 'Failed to create dashboard')
}

// In DialogContent:
{error && (
  <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>
)}
```

### Pattern 5: Frontend — Character Counter for Description

**What:** Display "X/200" character count near the description field.

**Implementation approach:** Use MUI `TextField` with `helperText` prop or a separate `Typography` component:

```tsx
<TextField
  fullWidth
  label="Description"
  multiline
  rows={3}
  value={formData.description}
  onChange={(e) => {
    if (e.target.value.length <= 200) {
      setFormData({ ...formData, description: e.target.value })
    }
  }}
  helperText={`${formData.description.length}/200`}
  inputProps={{ maxLength: 200 }}
/>
```

### Pattern 6: Frontend — Layout Dropdown

**What:** Add an optional layout type dropdown to the create dialog.

**Implementation approach:** Use MUI `FormControl`, `InputLabel`, `Select`, `MenuItem`:

```tsx
<FormControl fullWidth sx={{ mt: 2 }}>
  <InputLabel>Layout</InputLabel>
  <Select
    value={formData.layout || ''}
    label="Layout"
    onChange={(e) => setFormData({ ...formData, layout: e.target.value })}
  >
    <MenuItem value="single-column">Single column</MenuItem>
    <MenuItem value="two-columns">Two columns</MenuItem>
    <MenuItem value="grid">Grid</MenuItem>
  </Select>
</FormControl>
```

### Anti-Patterns to Avoid

- **Don't add toast for success:** Phase decisions explicitly say "No toast. Modal closes + dashboard list refreshes. That's sufficient confirmation." The current code has `toast.success('Dashboard created successfully')` which should be removed.
- **Don't navigate after creation:** Stay on admin page. No redirect to the new dashboard.
- **Don't enforce name uniqueness:** Phase decisions say duplicate names are allowed.
- **Don't add owner concept:** The system only has viewer/editor roles, no owner.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|------------|-------------|-----|
| Form validation | Custom validation functions | Zod v4 schema | Already in use, type-safe, handles edge cases |
| Error display | Custom error modal | MUI Alert inside existing Dialog | Consistent with MUI patterns already in use |
| Character counter | Custom counter component | MUI TextField `helperText` | Built-in, accessible, consistent styling |
| API error parsing | Manual error extraction | Axios error response `error.response.data.detail` | Backend already returns structured errors |
| State management for form | Redux/Zustand | useState (simple form) | Form is simple, no need for global state |

## Common Pitfalls

### Pitfall 1: Schema Mismatch Between Frontend and Backend

**What goes wrong:** Frontend sends `{name, description}` but backend `DashboardCreate` requires `config: DashboardConfig`. This causes a 422 validation error.

**Why it happens:** The `DashboardCreate` model at `dashboard.py:48-54` has `config: DashboardConfig` as required. The frontend `CreateDashboardRequest` at `api.types.ts:217-220` only has `name` and `description`.

**How to fix:** Make `config` optional in `DashboardCreate` with a default value of `DashboardConfig(graph_types=["bar"])`. This matches the existing default in `_dashboard_to_read`.

**Warning signs:** 422 Unprocessable Entity response when creating a dashboard.

### Pitfall 2: Double Transaction Commit

**What goes wrong:** `"A transaction is already begun on this Session"` error.

**Why it happens:** The FastAPI DI provides a session with an active transaction. The service's `create_dashboard()` also calls `db.commit()`. When the endpoint then tries to use the session again or the DI context manager tries to clean up, it conflicts.

**How to fix:** Remove `db.commit()` from `create_dashboard()` when `db` is provided. Let the endpoint handle commit. The service should only manage its own transaction when it creates its own session (the `db is None` recursive branch).

**Warning signs:** Error logs showing "A transaction is already begun on this Session" (visible in `data/logs/app.json.log.1`).

### Pitfall 3: Frontend Not Sending Config

**What goes wrong:** Even after making config optional on the backend, the frontend `createDashboard` function sends `CreateDashboardRequest` which doesn't include config. This is fine if the backend provides a default, but the frontend type should be updated for consistency.

**How to fix:** The frontend doesn't need to send config — the backend default handles it. But the `CreateDashboardRequest` type should include optional `layout` field for the layout dropdown.

### Pitfall 4: MUI Select/Dialog Import Missing

**What goes wrong:** Adding layout dropdown requires `FormControl`, `InputLabel`, `Select`, `MenuItem` from MUI. If not imported, build fails.

**How to fix:** Add to the existing MUI imports in `DashboardManagement.tsx`.

### Pitfall 5: Zod Schema Not Matching Backend Validation

**What goes wrong:** Frontend allows names with special chars but backend may reject them, or vice versa.

**Why it happens:** The phase specifies "alphanumeric + spaces + hyphens only" for the name field. The current Zod schema only checks `min(1).max(100)`.

**How to fix:** Add `.regex(/^[a-zA-Z0-9\s-]+$/)` to the name field in the Zod schema. The backend `DashboardCreate` model should also validate this (add a Pydantic field validator).

## Code Examples

### Backend: Make config optional in DashboardCreate

```python
# src/mkobi/models/dashboard.py — DashboardCreate class
class DashboardCreate(BaseModel):
    name: str
    description: str | None = None
    config: DashboardConfig = DashboardConfig(graph_types=["bar"])
    layout_id: UUID | None = None
```

### Backend: Fix transaction in create_dashboard

```python
# src/mkobi/services/dashboard_service.py — create_dashboard method
# Remove db.commit() from the method when db is provided
# The endpoint should commit instead

# In the endpoint (dashboards.py):
result = await dashboard_service.create_dashboard(
    name=dashboard.name,
    config=dashboard.config.model_dump(),
    owner_id=current_user.id,
    db=db,
)
await db.commit()
return result
```

### Backend: Add name validation

```python
# src/mkobi/models/dashboard.py
from pydantic import field_validator

class DashboardCreate(BaseModel):
    name: str
    description: str | None = None
    config: DashboardConfig = DashboardConfig(graph_types=["bar"])
    layout_id: UUID | None = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if len(v) < 3:
            raise ValueError('Name must be at least 3 characters')
        if len(v) > 100:
            raise ValueError('Name must be at most 100 characters')
        import re
        if not re.match(r'^[a-zA-Z0-9\s-]+$', v):
            raise ValueError('Name can only contain letters, numbers, spaces, and hyphens')
        return v
```

### Frontend: Updated Zod schema

```typescript
// frontend/src/shared/types/formSchemas.ts
export const createDashboardSchema = z.object({
  name: z.string()
    .min(3, { error: 'Name must be at least 3 characters' })
    .max(100, { error: 'Name must be at most 100 characters' })
    .regex(/^[a-zA-Z0-9\s-]+$/, {
      error: 'Name can only contain letters, numbers, spaces, and hyphens',
    }),
  description: z.string()
    .max(200, { error: 'Description must be at most 200 characters' })
    .optional(),
  layout: z.enum(['single-column', 'two-columns', 'grid']).optional(),
})
```

### Frontend: Updated CreateDashboardRequest type

```typescript
// frontend/src/shared/types/api.types.ts
export interface CreateDashboardRequest {
  name: string
  description?: string
  layout?: 'single-column' | 'two-columns' | 'grid'
}
```

### Frontend: Error state in DashboardManagement.tsx

```tsx
const [error, setError] = useState<string | null>(null)

const createMutation = useMutation({
  mutationFn: createDashboard,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['admin', 'dashboards'] })
    setCreateDialogOpen(false)
    setFormData({ name: '', description: '' })
    setError(null)
    // No toast per phase decisions
  },
  onError: (err: Error) => {
    setError(err.message || 'Failed to create dashboard')
  },
})

// In DialogContent, after TextField for description:
{error && (
  <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>
)}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|-------------|-----------------|--------------|--------|
| `z.string().email()` | `z.email()` | Zod v4 | Already migrated in this codebase |
| Manual form validation | Zod schema validation | Already adopted | Already in use in `formSchemas.ts` |
| Toast for all feedback | Contextual feedback (inline errors, no toast for success) | Phase 3 decisions | Simpler UX |

**Deprecated/outdated:**
- `z.string().email()` — use `z.email()` (Zod v4, already migrated)
- Toast for create success — phase says no toast, just close modal + refresh list

## Open Questions

1. **Should the layout value be stored in the DB?**
   - What we know: The `dashboards` table has a `layout_id` FK column. The phase says "if backend doesn't support layout yet, it can be stored as a default/ignored value for future use."
   - What's unclear: Whether to wire the layout dropdown to the `layout_id` column or just store it in the `config` JSONB.
   - Recommendation: Store the layout selection in the `config` JSONB as a `layout` field (e.g., `config.layout = "two-columns"`). This avoids requiring a `layouts` table entry and aligns with the "empty dashboard" default approach.

2. **Should the description field be added to the backend create endpoint?**
   - What we know: The `DashboardCreate` model already has `description: str | None = None`. The `DashboardService.create_dashboard()` accepts `name, config, owner_id` but NOT `description`. The `Dashboard` DB model has a `description` column.
   - What's unclear: Whether the service needs to pass `description` through to the repository.
   - Recommendation: Update `create_dashboard()` to accept and pass `description` to the repository's `create()` call.

3. **Should the `created_by` field be set?**
   - What we know: The service passes `created_by=owner_id` to the repository. The DB column is `created_by`. The frontend `DashboardAdmin` type includes `created_by`.
   - Recommendation: This already works. No changes needed.

## Sources

### Primary (HIGH confidence)
- `src/mkobi/models/dashboard.py` — `DashboardCreate`, `DashboardRead`, `DashboardConfig` models
- `src/mkobi/services/dashboard_service.py` — `create_dashboard()` method with transaction issue
- `src/mkobi/api/routes/dashboards.py` — `create_dashboard_endpoint()` 
- `src/mkobi/api/deps.py` — `get_db_dependency()` session management
- `src/mkobi/db/repositories/dashboard_repo.py` — `DashboardRepository.create()`
- `src/mkobi/db/models/dashboard.py` — `Dashboard` SQLAlchemy model
- `src/mkobi/models/enums.py` — All StrEnum definitions
- `frontend/src/features/admin/ui/DashboardManagement.tsx` — Existing create dialog
- `frontend/src/features/admin/api/adminApi.ts` — `createDashboard()` API function
- `frontend/src/shared/types/api.types.ts` — `CreateDashboardRequest`, `DashboardAdmin` types
- `frontend/src/shared/types/formSchemas.ts` — Existing Zod v4 schemas
- `frontend/src/shared/api/axiosInstance.ts` — Axios setup with error handling
- `tests/test_dashboards_api.py` — Existing create dashboard tests
- `tests/conftest.py` — Test fixtures and session management
- Context7: `/colinhacks/zod` — Zod v4 string validation API

### Secondary (MEDIUM confidence)
- `data/logs/app.json.log.1` — Historical error logs showing "transaction already begun" errors
- `docs/SPEC.md` — Project specification and architecture decisions

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — All libraries already in use, no new dependencies needed
- Architecture: HIGH — Existing patterns well-established, changes are incremental
- Pitfalls: HIGH — Root causes identified from code analysis and historical error logs

**Research date:** 2026-05-20
**Valid until:** 2026-06-20 (30 days — stable phase with existing codebase patterns)
