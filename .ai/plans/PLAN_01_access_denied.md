---
wave: 1
depends_on: []
files_modified:
  - frontend/src/shared/components/AccessDenied.tsx
autonomous: true
---

# Plan 01.5: Access Denied Component

## Goal
Create an `AccessDenied` component that displays "No access — contact your administrator" with no additional actions, per the locked UX decision.

## must_haves
- [ ] Displays text: "No access — contact your administrator"
- [ ] No buttons or additional actions
- [ ] Centered display suitable for embedding in content area
- [ ] Uses MUI components for consistent styling

## Tasks

### Task 1: Create AccessDenied component
Create file `frontend/src/shared/components/AccessDenied.tsx`:

```tsx
import { Box, Typography } from '@mui/material'

export function AccessDenied() {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 4 }}>
      <Typography color="text.secondary">No access — contact your administrator</Typography>
    </Box>
  )
}
```

## Validation
- Verify the component renders the exact text "No access — contact your administrator"
- Verify no interactive elements are present

## Acceptance Criteria
- [ ] AccessDenied component created
- [ ] Exact text matches the locked decision
- [ ] No buttons or actions
