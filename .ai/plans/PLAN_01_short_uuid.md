---
wave: 1
depends_on: []
files_modified:
  - frontend/src/shared/utils/shortUuid.ts
autonomous: true
---

# Plan 01.3: Short UUID Utility

## Goal
Create a shared utility function for displaying short UUIDs (first 8 characters) to be used across all tables and ID displays.

## must_haves
- [ ] Utility function `shortUuid(id: string): string` that returns first 8 characters
- [ ] Exported from a shared module
- [ ] Used consistently across all DataGrid columns that display IDs

## Tasks

### Task 1: Create shortUuid utility
Create file `frontend/src/shared/utils/shortUuid.ts`:

```typescript
export const shortUuid = (id: string): string => id.slice(0, 8)
```

## Validation
- Import and test: `shortUuid('550e8400-e29b-41d4-a716-446655440000')` returns `'550e8400'`

## Acceptance Criteria
- [ ] `shortUuid` function created and exported
- [ ] Returns first 8 characters of any string
