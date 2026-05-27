---
name: audit-findings
description: Runtime error finding for Log Viewer empty table bug
agent: auditor
alwaysApply: false
---

# Runtime Bug Analysis — Log Viewer Empty Table

**Executor:** auditor
**Template:** audit-findings.md
**Status:** complete
**Validated:** yes

---

## Findings

### BUG-004: Log Viewer — Empty Table Despite Data Existing in Database

| Field | Value |
|-------|-------|
| **ID** | BUG-004 |
| **Severity** | HIGH |
| **Type** | RUNTIME-ERROR |
| **Affected Modules** | `frontend/src/features/admin/ui/LogViewer.tsx`, `frontend/src/features/admin/api/adminApi.ts`, `src/mkobi/api/routes/processing_logs.py`, `src/mkobi/models/processing_logs.py`, `src/mkobi/db/repositories/processing_log_repo.py` |
| **Classification** | mandatory |

**Description:**
The Log Viewer tab at `/admin` → Log Viewer displays an empty table even when processing log records exist in the database. The table shows no rows, no error message — just an empty grid.

**Root Cause Analysis — Multiple contributing factors:**

---

#### Factor 1: Frontend sends `date_from` / `date_to` as date-only strings, backend expects full datetime

**Frontend** (`LogViewer.tsx:103-104` and `109-110`):
```typescript
onChange={(date) => setFilters({ ...filters, date_from: date ? date.toISOString().split('T')[0] : undefined })}
onChange={(date) => setFilters({ ...filters, date_to: date ? date.toISOString().split('T')[0] : undefined })}
```
The DatePicker values are converted to date-only strings like `"2026-05-27"` (format `YYYY-MM-DD`).

**Backend** (`processing_logs.py:42-48`):
```python
date_from: datetime | None = Query(None, description="Filter by start date (started_at)"),
date_to: datetime | None = Query(None, description="Filter by end date (started_at)"),
```
The endpoint declares `date_from` and `date_to` as `datetime` type. When FastAPI receives `"2026-05-27"` (a date-only string), it **fails to parse it as a `datetime`** and returns a **422 Unprocessable Entity** validation error.

**Frontend API call** (`adminApi.ts:78-80`):
```typescript
export async function getLogs(filters?: LogFilters): Promise<ProcessingLog[]> {
  const response = await axiosInstance.get<ProcessingLog[]>('/admin/logs', { params: filters })
  return response.data
}
```
The 401/403/422 error handling in `axiosInstance.ts` does not catch 422 errors — they propagate as rejected promises. The `useQuery` in `LogViewer.tsx` receives the error but has **no error state handling** — it simply shows an empty table (default `logs = []`).

**Result:** When the user applies date filters, the API returns 422, the query fails silently, and the table remains empty.

---

#### Factor 2: `appliedFilters` initialized as `{}` — first query sends empty object with no params

**Frontend** (`LogViewer.tsx:44-45`):
```typescript
const [filters, setFilters] = useState<LogFilters>({})
const [appliedFilters, setAppliedFilters] = useState<LogFilters>({})
```

**Query** (`LogViewer.tsx:47-50`):
```typescript
const { data: logs = [], isLoading } = useQuery({
  queryKey: ['admin', 'logs', appliedFilters],
  queryFn: () => getLogs(appliedFilters),
})
```

On initial mount, `appliedFilters` is `{}`. The `getLogs({})` call sends `GET /admin/logs` with no query parameters. This should actually work — the backend defaults to `skip=0, limit=100` and returns all logs. So the initial load **should** display data.

However, the `useQuery` result defaults to `[]` on error. If the initial request fails for any reason (network, auth, backend error), the table stays empty with no visible error.

---

#### Factor 3: Backend `ProcessingLogRead` model does not include `dashboard_name` field

**Backend model** (`models/processing_logs.py:72-80`):
```python
class ProcessingLogRead(BaseModel):
    id: UUID
    dashboard_id: UUID | None = None
    status: ProcessingStatus
    message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
```

**Frontend type** (`api.types.ts:248-256`):
```typescript
export interface ProcessingLog {
  id: string
  dashboard_id: string | null
  dashboard_name?: string      // ← Expected by frontend but never returned by backend
  status: ProcessingStatus
  message?: string
  started_at: string
  finished_at?: string
}
```

**Frontend row mapping** (`LogViewer.tsx:61-68`):
```typescript
const rows = logs.map((log) => ({
  id: log.id.slice(0, 8),
  dashboard_name: log.dashboard_name || 'N/A',  // ← Always 'N/A' since backend never sends it
  status: log.status,
  message: log.message || '',
  started_at: new Date(log.started_at).toLocaleString(),
  finished_at: log.finished_at ? new Date(log.finished_at).toLocaleString() : '',
}))
```

The backend returns `dashboard_id` but never resolves it to a `dashboard_name`. The frontend expects `dashboard_name` as an optional field, so it always falls back to `'N/A'`. This is a **data completeness issue** — the table would show rows but with `'N/A'` in the Dashboard column.

However, this alone does not cause an empty table — it would still show rows with `dashboard_name: 'N/A'`.

---

#### Factor 4: `started_at` can be `null` in the database, causing `new Date(null)` in frontend

**SQLAlchemy model** (`db/models/processing_logs.py:57-60`):
```python
started_at: Mapped[datetime | None] = mapped_column(
    DateTime(timezone=True),
    nullable=True,
)
```

**Frontend** (`LogViewer.tsx:66`):
```typescript
started_at: new Date(log.started_at).toLocaleString(),
```

If `started_at` is `null` in the database (which is allowed by the schema), `new Date(null)` produces `Invalid Date` in JavaScript, which renders as `"Invalid Date"` in the table. This does not crash but produces garbage output.

---

#### Factor 5: No error handling in LogViewer — silent failure

**Frontend** (`LogViewer.tsx:47-50`):
```typescript
const { data: logs = [], isLoading } = useQuery({
  queryKey: ['admin', 'logs', appliedFilters],
  queryFn: () => getLogs(appliedFilters),
})
```

The component does not destructure `error` or `isError` from `useQuery`. If the API call fails (422 from date parsing, 500 from backend, network error), the user sees an empty table with no indication of what went wrong. Compare with `DashboardManagement.tsx:50-52` which properly handles mutation errors:
```typescript
onError: (err: Error) => {
  setError(err.message || 'Failed to create dashboard')
}
```

---

#### Factor 6: `status` query parameter type mismatch

**Backend** (`processing_logs.py:38-41`):
```python
status_filter: ProcessingStatus | None = Query(
    None,
    description="Filter by status (STARTED, UPLOADED, PROCESSING, SUCCESS, FAILED)",
),
```

The backend expects `status_filter` as a `ProcessingStatus` enum value. The query parameter name is `status_filter`, but the frontend sends `status` (from `LogFilters.status`).

**Frontend type** (`api.types.ts:258-263`):
```typescript
export interface LogFilters {
  dashboard_id?: string
  status?: string          // ← Sent as query param "status"
  date_from?: string
  date_to?: string
}
```

**Frontend API call** (`adminApi.ts:78-80`):
```typescript
const response = await axiosInstance.get<ProcessingLog[]>('/admin/logs', { params: filters })
```

When `filters = { status: "success" }`, axios sends `?status=success`. But the backend expects `?status_filter=success`. FastAPI will ignore the unknown `status` parameter (it's not declared), so the status filter is silently ignored. This is a **query parameter name mismatch** — the filter is sent but never applied.

---

## Summary of Factors

| # | Factor | Impact | Severity |
|---|--------|--------|----------|
| 1 | `date_from`/`date_to` sent as `YYYY-MM-DD` strings, backend expects `datetime` | 422 error when date filters applied; silent failure | HIGH |
| 2 | No error handling in `useQuery` | Empty table shown on any API failure with no user feedback | HIGH |
| 3 | Backend never returns `dashboard_name` | Dashboard column always shows "N/A" | MEDIUM |
| 4 | `started_at` nullable, frontend calls `new Date(null)` | Shows "Invalid Date" for null timestamps | LOW |
| 5 | No `error`/`isError` handling in component | User sees no error indication | MEDIUM |
| 6 | Query param `status` vs `status_filter` name mismatch | Status filter silently ignored | MEDIUM |

**The primary cause of the empty table** is Factor 1 (date format mismatch causing 422) combined with Factor 5 (no error handling). Even without date filters, if the initial `GET /admin/logs` call fails for any reason, Factors 2 and 5 ensure the user sees an empty table with no error message.

**Evidence:**
- `LogViewer.tsx:103` — `date.toISOString().split('T')[0]` produces `"YYYY-MM-DD"`
- `LogViewer.tsx:109` — Same pattern for `date_to`
- `processing_logs.py:42-48` — `date_from: datetime | None`, `date_to: datetime | None`
- `processing_logs.py:38-41` — Parameter named `status_filter`, not `status`
- `adminApi.ts:78-80` — No error handling, params passed directly
- `LogViewer.tsx:47-50` — No `error`/`isError` destructured from `useQuery`
- `api.types.ts:251` — `dashboard_name?: string` expected but never returned
- `models/processing_logs.py:79` — `started_at: datetime | None` (nullable)
- `db/models/processing_logs.py:57-60` — `started_at` column is `nullable=True`

**Recommendation:**
1. **Fix date format:** Send `date_from`/`date_to` as full ISO datetime strings (e.g., `date.toISOString()`) or change the backend to accept `date` type instead of `datetime`.
2. **Fix query param naming:** Align frontend `LogFilters.status` with backend's `status_filter` parameter name (rename in frontend or backend).
3. **Add error handling:** Destructure `error` and `isError` from `useQuery` and display an error message to the user.
4. **Add `dashboard_name` to backend response:** Either join with the `dashboards` table in the repository or add a computed field to `ProcessingLogRead`.
5. **Handle nullable `started_at`:** Add a null check before calling `new Date(log.started_at)`.

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 0 |
| LOW | 0 |

## Mandatory Fixes

| ID | Issue | File | Effort |
|----|-------|------|--------|
| BUG-004 | Log Viewer empty table: date format mismatch (422 error), query param name mismatch (`status` vs `status_filter`), no error handling in component | `LogViewer.tsx`, `adminApi.ts`, `processing_logs.py` | small — fix date serialization, align param names, add error display |

## Advisory Recommendations

| ID | Issue | File | Effort |
|----|-------|------|--------|
| BUG-004c | `dashboard_name` never returned by backend — Dashboard column always shows "N/A" | `processing_logs.py`, `processing_log_repo.py` | small — join with dashboards table or add computed field |
| BUG-004d | `started_at` nullable — `new Date(null)` produces "Invalid Date" | `LogViewer.tsx:66` | trivial — add null check |

## Doc Updates Needed

| ID | Doc | Update |
|----|-----|--------|
| BUG-004 | `docs/04-admin/admin-api.md` | Document that `date_from`/`date_to` must be full ISO 8601 datetime strings (not date-only). Document that the status query parameter is named `status_filter`, not `status`. |
