---
phase: 1
name: Auth Token Management
description: Implementation of secure authentication token management using in-memory access tokens and httpOnly secure cookie refresh tokens
depends_on: []
files_modified:
  - backend config files
  - security module
  - auth routes and endpoints
  - auth service
  - models
  - frontend auth modules
  - axios interceptors
  - routing
autonomous: false
---

# Auth Token Management - Phase 1

## Executive Summary

Implement secure authentication token management using in-memory access tokens and httpOnly secure cookie refresh tokens. Users stay logged in across page refreshes without exposing tokens to XSS. This phase includes backend token creation/refresh endpoints with cookie-based refresh tokens and frontend silent refresh on initialization.

## Waves Structure

### Wave 1: Backend Configuration and Token Infrastructure ⚙️
*Dependencies: None - Infrastructure setup*
*Tasks: 1-5*

### Wave 2: Security and Token Generation 🔒
*Dependencies: Wave 1*
*Tasks: 6-9*

### Wave 3: Backend Auth Routes and Endpoints 🔄
*Dependencies: Wave 2*
*Tasks: 10-13*

### Wave 4: Frontend Auth Integration ⚛️
*Dependencies: Wave 3*
*Tasks: 14-17*

### Wave 5: Testing and Validation ✅
*Dependencies: All previous waves*
*Tasks: 18-20*

## Dependency Graph

```
Wave 1 (Config & Infrastructure) ──┐
                                   ├─> Wave 2 (Security & Token Logic) ──┐
                                   │                                     ├─> Wave 3 (API Endpoints) ──┐
                                   │                                     │                           ├─> Wave 4 (Frontend) ──┐
                                   │                                     │                           │                       ├─> Wave 5 (Testing)
                                   └─────────────────────────────────────┴───────────────────────────┴───────────────────────┘
```

## Tasks

### Wave 1: Backend Configuration and Token Infrastructure

#### Task 1: Update JWT Configuration
- **ID**: TASK_01_01_config_update_jwt
- **Title**: Update JWT token expiration defaults
- **Description**: Modify config.py to include refresh token expiration setting and change access token default from 30 to 15 minutes
- **Files affected**: `src/mkobi/config.py:99-104`
- **Targets**:
  - Add `refresh_token_expire_minutes: int = 10080` (7 days) to JWTSettings class
  - Change `access_token_expire_minutes: int = 30` to `access_token_expire_minutes: int = 15`
- **Acceptance criteria**:
  - JWTSettings class has refresh_token_expire_minutes attribute
  - Access token default expiration is 15 minutes
  - Configuration loads without errors
- **Tests to run**:
  - `pytest tests/ -k "test_config" -v`
  - Manual verification: `python -c "from mkobi.config import get_config; print(get_config().jwt.access_token_expire_minutes, get_config().jwt.refresh_token_expire_minutes)"`

#### Task 2: Add Create Refresh Token Function
- **ID**: TASK_01_02_security_refresh_token
- **Title**: Add refresh token creation function to security module
- **Description**: Create new function in security.py to generate refresh tokens with longer expiration
- **Files affected**: `src/mkobi/core/security.py:297-320`
- **Targets**:
  - Add `create_refresh_token(data: dict[str, Any]) -> str` function
  - Function should use refresh token expiration from config
  - Include proper logging
- **Acceptance criteria**:
  - Function creates valid JWT tokens with refresh token expiration
  - Uses config.jwt.refresh_token_expire_minutes
  - Function is properly documented with docstring
- **Tests to run**:
  - `pytest tests/ -k "test_security" -v`

#### Task 3: Create Logout Endpoint
- **ID**: TASK_01_03_auth_logout
- **Title**: Add logout endpoint that clears refresh token cookie
- **Description**: Create new POST /auth/logout endpoint that sets refresh token cookie expiration to 0
- **Files affected**: `src/mkobi/api/routes/auth.py:464-485`
- **Targets**:
  - Add new route: `@router.post("/logout")`
  - Return 200 OK with success message
  - Validate current user authentication
- **Acceptance criteria**:
  - Endpoint requires valid JWT token
  - Returns standardized success response
  - Cookie is cleared on response
- **Tests to run**:
  - Manual API test using curl or Postman

#### Task 4: Update Refresh Token Model
- **ID**: TASK_01_04_models_refresh_request
- **Title**: Remove RefreshRequest model (no longer needed)
- **Description**: Since refresh tokens move to cookies, RefreshRequest BODY model becomes unnecessary
- **Files affected**: `src/mkobi/models/auth.py:134-146`
- **Targets**:
  - Remove RefreshRequest model completely
- **Acceptance criteria**:
  - RefreshRequest model is removed
  - No references to RefreshRequest remain in imports
  - Models validate without errors
- **Tests to run**:
  - `pytest tests/ -k "test_auth" -v`

#### Task 5: Configure Secure Cookie Defaults
- **ID**: TASK_01_05_security_cookie_config
- **Title**: Add cookie security configuration
- **Description**: Add constants for cookie security attributes (httponly, secure, samesite)
- **Files affected**: `src/mkobi/core/security.py:32-36`
- **Targets**:
  - Add `COOKIE_HTTPONLY: bool = True`
  - Add `COOKIE_SECURE: bool = True`
  - Add `COOKIE_SAMESITE: str = "strict"`
- **Acceptance criteria**:
  - Security constants are defined and used throughout codebase
  - Cookie attributes are consistently applied
- **Tests to run**:
  - Code review for consistent usage

### Wave 2: Security and Token Generation

#### Task 6: Implement Token in Validation
- **ID**: TASK_02_01_security_token_validation
- **Title**: Add comprehensive token validation function
- **Description**: Create function to validate refresh tokens and extract user data
- **Files affected**: `src/mkobi/core/security.py:321-340`
- **Targets**:
  - Add `validate_refresh_token(token: str) -> dict[str, Any] | None`
  - Function should handle expired/invalid tokens gracefully
  - Include proper error logging
- **Acceptance criteria**:
  - Function returns None for invalid/expired tokens
  - Function extracts user_id, email, role from valid tokens
  - Proper error handling for malformed tokens
- **Tests to run**:
  - `pytest tests/ -k "test_security" -v`

#### Task 7: Update Login to Set Refresh Token
- **ID**: TASK_02_02_auth_login_cookie
- **Title**: Modify login to set httpOnly refresh token cookie
- **Description**: Update login endpoint to set refresh token cookie alongside access token in JSON response
- **Files affected**: `src/mkobi/api/routes/auth.py:60-80`
- **Targets**:
  - Import cookie response functions
  - After successful authentication, set refresh token cookie
  - Cookie should use security constants
- **Acceptance criteria**:
  - Login returns TokenWithUser with access_token
  - Refresh token cookie is set with httponly, secure, samesite attributes
  - Cookie expiration set to 7 days
  - Return standard JSON response
- **Tests to run**:
  - Manual API test: login and verify cookie is present

#### Task 8: Implement Cookie-Based Refresh Endpoint
- **ID**: TASK_02_03_auth_refresh_cookie
- **Title**: Rewrite refresh endpoint to use cookie instead of request body
- **Description**: Modify refresh endpoint to read refresh token from cookie instead of request body
- **Files affected**: `src/mkobi/api/routes/auth.py:212-277`
- **Targets**:
  - Change from `refresh_data: RefreshRequest` to `request: Request`
  - Read refresh token: `request.cookies.get("mkobi_refresh_token")`
  - Validate refresh token using new validation function
  - Issue new access token
  - Remove RefreshRequest model dependency
- **Acceptance criteria**:
  - Endpoint reads refresh token from cookie
  - Returns new access token on success
  - Proper error handling for missing/invalid cookies
- **Tests to run**:
  - Manual API test: refresh token using cookies

#### Task 9: Add Cookie Management Utilities
- **ID**: TASK_02_04_security_cookie_utils
- **Title**: Create cookie response utility functions
- **Description**: Add helper functions for creating secure cookie responses
- **Files affected**: `src/mkobi/core/security.py:341-365`
- **Targets**:
  - Add `create_secure_cookie(name: str, value: str, max_age: int) -> dict[str, Any]`
  - Add `delete_cookie(name: str) -> dict[str, Any]`
  - Functions should use security constants
- **Acceptance criteria**:
  - Functions use httponly, secure, samesite attributes
  - Functions are properly documented
  - Consistent cookie creation throughout codebase
- **Tests to run**:
  - `pytest tests/ -k "test_security" -v`

### Wave 3: Backend Auth Routes and Endpoints

#### Task 10: Complete Logout Implementation
- **ID**: TASK_03_01_auth_complete_logout
- **Title**: Complete logout implementation with cookie clearing
- **Description**: Finish logout endpoint implementation that clears refresh token cookie
- **Files affected**: `src/mkobi/api/routes/auth.py:464-485`
- **Targets**:
  - Use cookie deletion utility function
  - Return success response
  - Validate current user
- **Acceptance criteria**:
  - Logout clears refresh token cookie
  - Returns standardized success response
  - User remains authenticated (no token clearing in backend)
- **Tests to run**:
  - Manual API test: logout and verify cookie is removed

#### Task 11: Update Auth Service for Cookie Operations
- **ID**: TASK_03_02_auth_service_cookie_ops
- **Title**: Update AuthService to support cookie-based refresh operations
- **Description**: Update authentication service to work with cookie-based token refresh
- **Files affected**: `src/mkobi/services/auth_service.py:237-260`
- **Targets**:
  - Update refresh_token method documentation
  - Ensure token creation uses new security utilities
  - Remove any RefreshRequest dependencies
- **Acceptance criteria**:
  - AuthService methods are updated for cookie-based flow
  - No breaking changes to existing functionality
  - Proper error handling maintained
- **Tests to run**:
  - `pytest tests/ -k "test_auth_service" -v`

#### Task 12: Add Refresh Token Validation Service Method
- **ID**: TASK_03_03_auth_service_validate
- **Title**: Add refresh token validation service method
- **Description**: Add method to AuthService for validating refresh tokens
- **Files affected**: `src/mkobi/services/auth_service.py:277-290`
- **Targets**:
  - Add `validate_refresh_token(self, token: str) -> dict[str, Any] | None`
  - Use security module validation function
  - Return user data if valid
- **Acceptance criteria**:
  - Method integrates with existing AuthService
  - Proper error handling
  - Consistent with service architecture
- **Tests to run**:
  - `pytest tests/ -k "test_auth_service" -v`

#### Task 13: Update Database Access for User Lookup
- **ID**: TASK_03_04_db_user_lookup
- **Title**: Update refresh logic to use proper user lookup
- **Description**: Ensure refresh token validation includes database lookup for user verification
- **Files affected**: `src/mkobi/api/routes/auth.py:234-256`
- **Targets**:
  - After validating token, check user exists in database
  - Raise appropriate error if user not found
  - Maintain proper error logging
- **Acceptance criteria**:
  - Refresh works only for valid, existing users
  - Proper 401 errors for invalid tokens
  - User lookup is atomic with token validation
- **Tests to run**:
  - Manual API test: refresh with invalid/deleted user account

### Wave 4: Frontend Auth Integration

#### Task 14: Implement Silent Refresh on App Initialization
- **ID**: TASK_04_01_frontend_silent_refresh
- **Title**: Add silent refresh when access token missing but refresh cookie exists
- **Description**: Modify frontend auth to check for access token on app init and perform silent refresh if needed
- **Files affected**: `src/features/auth/model/useAuth.ts:45-67`
- **Targets**:
  - Add refresh token API function
  - Implement silent refresh logic in useEffect
  - Handle refresh cookie with credentials: 'include'
  - Queue requests during refresh
- **Acceptance criteria**:
  - App stays logged in after page refresh
  - No loading screen interruption
  - Graceful handling of refresh failures
- **Tests to run**:
  - Manual test: refresh page and verify automatic re-login

#### Task 15: Implement Refresh Token API Function
- **ID**: TASK_04_02_frontend_refresh_api
- **Title**: Add refresh token API function
- **Description**: Create API function to call POST /auth/refresh with credentials
- **Files affected**: `src/features/auth/api/authApi.ts:1-22`
- **Targets**:
  - Add `refreshToken()` function
  - Call with `credentials: 'include'` for cookie access
  - Return response data
- **Acceptance criteria**:
  - Function properly calls refresh endpoint
  - Cookies are included in request
  - Function is properly typed
- **Tests to run**:
  - Unit test: refreshToken function mock

#### Task 16: Implement Request Queuing for Concurrent 401s
- **ID**: TASK_04_03_frontend_request_queue
- **Title**: Add request queuing mechanism for concurrent 401 handling
- **Description**: Implement queue for pending requests during token refresh to handle concurrent 401s
- **Files affected**: `src/features/auth/model/useAuth.ts:45-67`
- **Targets**:
  - Add isRefreshing flag
  - Add failedQueue array
  - Implement queue management functions
  - Retry queued requests after refresh
- **Acceptance criteria**:
  - Only single refresh operation for concurrent 401s
  - All queued requests are retried on successful refresh
  - No duplicate refresh calls
- **Tests to run**:
  - Manual test: multiple concurrent requests during token expiry

#### Task 17: Complete Logout Frontend Implementation
- **ID**: TASK_04_04_frontend_logout_complete
- **Title**: Complete frontend logout implementation with API call
- **Description**: Update logout to call POST /auth/logout and redirect with location preservation
- **Files affected**: `src/features/auth/model/useAuth.ts:39-44`
- **Targets**:
  - Call POST /auth/logout API endpoint
  - Use credentials: 'include' for cookie clearing
  - Preserve location state for redirect
- **Acceptance criteria**:
  - Logout clears backend refresh cookie
  - Frontend clears local token storage
  - Redirect preserves intended destination
- **Tests to run**:
  - Manual test: logout and verify redirect to intended page

### Wave 5: Testing and Validation

#### Task 18: Backend Authorization Tests
- **ID**: TASK_05_01_backend_auth_tests
- **Title**: Add comprehensive backend authentication tests
- **Description**: Create tests for new auth endpoints and cookie functionality
- **Files affected**: `tests/ -k auth -v`
- **Targets**:
  - Test logout endpoint cookie clearing
  - Test refresh endpoint with cookies
  - Test refresh token validation
  - Test access token expiration (15 min)
- **Acceptance criteria**:
  - All auth endpoints have proper test coverage
  - Cookie operations are tested
  - Error scenarios are covered
  - Rate limiting still works
- **Tests to run**:
  - `pytest tests/ -k "test_auth" -v --tb=short`

#### Task 19: Frontend Token Management Tests
- **ID**: TASK_05_02_frontend_token_tests
- **Title**: Add frontend token management test coverage
- **Description**: Create comprehensive tests for frontend auth token handling
- **Files affected**: `src/features/auth/model/__tests__/authToken.test.ts`
- **Targets**:
  - Test silent refresh functionality
  - Test request queuing mechanism
  - Test logout with API call
  - Test location state preservation
- **Acceptance criteria**:
  - Frontend auth flow is properly tested
  - Edge cases are covered (network errors, expired cookies)
  - Token expiration handling works correctly
- **Tests to run**:
  - `npm test -- --testPathPattern="auth" --verbose`

#### Task 20: End-to-End Auth Flow Validation
- **ID**: TASK_05_03_e2e_auth_flow
- **Title**: Validate complete authentication flow end-to-end
- **Description**: Manual validation of complete auth flow with new cookie-based mechanism
- **Files affected**: Manual validation - no code changes
- **Targets**:
  - Login sets both access token and refresh cookie
  - App stays logged in across page refreshes
  - Token refresh works transparently
  - Logout clears everything properly
  - Error scenarios handled gracefully
- **Acceptance criteria**:
  - Complete auth flow works as specified
  - Security requirements met (httponly cookies, no XSS exposure)
  - Performance is acceptable (no unnecessary refresh calls)
  - User experience is seamless
- **Tests to run**:
  - Manual end-to-end testing
  - Security audit of token storage mechanism
  - Performance testing

## Must Have Requirements (Derived from Phase Goal)

1. **Secure Token Storage**: All tokens properly stored with no XSS exposure
2. **Authentication Persistence**: Users remain logged in across page refreshes
3. **Token Expiration**: Access tokens expire after 15 minutes, refresh tokens after 7 days
4. **Transparent Refresh**: Token refresh happens automatically without user interaction
5. **Error Handling**: Graceful handling of expired/invalid refresh cookies
6. **Concurrent Request Handling**: Multiple requests during token refresh are queued and retried
7. **Logout Functionality**: Proper logout clears all tokens and cookies
8. **Backward Compatibility**: Existing authentication still works during transition

## Security Requirements

- **Cookie Security**: All refresh tokens in httpOnly, secure, SameSite=Strict cookies
- **Token Protection**: No token exposure to client-side JavaScript attacks
- **Rate Limiting**: Maintain existing per-IP rate limiting
- **Error Messages**: No information leakage in error responses

## Performance Requirements

- **Refresh Efficiency**: Only one refresh operation for concurrent requests
- **App Initialization**: Silent refresh doesn't delay app startup
- **Memory Usage**: Efficient queue management for pending requests

## Acceptance Criteria Summary

✅ **Backend**: JWT configuration updated, refresh tokens in httpOnly cookies, logout endpoint implemented
✅ **Frontend**: Silent refresh on app init, request queuing for concurrent 401s, logout with API call
✅ **Security**: No XSS token exposure, proper cookie attributes, rate limiting maintained
✅ **User Experience**: Seamless authentication across page refreshes, transparent token refresh
✅ **Testing**: Comprehensive test coverage for new functionality
✅ **Error Handling**: Graceful handling of expired tokens and network errors