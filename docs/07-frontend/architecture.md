---
id: frontend-architecture
domain: frontend
tags:
  - react
  - typescript
  - spa
  - routing
  - state-management
  - http-client
  - tanstack-query
related:
  - fsd-structure
  - pages
  - auth-flow
  - frontend-security
  - auth-api
---

# Frontend Architecture

## Overview

The frontend is a React 18+ Single Page Application (SPA) built with TypeScript and Vite. It communicates with the FastAPI backend exclusively through a REST API over HTTPS/JSON.

**Architectural pattern:** Clean Architecture + Feature-Sliced Design (FSD)

## System Context

```
Browser (React SPA)
       ↓ HTTPS/JSON
FastAPI (REST API)
       ↓
Service Layer
       ↓
PostgreSQL
```

## Key Principles

1. **Separation of Concerns** — React is responsible only for UI and visualization. FastAPI handles all business logic and data operations.
2. **Stateless Backend** — The backend does not store sessions. JWT tokens carry authentication state.
3. **Type Safety** — TypeScript on the frontend, Pydantic v2 on the backend. Shared types via OpenAPI.
4. **No Overengineering** — Proven libraries are used; no unnecessary abstraction layers.
5. **Business Logic Boundary** — All business logic resides in the FastAPI service layer. React contains only UI state.

## Technology Stack

| Layer | Technology |
| --- | --- |
| Framework | React 18+ with TypeScript |
| Build Tool | Vite |
| UI Kit | Material UI v5 |
| State Management (server) | TanStack Query (React Query) |
| State Management (client) | React hooks (`useState`, `useReducer`) |
| Forms | React Hook Form + Zod |
| Charts | Plotly.js React |
| File Upload | react-dropzone |
| HTTP Client | Axios (with JWT interceptors) |
| Notifications | react-hot-toast |
| Routing | React Router v6 |

**Note:** Redux/Zustand is intentionally not used. TanStack Query is sufficient for all server state management.

## Application Bootstrap

The application is composed in `frontend/src/app/providers.tsx`:

```
QueryClientProvider (TanStack Query)
  └─ BrowserRouter (React Router)
       └─ ThemeProvider (MUI)
            └─ CssBaseline
                 └─ Toaster (react-hot-toast)
                      └─ AppRoutes
```

- **QueryClient** is configured with `retry: 1` and `staleTime: 5 minutes`.
- **Theme** uses MUI's light mode by default.

## Routing

All routes are defined in `frontend/src/app/routes.tsx` using React Router v6. The root path (`/`) redirects to `/dashboards`. Unmatched routes render a `NotFound` component.

| Path | Component | Access |
| --- | --- | --- |
| `/login` | `LoginForm` | Public |
| `/register` | `RegisterForm` | Public |
| `/dashboards` | `DashboardList` | Authenticated |
| `/dashboard/:id` | `DashboardView` | Authenticated |
| `/dashboard/:id/upload` | `UploadPage` | Admin, Editor |
| `/admin` | `AdminPanel` | Admin only |
| `/profile` | `UserProfile` | Authenticated |
| `/profile/change-password` | `ChangePasswordPage` | Authenticated |
| `*` | `NotFound` | Public |

## HTTP Client

A single Axios instance (`frontend/src/shared/api/axiosInstance.ts`) is configured with:

- **Base URL:** `/api/v1`
- **Credentials:** `withCredentials: true`
- **Request interceptor:** Attaches `Authorization: Bearer <token>` header after checking token expiration.
- **Response interceptor:** On `401` responses, removes the token, shows a toast notification, and redirects to `/login`.

## State Management Strategy

| State Type | Tool | Scope |
| --- | --- | --- |
| Server state | TanStack Query | API data (dashboards, users, etc.) |
| Auth state | `useAuth` hook | Current user, login/logout |
| UI state | React hooks | Form inputs, toggles, local UI |
| Global client state | None (intentionally) | — |

## Data Flow

```
User Action → React Component → API Call (Axios) → FastAPI Endpoint
     ↑                                                      │
     └─────────────── UI Update ←── TanStack Query ←────────┘
```

1. User interacts with a component.
2. Component calls an API function (via TanStack Query or direct call).
3. Axios sends the request with JWT token to FastAPI.
4. FastAPI processes the request and returns JSON.
5. TanStack Query caches the response; component re-renders.

## Cross-References

- [FSD Structure](fsd-structure.md) — Detailed project folder tree
- [Pages](pages.md) — All 8 UI pages with endpoints and elements
- [Auth Flow](auth-flow.md) — JWT handling, role-based access, email validation
- [Upload UI](upload-ui.md) — Upload page and file handling
- [Frontend Security](frontend-security.md) — CORS, file upload security, JWT handling
- [Authentication API](../../01-auth/auth-api.md) — Backend auth endpoints
- [Processing API](../../03-processing/processing-api.md) — Upload and data endpoints
- [System Overview](../../00-overview/overview.md) — Technology stack and system context
