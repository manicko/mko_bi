# SPEC.md Content Inventory

**Source**: `docs/SPEC.md`
**Generated**: 2026-05-18
**Version**: 2.2

---

## 1. All `##` Sections

| # | Section Title | Lines | Notes |
|---|--------------|-------|-------|
| 1 | Purpose | 1–13 | Russian language |
| 2 | Stack | 15–38 | English |
| 3 | Core Entities | 40–66 | English (entity field names in Russian comments) |
| 4 | Roles & Permissions | 68–90 | Russian language |
| 5 | Authentication | 92–98 | English |
| 6 | Security & ограничения | 100–131 | Mixed (Russian title, English content) |
| 6.1 | Configuration & Secrets Management | 133–141 | English |
| 6.2 | Rate Limiter Failure Behavior | 112–120 | English |
| 6.3 | Production Credential Enforcement | 122–131 | English |
| 7 | Data Flow | 144–153 | English |
| 8 | Data Upload | 155–166 | English |
| 9 | Data Processing | 168–192 | English |
| 9.1 | Custom Metrics (Formula Parser) | 184–192 | English |
| 10 | Data Storage | 194–200 | English |
| 11 | Background Processing | 202–218 | English |
| 11.1 | Task Ownership Validation | 210–213 | English |
| 11.2 | Task Queue Migration | 214–218 | English |
| 12 | Dashboards | 220–240 | English |
| 13 | Filters | 242–250 | English |
| 14 | API Responsibilities (FastAPI) | 253–353 | English |
| 14.1 | Auth Endpoints | 269–277 | English |
| 14.2 | Dashboard Endpoints | 279–285 | English |
| 14.3 | Layout Endpoints | 287–293 | English |
| 14.4 | Graph Endpoints | 295–301 | English |
| 14.5 | Filter Endpoints | 303–309 | English |
| 14.6 | Processing Config Endpoints | 311–315 | English |
| 14.7 | Data Endpoints | 317–323 | English |
| 14.8 | User Endpoints | 325–334 | English |
| 14.9 | Admin Endpoints | 336–347 | English |
| 14.10 | Health Endpoints | 349–353 | English |
| 15 | Access Control | 355–370 | English |
| 15.1 | Dashboard Access Enforcement | 361–370 | English |
| 16 | Database Schema (PostgreSQL) | 372–571 | English |
| 16.1 | Core Tables | 375–550 | English (table/column comments in Russian) |
| 16.2 | Indexes | 552–563 | SQL |
| 16.3 | Data Principles | 565–571 | Russian language |
| 17 | Frontend Architecture (React SPA) | 573–644 | English |
| 17.1 | Общая концепция | 575–589 | Russian title, English content |
| 17.2 | Ключевые принципы | 590–596 | Russian title, English content |
| 17.3 | Project Structure (Frontend) | 597–644 | English |
| 18 | UI Pages (React SPA) | 648–715 | English (some Russian UI labels) |
| 18.1 | Login Page (`/login`) | 650–656 | Russian UI labels |
| 18.2 | Registration Page (`/register`) | 658–664 | Russian UI labels |
| 18.3 | Dashboard List Page (`/dashboards`) | 666–673 | Russian UI labels |
| 18.4 | Dashboard View Page (`/dashboard/:id`) | 675–681 | English |
| 18.5 | User Profile Page (`/profile`) | 683–690 | Russian UI labels |
| 18.6 | Change Password Page (`/profile/change-password`) | 692–700 | Russian UI labels |
| 18.7 | Admin Panel (`/admin`) | 702–707 | English |
| 18.8 | Data Upload Page (`/dashboard/:id/upload`) | 709–715 | Russian UI labels |
| 19 | Architecture (React + FastAPI) | 718–805 | English |
| 19.1 | Общая архитектура | 720–733 | Russian title, English content |
| 19.2 | Ключевые принципы | 734–741 | Russian title, English content |
| 19.3 | Поток работы | 742–755 | Russian title, English content |
| 19.4 | Stateless Architecture | 757–762 | English |
| 19.5 | Application Startup Behavior | 764–805 | English |
| 20 | Logging | 807–824 | Russian title, English content |
| 20.1 | Code Comments | 826–836 | English |
| 21 | Testing | 838–848 | Russian title, English content |
| 22 | Enums (StrEnum) | 850–981 | English |
| 23 | Frontend Security | 983–1026 | English |
| 23.1 | JWT Handling | 985–993 | English |
| 23.2 | File Upload | 995–999 | English |
| 23.3 | Role-Based Access | 1001–1004 | English |
| 23.4 | Email Validation (Registration) | 1006–1009 | English |
| 23.5 | CORS Configuration (FastAPI) | 1011–1026 | English |
| 24 | Deployment | 1028–1069 | English |
| 24.1 | Development | 1030–1035 | English |
| 24.2 | Production | 1037–1052 | English |
| 24.3 | No Overengineering | 1054–1058 | English |
| 24.4 | Миграция с Dash | 1060–1064 | Russian title, English content |

**Total ## sections**: 48 (including sub-sections like 6.1, 6.2, 6.3, 9.1, 11.1, 11.2, 14.1–14.10, 15.1, 16.1–16.3, 17.1–17.3, 18.1–18.8, 19.1–19.5, 20.1, 23.1–23.5, 24.1–24.4)

---

## 2. High-Risk Sections (7 total)

| # | Section | Risk | Reason |
|---|---------|------|--------|
| 1 | **§6 — Security & ограничения** | HIGH | Core security constraints: rate limiting, file size limits, MIME validation, SQL injection prevention, temp file cleanup, email domain blocklist |
| 2 | **§6.2 — Rate Limiter Failure Behavior** | HIGH | Fail-open vs fail-closed behavior directly impacts security posture during Redis outages |
| 3 | **§6.3 — Production Credential Enforcement** | HIGH | Default credential rejection in production; misconfiguration leads to security vulnerabilities |
| 4 | **§14 — API Responsibilities (FastAPI)** | HIGH | All ~30 API endpoints with auth requirements; incorrect auth annotations = access control bugs |
| 5 | **§15 — Access Control** | HIGH | Per-request access control enforcement; errors lead to data leakage |
| 6 | **§16 — Database Schema (PostgreSQL)** | HIGH | DDL definitions, constraints, JSONB normalization, CASCADE rules; schema errors = data loss |
| 7 | **§23 — Frontend Security** | HIGH | JWT handling, CORS config, file upload security, role-based access, email validation |

---

## 3. SQL DDL Blocks

| # | Table Name | Lines | Columns | Constraints |
|---|-----------|-------|---------|-------------|
| 1 | `users` | 379–388 | id, email, password_hash, role, is_active, created_at | PK(id), UNIQUE(email), CHECK(role IN ('admin','editor','viewer')) |
| 2 | `layouts` | 395–402 | id, name, definition, created_at | PK(id), UNIQUE(name) |
| 3 | `dashboards` | 418–428 | id, name, description, layout_id, created_by, created_at, updated_at | PK(id), UNIQUE(name), FK(layout_id→layouts.id), FK(created_by→users.id) |
| 4 | `graphs` | 432–444 | id, dashboard_id, name, type, config, dimensions, metrics, created_at | PK(id), FK(dashboard_id→dashboards.id ON DELETE CASCADE), CHECK(type IN ('bar','line','pie','table')), UNIQUE(dashboard_id,name) |
| 5 | `filters` | 453–461 | id, name, type, config, created_at | PK(id), UNIQUE(name) |
| 6 | `dashboard_access` | 468–475 | user_id, dashboard_id, permission | PK(user_id,dashboard_id), FK(user_id→users.id ON DELETE CASCADE), FK(dashboard_id→dashboards.id ON DELETE CASCADE), CHECK(permission IN ('view','edit','admin')) |
| 7 | `dashboard_filters` | 481–487 | dashboard_id, filter_id | PK(dashboard_id,filter_id), FK(dashboard_id→dashboards.id ON DELETE CASCADE), FK(filter_id→filters.id ON DELETE CASCADE) |
| 8 | `processing_configs` | 494–500 | dashboard_id, settings, updated_at | PK(dashboard_id), FK(dashboard_id→dashboards.id ON DELETE CASCADE) |
| 9 | `aggregated_data` | 507–515 | id, dashboard_id, graph_id, dims, metrics | PK(id), FK(dashboard_id→dashboards.id ON DELETE CASCADE), FK(graph_id→graphs.id ON DELETE CASCADE) |
| 10 | `processing_logs` | 524–533 | id, dashboard_id, status, message, started_at, finished_at | PK(id), FK(dashboard_id→dashboards.id ON DELETE SET NULL), CHECK(status IN ('started','uploaded','processing','success','failed','completed')) |
| 11 | `registration_requests` | 537–547 | id, email, status, requested_by_ip, reviewed_by, reviewed_at, created_at | PK(id), UNIQUE(email), CHECK(status IN ('pending','approved','rejected')), FK(reviewed_by→users.id) |

**Total SQL DDL blocks**: 11 tables

### 3.1 Index Definitions (Section 16.2)

| # | Index Name | Table | Columns | Type |
|---|-----------|-------|---------|------|
| 1 | `idx_aggregated_data_graph_id` | aggregated_data | graph_id | btree |
| 2 | `idx_aggregated_data_dashboard_id` | aggregated_data | dashboard_id | btree |
| 3 | `idx_aggregated_data_dashboard_graph` | aggregated_data | (dashboard_id, graph_id) | btree |
| 4 | `idx_aggregated_data_dims_gin` | aggregated_data | dims | GIN |
| 5 | `idx_dashboard_access_user` | dashboard_access | user_id | btree |
| 6 | `idx_dashboard_access_dashboard` | dashboard_access | dashboard_id | btree |
| 7 | `idx_graphs_dashboard` | graphs | dashboard_id | btree |
| 8 | `idx_dashboard_filters_dashboard_filter` | dashboard_filters | (dashboard_id, filter_id) | btree |

---

## 4. StrEnum Classes (19 total — Section 22)

| # | Class Name | Members | Line |
|---|-----------|---------|------|
| 1 | `UserRole` | ADMIN, EDITOR, VIEWER | 858 |
| 2 | `DashboardPermission` | VIEW, EDIT, ADMIN | 864 |
| 3 | `GraphType` | BAR, LINE, PIE, TABLE | 870 |
| 4 | `FilterType` | SELECT, MULTISELECT, RANGE, DATE | 877 |
| 5 | `RegistrationStatus` | PENDING, APPROVED, REJECTED | 884 |
| 6 | `UploadMode` | OVERWRITE, APPEND | 890 |
| 7 | `ProcessingStatus` | STARTED, UPLOADED, PROCESSING, SUCCESS, FAILED, COMPLETED | 895 |
| 8 | `EnvironmentEnum` | PRODUCTION, STAGING, DEVELOPMENT, TEST | 904 |
| 9 | `MimeTypeEnum` | TEXT_CSV, APPLICATION_GZIP, APPLICATION_X_GZIP | 911 |
| 10 | `FileExtensionEnum` | CSV, CSV_GZ | 917 |
| 11 | `AggregationFunctionEnum` | SUM, MEAN, COUNT, MIN, MAX, MEDIAN, STD, VAR, FIRST, LAST | 922 |
| 12 | `FilterOperatorEnum` | EQ, NE, GT, LT, GTE, LTE | 935 |
| 13 | `OrientationEnum` | VERTICAL, HORIZONTAL | 944 |
| 14 | `BarmodeEnum` | GROUP, STACK | 949 |
| 15 | `YoyModeEnum` | ABSOLUTE, PERCENT | 954 |
| 16 | `ButtonVariant` | PRIMARY, SECONDARY, SUCCESS, DANGER, WARNING, INFO, LIGHT, DARK | 962 |
| 17 | `ComponentSize` | SMALL, MEDIUM, LARGE | 975 |

**Note**: `ButtonVariant` and `ComponentSize` are marked as "frontend-only" — defined in backend for OpenAPI type sharing, not used in backend logic.

**Total StrEnum classes**: 17 (not 19 as originally estimated in the task; the SPEC contains 17 distinct StrEnum class definitions)

---

## 5. API Endpoints (~30 total — Section 14)

### 5.1 Auth Endpoints (§14.1)

| # | Method | Path | Auth | Description |
|---|--------|------|------|-------------|
| 1 | POST | `/api/v1/auth/login` | Public | Returns `{access_token, user}` |
| 2 | POST | `/api/v1/auth/login/form` | Public | OAuth2 form login |
| 3 | POST | `/api/v1/auth/register-request` | Public | Submit registration request |
| 4 | POST | `/api/v1/auth/register` | Admin | Approve & create user |
| 5 | POST | `/api/v1/auth/refresh` | JWT | Refresh access token |
| 6 | GET | `/api/v1/auth/me` | JWT | Get current user profile |
| 7 | POST | `/api/v1/auth/change-password` | JWT | Change own password |

### 5.2 Dashboard Endpoints (§14.2)

| # | Method | Path | Auth | Description |
|---|--------|------|------|-------------|
| 8 | GET | `/api/v1/dashboards/my` | JWT | List accessible dashboards |
| 9 | GET | `/api/v1/dashboards/:id` | JWT | Get dashboard detail |
| 10 | POST | `/api/v1/dashboards` | Admin | Create dashboard |
| 11 | PUT | `/api/v1/dashboards/:id` | Admin | Update dashboard |
| 12 | DELETE | `/api/v1/dashboards/:id` | Admin | Delete dashboard |

### 5.3 Layout Endpoints (§14.3)

| # | Method | Path | Auth | Description |
|---|--------|------|------|-------------|
| 13 | GET | `/api/v1/layouts` | JWT | List layouts |
| 14 | GET | `/api/v1/layouts/:id` | JWT | Get layout detail |
| 15 | POST | `/api/v1/layouts` | Admin | Create layout |
| 16 | PUT | `/api/v1/layouts/:id` | Admin | Update layout |
| 17 | DELETE | `/api/v1/layouts/:id` | Admin | Delete layout |

### 5.4 Graph Endpoints (§14.4)

| # | Method | Path | Auth | Description |
|---|--------|------|------|-------------|
| 18 | GET | `/api/v1/graphs` | JWT | List graphs |
| 19 | GET | `/api/v1/graphs/:id` | JWT | Get graph detail |
| 20 | POST | `/api/v1/graphs` | Admin | Create graph |
| 21 | PUT | `/api/v1/graphs/:id` | Admin | Update graph |
| 22 | DELETE | `/api/v1/graphs/:id` | Admin | Delete graph |

### 5.5 Filter Endpoints (§14.5)

| # | Method | Path | Auth | Description |
|---|--------|------|------|-------------|
| 23 | GET | `/api/v1/filters` | Editor+ | List filters |
| 24 | GET | `/api/v1/filters/:id` | Editor+ | Get filter detail |
| 25 | POST | `/api/v1/filters` | Admin | Create filter |
| 26 | PUT | `/api/v1/filters/:id` | Admin | Update filter |
| 27 | DELETE | `/api/v1/filters/:id` | Admin | Delete filter |

### 5.6 Processing Config Endpoints (§14.6)

| # | Method | Path | Auth | Description |
|---|--------|------|------|-------------|
| 28 | GET | `/api/v1/processing-configs/:dashboard_id` | Viewer+ | Get processing config |
| 29 | PUT | `/api/v1/processing-configs/:dashboard_id` | Editor+ | Update processing config |
| 30 | DELETE | `/api/v1/processing-configs/:dashboard_id` | Editor+ | Delete processing config |

### 5.7 Data Endpoints (§14.7)

| # | Method | Path | Auth | Description |
|---|--------|------|------|-------------|
| 31 | GET | `/api/v1/data/aggregated` | JWT | Get aggregated graph data (query: dashboard_id, graph_id, filters) |
| 32 | POST | `/api/v1/upload/:dashboard_id` | Editor+ | Upload CSV/CSV.gz file (query: mode=overwrite|append) |
| 33 | POST | `/api/v1/upload/:dashboard_id/process` | Editor+ | Trigger processing (query: task_id) |
| 34 | GET | `/api/v1/upload/status/:task_id` | Editor+ | Get processing status |
| 35 | GET | `/api/v1/upload/result/:task_id` | Editor+ | Get processing result |

### 5.8 User Endpoints (§14.8)

| # | Method | Path | Auth | Description |
|---|--------|------|------|-------------|
| 36 | GET | `/api/v1/users` | Admin | List all users |
| 37 | GET | `/api/v1/users/:id` | Self or Admin | Get user detail |
| 38 | POST | `/api/v1/users` | Admin | Create user (body: `{email, password, role}`) |
| 39 | PATCH | `/api/v1/users/:id/role` | Admin | Update user role (body: `{new_role}`) |
| 40 | DELETE | `/api/v1/users/:id` | Admin | Delete user |
| 41 | DELETE | `/api/v1/users/me` | Self (non-admin) | Self-deletion |

### 5.9 Admin Endpoints (§14.9)

| # | Method | Path | Auth | Description |
|---|--------|------|------|-------------|
| 42 | GET | `/api/v1/admin/users` | Admin | List users |
| 43 | PATCH | `/api/v1/admin/users/:id/role` | Admin | Update role |
| 44 | DELETE | `/api/v1/admin/users/:id` | Admin | Delete user |
| 45 | GET | `/api/v1/admin/registration-requests` | Admin | List registration requests |
| 46 | POST | `/api/v1/admin/registration-requests/:id/approve` | Admin | Approve registration (returns temp_password) |
| 47 | POST | `/api/v1/admin/registration-requests/:id/reject` | Admin | Reject registration |
| 48 | GET | `/api/v1/admin/logs` | Admin | List processing logs (filtering + pagination) |
| 49 | GET | `/api/v1/admin/logs/:log_id` | Admin | Get single log entry |

### 5.10 Health Endpoints (§14.10)

| # | Method | Path | Auth | Description |
|---|--------|------|------|-------------|
| 50 | GET | `/health` | Public | Basic health check (DB connectivity) |
| 51 | GET | `/health/detailed` | Public | Detailed health (DB + static files) |

**Total API endpoints**: 51 (the task estimated ~30; the actual count from SPEC is 51 distinct endpoint definitions)

---

## 6. Russian-Language Sections

| # | Section | Type | Description |
|---|---------|------|-------------|
| 1 | §1 — Purpose | Full section | Entire section in Russian |
| 2 | §4 — Roles & Permissions | Full section | Entire section in Russian |
| 3 | §6 — Security & ограничения | Title | Russian title ("ограничения") |
| 4 | §16.1 — `users` table comment | Inline | "Пользователи системы" |
| 5 | §16.1 — `layouts` table comment | Inline | "UI композиция (без привязки к данным)" |
| 6 | §16.1 — `dashboards` table comment | Inline | "Дашборды" |
| 7 | §16.1 — `graphs` table comment | Inline | "Определения графиков" |
| 8 | §16.1 — `graphs` column comments | Inline | "оси, цвета, настройки визуализации", "список измерений", "список метрик" |
| 9 | §16.1 — `filters` table comment | Inline | "Глобальные фильтры" |
| 10 | §16.1 — `dashboard_access` table comment | Inline | "Управление доступом" |
| 11 | §16.1 — `dashboard_filters` table comment | Inline | "Связь дашбордов с фильтрами (many-to-many)" |
| 12 | §16.1 — `processing_configs` table comment | Inline | "Настройки обработки" |
| 13 | §16.1 — `aggregated_data` table comment | Inline | "Агрегированные данные (CORE)" |
| 14 | §16.1 — `processing_logs` table comment | Inline | "Логи обработки" |
| 15 | §16.1 — `registration_requests` table comment | Inline | "Заявки на регистрацию" |
| 16 | §16.3 — Data Principles | Full section | Entire section in Russian |
| 17 | §17.1 — Общая концепция | Title + content | Russian title, mixed content |
| 18 | §17.2 — Ключевые принципы | Title + content | Russian title, mixed content |
| 19 | §18.1 — Login Page | UI labels | Russian UI labels ("Войти", "Зарегистрироваться") |
| 20 | §18.2 — Registration Page | UI labels | Russian UI labels ("Отправить заявку") |
| 21 | §18.3 — Dashboard List Page | UI labels | Russian UI labels ("Открыть", "profile") |
| 22 | §18.5 — User Profile Page | UI labels | Russian UI labels ("Удалить аккаунт", "Сменить пароль", "Мои дашборды") |
| 23 | §18.6 — Change Password Page | UI labels | Russian UI labels ("Текущий пароль", "Новый пароль", "Подтверждение нового пароля", "Сменить пароль") |
| 24 | §18.8 — Data Upload Page | UI labels | Russian UI labels ("Перезаписать", "Добавить данные") |
| 25 | §19.1 — Общая архитектура | Title | Russian title |
| 26 | §19.2 — Ключевые принципы | Title | Russian title |
| 27 | §19.3 — Поток работы | Title | Russian title |
| 28 | §20 — Logging | Title | Russian title |
| 29 | §21 — Testing | Title | Russian title |
| 30 | §24.4 — Миграция с Dash | Title | Russian title |
| 31 | Footer | Metadata | "Автор: Senior Python Architect", "Дата: 2026-05-16" |

---

## 7. Code Blocks (Non-SQL)

| # | Language | Section | Description |
|---|----------|---------|-------------|
|1|json|`layouts` definition example|JSONB structure for layout definition |
|2|sql|§16.2|CREATE INDEX statements (8 indexes) |
|3|python|§22|StrEnum class definitions (17 classes) |
|4|yaml|§19.5|docker-compose.yml environment variables |
|5|python|§23.5|CORS middleware configuration |

---

## 8. Frontend Routes (Section 18)

| # | Route | Page | Auth Required |
|---|-------|------|---------------|
|1|`/login`|Login Page|No|
|2|`/register`|Registration Page|No|
|3|`/dashboards`|Dashboard List Page|Yes|
|4|`/dashboard/:id`|Dashboard View Page|Yes|
|5|`/dashboard/:id/upload`|Data Upload Page|Editor+|
|6|`/profile`|User Profile Page|Yes|
|7|`/profile/change-password`|Change Password Page|Yes|
|8|`/admin`|Admin Panel|Admin|

---

## 9. Summary Statistics

| Metric | Count |
|--------|-------|
| Total `##` sections | 48 |
| High-risk sections | 7 |
| SQL DDL tables | 11 |
| SQL index definitions | 8 |
| StrEnum classes | 17 |
| API endpoints | 51 |
| Frontend routes | 8 |
| Russian-language items | 31 |
| Non-SQL code blocks | 5 |
