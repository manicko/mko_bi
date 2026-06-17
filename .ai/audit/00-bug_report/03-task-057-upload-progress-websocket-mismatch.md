# Bug Report: TASK_057 — Upload Progress WebSocket Test Mismatch

**Date:** 2026-06-17
**Severity:** HIGH
**Status:** BLOCKED
**Related Task:** TASK_057_int016_add_upload_progress_websocket_test.yaml

## Problem

Task `TASK_057_int016_add_upload_progress_websocket_test.yaml` requests adding an integration test for "upload progress via WebSocket" but **no WebSocket implementation exists** for upload progress in the codebase.

## Evidence

### Backend Search
- `grep -r "websocket" src/mkobi/` returns no results
- `src/mkobi/api/routes/upload.py` uses HTTP polling via `GET /upload/status/{task_id}`
- No `@router.websocket` or WebSocket route handlers exist in any API route

### Frontend Search
- `frontend/src/features/upload/api/uploadApi.ts` uses TanStack Query's polling mechanism:
  - `useProcessingStatus` hook uses `refetchInterval: 2000` to poll every 2 seconds
  - No WebSocket client implementation exists anywhere in `frontend/src/`

### Current Implementation
Processing status is obtained via HTTP polling, not WebSocket:
```python
# Backend: src/mkobi/api/routes/upload.py:252-307
@router.get(
    "/status/{task_id}",
    response_model=ProcessingStatusResponse,
    summary="Get processing status",
    description="Returns current processing status of file.",
)
async def get_status_endpoint(...):
    result = await data_service.get_processing_status(...)
    return result
```

```typescript
// Frontend: frontend/src/features/upload/api/uploadApi.ts:44-58
export function useProcessingStatus(logId: string | null, enabled: boolean = true) {
  return useQuery({
    queryKey: ['processingStatus', logId],
    queryFn: () => uploadApi.getProcessingStatus(logId!),
    enabled: enabled && !!logId,
    refetchInterval: (query) => {
      const data = query.state.data
      if (data?.status === ProcessingStatus.COMPLETED || data?.status === ProcessingStatus.FAILED) {
        return false
      }
      return 2000 // Poll every 2 seconds
    },
  })
}
```

## Analysis

The task description claims "upload progress via WebSocket is untested" but the WebSocket functionality has **never been implemented**. The application uses HTTP polling instead:

1. Upload flow: `POST /upload/{dashboard_id}` → returns `task_id`
2. Status polling: `useQuery` with `refetchInterval: 2000` polls `GET /upload/status/{task_id}`
3. No WebSocket: There is no `/ws` endpoint or WebSocket route

This is the same underlying issue as `02-missing-websocket-implementation.md` (which covers `TASK_054_int013_add_websocket_reconnect_test.yaml`).

## Resolution

This task is **BLOCKED** because WebSocket functionality does not exist. Two options to resolve:

### Option A: Implement WebSocket (Requires separate implementation tasks)
1. Add WebSocket endpoint in backend (`src/mkobi/api/routes/upload.py`)
2. Implement server-side WebSocket handler using FastAPI's WebSocket support
3. Add client-side WebSocket hook (`frontend/src/features/upload/api/websocket.ts`)
4. Replace HTTP polling with WebSocket-based communication
5. Then add the integration test

### Option B: Update Task to Test HTTP Polling (Recommended)
The task should be revised to test HTTP polling resilience instead:
- Test that `useProcessingStatus` correctly polls and updates
- Test that status transitions are correctly detected
- No WebSocket-specific testing needed

## Related

See also: `02-missing-websocket-implementation.md` - covers the same issue for TASK_054