# Bug Report: LogViewer.tsx UTF-8 Encoding Issue Blocking Build

**Date:** 2026-06-17
**Severity:** HIGH
**Status:** FIXED

## Problem

The frontend build fails with a UTF-8 encoding error when loading `LogViewer.tsx`:

```
[UNLOADABLE_DEPENDENCY] Error: Could not load src/features/admin/ui/LogViewer.tsx
stream did not contain valid UTF-8
```

This error occurs at `AdminPanel.tsx:6` when importing `LogViewer`:
```tsx
import { LogViewer } from './LogViewer'
```

## Evidence

1. `./frontend/src/features/admin/ui/LogViewer.tsx` fails to load during Vite/Rolldown build
2. TypeScript and ESLint both pass successfully - the issue is in the bundler
3. Raw byte analysis showed UTF-16 LE BOM (`ff fe`) at file start

## Root Cause

The file `LogViewer.tsx` was committed with UTF-16 LE BOM encoding. Git stored the file as-is without any conversion. Rollup/Rolldown (Vite's bundler) strictly requires UTF-8 encoding and fails when encountering non-UTF-8 files.

Raw byte analysis:
- Original file: `ff fe 69 00 6d 00 70 00` (UTF-16 LE BOM + "imp" in UTF-16)
- After fix: `69 6d 70 6f 72 74 20 7b` ("import { " in clean UTF-8)

## Resolution

1. Converted `LogViewer.tsx` from UTF-16 LE to UTF-8 using Python
2. Added `.gitattributes` entries to enforce LF line endings for TypeScript/JavaScript files
3. Committed the fix (commit `474f0ea`)
4. Build now succeeds (`npm run run` completes successfully)

## Prevention

Added to `.gitattributes`:
```
*.tsx text eol=lf
*.ts text eol=lf
*.jsx text eol=lf
*.js text eol=lf
```

## Related Task

This bug was discovered while implementing frontend env validation. The env validation changes are correct and pass TypeScript/lint checks. The build failure was unrelated to the task changes.