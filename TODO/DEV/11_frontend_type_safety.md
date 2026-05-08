---
## DATA PROCESSING
---

### TASK: Frontend TypeScript Strict Mode

FILE: frontend/src/**/*.ts, frontend/src/**/*.tsx

GOAL: Ensure TypeScript strict mode and no `any` types

IMPLEMENT:

* Check tsconfig.json for strict mode enabled
* Remove all `any` types from TypeScript code
* Add proper interfaces for:
  - API responses (AuthResponse, DashboardSummary, etc.)
  - Component props
  - Form data
* Add Zod schemas for form validation (React Hook Form)
* Ensure `tsc --noEmit` passes with no errors

LOGIC:

1. Check frontend/tsconfig.json for `"strict": true`
2. Search for `any` in TypeScript files: `grep -r ": any" frontend/src/`
3. Replace with proper type definitions
4. Create types/api.types.ts with all API response types
5. Create types/enums.ts with TypeScript enums matching backend StrEnum
6. Add Zod schemas for forms (login, register, dashboard creation)
7. Run `cd frontend && npm run tsc --noEmit`

DONE:

* [ ] TypeScript strict mode enabled
* [ ] No `any` types in codebase
* [ ] All API responses typed
* [ ] All component props typed
* [ ] Zod schemas added for forms
* [ ] Command `tsc --noEmit` passes

---

### TASK: Frontend API Integration

FILE: frontend/src/features/*/api/*.ts

GOAL: Ensure proper API integration with error handling

IMPLEMENT:

* Verify axiosInstance configured with:
  - Base URL from env
  - JWT token interceptor
  - Error handling (react-hot-toast)
* Check TanStack Query usage for server state
* Verify polling for long operations (processing status)
* Ensure all API calls use axiosInstance (not direct axios)

LOGIC:

1. Review frontend/src/shared/api/axiosInstance.ts
2. Verify interceptor adds JWT token
3. Verify error handling shows user-friendly messages
4. Check TanStack Query usage in features/*/api/
5. Add polling for processing status endpoint
6. Test: login flow, API calls work

DONE:

* [ ] axiosInstance properly configured
* [ ] JWT interceptor works
* [ ] Error handling user-friendly
* [ ] TanStack Query used correctly
* [ ] Polling implemented for long operations
* [ ] All API calls use axiosInstance

---

### TASK: Frontend Security (Token Storage)

FILE: frontend/src/features/auth/model/authToken.ts

GOAL: Ensure secure JWT token storage

IMPLEMENT:

* Move from localStorage to:
  - Memory storage (recommended for production)
  - OR httpOnly cookies (requires backend change)
* Keep localStorage only for development
* Add token expiration check
* Clear token on logout

LOGIC:

1. Review current token storage in authToken.ts
2. Implement in-memory storage:
   - Store token in variable (not localStorage)
   - Persist only session data
3. OR implement httpOnly cookie approach (backend change required)
4. Add automatic token refresh logic if needed
5. Test: login, token stored, logout clears token

DONE:

* [ ] JWT stored securely (memory or httpOnly cookie)
* [ ] Token expiration handled
* [ ] Logout clears token
* [ ] No sensitive data in localStorage (production)

---
