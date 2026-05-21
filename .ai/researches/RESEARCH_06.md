# 06 CSS Framework Unification - Research

**Researched:** 2026-05-20
**Domain:** MUI v9 styling architecture, DataGrid community edition, license compliance
**Confidence:** HIGH

## Summary

Phase 6 is a **validation and cleanup phase**, not a migration. The codebase is already ~99.5% MUI v9. The research confirms:

1. **No DataGrid migration is needed** — the project already uses `@mui/x-data-grid` (community/MIT) v9.0.4. Zero imports of `@mui/x-data-grid-pro` exist. No license key (`LicenseInfo`, `setLicenseKey`) is present. The community version already provides all features the codebase uses: sorting, filtering, pagination, editing, CSV export, print, column resizing, and the `GridToolbar` with quick filter.

2. **No `styled()` usage exists** — the entire codebase uses `sx` prop exclusively (73 occurrences across 18 files). This is acceptable for the current scale. The `styled()` API should be introduced only when a style pattern repeats ≥3 times.

3. **Tailwind is not installed** — `NotFound.tsx` is the only Tailwind file (uses `className` with Tailwind classes), but Tailwind CSS is not in `package.json` and no `tailwind.config.*` exists. This is already scoped for Phase 5.

4. **react-code-standards.md is already correct** — lines 43-45 codify the MUI-only policy, license requirement, and `sx`/`styled()` convention. No changes needed.

**Primary recommendation:** Phase 6 tasks are primarily audit/verification — confirm no Pro imports exist, verify all dependencies have permissive licenses, and update `NotFound.tsx` (already in Phase 5 scope). The phase should be lightweight.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `@mui/material` | ^9.0.0 | UI component library | Already sole framework; MIT license |
| `@mui/icons-material` | ^9.0.0 | Icon components | Pairs with MUI; MIT license |
| `@mui/x-data-grid` | ^9.0.4 | Data tables (community) | Already installed; MIT license; all required features present |
| `@emotion/react` | ^11.14.0 | CSS-in-JS engine for MUI | Required by MUI v9; MIT license |
| `@emotion/styled` | ^11.14.1 | `styled()` API for MUI | Required by MUI v9; MIT license |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|--------------|
| `license-checker` (dev) | ^25.0.0 | Audit dependency licenses | Add as devDep for CI license verification; `--production --json` |
| `license-checker-rseidelsohn` (dev) | ^4.4.2 | Alternative license checker | More actively maintained fork of license-checker |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `@mui/x-data-grid` (community) | `@mui/x-data-grid-pro` | Pro requires commercial license (~$600/dev/year); no feature gap justifies cost |
| `sx` prop everywhere | `styled()` for all | `styled()` adds unnecessary abstraction for one-off styles; `sx` is idiomatic for MUI v9 one-offs |
| Manual license audit | `license-checker` in CI | Manual is error-prone; automated is reproducible |

**Installation (if adding license checker):**
```bash
cd frontend
npm install --save-dev license-checker
# or
npm install --save-dev license-checker-rseidelsohn
```

## Architecture Patterns

### Current Styling Architecture (confirmed)

```
frontend/src/
├── app/
│   └── providers.tsx          # ThemeProvider + createTheme (MUI v9)
├── features/
│   ├── admin/ui/              # 4 DataGrid files (all community imports)
│   ├── dashboards/ui/         # 1 DataGrid file + DashboardList
│   ├── auth/ui/               # LoginForm, RegisterForm (sx only)
│   ├── upload/ui/             # FileDropzone, UploadModal (sx only)
│   └── users/ui/              # UserProfile, ChangePasswordPage (sx only)
├── shared/
│   ├── components/
│   │   ├── Layout/            # Header, Sidebar (sx only)
│   │   ├── NotFound.tsx       # ONLY Tailwind file (Phase 5 scope)
│   │   ├── AccessDenied.tsx   # sx only
│   │   └── ProtectedRoute.tsx # sx only
```

### Pattern 1: `sx` Prop for One-Off Styles

**What:** Inline styles via MUI's `sx` prop, leveraging theme tokens.
**When to use:** Single-use styles, 1-3 properties, layout-specific adjustments.
**Example:**
```tsx
// Source: MUI official docs + codebase pattern (UserManagement.tsx:150)
<DataGrid
  sx={{
    '& .row-saving': {
      backgroundColor: '#fef08a',
    },
  }}
/>
```

### Pattern 2: `styled()` for Reusable Components

**What:** Create styled components using MUI's `styled()` API (wraps Emotion).
**When to use:** Style repeats ≥3 times, UI primitives, app-wide reusable components.
**Example:**
```tsx
// Source: MUI official docs
import { styled } from '@mui/material/styles';

const StyledCard = styled('div')(({ theme }) => ({
  padding: theme.spacing(2),
  borderRadius: theme.spacing(1),
  backgroundColor: theme.palette.background.paper,
}));
```

### Anti-Patterns to Avoid

- **Mixing Tailwind with MUI:** Never add Tailwind classes to MUI components. Use `sx` prop instead.
- **Using `styled()` for one-offs:** Don't create a styled component for a single-use style. Use `sx`.
- **Adding non-MUI UI libraries:** No Bootstrap, no shadcn/ui, no Headless UI. MUI is the sole framework.
- **Circular `sx` dependencies:** Don't pass complex objects in `sx` that reference the component itself.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| License compliance audit | Manual `package.json` scanning | `license-checker --production --json` | Catches transitive dependency licenses automatically |
| DataGrid features (sorting, filtering, pagination) | Custom table component | `@mui/x-data-grid` community | Battle-tested, accessible, performant |
| Theme/styling system | Custom CSS modules or Tailwind | MUI `sx` + `styled()` + `ThemeProvider` | Already set up; consistent with MUI ecosystem |
| CSV export from DataGrid | Custom CSV generation | Built-in `exportDataAsCsv()` | Handles column visibility, sorting, filtering automatically |

**Key insight:** The codebase already has the right tools. Phase 6 is about verifying and enforcing, not building new things.

## Common Pitfalls

### Pitfall 1: Assuming DataGrid Pro Migration is Needed

**What goes wrong:** Developer spends time migrating from Pro to Community, changing imports, removing license keys.
**Why it happens:** The phase brief mentions "DataGrid migration" which implies work is needed.
**How to verify:** `grep -r "DataGridPro\|data-grid-pro\|licenseKey\|LicenseInfo" frontend/` — returns zero results.
**Warning signs:** If you find yourself changing DataGrid imports, stop. The work is already done.

### Pitfall 2: Adding `styled()` Prematurely

**What goes wrong:** Developer converts all `sx` usages to `styled()` components, adding abstraction without benefit.
**Why it happens:** `styled()` is the "recommended" pattern for reusable components, but the codebase doesn't have enough repetition to justify conversion.
**How to avoid:** Only introduce `styled()` when a style pattern is used ≥3 times. Current 73 `sx` usages are appropriate for the codebase scale.
**Warning signs:** Creating `styled()` wrappers for single-file use.

### Pitfall 3: License Checker False Positives

**What goes wrong:** `license-checker` reports "unknown" licenses for packages with non-standard license files.
**Why it happens:** Some packages don't use SPDX identifiers in their `package.json` license field.
**How to handle:** Use `--unknown` flag to flag ambiguous packages for manual review. Don't fail CI on unknown — fail only on known non-permissive licenses (GPL, AGPL, proprietary).
**Warning signs:** CI fails on packages like `plotly.js-dist-min` which is MIT but may have complex license metadata.

### Pitfall 4: NotFound.tsx Tailwind Dependency

**What goes wrong:** `NotFound.tsx` uses Tailwind classes but Tailwind CSS isn't installed, so styles don't apply in production.
**Why it happens:** The file was created as a quick placeholder with Tailwind classes, but Tailwind was never added to the project.
**How to handle:** This is Phase 5 scope (rewriting NotFound.tsx from Tailwind to MUI). Don't address it in Phase 6.
**Warning signs:** Adding Tailwind to package.json to "fix" NotFound.tsx — don't.

## Code Examples

### Verifying No Pro Imports

```bash
# Run these commands from project root — all should return zero results
cd frontend
grep -r "DataGridPro\|data-grid-pro\|@mui/x-data-grid-pro" src/
grep -r "LicenseInfo\|setLicenseKey\|licenseKey" src/
grep -r "tailwind" package.json
find . -name "tailwind.config.*"
```

### License Checker Usage

```bash
# Install
npm install --save-dev license-checker

# Audit production dependencies only
npx license-checker --production --json > licenses.json

# Fail CI on non-permissive licenses
npx license-checker --production --failOn "GPL;AGPL;SSPL;Proprietary"

# Show only unknown licenses (for manual review)
npx license-checker --production --unknown
```

### MUI `sx` Prop Pattern (from codebase)

```tsx
// Source: frontend/src/features/admin/ui/UserManagement.tsx:150
<DataGrid<UserRow>
  rows={rows}
  columns={columns}
  loading={isLoading}
  autoHeight
  pageSizeOptions={[10, 25, 50]}
  initialState={{
    pagination: { paginationModel: { pageSize: 25 } },
  }}
  processRowUpdate={handleProcessRowUpdate}
  getRowClassName={getRowClassName}
  sx={{
    '& .row-saving': {
      backgroundColor: '#fef08a',
    },
  }}
/>
```

### MUI `styled()` Pattern (for future use)

```tsx
// Source: MUI official docs
import { styled } from '@mui/material/styles';
import Box from '@mui/material/Box';

const StyledContainer = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2),
  backgroundColor: theme.palette.background.paper,
  borderRadius: theme.shape.borderRadius,
  boxShadow: theme.shadows[1],
}));
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `@mui/x-data-grid-pro` | `@mui/x-data-grid` (community) | Already in place | MIT license, no cost, all needed features present |
| `makeStyles` / `withStyles` | `sx` prop + `styled()` | MUI v5 (2022) | `makeStyles` removed in MUI v9; `sx` is now idiomatic |
| Tailwind CSS | MUI `sx` prop | Never adopted | Tailwind was never installed; only `NotFound.tsx` has Tailwind classes |
| Manual license audit | `license-checker` in CI | Proposed for Phase 6 | Automated, reproducible compliance |

**Deprecated/outdated:**
- `@mui/x-data-grid-pro`: Commercial license required; community version already installed
- `makeStyles`: Removed in MUI v9; no usage in codebase
- Tailwind CSS: Never installed; only accidental usage in `NotFound.tsx`

## Open Questions

1. **Should license-checker be added as a devDependency or used via npx?**
   - What we know: `license-checker` is stable (v25.0.1) but unmaintained since 2019. `license-checker-rseidelsohn` (v4.4.2) is actively maintained.
   - What's unclear: Whether to add it as a permanent devDependency or run via `npx` in CI.
   - Recommendation: Add `license-checker-rseidelsohn` as a devDependency for CI integration. It's actively maintained and has better output formats.

2. **Should the license check be a pre-commit hook or CI-only?**
   - What we know: Pre-commit hooks catch issues earlier but slow down commits.
   - What's unclear: Team preference for feedback speed vs. commit speed.
   - Recommendation: CI-only for now. Add pre-commit hook only if non-permissive licenses slip through.

## Sources

### Primary (HIGH confidence)
- Context7 `/mui/material-ui` — MUI System `sx` prop usage, when to use `sx` vs `styled()`
- Context7 `/mui/mui-x` — DataGrid community version features, export capabilities, licensing plans
- Official MUI X docs: https://mui.com/x/introduction/licensing/ — Community vs Pro vs Premium feature breakdown
- Official MUI X docs: https://mui.com/x/react-data-grid/export/ — CSV, Print, Excel export availability by plan
- Codebase verification: `grep` searches confirming zero Pro imports, zero `styled()` usage, 73 `sx` usages
- `frontend/package.json` — Confirms `@mui/x-data-grid` ^9.0.4 (community), no Tailwind, no Pro packages

### Secondary (MEDIUM confidence)
- npm: https://www.npmjs.com/package/license-checker — License checker CLI tool
- npm: https://www.npmjs.com/package/license-checker-rseidelsohn — Actively maintained fork
- npm: https://www.npmjs.com/package/license-checker-evergreen — Modern TypeScript fork

### Tertiary (LOW confidence)
- None — all findings verified from primary sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Verified from `package.json` and Context7
- Architecture: HIGH — Verified from codebase analysis (grep, file reads)
- Pitfalls: HIGH — Based on actual codebase state and official MUI docs
- DataGrid community vs Pro: HIGH — Verified from MUI official licensing docs and codebase grep

**Research date:** 2026-05-20
**Valid until:** 2026-06-20 (30 days — stable domain, MUI v9 is current)
