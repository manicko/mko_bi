---
phase: "03 — Admin Dashboard Creation"
description: "Fix 'Create Dashboard' functionality in admin panel: make config optional in backend, fix transaction handling, add Zod v4 validation, layout dropdown, description character counter, inline error display"
autonomous: true
depends_on: []
files_modified:
  - src/mkobi/models/dashboard.py
  - src/mkobi/services/dashboard_service.py
  - src/mkobi/api/routes/dashboards.py
  - src/mkobi/db/repositories/dashboard_repo.py
  - frontend/src/features/admin/ui/DashboardManagement.tsx
  - frontend/src/shared/types/formSchemas.ts
  - frontend/src/shared/types/api.types.ts
  - frontend/src/features/admin/api/adminApi.ts
  - tests/test_dashboards_api.py
waves:
  - id: 1
    tasks: [TASK_01, TASK_02, TASK_04]
    parallel: true
  - id: 2
    tasks: [TASK_03]
    depends_on: [TASK_01, TASK_02]
  - id: 3
    tasks: [TASK_05, TASK_06]
    parallel: true
    depends_on: [TASK_04]
  - id: 4
    tasks: [TASK_07]
    depends_on: [TASK_01, TASK_02, TASK_03]
---

# PLAN_03: Admin Dashboard Creation

## must_haves

When this phase is complete, ALL of the following must be true:

1. **Backend schema fix:** `POST /dashboards/` accepts `{name, description?, layout?}` without requiring `config` field — no 422 error.
2. **Backend transaction fix:** Dashboard creation does not throw "A transaction is already begun on this Session" — service does not call `db.commit()` when `db` is provided externally.
3. **Backend name validation:** `DashboardCreate` model validates name: 3-100 chars, alphanumeric + spaces + hyphens only. Returns 422 with descriptive message on violation.
4. **Backend description pass-through:** `create_dashboard()` accepts and passes `description` to the repository.
5. **Frontend Zod validation:** `createDashboardSchema` enforces name (3-100 chars, alphanumeric+spaces+hyphens regex) and description (max 200 chars).
6. **Frontend layout dropdown:** Create dialog has optional layout dropdown with "Single column", "Two columns", "Grid" options.
7. **Frontend character counter:** Description field shows "X/200" character count via MUI `helperText`.
8. **Frontend inline errors:** On creation failure, MUI `Alert` with error message appears inside modal below form fields. Modal stays open. User input preserved.
9. **Frontend no toast on success:** On success, modal closes, dashboard list refreshes, no toast shown. No navigation to new dashboard.
10. **Frontend submit button:** Disabled during request (`createMutation.isPending`), no spinner.
11. **Tests updated:** `test_dashboards_api.py` create tests send valid payloads that match the updated schema.

---

## Wave 1 (Parallel — Backend Foundation + Frontend Types)

### TASK_01: Make config optional + add name validation in DashboardCreate model

**File:** `src/mkobi/models/dashboard.py`
**Symbol:** `DashboardCreate` class
**Semantic anchor:** Lines 48-54 — `DashboardCreate` class definition with `config: DashboardCreate` required field

**Changes:**

1. Add `field_validator` import (line 3 area):
   ```python
   from pydantic import BaseModel, ConfigDict, field_validator
   ```

2. Add `import re` at module level (top of file with other imports).

3. Replace the `DashboardCreate` class (lines 48-76):
   ```python
   class DashboardCreate(BaseModel):
       """Model for creating new dashboard."""

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
        if not re.match(r'^[a-zA-Z0-9\s-]+$', v):
            raise ValueError('Name can only contain letters, numbers, spaces, and hyphens')
        return v

       model_config = ConfigDict(
           from_attributes=True,
           json_schema_extra={
               "example": {
                   "name": "Sales Dashboard",
                   "description": "Overview of sales performance",
                   "config": {
                       "graph_types": ["bar", "line"],
                       "filters": [{"field": "year", "type": "select"}],
                       "charts": [
                           {
                               "type": "bar",
                               "x": "category",
                               "y": "revenue",
                           }
                       ],
                   },
                   "layout_id": "550e8400-e29b-41d4-a716-446655440000",
               }
           },
       )
   ```

**Rationale:** Making `config` optional with `DashboardConfig(graph_types=["bar"])` default eliminates the 422 schema mismatch when frontend sends only `{name, description}`. The name validator enforces the phase decision rules (3-100 chars, alphanumeric+spaces+hyphens).

**Acceptance criteria:**
- `DashboardCreate` can be instantiated with only `name` (config defaults to `DashboardConfig(graph_types=["bar"])`)
- `DashboardCreate(name="ab")` raises `ValueError` — too short
- `DashboardCreate(name="a" * 101)` raises `ValueError` — too long
- `DashboardCreate(name="test@dashboard")` raises `ValueError` — invalid chars
- `DashboardCreate(name="test-dashboard 123")` succeeds — valid chars
- `DashboardUpdate` class is unchanged

**Validation:**
- `cd src/mkobi && python -c "from models.dashboard import DashboardCreate; d = DashboardCreate(name='test'); print(d.config)"` — should print config with `graph_types=['bar']`
- `ruff check src/mkobi/models/dashboard.py` — no lint errors

---

### TASK_02: Fix transaction handling + add description param in DashboardService

**File:** `src/mkobi/services/dashboard_service.py`
**Symbol:** `create_dashboard` method
**Semantic anchor:** Lines 53-133 — `create_dashboard` method with `await db.commit()` on line 116

**Changes:**

1. Update the method signature (line 53-58) to accept `description`:
   ```python
   async def create_dashboard(
       self,
       name: str,
       config: dict[str, Any],
       owner_id: UUID,
       description: str | None = None,
       db: AsyncSession | None = None,
   ) -> DashboardRead:
   ```

2. Update the recursive call (line 77) to pass `description` and commit:
   ```python
   if db is None:
       async with get_session() as db:
           result = await self.create_dashboard(name, config, owner_id, description, db)
           await db.commit()
           return result
   ```

3. Update the repository call (lines 84-89) to pass `description`:
   ```python
   dashboard_obj = await self.dashboard_repo.create(
       db=db,
       name=name,
       config=config_obj.model_dump(),
       created_by=owner_id,
       description=description,
   )
   ```

4. Remove `await db.commit()` (line 116) and its log line (line 117). The endpoint handles commit when `db` is provided externally:
   ```python
   # DELETE these two lines:
   # await db.commit()
   # logger.info("Transaction committed for dashboard id=%s", dashboard_obj.id)
   ```

**Rationale:** The `get_db_dependency` in `deps.py:89-104` uses `async with get_session() as db: yield db`. The session context manager handles cleanup. When the service also calls `db.commit()`, it conflicts with the already-active transaction. The endpoint should commit after the service returns successfully. When the service creates its own session (the `db is None` recursive branch), it must explicitly commit before the session closes, otherwise the `get_session()` context manager only closes without committing, silently losing data.

**Acceptance criteria:**
- `create_dashboard()` accepts optional `description` parameter
- `description` is passed to `dashboard_repo.create()`
- No `db.commit()` call in `create_dashboard()` when `db` is provided
- Recursive `db is None` branch commits before returning (prevents silent data loss)
- `update_dashboard`, `delete_dashboard`, `grant_access`, `revoke_access` methods are unchanged

**Validation:**
- `ruff check src/mkobi/services/dashboard_service.py` — no lint errors
- `mypy src/mkobi/services/dashboard_service.py` — no type errors (if mypy configured)

---

## Wave 2 (Backend Integration — depends on TASK_01, TASK_02)

### TASK_03: Update create endpoint to commit + pass description

**File:** `src/mkobi/api/routes/dashboards.py`
**Symbol:** `create_dashboard_endpoint` function
**Semantic anchor:** Lines 50-116 — `create_dashboard_endpoint` with service call on lines 87-92

**Changes:**

1. Update the endpoint to pass `description` and commit after service call (lines 86-99):
   ```python
   try:
       result = await dashboard_service.create_dashboard(
           name=dashboard.name,
           config=dashboard.config.model_dump(),
           owner_id=current_user.id,
           description=dashboard.description,
           db=db,
       )
       await db.commit()

       logger.info(
           "Dashboard created successfully: id=%s, name=%s",
           result.id,
           result.name,
       )
       return result
   ```

2. Remove the redundant `DashboardCreate` reconstruction (lines 74-78). The `dashboard_data` parameter is already a `DashboardCreate` instance validated by FastAPI:
   ```python
   # DELETE these lines:
   # dashboard = DashboardCreate(
   #     name=dashboard_data.name,
   #     description=dashboard_data.description,
   #     config=dashboard_data.config,
   # )
   ```
   
   And update the references from `dashboard.name`/`dashboard.config`/`dashboard.description` to `dashboard_data.name`/`dashboard_data.config`/`dashboard_data.description` in the logger call (line 81) and service call (lines 87-92):
   ```python
   logger.info(
       "Creating dashboard: name=%s, owner_id=%s",
       dashboard_data.name,
       current_user.id,
   )

   try:
       result = await dashboard_service.create_dashboard(
           name=dashboard_data.name,
           config=dashboard_data.config.model_dump(),
           owner_id=current_user.id,
           description=dashboard_data.description,
           db=db,
       )
   ```

**Rationale:** The endpoint must commit the transaction after the service returns successfully, since the service no longer commits. The redundant `DashboardCreate` reconstruction is unnecessary — FastAPI already validates the request body into a `DashboardCreate` instance.

**Acceptance criteria:**
- Endpoint passes `description` to `create_dashboard()`
- Endpoint calls `await db.commit()` after successful service call
- No redundant `DashboardCreate` reconstruction
- Error handling (ValueError → 422, Exception → 500) unchanged

**Validation:**
- `ruff check src/mkobi/api/routes/dashboards.py` — no lint errors

---

## Wave 3 (Parallel — Frontend UI + API)

### TASK_04: Update Zod schema + API types for dashboard creation

**Files:**
- `frontend/src/shared/types/formSchemas.ts` — Update `createDashboardSchema`
- `frontend/src/shared/types/api.types.ts` — Update `CreateDashboardRequest`

**Semantic anchors:**
- `formSchemas.ts` lines 24-27: `createDashboardSchema` definition
- `api.types.ts` lines 217-220: `CreateDashboardRequest` interface

#### Change 4a: Update `createDashboardSchema`

File: `frontend/src/shared/types/formSchemas.ts`, lines 23-27

```typescript
// Before:
export const createDashboardSchema = z.object({
  name: z.string().min(1, { error: 'Dashboard name is required' }).max(100, { error: 'Dashboard name is too long' }),
  description: z.string().max(500, { error: 'Description is too long' }).optional(),
})

// After:
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

**Rationale:** Matches phase decisions — name 3-100 chars with regex validation, description max 200 chars (was 500), adds optional layout field.

#### Change 4b: Update `CreateDashboardRequest` type

File: `frontend/src/shared/types/api.types.ts`, lines 217-220

```typescript
// Before:
export interface CreateDashboardRequest {
  name: string
  description?: string
}

// After:
export interface CreateDashboardRequest {
  name: string
  description?: string
  layout?: 'single-column' | 'two-columns' | 'grid'
}
```

**Acceptance criteria:**
- `createDashboardSchema` validates name: min 3, max 100, regex for alphanumeric+spaces+hyphens
- `createDashboardSchema` validates description: max 200 chars optional
- `createDashboardSchema` accepts optional `layout` enum
- `CreateDashboardRequest` includes optional `layout` field
- `updateDashboardSchema` and other schemas unchanged

**Validation:**
- `cd frontend && npx tsc --noEmit` — no type errors

---

### TASK_05: Update DashboardManagement.tsx — layout dropdown, char counter, inline errors, no toast

**File:** `frontend/src/features/admin/ui/DashboardManagement.tsx`
**Semantic anchor:** Lines 1-249 — entire component

**Changes:**

1. Add MUI imports for `Alert`, `FormControl`, `InputLabel`, `Select`, `MenuItem` (line 4-12 area):
   ```typescript
   import {
     Box,
     Button,
     Dialog,
     DialogTitle,
     DialogContent,
     DialogActions,
     TextField,
     Alert,
     FormControl,
     InputLabel,
     Select,
     MenuItem,
   } from '@mui/material'
   ```

2. Add `error` state after `formData` state (after line 26):
   ```typescript
   const [error, setError] = useState<string | null>(null)
   ```

3. Update `createMutation` (lines 36-47) — remove toast, add inline error:
   ```typescript
   const createMutation = useMutation({
     mutationFn: createDashboard,
     onSuccess: () => {
       queryClient.invalidateQueries({ queryKey: ['admin', 'dashboards'] })
       setCreateDialogOpen(false)
       setFormData({ name: '', description: '' })
       setError(null)
     },
     onError: (err: Error) => {
       setError(err.message || 'Failed to create dashboard')
     },
   })
   ```

4. Update `handleCreate` (lines 73-75) to reset error:
   ```typescript
   const handleCreate = () => {
     setError(null)
     createMutation.mutate(formData)
   }
   ```

5. Update the Create Dialog (lines 183-208) — add layout dropdown, char counter, inline error:
   ```tsx
   {/* Create Dialog */}
   <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
     <DialogTitle>Create Dashboard</DialogTitle>
     <DialogContent>
       <TextField
         fullWidth
         label="Name"
         value={formData.name}
         onChange={(e) => setFormData({ ...formData, name: e.target.value })}
         sx={{ mt: 2, mb: 2 }}
       />
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
       {error && (
         <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>
       )}
     </DialogContent>
     <DialogActions>
       <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
       <Button onClick={handleCreate} disabled={createMutation.isPending || !formData.name}>
         Create
       </Button>
     </DialogActions>
   </Dialog>
   ```

6. Update `formData` state to include `layout` (line 26):
   ```typescript
   const [formData, setFormData] = useState({ name: '', description: '', layout: '' })
   ```

7. Update the "Create Dashboard" button handler (line 163) to reset layout:
   ```typescript
   onClick={() => {
     setFormData({ name: '', description: '', layout: '' })
     setError(null)
     setCreateDialogOpen(true)
   }}
   ```

**Rationale:** Per phase decisions: layout dropdown for selecting layout type, character counter via MUI `helperText`, inline error via `Alert` (no toast), modal stays open on error, no toast on success, submit button disabled during request.

**Acceptance criteria:**
- Create dialog has Name, Description (with "X/200" counter), Layout dropdown, and inline error Alert
- Description field truncates input at 200 chars
- Layout dropdown has 3 options: Single column, Two columns, Grid
- On error: Alert appears below form fields, modal stays open, form data preserved
- On success: modal closes, list refreshes, no toast
- Submit button disabled when `createMutation.isPending` or name is empty
- `react-hot-toast` import can be removed if no longer used elsewhere in the file (check if `toast` is used for edit/delete — it is, so keep the import)

**Validation:**
- `cd frontend && npx tsc --noEmit` — no type errors

---

### TASK_06: Update createDashboard API function to send layout

**File:** `frontend/src/features/admin/api/adminApi.ts`
**Symbol:** `createDashboard` function
**Semantic anchor:** Lines 55-58 — `createDashboard` function

**Change:**

```typescript
// Before:
export async function createDashboard(data: CreateDashboardRequest): Promise<DashboardAdmin> {
  const response = await axiosInstance.post<DashboardAdmin>('/dashboards', data)
  return response.data
}

// After:
export async function createDashboard(data: CreateDashboardRequest): Promise<DashboardAdmin> {
  const payload: Record<string, unknown> = {
    name: data.name,
  }
  if (data.description) {
    payload.description = data.description
  }
  if (data.layout) {
    payload.config = { graph_types: ['bar'], layout: data.layout }
  }
  const response = await axiosInstance.post<DashboardAdmin>('/dashboards', payload)
  return response.data
}
```

**Rationale:** The backend `DashboardConfig` model has no `layout` field, so Pydantic v2 `extra='ignore'` would silently discard it. Instead, layout is stored inside the `config` JSONB column by including it in the config object alongside `graph_types`. The service/repo stores `config` as JSONB, so layout persists without requiring a schema change. If no layout is selected, the backend default config (without layout) applies. The `description` is only sent if non-empty to keep the payload clean.

**Acceptance criteria:**
- `createDashboard` sends `layout` inside `config` object when layout is selected
- `createDashboard` sends `description` only when non-empty
- Layout value is stored in the config JSONB column (not silently dropped)
- Other API functions (`getDashboardsAdmin`, `updateDashboard`, `deleteDashboard`) unchanged

**Validation:**
- `cd frontend && npx tsc --noEmit` — no type errors

---

## Wave 4 (Tests — depends on backend)

### TASK_07: Update create dashboard tests to match new schema

**File:** `tests/test_dashboards_api.py`
**Symbol:** `TestCreateDashboard` class
**Semantic anchor:** Lines 143-188 — `TestCreateDashboard` with test payloads

**Changes:**

1. Update `test_create_dashboard_admin` payload (lines 150-156) — add `description`:
   ```python
   async def test_create_dashboard_admin(
       self, authenticated_client: AsyncClient, async_db_session, test_user: dict
   ) -> None:
       """Test creating dashboard as admin (success)."""
       response = await authenticated_client.post(
           "/dashboards/",
           json={
               "name": "new_dashboard",
               "description": "Test desc",
           },
       )
       assert response.status_code == status.HTTP_201_CREATED
       data = response.json()
       assert data["name"] == "new_dashboard"
       assert data["description"] == "Test desc"
   ```

2. Update `test_create_dashboard_forbidden` payload (lines 184-187) — add `description`:
   ```python
   response = await authenticated_client.post(
       "/dashboards/",
       json={"name": "forbidden_dashboard"},
   )
   ```
   (No change needed here — name-only is still valid since config is optional.)

**Rationale:** The test payload for `test_create_dashboard_admin` should verify that `description` is passed through correctly. The `config` field is no longer required since it has a default.

**Acceptance criteria:**
- `test_create_dashboard_admin` sends `description` and verifies it in response
- `test_create_dashboard_forbidden` still works with name-only payload
- All other tests unchanged

**Validation:**
- `cd src/mkobi && python -m pytest tests/test_dashboards_api.py::TestCreateDashboard -v` — tests pass

---

## Execution Order Summary

| Wave | Task | File(s) | Dependencies |
|------|------|---------|-------------|
| 1 | TASK_01 | `src/mkobi/models/dashboard.py` | None |
| 1 | TASK_02 | `src/mkobi/services/dashboard_service.py` | None |
| 1 | TASK_04 | `formSchemas.ts`, `api.types.ts` | None |
| 2 | TASK_03 | `src/mkobi/api/routes/dashboards.py` | TASK_01, TASK_02 (model has description field; service signature has description param) |
| 3 | TASK_05 | `DashboardManagement.tsx` | TASK_04 (uses updated schema/types) |
| 3 | TASK_06 | `adminApi.ts` | TASK_04 (uses updated types) |
| 4 | TASK_07 | `tests/test_dashboards_api.py` | TASK_01, TASK_02, TASK_03 (backend must work) |

**Note:** Wave 1 tasks (TASK_01, TASK_02, TASK_04) are fully parallel — two backend tasks and one frontend task with no cross-dependencies. Wave 3 tasks (TASK_05, TASK_06) are parallel but both depend on TASK_04's type changes.

---

## Final Validation (All Tasks Complete)

1. `cd src/mkobi && ruff check .` — zero lint errors
2. `cd frontend && npx tsc --noEmit` — zero type errors
3. `cd src/mkobi && python -m pytest tests/test_dashboards_api.py -v` — all dashboard tests pass
4. Manual verification checklist:
   - [ ] Open admin panel → click "Create Dashboard" → dialog opens with Name, Description, Layout fields
   - [ ] Description field shows "0/200" counter, truncates at 200 chars
   - [ ] Layout dropdown has 3 options: Single column, Two columns, Grid
   - [ ] Submit with empty name → button disabled
   - [ ] Submit with name "ab" → backend returns 422 (name too short)
   - [ ] Submit with name "test@bad" → backend returns 422 (invalid chars)
   - [ ] Submit with valid name → modal closes, dashboard appears in list, no toast
   - [ ] On server error → Alert appears inside modal, modal stays open, form data preserved
   - [ ] Submit button disabled during request (no spinner)
