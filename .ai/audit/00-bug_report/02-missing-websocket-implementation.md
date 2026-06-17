# Bug Report: Missing WebSocket Implementation for Processing Status

**Date:** 2026-06-17
**Severity:** HIGH
**Status:** UNIMPLEMENTED

## Problem

The task `TASK_054_int013_add_websocket_reconnect_test.yaml` requests adding a test for WebSocket reconnection for processing status updates. However, **no WebSocket implementation exists in the codebase** for this purpose.

## Evidence

### Backend Search
No WebSocket endpoints or handlers found in the backend:
- `grep -r "websocket" src/mkobi/` returns no results
- `src/mkobi/api/routes/upload.py` uses HTTP polling via `GET /upload/status/{task_id}`
- No `@router.websocket` or WebSocket route handlers exist

### Frontend Search  
No WebSocket client implementation found:
- Frontend uses `useProcessingStatus` hook in `frontend/src/features/upload/api/uploadApi.ts`
- This hook uses TanStack Query's polling mechanism (`refetchInterval: 2000`)
- No WebSocket connection logic exists in the frontend

### Current Implementation
Processing status is obtained via HTTP polling:
```typescript
// frontend/src/features/upload/api/uploadApi.ts:44-58
export function useProcessingStatus(logId: string | null, enabled: boolean = true) {
  return useQuery({
    queryKey: ['processingStatus', logId],
    queryFn: () => uploadApi.getProcessingStatus(logId!),
    enabled: enabled && !!logId,
    refetchInterval: (query) => {
      // Stop polling when processing is complete or failed
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

The task claims "WebSocket reconnection for processing status updates is untested" but the WebSocket functionality itself has **never been implemented**. The application uses HTTP long-polling instead:

1. **Upload flow**: `POST /upload/{dashboard_id}` → returns `task_id`
2. **Status polling**: `useQuery` with `refetchInterval: 2000` polls `GET /upload/status/{task_id}`
3. **No WebSocket**: There is no `/ws` endpoint or WebSocket route

## Recommendation

Two options to resolve this:

### Option A: Implement WebSocket (Recommended)
Add WebSocket support to replace polling:
1. Add WebSocket endpoint in backend (`src/mkobi/api/routes/upload.py`)
2. Implement server-side WebSocket handler using FastAPI's WebSocket support
3. Add client-side WebSocket hook (`frontend/src/features/upload/api/websocket.ts`)
4. Then add the reconnection test

### Option B: Update Task to Test HTTP Polling
The task should be revised to test HTTP polling resilience instead:
- Test that `useProcessingStatus` correctly polls and updates
- Test that status transitions are correctly detected
- No WebSocket-specific testing would be needed

## Related Tasks

- `TASK_057_int016_add_upload_progress_websocket_test.yaml` - Also references non-existent WebSocket for upload progress
- Both tasks appear to be based on a planned but unimplemented WebSocket feature

## Affected Files

None - this is a missing feature, not a bug in existing code.