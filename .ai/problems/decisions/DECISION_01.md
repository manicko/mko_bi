# Phase 1: Initial Setup & Test Configuration - Context

**Gathered:** 2026-05-15
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase covers initial system setup including:
- Default admin user creation with secure credentials
- Test database configuration that mirrors production behavior
- Frontend UI adjustments (removing dashboard links from auth screens)
- User profile password change functionality

Any features beyond these core requirements (additional user roles, advanced auth features, etc.) belong to future phases.
</domain>

<decisions>
## Implementation Decisions

### Admin User Creation

- Admin user should be created via a one-time migration that checks if any user with admin privileges exists
- Password must be hashed using bcrypt with automatic salt generation (per specification)
- Admin credentials (username/password) should be fully configurable via environment variables (MK_ADMIN_USERNAME, MK_ADMIN_PASSWORD) with fallback to hardcoded defaults
- If admin user already exists during initialization, skip creation without updating credentials or throwing an error

### Test Database Setup

- Test database should contain schema-only structure (tables, indexes, constraints, types, functions, triggers) plus minimal baseline data for critical reference data
- Baseline data should include enum/reference data (order statuses, user roles, countries, currencies) and minimal system settings
- Admin user should NOT be included in baseline data - created dynamically in tests
- Schema creation should use Alembic migrations for most tests to match production behavior exactly
- For very fast unit tests, Base.metadata.create_all() can be used via a separate pytest marker
- Data isolation should use database transactions with rollback (function-scoped fixture that begins transaction, yields session, then rolls back)
- Test database must verify production-like behavior including: constraint enforcement, triggers, generated columns, default values, sequences, collation, transaction isolation level, and indexes

### Frontend Dashboard Link Removal

- Remove dashboard links from login and registration screens (specifically the links that appear on these pages)
- This removal should be conditional based on authentication state - only show links when user is authenticated
- Do not replace removed links with anything else - simply remove them
- Review all auth-related screens for any other dashboard links that should be conditionally hidden

### Password Change Functionality

- User profile page must have a "Change password" button
- Clicking the button navigates to a dedicated password change page
- Password change form requires: current password, new password, and new password confirmation
- New password must follow existing validation rules (length, complexity requirements already implemented)
- Current password MUST be required for password change
- Password strength requirements should be implemented and communicated to users via UI feedback
- After successful password change, redirect user back to their profile page
- No email confirmation should be sent on password change
- User should remain logged in after password change (no forced re-login)
</decisions>

<specifics>
## Specific Ideas

- Admin creation should be idempotent and safe to run multiple times
- Test baseline data should be loaded via session-scoped fixture that applies once per test session
- Password change button should be prominently placed on the user profile page
- Password change form should include current password field, new password field, and confirmation field
- Consider showing password strength meter during new password entry
- After password change, show success message on profile page
</specifics>

<deferred>
## Deferred Ideas

- Additional default user roles beyond admin
- Social login or OAuth integrations
- Advanced password policies (password history, expiration)
- Email/SMS verification for password changes
- Admin user management interface in UI
- Separate backup/restore functionality for test databases
</deferred>

---

_Phase: 01-initial-setup_
_Context gathered: 2026-05-15_