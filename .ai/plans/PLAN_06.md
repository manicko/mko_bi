---
phase: "06 — CSS Framework Unification"
description: "Verify and enforce CSS framework unification: audit confirms MUI v9 is the sole UI framework with community DataGrid, add license-checker-rseidelsohn for CI license enforcement, verify react-code-standards.md correctness."
autonomous: true
depends_on: []
files_modified:
  - frontend/package.json
  - frontend/package-lock.json
waves:
  - id: 1
    tasks: [TASK_01, TASK_02]
    parallel: true
  - id: 2
    tasks: [TASK_03]
    parallel: false
---

# PLAN_06: CSS Framework Unification

## must_haves

When this phase is complete, ALL of the following must be true:

1. **No DataGrid Pro imports:** Zero imports of `@mui/x-data-grid-pro`, `DataGridPro`, `LicenseInfo`, or `setLicenseKey` exist anywhere in `frontend/src/`. All 5 DataGrid files import from `@mui/x-data-grid` (community/MIT).
2. **No Tailwind in package.json:** `tailwindcss` is not listed in `frontend/package.json` dependencies or devDependencies. No `tailwind.config.*` file exists.
3. **react-code-standards.md verified:** Lines 43-45 correctly codify: MUI-only policy, permissive license requirement, `sx`/`styled()` convention. No changes needed.
4. **No `styled()` usage:** Zero `styled()` calls exist in production code. All 73 `sx` prop usages across 18 files remain appropriate for current scale.
5. **License checker installed:** `license-checker-rseidelsohn` added as a devDependency in `frontend/package.json`.
6. **License audit script:** `npm run licenses` script added to `package.json` that runs `license-checker-rseidelsohn --production --json` and outputs all production dependency licenses.
7. **License audit passes:** Running `npm run licenses` completes without errors. All production dependencies use permissive licenses (MIT, BSD, Apache 2.0, ISC, Unlicense).

---

## Wave 1 (Parallel — independent audit tasks)

### TASK_01: Audit — verify no Pro imports, no license keys, no Tailwind

**Files:** None (read-only audit)
**Symbol:** N/A — grep-based verification
**Semantic anchor:** N/A

**Changes:**

No code changes. Run the following verification commands and confirm zero matches:

```bash
# 1. No DataGrid Pro imports
cd frontend
grep -r "DataGridPro\|data-grid-pro\|@mui/x-data-grid-pro" src/
# Expected: 0 matches

# 2. No MUI license keys
grep -r "LicenseInfo\|setLicenseKey\|licenseKey" src/
# Expected: 0 matches

# 3. No Tailwind in package.json
grep -r "tailwind" package.json
# Expected: 0 matches

# 4. No tailwind.config.* files
find . -name "tailwind.config.*" -not -path "*/node_modules/*"
# Expected: 0 results

# 5. All DataGrid imports are community
grep -r "@mui/x-data-grid" src/
# Expected: 10 matches across 5 files, all from '@mui/x-data-grid' (no -pro suffix)

# 6. No styled() usage in production code
grep -r "styled(" src/ | grep -v "node_modules"
# Expected: 0 matches (providers.tsx imports from '@mui/material/styles' but does not call styled())

# 7. react-code-standards.md lines 43-45 are correct
# Read lines 43-45 of .ai/context/react-code-standards.md — verify MUI-only, license, sx/styled convention
```

**Rationale:** This is a verification audit. The research (RESEARCH_06.md, HIGH confidence) confirms all conditions are already met. This task formally validates that state before proceeding with enforcement. If any check fails, the phase scope changes significantly — but research indicates zero failures.

**Acceptance criteria:**
- All 7 grep/find commands return zero matches (or expected counts for #5)
- `react-code-standards.md` lines 43-45 match the MUI-only, license, and sx/styled policy
- Audit results documented (pass/fail for each check)

**Validation:**
- All grep commands return expected results
- No code changes made

---

### TASK_02: Audit — verify react-code-standards.md correctness

**File:** `.ai/context/react-code-standards.md`
**Symbol:** Lines 43-45
**Semantic anchor:** Lines 43-45 — the MUI-only, license, and sx/styled convention rules.

**Changes:**

No code changes. Read lines 43-45 and verify:

```
43: - **MUI only** — Use `@mui/material` + `@mui/icons-material` + `@mui/x-data-grid` (community) as the sole UI framework. No Tailwind, no Bootstrap, no other CSS frameworks.
44: - **License requirement** — All dependencies must use MIT or similarly permissive licenses (BSD, Apache 2.0, ISC, Unlicense). No paid, proprietary, or "free for open source only" packages. Verify license before adding any dependency.
45: - **Styling: `sx` prop for one-offs, `styled()` for reusable** — Use `sx` for single-use, small, layout-specific styles. Use `styled()` for anything repeated ≥3 times, UI primitives, or app-wide reusable components.
```

Verify:
- Line 43: MUI-only policy present, lists all 3 allowed MUI packages, explicitly forbids Tailwind/Bootstrap
- Line 44: License requirement present, lists allowed licenses, forbids paid/proprietary
- Line 45: sx/styled convention present, defines threshold (≥3 repetitions for styled)

**Rationale:** RESEARCH_06.md confirmed these lines are already correct. This task is a formal verification that the standards document matches the locked decisions (MUI-only, permissive licenses, hybrid sx/styled).

**Acceptance criteria:**
- Lines 43-45 match the expected content described above
- No edits needed — file is already correct
- If any discrepancy is found, flag for user review (do not auto-edit)

**Validation:**
- Read lines 43-45 and confirm match
- No code changes made

---

## Wave 2 (Sequential — enforcement task)

### TASK_03: Add license-checker-rseidelsohn and license audit script

**File:** `frontend/package.json`
**Symbol:** `devDependencies` object, `scripts` object
**Semantic anchor:** Lines 35-53 — devDependencies block. Lines 6-12 — scripts block.

**Changes:**

1. Add `license-checker-rseidelsohn` to `devDependencies`:

```json
"devDependencies": {
  "@eslint/js": "^10.0.1",
  "@testing-library/jest-dom": "^6.9.1",
  "@testing-library/react": "^16.3.2",
  "@testing-library/user-event": "^14.6.1",
  "@types/node": "^24.12.2",
  "@types/plotly.js": "^3.0.10",
  "@types/react": "^19.2.14",
  "@types/react-dom": "^19.2.3",
  "@vitejs/plugin-react": "^6.0.1",
  "eslint": "^10.2.1",
  "eslint-plugin-react-hooks": "^7.1.1",
  "eslint-plugin-react-refresh": "^0.5.2",
  "globals": "^17.5.0",
  "jsdom": "^29.1.1",
  "license-checker-rseidelsohn": "^4.4.2",
  "typescript": "~6.0.2",
  "typescript-eslint": "^8.58.2",
  "vite": "^8.0.10",
  "vitest": "^4.1.6"
}
```

2. Add `licenses` script to `scripts`:

```json
"scripts": {
  "dev": "vite",
  "build": "tsc -b && vite build",
  "lint": "eslint .",
  "licenses": "license-checker-rseidelsohn --production --json",
  "test": "vitest run",
  "test:watch": "vitest",
  "preview": "vite preview"
}
```

3. Run `npm install` to install the new devDependency.

4. Run `npm run licenses` to verify all production dependencies use permissive licenses.

**Rationale:** `license-checker-rseidelsohn` is the actively maintained fork of `license-checker` (which is unmaintained since 2019). It audits all production dependencies (including transitive) and outputs JSON with license information. The `npm run licenses` script makes this reproducible for CI. RESEARCH_06.md recommends this approach. The `--production` flag excludes devDependencies (which are not shipped to users). If any non-permissive licenses are found (GPL, AGPL, SSPL, Proprietary), they must be flagged for user review — but research indicates all current dependencies are permissive.

**Acceptance criteria:**
- `license-checker-rseidelsohn` listed in `devDependencies` at version `^4.4.2`
- `npm run licenses` script added and functional
- `npm install` completes without errors
- `npm run licenses` outputs JSON with all production dependency licenses
- All listed licenses are permissive (MIT, BSD, Apache 2.0, ISC, Unlicense)

**Validation:**
- `cd frontend && npm install` — installs without errors
- `cd frontend && npm run licenses` — outputs valid JSON, zero non-permissive licenses
- `cd frontend && npm run build` — build still passes (no regressions)

---

## Execution Order Summary

| Wave | Task | File(s) | Dependencies |
|------|------|---------|-------------|
| 1 | TASK_01 | None (grep audit) | None |
| 1 | TASK_02 | `react-code-standards.md` (read-only) | None |
| 2 | TASK_03 | `package.json` | TASK_01 (audit passes), TASK_02 (standards verified) |

**Wave dependencies:** Wave 1 (TASK_01 + TASK_02) runs first in parallel — both are read-only audits. Wave 2 (TASK_03) depends on both audits passing. If TASK_01 or TASK_02 find discrepancies, TASK_03 should not proceed until the discrepancies are resolved.

---

## Final Validation (All Tasks Complete)

1. `cd frontend && npm run build` — zero build errors
2. `cd frontend && npm run lint` — zero lint errors
3. `cd frontend && npm run licenses` — all production licenses are permissive
4. `cd frontend && grep -r "DataGridPro\|data-grid-pro\|@mui/x-data-grid-pro" src/` — zero matches
5. `cd frontend && grep -r "LicenseInfo\|setLicenseKey\|licenseKey" src/` — zero matches
6. `cd frontend && grep -r "tailwind" package.json` — zero matches
7. `cd frontend && grep -r "styled(" src/` — zero matches in production code
8. `react-code-standards.md` lines 43-45 verified correct
