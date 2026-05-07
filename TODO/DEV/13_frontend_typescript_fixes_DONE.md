---
## FRONTEND TYPESCRIPT FIXES
---

### TASK: Fix Frontend TypeScript Types and Standards

FILE: `frontend/src/shared/types/api.types.ts`, `frontend/src/features/*`

GOAL: Ensure TypeScript types match backend enums and follow best practices

ISSUE DESCRIPTION:

1. **TypeScript types use string literals instead of importing/enums**:
   ```typescript
   // Current (api.types.ts):
   role: 'admin' | 'editor' | 'viewer'  // Should be consistent with backend
   type: 'bar' | 'line' | 'pie' | 'table'
   permission: 'view' | 'edit' | 'admin'
   ```

2. **No shared enum definitions between frontend and backend**:
   - Backend uses `StrEnum` in `src/mkobi/models/enums.py`
   - Frontend uses inline string unions
   - Easy to get out of sync

3. **Inconsistent naming conventions**:
   - Some files use Ukrainian (`Завантаження`)
   - Some use English
   - Mixed in the same file (`upload.tsx` has Ukrainian comments)

4. **Missing type exports**:
   - Some components use `unknown` instead of proper types
   - `GraphData.data: unknown` - should be proper Plotly type

IMPACT:
- Type safety issues
- Hard to maintain (changes in backend enums need manual sync)
- Confusing for developers

FILES TO FIX:
- `frontend/src/shared/types/api.types.ts` - Create proper enums or constants
- `frontend/src/features/upload/ui/UploadPage.tsx` - Fix language
- `frontend/src/features/*/api/*.ts` - Ensure proper typing
- Create shared enum file: `frontend/src/shared/types/enums.ts`

IMPLEMENTATION:

1. **Create shared enum file** `frontend/src/shared/types/enums.ts`:
   ```typescript
   export enum UserRole {
     ADMIN = 'admin',
     EDITOR = 'editor',
     VIEWER = 'viewer',
   }
   
   export enum GraphType {
     BAR = 'bar',
     LINE = 'line',
     PIE = 'pie',
     TABLE = 'table',
   }
   
   export enum DashboardPermission {
     VIEW = 'view',
     EDIT = 'edit',
     ADMIN = 'admin',
   }
   
   export enum UploadMode {
     OVERWRITE = 'overwrite',
     APPEND = 'append',
   }
   
   export enum ProcessingStatus {
     STARTED = 'started',
     UPLOADED = 'uploaded',
     PROCESSING = 'processing',
     SUCCESS = 'success',
     FAILED = 'failed',
     COMPLETED = 'completed',
   }
   ```

2. **Update `api.types.ts` to use enums**:
   ```typescript
   import { UserRole, GraphType, DashboardPermission } from './enums'
   
   export interface UserProfile {
     id: string
     email: string
     role: UserRole  // Instead of string literal
   }
   
   export interface GraphConfig {
     id: string
     name: string
     type: GraphType  // Instead of string literal
     // ...
   }
   ```

3. **Fix language consistency** (choose English for open source):
   ```tsx
   // BEFORE (UploadPage.tsx):
   // Завантаження файлу
   
   // AFTER:
   // Upload file
   ```

4. **Add proper Plotly types**:
   ```typescript
   import { Data, Layout } from 'plotly.js'
   
   export interface GraphData {
     graph_id: string
     data: Data[]  // Instead of unknown
   }
   ```

TESTING:
- [ ] TypeScript compiles without errors: `cd frontend && npm run build`
- [ ] All enum values match backend StrEnum values
- [ ] No `unknown` types where proper types can be used
- [ ] Consistent language (English) across codebase

PRIORITY: Medium (type safety)

SPEC REFERENCE:
- SPEC_FRONTEND.md section 5: API endpoints with type definitions
- Requirements: "Typing", "Code standards"
