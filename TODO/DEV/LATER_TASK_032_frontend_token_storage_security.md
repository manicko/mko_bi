---
## FRONTEND SECURITY
---

### TASK: Fix frontend token storage security

FILE: `frontend/src/shared/api/axiosInstance.ts`

**PROBLEM**: 
JWT token is stored in `sessionStorage` (line 15), which is vulnerable to XSS attacks. For production, httpOnly cookies should be considered.

**CURRENT CODE** (line 15):
```typescript
// Store token in sessionStorage
sessionStorage.setItem('token', token);
```

**ISSUE**:
- `sessionStorage` can be accessed by any JavaScript running on the page
- XSS attacks can steal the token
- Not as secure as httpOnly cookies

**IMPLEMENT**:

**Option A (Recommended for production)**: Use httpOnly cookies
1. Backend should set httpOnly cookie on login:
   ```python
   response.set_cookie(
       key="access_token",
       value=token,
       httponly=True,
       secure=True,  # HTTPS only
       samesite="Lax"
   )
   ```
2. Frontend doesn't need to store token manually
3. Axios interceptor should not add Authorization header (cookie sent automatically)

**Option B (If keeping sessionStorage)**: Add CSRF protection
1. Implement CSRF token mechanism
2. Add CSRF token to requests

**Option C (Temporary/Development)**: Document as known issue
1. Add comment about security consideration
2. Plan to fix before production deployment

**RECOMMENDATION**: 
For production: Use **Option A** (httpOnly cookies).
For now: Document as **Option C** and create follow-up task for production.

**IMPLEMENT (Document as future improvement)**:
1. Add comment in `axiosInstance.ts`:
   ```typescript
   // SECURITY NOTE: Token stored in sessionStorage is vulnerable to XSS.
   // For production, use httpOnly cookies instead.
   // See: TASK_032_frontend_token_storage_security.md
   ```

2. Create backend task for httpOnly cookie implementation

3. Update frontend to handle cookie-based auth

**REFERENCES**:
- `frontend/src/shared/api/axiosInstance.ts:15`
- `src/mkobi/api/routes/auth.py` (login endpoint)
- OWASP guidelines on token storage

**DONE**:
- [ ] Security issue documented
- [ ] Comment added to code
- [ ] Backend task created for httpOnly cookies (if proceeding)
- [ ] Frontend updated for cookie-based auth (if proceeding)
- [ ] Tested in development environment
