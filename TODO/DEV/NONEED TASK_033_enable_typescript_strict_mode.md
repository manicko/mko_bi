---
## FRONTEND TYPE SAFETY
---

### TASK: Enable TypeScript strict mode

FILE: `frontend/tsconfig.json`

**PROBLEM**: 
TypeScript strict mode is not enabled in the frontend configuration. This allows implicit `any` types and reduces type safety.

**CURRENT CODE** (`frontend/tsconfig.json`):
```json
{
  "compilerOptions": {
    // ... other options
    // "strict": true,  // Not enabled
  }
}
```

**ISSUE**:
- No strict null checks
- No strict function types
- No strict property initialization
- Implicit `any` types allowed
- Reduces effectiveness of TypeScript

**IMPLEMENT**:

1. Enable strict mode in `tsconfig.json`:
   ```json
   {
     "compilerOptions": {
       "strict": true,
       // ... other options
     }
   }
   ```

2. Run TypeScript compiler to check for errors:
   ```bash
   cd frontend && npx tsc --noEmit
   ```

3. Fix any new type errors that appear:
   - Add explicit type annotations
   - Fix null/undefined handling
   - Update function signatures

4. Consider enabling additional strict options:
   ```json
   {
     "compilerOptions": {
       "strict": true,
       "noImplicitAny": true,
       "strictNullChecks": true,
       "strictFunctionTypes": true,
       "strictPropertyInitialization": true,
       "noImplicitThis": true,
       "alwaysStrict": true
     }
   }
   ```

5. Update frontend code to be strict-mode compliant:
   - `frontend/src/features/dashboards/ui/DashboardView.tsx`
   - `frontend/src/shared/api/axiosInstance.ts`
   - All other TypeScript files

**REFERENCES**:
- `frontend/tsconfig.json`
- TypeScript documentation on strict mode
- Run `npx tsc --init --strict` to see all strict options

**DONE**:
- [ ] Strict mode enabled in tsconfig.json
- [ ] TypeScript compiler errors fixed
- [ ] All frontend files updated for strict mode
- [ ] `npx tsc --noEmit` passes without errors
- [ ] Tests still pass
- [ ] Documentation updated (if needed)
