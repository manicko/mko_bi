# Phase 1: Secure Temp Password Delivery - Context

**Gathered:** 2026-06-01
**Status:** Ready for planning

## Phase Boundary

Eliminate plaintext temporary passwords from HTTP response bodies in admin endpoints (registration approval `POST /api/v1/admin/registration-requests/{id}/approve` and password reset `POST /api/v1/admin/users/{id}/reset-password`), satisfying audit finding SEC-004 — **without adding a mail/SMTP service** to the system. Admin continues to deliver passwords to users out-of-band; the system just stops leaking them through API responses.

## Implementation Decisions

### Password response removal

- Approval and reset endpoints must **no longer return `temp_password` in the response body** under any circumstance.
- Response returns only: `message`, `user_id`, and a `retrieval_token` (random UUID).
- This removes the password from server logs, browser history, and proxy caches.

### One-Time Retrieval Pattern

- A new endpoint `GET /api/v1/admin/temp-passwords/{retrieval_token}` retrieves the password.
- The password is stored server-side in **Redis** (already available for rate limiting), keyed by the retrieval token.
- On retrieval, the password is **returned once and immediately deleted** from Redis — single-use.
- Token has a configurable TTL (default 24 hours); expired tokens auto-clean via Redis expiry.
- After expiry, if the password was never retrieved, a new approval/reset must be performed.

### Admin role enforcement

- Both the retrieval endpoint and the approval/reset endpoints require **admin role authentication**.
- Retrieval endpoint must validate the caller is an admin before releasing the password.

### No mail service

- SMTP/email integration is **explicitly excluded** from this phase and from the system architecture.
- Out-of-band password delivery (in person, messenger, phone) remains the admin's responsibility.

### force_password_change unchanged

- Approval/reset flows continue setting `force_password_change=True` on the target user (existing behavior, already implemented).
- User must change password on first login — this is unchanged.

## Specific Ideas

- Admin UI: "Approve" button triggers approval, then shows a "Show Password" button that calls the retrieval endpoint and displays the password in a modal/dialog with copy-to-clipboard — similar to the existing `ResetPasswordResultDialog` pattern already in the frontend.
- The retrieval approach acts as an abstraction layer: if email is added later, the same Redis storage can serve as the delivery queue — no architectural redesign needed.

## Deferred Ideas

- **Retrieval audit trail** — logging who retrieved which password and when, for compliance. Useful but out of scope for this phase.
- **Email delivery** — if added later, it plugs into the same Redis store. Not part of this system.
- **End-user self-service password setup** — e.g., a registration link the user clicks to set their own password. This is a separate capability entirely.

---

_Phase: 01-secure-temp-password-delivery_
_Context gathered: 2026-06-01_
