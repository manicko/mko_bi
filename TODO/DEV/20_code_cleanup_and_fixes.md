# Task: Code Cleanup and Fixes

## Status: TODO

## Priority: Medium

## Description

Unrelated issues found during database improvements task that need to be addressed:

### Issues Found

1. **Russian Comments in `src/mkobi/models/data.py`**
   - Per SPEC.md requirement: "All comments and logs must be in English"
   - Location: `CustomMetricConfig` class, line 278
   - Issue: `description="Разрешенные типы файлов"` should be in English
   - Additional Russian comments may exist in this file

2. **Temporary/Fix Files in Root Directory**
   - These files appear to be temporary fix scripts that should be cleaned up:
     - `add_cors_tests.py`
     - `fix_config.py`
     - `fix_cors_validator.py`
     - `fix_mypy.py`
     - `fix_repositories.py`
     - `fix_static_calls.py`
     - `check_paths.py`
     - `check_tables.py`
     - `setup_test_db.py`
   - Action: Review and delete if no longer needed

3. **`to_thread_run` Bug in `starter.py`** (FIXED)
   - Was using undefined `to_thread_run` function
   - Fixed to use `asyncio.to_thread()` which is already imported
   - This is now resolved

4. **`mypy_errors.txt` and `mypy_output.txt`**
   - These appear to be temporary mypy output files
   - Should be cleaned up or added to `.gitignore`

## Tasks

- [ ] Search for and fix any remaining Russian comments in `src/mkobi/models/data.py`
- [ ] Review temporary files in root directory and delete if not needed
- [ ] Clean up or gitignore mypy output files
- [ ] Run full test suite after cleanup to ensure nothing is broken

## Acceptance Criteria

- All comments in the codebase are in English (per SPEC.md)
- No temporary/fix files cluttering the root directory
- Repository is clean and well-organized

## Notes

These issues were discovered during the database improvements task (09_database_improvements_DONE.md) but are not directly related to database functionality.
