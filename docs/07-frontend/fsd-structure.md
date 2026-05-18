---
id: fsd-structure
domain: frontend
tags:
  - feature-sliced-design
  - folder-structure
  - layers
  - features
  - shared
  - enums
related:
  - frontend-architecture
  - pages
  - auth-flow
  - upload-ui
---

# FSD Project Structure

## Overview

The frontend follows **Feature-Sliced Design (FSD)** methodology. The `src/` directory is organized into layers with clear boundaries and unidirectional dependencies:

```
app        → providers, routing (top-level composition)
features   → business features (auth, dashboards, upload, users, admin)
shared     → reusable infrastructure (API client, components, types)
```

**Dependency rule:** `app` → `features` → `shared`. Lower layers must never import from higher layers.

## Complete Folder Tree

```
frontend/
├── public/
│   └── (static assets)
├── src/
│   ├── main.tsx                          # Entry point
│   ├── react-plotly.d.ts                 # Plotly.js type declarations
│   │
│   ├── app/                              # Application composition layer
│   │   ├── providers.tsx                 # QueryClient, Router, Theme, Toaster
│   │   └── routes.tsx                    # Route definitions with access control
│   │
│   ├── features/                         # Business features
│   │   │
│   │   ├── auth/                         # Authentication feature
│   │   │   ├── index.ts                  # Public API exports
│   │   │   ├── api/
│   │   │   │   └── authApi.ts            # login, registerRequest, getProfile, logoutClient
│   │   │   ├── model/
│   │   │   │   ├── authToken.ts          # Token storage (memory / sessionStorage)
│   │   │   │   └── useAuth.ts            # Auth state hook (user, login, logout)
│   │   │   └── ui/
│   │   │       ├── LoginForm.tsx         # Login page form
│   │   │       └── RegisterForm.tsx      # Registration request form
│   │   │
│   │   ├── dashboards/                   # Dashboard viewing feature
│   │   │   ├── index.ts                  # Public API exports
│   │   │   ├── api/
│   │   │   │   └── dashboardApi.ts       # Dashboard data fetching
│   │   │   ├── model/                    # (empty — state via TanStack Query)
│   │   │   └── ui/
│   │   │       ├── DashboardList.tsx     # Dashboard list page
│   │   │       ├── DashboardView.tsx     # Single dashboard view with charts
│   │   │       ├── DashboardFilters.tsx  # Filter panel component
│   │   │       └── charts/
│   │   │           ├── index.ts          # Chart exports
│   │   │           ├── BarChart.tsx      # Bar chart (Plotly.js)
│   │   │           ├── LineChart.tsx     # Line chart (Plotly.js)
│   │   │           ├── PieChart.tsx      # Pie chart (Plotly.js)
│   │   │           ├── PlotlyChart.tsx   # Generic Plotly wrapper
│   │   │           └── TableChart.tsx    # Table chart
│   │   │
│   │   ├── upload/                       # File upload feature
│   │   │   ├── index.ts                  # Public API exports
│   │   │   ├── api/
│   │   │   │   └── uploadApi.ts          # File upload and processing status
│   │   │   └── ui/
│   │   │       ├── UploadPage.tsx        # Upload page with mode toggle
│   │   │       └── FileDropzone.tsx      # Drag-and-drop file selector
│   │   │
│   │   ├── users/                        # User profile feature
│   │   │   ├── index.ts                  # Public API exports
│   │   │   ├── api/
│   │   │   │   └── userApi.ts            # Profile, change password, delete account
│   │   │   └── ui/
│   │   │       ├── UserProfile.tsx       # Profile page (email, role, actions)
│   │   │       └── ChangePasswordPage.tsx # Password change form
│   │   │
│   │   └── admin/                        # Admin panel feature
│   │       ├── api/
│   │       │   └── adminApi.ts           # Admin API calls
│   │       └── ui/
│   │           ├── AdminPanel.tsx        # Tabbed admin panel container
│   │           ├── UserManagement.tsx    # User CRUD and role management
│   │           ├── RegistrationRequests.tsx # Approve/reject registration requests
│   │           ├── DashboardManagement.tsx  # Dashboard CRUD
│   │           └── LogViewer.tsx         # Processing log viewer
│   │
│   └── shared/                           # Shared infrastructure layer
│       ├── api/
│       │   ├── index.ts                  # API exports
│       │   └── axiosInstance.ts          # Axios instance with interceptors
│       │
│       ├── components/
│       │   ├── index.ts                  # Component exports
│       │   ├── Layout/
│       │   │   ├── index.ts              # Layout exports
│       │   │   ├── AppLayout.tsx         # Main application layout wrapper
│       │   │   ├── Header.tsx            # Top navigation bar
│       │   │   └── Sidebar.tsx           # Side navigation
│       │   ├── NotFound.tsx              # 404 page
│       │   ├── PlaceholderPage.tsx       # Placeholder for unimplemented pages
│       │   ├── ProtectedRoute.tsx        # Auth guard (redirects to /login)
│       │   └── RoleBasedAccess.tsx       # Role-based component visibility
│       │
│       └── types/
│           ├── api.types.ts              # API response/request type definitions
│           ├── enums.ts                  # Frontend enum constants (mirrors backend StrEnum)
│           └── formSchemas.ts            # Zod validation schemas for all forms
│
├── package.json
└── vite.config.ts
```

## Layer Responsibilities

### `app/` — Application Composition

- **Purpose:** Wires together all providers and defines the routing table.
- **Files:** `providers.tsx` (composition root), `routes.tsx` (route definitions).
- **Rules:** This layer knows about all features but contains no business logic.

### `features/` — Business Features

Each feature is a self-contained vertical slice with four sublayers:

| Sublayer | Purpose |
| --- | --- |
| `api/` | API call functions (Axios requests to specific endpoints) |
| `model/` | Business logic hooks and state management for the feature |
| `ui/` | React components (pages, forms, sub-components) |
| `index.ts` | Public API — only exports that other features may import |

**Feature dependency rule:** Features should not import from each other's `model/` or `ui/` sublayers. Cross-feature communication happens through `shared/` or the `app/` layer.

### `shared/` — Reusable Infrastructure

| Sublayer | Purpose |
| --- | --- |
| `api/` | Shared Axios instance with interceptors |
| `components/` | Generic UI components (layout, guards, utilities) |
| `types/` | Shared TypeScript types, enums, and Zod schemas |

**Rules:** `shared/` must never import from `features/` or `app/`.

## Enum Synchronization

Frontend enums in `shared/types/enums.ts` mirror the backend `StrEnum` values defined in `src/mkobi/models/enums.py`. This ensures type safety across the API boundary. The frontend uses `as const` objects with derived union types instead of TypeScript enums for `erasableSyntaxOnly` compatibility.

## Cross-References

- [Frontend Architecture](architecture.md) — System context, principles, and data flow
- [Pages](pages.md) — UI pages mapped to these features
- [Auth Flow](auth-flow.md) — Detailed auth feature documentation
- [Upload UI](upload-ui.md) — Upload feature page and API integration
- [Frontend Security](frontend-security.md) — Security measures across all features
