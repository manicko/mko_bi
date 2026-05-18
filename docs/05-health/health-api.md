---
id: health-api
domain: health
tags:
  - health-check
  - monitoring
  - database
  - kubernetes
  - load-balancer
  - uptime
related:
  - system-overview
  - data-flow
  - deployment
  - backend-architecture
---

# Health Check API

## Overview

The health check API provides endpoints for monitoring application availability and component status. These endpoints are intended for load balancers, container orchestrators (e.g., Kubernetes liveness/readiness probes), and monitoring systems.

**Base path:** `/`

**Auth level:** Public (no authentication required)

---

## Endpoints

### 1. Basic Health Check

Returns the overall application status and database connectivity state.

| Attribute      | Value                          |
| -------------- | ------------------------------ |
| **Method**     | `GET`                          |
| **Path**       | `/health`                      |
| **Auth level** | Public                         |

**Response** (`200 OK`):

```json
{
  "status": "healthy",
  "database": "connected"
}
```

**Response** (`503 Service Unavailable`):

Returned when the database is not reachable.

```json
{
  "status": "unhealthy",
  "database": "disconnected"
}
```

**Behavior:**
- Executes a `SELECT 1` query against the PostgreSQL database to verify connectivity
- Returns `200` with `"status": "healthy"` if the query succeeds
- Returns `503` with `"status": "unhealthy"` if the query fails (database unreachable or connection error)
- Logs the error at `ERROR` level on failure

---

### 2. Detailed Health Check

Returns the overall application status along with per-component health information.

| Attribute      | Value                          |
| -------------- | ------------------------------ |
| **Method**     | `GET`                          |
| **Path**       | `/health/detailed`             |
| **Auth level** | Public                         |

**Response** (`200 OK`):

```json
{
  "status": "healthy",
  "components": {
    "database": {
      "status": "connected",
      "type": "postgresql"
    },
    "static_files": {
      "status": "available",
      "path": "frontend/dist"
    }
  }
}
```

**Response** (`200 OK` with unhealthy status):

Returned when one or more components are unavailable. The overall `status` field reflects the worst component state.

```json
{
  "status": "unhealthy",
  "components": {
    "database": {
      "status": "disconnected",
      "error": "connection refused"
    },
    "static_files": {
      "status": "unavailable",
      "path": "frontend/dist"
    }
  }
}
```

**Components checked:**

| Component      | Check                                                      | Type        |
| -------------- | ---------------------------------------------------------- | ----------- |
| `database`     | Executes `SELECT 1` against PostgreSQL                     | Critical    |
| `static_files` | Verifies `frontend/dist` directory exists on disk          | Non-critical|

**Behavior:**
- Database check: same connectivity test as the basic endpoint; includes the error message in the response on failure
- Static files check: verifies the `frontend/dist` directory exists (populated by `npm run build`); reports `"available"` or `"unavailable"`
- The overall `status` is `"unhealthy"` if any component reports a failure

---

### 3. Root Endpoint

Returns basic API identification information.

| Attribute      | Value                          |
| -------------- | ------------------------------ |
| **Method**     | `GET`                          |
| **Path**       | `/`                            |
| **Auth level** | Public                         |

**Response** (`200 OK`):

```json
{
  "message": "BI Dashboard API",
  "status": "active",
  "version": "1.0.0"
}
```

---

## Database Connectivity Check

Both `/health` and `/health/detailed` verify database connectivity by executing a lightweight `SELECT 1` query through the SQLAlchemy async session. This confirms:

1. The database server is reachable over the network
2. The connection pool can acquire a connection
3. The database is in a state that accepts queries

**Failure modes:**

| Condition               | HTTP Status | `database` field      |
| ----------------------- | ----------- | --------------------- |
| Database unreachable    | 503         | `disconnected`        |
| Connection pool exhausted | 503       | `disconnected`        |
| Database does not exist | 503         | `disconnected`        |
| Normal operation        | 200         | `connected`           |

On failure, the exception message is included in the detailed health check response and logged server-side at `ERROR` level.

---

## Monitoring Integration

These endpoints are designed for integration with:

- **Kubernetes:** Configure as `livenessProbe` and `readinessProbe` targets
- **Load balancers:** Use `/health` for health check pings to determine instance availability
- **Uptime monitors:** Poll `/health` at regular intervals; alert on non-200 responses
- **Admin dashboards:** Use `/health/detailed` for a component-level status overview

**Recommended polling interval:** 10–30 seconds for `/health`.

---

## Cross-References

- [System Overview](../00-overview/overview.md) — Technology stack and architecture summary
- [Data Flow](../00-overview/data-flow.md) — End-to-end data processing pipeline
- [API Responsibilities](../SPEC.md#14-api-responsibilities-fastapi) — Full API endpoint listing
- [Database Schema](../09-database/schema-core.md) — PostgreSQL table definitions and indexes
- [Deployment](../10-deployment/deployment.md) — Production deployment and container orchestration
- [Configuration](../06-backend/configuration.md) — Health check configuration and environment variables
