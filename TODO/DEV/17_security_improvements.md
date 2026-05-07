---
## SECURITY IMPROVEMENTS
---

### TASK: Fix Security Issues

FILE: `src/mkobi/core/security.py`, `src/mkobi/api/routes/upload.py`

GOAL: Address security vulnerabilities and improve auth practices

ISSUE DESCRIPTION:

1. **Rate limiting not properly implemented**:
   - `RateLimiter` and `AsyncRateLimiter` classes exist in `security.py`
   - But they're not used in the upload endpoints (or other endpoints)
   - SPEC.md section 6 requires rate limiting for upload endpoints

2. **JWT secret key handling**:
   - `jwt_secret_key` property returns `None` if not configured
   - Need to ensure secret key is always set (fail fast if not)

3. **Password truncation issue** (line 70 in `security.py`):
   ```python
   truncated = encoded[:MAX_PASSWORD_LENGTH].decode("utf-8", errors="ignore")
   ```
   This could create invalid UTF-8 sequences. Better to truncate at character boundary.

4. **CORS configuration**:
   - `app.py` uses `config.cors_origins`
   - Need to ensure it's properly configured for production (not `*`)

5. **File upload security**:
   - `upload.py` checks MIME types - GOOD
   - But need to ensure file size limit is enforced before reading file into memory

IMPACT:
- Security vulnerabilities
- Potential for abuse (no rate limiting)
- JWT tokens could be insecure if secret not set

FILES TO FIX:
- `src/mkobi/core/security.py` - Fix password truncation, ensure secret key set
- `src/mkobi/api/routes/upload.py` - Add rate limiting
- `src/mkobi/app.py` - Review CORS config
- All auth endpoints - Add rate limiting

IMPLEMENTATION:

1. **Add rate limiting to upload endpoints**:
   ```python
   from mkobi.core.security import AsyncRateLimiter

   # In upload endpoint:
   rate_limiter = AsyncRateLimiter(get_async_redis_client())
   if not await rate_limiter.check_rate_limit(
       f"upload:{current_user.id}", max_attempts=10, ttl=3600
   ):
       raise HTTPException(429, "Rate limit exceeded")
   ```

2. **Fix JWT secret key validation**:
   ```python
   # In config.py or startup:
   if not get_config().jwt.secret_key:
       logger.error("JWT secret key not configured!")
       raise ValueError("JWT_SECRET_KEY must be set")
   ```

3. **Fix password truncation**:
   ```python
   def _truncate_password(password: str) -> str:
       # Truncate at character boundary, not byte boundary
       if len(password) > MAX_PASSWORD_LENGTH:
           truncated = password[:MAX_PASSWORD_LENGTH]
           logger.warning("Password truncated to %d chars", MAX_PASSWORD_LENGTH)
           return truncated
       return password
   ```

4. **Enforce CORS for production**:
   ```python
   # In app.py:
   if config.environment == EnvironmentEnum.PRODUCTION:
       assert config.cors_origins, "CORS origins must be set in production"
   ```

5. **Enforce file size before reading**:
   ```python
   # In upload endpoint, check file size before reading:
   if file.size > config.max_file_size:
       raise HTTPException(413, "File too large")
   ```

TESTING:
- [ ] Rate limiting works on upload endpoints
- [ ] JWT secret key validation fails fast if not set
- [ ] Password truncation doesn't create invalid UTF-8
- [ ] CORS properly configured for production
- [ ] File size enforced before reading into memory

PRIORITY: High (security)

SPEC REFERENCE:
- SPEC.md section 6: "Security & ограничения"
- SPEC.md section 6: "Rate limiting on upload endpoints"
- Requirements: "Security"
