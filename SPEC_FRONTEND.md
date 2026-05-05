# Frontend Architecture Specification (React + FastAPI)

## 1. Архитектурный подход

### 1.1 Общая концепция
Переход от Dash к современному React SPA с сохранением FastAPI как единственного бэкенда.

**Архитектурный паттерн**: Clean Architecture + Feature-Sliced Design (FSD)

```
Browser (React SPA)
       ↓ HTTPS/JSON
FastAPI (REST API)
       ↓
Service Layer (существующий)
       ↓
PostgreSQL
```

### 1.2 Ключевые принципы
- **Separation of Concerns**: React отвечает только за UI, FastAPI — за бизнес-логику и данные
- **Stateless Backend**: JWT токены, сессии не хранятся на бэкенде
- **Type Safety**: TypeScript на фронтенде, Pydantic на бэкенде
- **No Overengineering**: Используем проверенные библиотеки, избегаем избыточной абстракции

---

## 2. Technology Stack

### 2.1 Frontend (React SPA)
- **Build Tool**: Vite
- **Framework**: React 18+ (TypeScript)
- **Routing**: React Router v6
- **State Management**: TanStack Query (React Query) для серверного состояния
- **Forms**: React Hook Form + Zod (валидация)
- **UI Kit**: Material UI (MUI) v5 или Ant Design (на выбор)
- **HTTP Client**: Axios (с интерцепторами для JWT)
- **File Upload**: react-dropzone
- **Charts**: Plotly.js React (для отображения дашбордов)
- **Notifications**: react-hot-toast

### 2.2 Integration
- FastAPI отдает API (JSON)
- React SPA разворачивается как статические файлы через FastAPI (или отдельно в nginx)
- CORS настроен для development

---

## 3. Project Structure (Frontend)

```
frontend/ (или отдельный репозиторий)
├── public/
├── src/
│   ├── app/                    # Инициализация, провайдеры
│   │   ├── providers.tsx       # QueryClient, Router, Theme
│   │   └── routes.tsx          # Все роуты приложения
│   ├── features/               # Фичи (Feature-Sliced Design)
│   │   ├── auth/
│   │   │   ├── ui/
│   │   │   │   ├── LoginForm.tsx
│   │   │   │   └── RegisterForm.tsx
│   │   │   ├── api/
│   │   │   │   └── authApi.ts
│   │   │   ├── model/
│   │   │   │   ├── useAuth.ts  # Хук аутентификации
│   │   │   │   └── authToken.ts # Работа с JWT
│   │   │   └── types.ts
│   │   ├── dashboards/
│   │   │   ├── ui/
│   │   │   │   ├── DashboardList.tsx
│   │   │   │   ├── DashboardView.tsx
│   │   │   │   └── DashboardFilters.tsx
│   │   │   ├── api/
│   │   │   │   └── dashboardApi.ts
│   │   │   └── model/
│   │   │       └── useDashboards.ts
│   │   ├── upload/
│   │   │   ├── ui/
│   │   │   │   ├── FileDropzone.tsx
│   │   │   │   └── UploadProgress.tsx
│   │   │   └── api/
│   │   │       └── uploadApi.ts
│   │   ├── users/
│   │   │   ├── ui/
│   │   │   │   ├── UserList.tsx
│   │   │   │   └── UserProfile.tsx
│   │   │   └── api/
│   │   │       └── userApi.ts
│   │   └── admin/
│   │       ├── ui/
│   │       │   ├── AdminPanel.tsx
│   │       │   ├── UserManagement.tsx
│   │       │   └── LogViewer.tsx
│   │       └── api/
│   │           └── adminApi.ts
│   ├── shared/                 # Переиспользуемый код
│   │   ├── api/
│   │   │   ├── axiosInstance.ts # Настроенный Axios с интерцепторами
│   │   │   └── errorHandling.ts
│   │   ├── components/
│   │   │   ├── ProtectedRoute.tsx
│   │   │   ├── RoleBasedAccess.tsx
│   │   │   └── Layout/
│   │   │       ├── AppLayout.tsx
│   │   │       ├── Sidebar.tsx
│   │   │       └── Header.tsx
│   │   ├── config/
│   │   │   └── constants.ts
│   │   └── types/
│   │       └── api.types.ts    # Общие типы (User, Dashboard и т.д.)
│   └── main.tsx                # Точка входа
├── package.json
├── tsconfig.json
└── vite.config.ts
```

---

## 4. Page Specifications

### 4.1 Login Page (`/login`)
**Назначение**: Аутентификация пользователя

**Компоненты**:
- Поле email (валидация формата)
- Поле password (type="password")
- Кнопка "Войти"
- Ссылка "Зарегистрироваться" → `/register`
- Сообщение об ошибке (под формой)

**Логика**:
1. POST `/api/v1/auth/login` с credentials
2. При успехе: сохранить JWT в localStorage/sessionStorage, редирект на `/dashboards`
3. При ошибке: показать сообщение "Неверный email или пароль"

**Типы**:
```typescript
interface LoginRequest {
  email: string;
  password: string;
}

interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}
```

---

### 4.2 Registration Page (`/register`)
**Назначение**: Запрос на регистрацию

**Компоненты**:
- Поле email (валидация через Zod: regex + blocked domains check)
- Кнопка "Отправить заявку"
- Ссылка "Уже есть аккаунт?" → `/login`

**Валидация**:
- Формат email (Zod schema)
- Проверка по списку заблокированных доменов (приходит с API или хардкод)
- Проверка по allowed pattern (если есть)

**Логика**:
1. POST `/api/v1/auth/register-request` с email
2. При успехе: сообщение "Заявка отправлена администратору"
3. Заявка сохраняется в БД (новая таблица `registration_requests`)

**Типы**:
```typescript
interface RegistrationRequest {
  email: string;
}

interface RegistrationResponse {
  message: string;
  request_id: string;
}
```

---

### 4.3 User Dashboard List Page (`/dashboards`)
**Назначение**: Список доступных пользователю дашбордов

**Компоненты**:
- Заголовок "Мои дашборды"
- Список дашбордов (карточки/таблица с ссылками)
- Каждая карточка: название, описание, ссылка "Открыть"
- Ссылка на профиль (иконка пользователя в header)

**Логика**:
1. GET `/api/v1/dashboards/my` (список дашбордов с доступом)
2. Рендер списка
3. Клик → переход на `/dashboard/:id`

**Типы**:
```typescript
interface DashboardSummary {
  id: string;
  name: string;
  description: string | null;
  permission: 'view' | 'edit' | 'admin';
}
```

---

### 4.4 User Profile Page (`/profile`)
**Назначение**: Просмотр и управление профилем

**Компоненты**:
- Email пользователя (read-only)
- Роль (read-only)
- Кнопка "Удалить аккаунт" (только для НЕ-админов)
- Модальное окно подтверждения удаления

**Логика**:
1. GET `/api/v1/users/me` (текущий пользователь)
2. DELETE `/api/v1/users/me` (удаление — только не-админ)
3. После удаления: редирект на `/login`, очистка JWT

**Защита**: Админ не может удалить свой аккаунт (проверка на бэкенде + скрытие кнопки)

---

### 4.5 Admin Panel (`/admin`)
**Назначение**: Управление пользователями, дашбордами, просмотр логов

**Подстраницы** (Tabs или отдельные роуты):
1. **User Management** (`/admin/users`)
   - Таблица пользователей (email, role, status, created_at)
   - Кнопки: "Изменить роль", "Заблокировать", "Удалить"
   - Форма создания пользователя (для админа)

2. **Registration Requests** (`/admin/requests`)
   - Список заявок на регистрацию
   - Кнопки: "Одобрить", "Отклонить"

3. **Dashboard Management** (`/admin/dashboards`)
   - CRUD дашбордов
   - Назначение доступов (user ↔ dashboard)

4. **Log Viewer** (`/admin/logs`)
   - Таблица логов (processing_logs)
   - Фильтры по dashboard_id, status, date range

**Компоненты**:
- Tabs для навигации
- DataGrid (MUI) для таблиц
- Модальные окна для редактирования

---

### 4.6 Dashboard View Page (`/dashboard/:id`)
**Назначение**: Просмотр графиков дашборда с фильтрами

**Компоненты**:
- Заголовок дашборда
- **Filters Panel** (слева или сверху):
  - Select/Range/Date фильтры (динамически по конфигу дашборда)
- **Charts Grid** (основная область):
  - Графики (Plotly.js React)
  - Таблицы
- **Upload Button** (видна только для роли `editor` и выше)

**Логика**:
1. GET `/api/v1/dashboards/:id` (конфигурация дашборда)
2. GET `/api/v1/data/aggregated?dashboard_id=:id&filters=...` (данные)
3. Рендер графиков согласно config (layout, graphs)
4. При изменении фильтров → обновление данных (TanStack Query invalidation)

**Права доступа**:
- `view`: только просмотр
- `edit`: + кнопка загрузки данных
- `admin`: + редактирование конфигурации

---

### 4.7 Data Upload Page (`/dashboard/:id/upload`)
**Назначение**: Загрузка CSV/CSV.gz данных для дашборда

**Компоненты**:
- **Mode Toggle**: "Перезаписать" / "Добавить данные"
  - Перезаписать: сброс всех данных графиков (кроме настроек), загрузка новых
  - Добавить: append новых строк к текущим таблицам
- **Dropzone**: Drag-and-drop зона для файлов
  - Поддержка множественной загрузки
  - Только `.csv`, `.csv.gz`
  - Визуализация очереди загрузки (FileUploader List)
- **Progress Bar** для каждого файла
- Кнопка "Начать загрузку"

**Логика**:
1. Выбор файлов → валидация (расширение, MIME-type на фронтенде)
2. Загрузка по одному: POST `/api/v1/upload/:dashboard_id` (multipart/form-data)
3. Параметр `mode` в query: `?mode=overwrite` или `?mode=append`
4. Отслеживание прогресса (UploadProgress event или polling статуса)
5. После загрузки всех файлов:
   - Сообщение "Данные успешно загружены"
   - Редирект на `/dashboard/:id` (обновление графиков)

**Типы**:
```typescript
type UploadMode = 'overwrite' | 'append';

interface UploadResponse {
  message: string;
  processing_log_id: string;
  status: 'uploaded' | 'processing' | 'failed';
}
```

---

## 5. API Endpoints (New/Modified for Frontend)

### 5.1 Auth
- `POST /api/v1/auth/login` → `{access_token, user}`
- `POST /api/v1/auth/register-request` → `{message}` (заявка)
- `GET /api/v1/auth/me` → `UserProfile`

### 5.2 Registration Requests (Admin)
- `GET /api/v1/admin/registration-requests` → `Request[]`
- `POST /api/v1/admin/registration-requests/:id/approve`
- `POST /api/v1/admin/registration-requests/:id/reject`

### 5.3 Users (Admin)
- `GET /api/v1/admin/users` → `User[]`
- `PATCH /api/v1/admin/users/:id/role` → обновление роли
- `DELETE /api/v1/admin/users/:id`

### 5.4 Dashboards
- `GET /api/v1/dashboards/my` → `DashboardSummary[]`
- `GET /api/v1/dashboards/:id` → `DashboardDetail` (с конфигом)
- `POST /api/v1/dashboards` (admin)
- `PUT /api/v1/dashboards/:id` (admin)
- `DELETE /api/v1/dashboards/:id` (admin)

### 5.5 Data
- `GET /api/v1/data/aggregated?dashboard_id=:id&filters=...` → графики данные
- `POST /api/v1/upload/:dashboard_id?mode=overwrite|append` (multipart file)

### 5.6 Logs (Admin)
- `GET /api/v1/admin/logs?dashboard_id=:id&status=:status` → `ProcessingLog[]`

---

## 6. Backend Changes Required

### 6.1 New Tables
```sql
-- Заявки на регистрацию
CREATE TABLE registration_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    status TEXT CHECK (status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
    requested_by_ip INET,
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Обновить users, если нужно добавить статус
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_approved BOOLEAN DEFAULT FALSE;
```

### 6.2 New Pydantic Models (`src/mko_bi/models/`)
```python
# auth.py
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: "UserResponse"

# registration.py
class RegistrationRequestCreate(BaseModel):
    email: EmailStr

class RegistrationRequestResponse(BaseModel):
    id: UUID
    email: str
    status: str
    created_at: datetime
```

### 6.3 New Enums (`src/mko_bi/models/enums.py`)
```python
class UserRole(StrEnum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"

class DashboardPermission(StrEnum):
    VIEW = "view"
    EDIT = "edit"
    ADMIN = "admin"

class RegistrationStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class UploadMode(StrEnum):
    OVERWRITE = "overwrite"
    APPEND = "append"
```

### 6.4 CORS Configuration (FastAPI)
```python
# app.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 7. Security Considerations

1. **JWT Handling**:
   - Access token хранится в memory/secure cookie (не в localStorage для продакшена)
   - Refresh token (опционально) для продления сессии

2. **File Upload**:
   - Rate limiting на `/api/v1/upload/*`
   - Максимальный размер файла (проверка на бэкенде)
   - MIME-type validation (уже есть в SPEC.md)

3. **Role-Based Access**:
   - Frontend: `ProtectedRoute` + `RoleBasedAccess` компоненты
   - Backend: существующие permissions (обновить для новых эндпоинтов)

4. **Email Validation (Registration)**:
   - Regex паттерн (на фронтенде и бэкенде)
   - Blacklist доменов (configurable через `app.yaml`)

---

## 8. Recommendations

### 8.1 Development Flow
1. Сначала расширить FastAPI (новые модели, эндпоинты, таблицы)
2. Настроить CORS и тестировать API через curl/Postman
3. Инициализировать React проект (Vite + TypeScript)
4. Реализовать фичи по порядку: auth → dashboards → upload → admin

### 8.2 Deployment
- **Development**: React dev server (port 3000) + FastAPI (port 8000) с CORS
- **Production**: 
  - Вариант А: FastAPI раздает собранные статические файлы React (`frontend/dist`)
  - Вариант Б: Nginx проксирует `/api` → FastAPI, остальное → React SPA

### 8.3 No Overengineering
- Не использовать Redux/Zustand (TanStack Query достаточно для серверного состояния)
- Не создавать лишние слои абстракции (axiosInstance → прямые вызовы API)
- Использовать существующие Pydantic модели (не дублировать логику)

### 8.4 Миграция с Dash
- Dash можно оставить как fallback для сложных графиков (iframe)
- Или полностью заменить на Plotly.js React (предпочтительно)

---

## 9. Next Steps

1. Создать миграции для `registration_requests`
2. Обновить Pydantic models + Enums
3. Реализовать новые API endpoints
4. Инициализировать React проект
5. Начать с Login/Register страниц

---

**Автор**: Senior Python Architect
**Дата**: 2026-05-05
**Версия**: 1.0
