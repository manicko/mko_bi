---
phase: 01
phase_name: Authorization
description: Authorization phase — 7 modifications across backend and frontend for admin bypass, registration flow, login response, profile display, header navigation, and 403 handling.
waves: 3
total_tasks: 11
autonomous: true
files_modified:
  - src/mkobi/models/user.py
  - src/mkobi/models/auth.py
  - src/mkobi/services/auth_service.py
  - src/mkobi/services/dashboard_service.py
  - src/mkobi/db/repositories/dashboard_repo.py
  - src/mkobi/api/routes/auth.py
  - src/mkobi/api/routes/dashboards.py
  - frontend/src/shared/types/api.types.ts
  - frontend/src/features/auth/api/authApi.ts
  - frontend/src/features/auth/model/useAuth.ts
  - frontend/src/shared/components/Layout/Header.tsx
  - frontend/src/shared/components/Layout/AppLayout.tsx
  - frontend/src/app/routes.tsx
  - frontend/src/features/users/ui/UserProfile.tsx
must_haves:
  - Admins see all dashboards without explicit dashboard_access entries
  - Registration duplicate handling differentiates pending/approved vs rejected
  - Blacklisted domain error message matches spec exactly
  - Login response includes user data (no race condition on frontend)
  - Profile page shows display_name computed from email prefix
  - Header only appears on authenticated pages (not login/register)
  - Direct URL to unauthorized dashboard returns 403 (not 404)
  - No deferred ideas implemented (email notifications, soft delete, rejection reason, dashboard-level roles)
---

# PLAN_01 — Authorization Phase

## Wave 1 — Backend Model/Type Changes (Independent)

### TASK_001_01_add_display_name_to_userread

```yaml
id: TASK_001_01_add_display_name_to_userread
title: Add computed display_name to UserRead model
status: pending
priority: high
depends_on: []
description: >
  Add a computed `display_name` property to the `UserRead` Pydantic model
  that derives the display name from the email prefix (text before @).
  No DB migration needed — this is a computed property.
goals:
  - UserRead model exposes display_name derived from email prefix
  - display_name is included in API responses automatically
files:
  - path: src/mkobi/models/user.py
    targets:
      - type: class
        name: UserRead
    changes:
      - action: add_code
        description: Add computed `display_name` property using @computed_field that extracts prefix from email before @
acceptance_criteria:
  - UserRead(display_name="john", email="john@example.com", ...) works correctly
  - display_name appears in all API responses returning UserRead
  - No database migration required
tests_to_run:
  - tests/
risk_level: low
```

### TASK_001_02_add_token_with_user_response_model

```yaml
id: TASK_001_02_add_token_with_user_response_model
status: pending
priority: high
depends_on: []
description: >
  Create a new Pydantic model `TokenWithUser` in models/auth.py that extends
  Token to include a `user` field of type UserRead. This will be the response
  model for the login endpoint.
goals:
  - Login endpoint can return both token and user data in one response
  - Frontend no longer needs separate /me call after login
files:
  - path: src/mkobi/models/auth.py
    targets:
      - type: class
        name: Token
    changes:
      - action: add_code
        description: Add TokenWithUser model with access_token, token_type, and user fields after Token class
acceptance_criteria:
  - TokenWithUser(access_token="...", token_type="bearer", user=UserRead(...)) validates correctly
  - Model is importable from mkobi.models.auth
tests_to_run:
  - tests/
risk_level: low
```

## Wave 2 — Backend Service/Route Logic (Depends on Wave 1)

### TASK_002_01_admin_bypass_dashboard_listing

```yaml
id: TASK_002_01_admin_bypass_dashboard_listing
status: pending
priority: high
depends_on: []
description: >
  Modify DashboardRepository.get_by_user() to check if the user is admin.
  If admin, return all dashboards via get_all() instead of JOINing with
  dashboard_access. Also modify DashboardService.get_user_dashboards() and
  DashboardService.get_dashboard() to pass user_role for admin bypass.
  Update the get_my_dashboards_endpoint route handler to pass current_user.role
  through to the service layer.
goals:
  - Admins see all dashboards without explicit access entries
  - Non-admins continue to see only dashboards with access entries
  - Admin can access any dashboard detail by direct URL
  - Route handler propagates user role to service layer
files:
  - path: src/mkobi/db/repositories/dashboard_repo.py
    targets:
      - type: method
        name: DashboardRepository.get_by_user
    changes:
      - action: modify_code
        description: Add is_admin parameter; if True, call get_all() instead of JOIN query
  - path: src/mkobi/services/dashboard_service.py
    targets:
      - type: method
        name: DashboardService.get_user_dashboards
      - type: method
        name: DashboardService.get_dashboard
    changes:
      - action: modify_code
        description: Pass user_role to repo methods; in get_dashboard, bypass access check for admins
  - path: src/mkobi/api/routes/dashboards.py
    targets:
      - type: function
        name: get_my_dashboards_endpoint
    changes:
      - action: modify_code
        description: Pass current_user.role to DashboardService.get_user_dashboards() so admin bypass works at the route level
acceptance_criteria:
  - Admin user sees all dashboards from GET /dashboards/my
  - Non-admin user sees only dashboards with explicit access
  - Admin can GET /dashboards/{id} for any dashboard
  - Non-admin without access gets 403 (not 404) for existing dashboard
tests_to_run:
  - tests/
risk_level: medium
```

### TASK_002_02_registration_request_validation

```yaml
id: TASK_002_02_registration_request_validation
status: pending
priority: high
depends_on: []
description: >
  Modify AuthService.register_request() to check existing registration request
  BEFORE checking blocked domain. Differentiate messages:
  - pending/approved → "A request for this email already exists"
  - rejected → "Your request was rejected. Contact an administrator for more information."
  Also change the blacklisted domain error message from
  "Registration with email domain 'X' is not allowed" to
  "This email domain is not allowed for registration".
goals:
  - Duplicate registration requests show specific messages based on status
  - Blocked domain check happens after duplicate check
  - Blacklisted domain error message matches spec exactly
files:
  - path: src/mkobi/services/auth_service.py
    targets:
      - type: method
        name: AuthService.register_request
    changes:
      - action: modify_code
        description: Move existing request check before blocked domain check; differentiate error messages by status (pending/approved vs rejected); change blocked domain message to "This email domain is not allowed for registration"
acceptance_criteria:
  - Pending request → "A request for this email already exists"
  - Approved request → "A request for this email already exists"
  - Rejected request → "Your request was rejected. Contact an administrator for more information."
  - Blocked domain → "This email domain is not allowed for registration" (checked only if no existing request)
tests_to_run:
  - tests/
risk_level: medium
```

### TASK_002_03_login_response_includes_user

```yaml
id: TASK_002_03_login_response_includes_user
status: pending
priority: high
depends_on:
  - TASK_001_01_add_display_name_to_userread
  - TASK_001_02_add_token_with_user_response_model
description: >
  Modify AuthService.login_user() to include user data in the return dict.
  Change the login endpoint response_model from Token to TokenWithUser.
  Update _handle_login to construct TokenWithUser from the dict returned by login_user.
  Return format: {access_token, token_type, user: {id, email, role, display_name, created_at}}
goals:
  - Login response includes user data to avoid race condition
  - Frontend can set user state immediately after login
files:
  - path: src/mkobi/services/auth_service.py
    targets:
      - type: method
        name: AuthService.login_user
    changes:
      - action: modify_code
        description: After successful auth, include user data (UserRead.model_validate) in the returned dict under "user" key
  - path: src/mkobi/api/routes/auth.py
    targets:
      - type: function
        name: _handle_login
      - type: function
        name: login
      - type: function
        name: login_form
    changes:
      - action: modify_code
        description: Change response_model from Token to TokenWithUser. _handle_login must construct TokenWithUser from the dict returned by login_user — change body from `return Token(access_token=token_data["access_token"], token_type="bearer")` to `return TokenWithUser(access_token=token_data["access_token"], token_type="bearer", user=token_data["user"])`
acceptance_criteria:
  - POST /auth/login returns {access_token, token_type, user: {id, email, role, display_name, created_at}}
  - POST /auth/login/form returns the same format
  - No separate /me call needed after login
tests_to_run:
  - tests/
risk_level: medium
```

### TASK_002_04_403_for_unauthorized_dashboard_access

```yaml
id: TASK_002_04_403_for_unauthorized_dashboard_access
status: pending
priority: high
depends_on:
  - TASK_002_01_admin_bypass_dashboard_listing
description: >
  Modify DashboardService.get_dashboard() to distinguish between
  "dashboard not found" (404) and "dashboard exists but no access" (403).
  Currently both cases return None which becomes 404. Must check dashboard
  existence first, then return a sentinel or raise exception for access denied.
  Update the route handler to return 403 "Access denied" when dashboard
  exists but user lacks access.
goals:
  - Non-admin accessing existing dashboard without permission gets 403
  - Non-existing dashboard still returns 404
  - Admin bypass still works
files:
  - path: src/mkobi/services/dashboard_service.py
    targets:
      - type: method
        name: DashboardService.get_dashboard
    changes:
      - action: modify_code
        description: Return a tuple or sentinel to distinguish "not found" from "access denied"; for non-admin users, check existence first then access
  - path: src/mkobi/api/routes/dashboards.py
    targets:
      - type: function
        name: get_dashboard_endpoint
    changes:
      - action: modify_code
        description: Handle access denied case with HTTP 403 "Access denied" instead of 404
acceptance_criteria:
  - GET /dashboards/{existing_id} without access → 403 "Access denied"
  - GET /dashboards/{non_existing_id} → 404 "Dashboard not found"
  - GET /dashboards/{existing_id} with access → 200 with dashboard data
tests_to_run:
  - tests/
risk_level: medium
```

## Wave 3 — Frontend Changes (Depends on Wave 1 & Wave 2)

### TASK_003_01_update_frontend_login_for_user_response

```yaml
id: TASK_003_01_update_frontend_login_for_user_response
status: pending
priority: high
depends_on:
  - TASK_002_03_login_response_includes_user
description: >
  Update the frontend AuthResponse type and useAuth hook to handle the new
  login response format that includes user data. Add display_name to the
  UserProfile interface in api.types.ts. The login function already
  expects response.user, but the backend now actually returns it.
goals:
  - Frontend login works with new backend response format
  - No race condition between login and getProfile
  - UserProfile interface includes display_name field
files:
  - path: frontend/src/shared/types/api.types.ts
    targets:
      - type: interface
        name: AuthResponse
      - type: interface
        name: UserProfile
    changes:
      - action: modify_code
        description: Verify AuthResponse already has user field; add display_name: string to UserProfile interface
  - path: frontend/src/features/auth/model/useAuth.ts
    targets:
      - type: function
        name: useAuth.login
    changes:
      - action: verify_code
        description: Verify login callback correctly uses response.user from the login API response
acceptance_criteria:
  - Login flow works end-to-end with backend returning user in login response
  - User state is set immediately without additional /me call
  - UserProfile interface includes display_name field
tests_to_run:
  - frontend/src/
risk_level: low
```

### TASK_003_02_restructure_routes_move_login_outside_layout

```yaml
id: TASK_003_02_restructure_routes_move_login_outside_layout
status: pending
priority: high
depends_on: []
description: >
  Move /login and /register routes outside of AppLayout in routes.tsx so that
  the Header (and Sidebar) are not rendered on authentication pages.
  Create a separate layout or simply render them without AppLayout wrapper.
goals:
  - Login and Register pages do NOT show Header or Sidebar
  - All other authenticated pages show Header with navigation
files:
  - path: frontend/src/app/routes.tsx
    targets:
      - type: function
        name: AppRoutes
    changes:
      - action: modify_code
        description: Move /login and /register routes to be siblings of AppLayout route, not children. Keep all protected routes inside AppLayout
acceptance_criteria:
  - GET /login renders without Header
  - GET /register renders without Header
  - GET /dashboards renders with Header
  - All existing route functionality preserved
tests_to_run:
  - frontend/src/
risk_level: medium
```

### TASK_003_03_update_header_navigation

```yaml
id: TASK_003_03_update_header_navigation
status: pending
priority: high
depends_on: []
description: >
  Restructure Header component: remove email display, remove logout button from header,
  ensure rightmost button is "Profile", other nav buttons to the left.
  No dropdown menu. Header is a narrow top navigation bar.
goals:
  - Header shows only navigation buttons, no email
  - Rightmost button is "Profile"
  - No logout in header (handled on profile page)
  - Narrow top nav bar on all authenticated pages
files:
  - path: frontend/src/shared/components/Layout/Header.tsx
    targets:
      - type: component
        name: Header
    changes:
      - action: modify_code
        description: Remove email Typography, remove logout Button, keep only Profile button (rightmost) and conditional Admin button to its left
acceptance_criteria:
  - Header does not display user email
  - Header has "Profile" button as rightmost element
  - Header has "Admin" button (for admins) to the left of Profile
  - No logout button in header
tests_to_run:
  - frontend/src/
risk_level: low
```

### TASK_003_04_add_display_name_to_profile_page

```yaml
id: TASK_003_04_add_display_name_to_profile_page
status: pending
priority: high
depends_on:
  - TASK_001_01_add_display_name_to_userread
description: >
  Update UserProfile component to show display_name (computed from email prefix)
  as a read-only field. Also update UserProfile type to include display_name.
  Profile page shows: Email (read-only), Display name (read-only), Global role (read-only),
  Change Password button, Delete Account button (non-admin only).
goals:
  - Profile page shows display_name derived from email
  - All profile fields are read-only
  - Delete Account button hidden for admin users
files:
  - path: frontend/src/features/users/ui/UserProfile.tsx
    targets:
      - type: component
        name: UserProfile
    changes:
      - action: modify_code
        description: Add display_name field (read-only) between email and role sections; ensure Delete Account is hidden for admins
  # Note: UserProfile interface is already updated by TASK_003_01 which adds display_name.
  # This task only modifies the UI component, not the type.
acceptance_criteria:
  - Profile page shows Display Name field (read-only) with email prefix value
  - Profile page shows Email (read-only)
  - Profile page shows Global Role (read-only)
  - Change Password button present
  - Delete Account button present for non-admin, hidden for admin
tests_to_run:
  - frontend/src/
risk_level: low
```

### TASK_003_05_update_register_form_success_message

```yaml
id: TASK_003_05_update_register_form_success_message
status: pending
priority: high
depends_on: []
description: >
  Update RegisterForm to show the specific error messages from the backend
  for duplicate registration requests and blocked domains. Also update the
  success message to match spec: "Your request has been submitted. An administrator will review it."
goals:
  - Success message matches spec exactly
  - Duplicate request errors show specific messages
  - Blocked domain error shows spec message
files:
  - path: frontend/src/features/auth/ui/RegisterForm.tsx
    targets:
      - type: component
        name: RegisterForm
    changes:
      - action: modify_code
        description: Update success message to "Your request has been submitted. An administrator will review it."; display backend error messages directly for duplicate/blocked cases
  - path: frontend/src/features/auth/api/authApi.ts
    targets:
      - type: function
        name: registerRequest
    changes:
      - action: modify_code
        description: Update RegistrationResponse type to match backend return; ensure error messages are propagated to the form
acceptance_criteria:
  - Success message: "Your request has been submitted. An administrator will review it."
  - Duplicate pending/approved: "A request for this email already exists"
  - Duplicate rejected: "Your request was rejected. Contact an administrator for more information."
  - Blocked domain: "This email domain is not allowed for registration"
tests_to_run:
  - frontend/src/
risk_level: low
```
