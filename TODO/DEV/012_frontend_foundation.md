---
## BLOCK 12: FRONTEND FOUNDATION
---

### TASK: Initialize Vite + React + TypeScript project

FILE: `frontend/` (новая папка)

GOAL: Создание frontend проекта (SPEC_FRONTEND.md п.2.1, п.3)

IMPLEMENT:

```bash
cd C:\py_exp\mko_bi
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

* Установка зависимостей:
  * `npm install @mui/material @emotion/react @emotion/styled` (или antd)
  * `npm install react-router-dom`
  * `npm install @tanstack/react-query`
  * `npm install react-hook-form @hookform/resolvers zod`
  * `npm install axios`
  * `npm install react-dropzone`
  * `npm install plotly.js-dist-min react-plotly.js`
  * `npm install react-hot-toast`
  * `npm install -D typescript @types/react @types/react-dom`

LOGIC:

1. Vite как build tool
2. React 18+ с TypeScript
3. Project structure согласно FSD (Feature-Sliced Design)

DONE:

* [ ] Проект создается
* [ ] Зависимости устанавливаются
* [ ] Dev server запускается (`npm run dev`)

---

### TASK: Project structure (FSD)

FILE: `frontend/src/`

GOAL: Структура папок согласно FSD (SPEC_FRONTEND.md п.3)

IMPLEMENT:

```
frontend/src/
├── app/
│   ├── providers.tsx       # QueryClient, Router, Theme
│   └── routes.tsx          # Все роуты
├── features/
│   ├── auth/
│   ├── dashboards/
│   ├── upload/
│   ├── users/
│   └── admin/
├── shared/
│   ├── api/
│   ├── components/
│   ├── config/
│   └── types/
└── main.tsx
```

LOGIC:

1. `app/` - инициализация, провайдеры
2. `features/` - фичи (Feature-Sliced Design)
3. `shared/` - переиспользуемый код

DONE:

* [ ] Структура создана
* [ ] Пустые файлы-заглушки созданы

---

### TASK: App providers

FILE: `frontend/src/app/providers.tsx`

GOAL: Настройка провайдеров (SPEC_FRONTEND.md п.3)

IMPLEMENT:

* `QueryClient` с настройками (TanStack Query)
* `BrowserRouter` (React Router)
* `ThemeProvider` (MUI или Ant Design)
* `Toaster` (react-hot-toast)

LOGIC:

1. QueryClient с `retry: 1`, `staleTime: 5 * 60 * 1000`
2. Axios interceptors для JWT
3. Error handling глобальный

DONE:

* [ ] Providers работают
* [ ] QueryClient настроен

---

### TASK: Axios instance with JWT interceptors

FILE: `frontend/src/shared/api/axiosInstance.ts`

GOAL: Настроенный Axios с JWT (SPEC_FRONTEND.md п.2.1, п.6.1)

IMPLEMENT:

* `axiosInstance = axios.create({ baseURL: '/api/v1' })`
* Request interceptor:
  * Чтение JWT из memory/storage
  * Добавление `Authorization: Bearer <token>` header
* Response interceptor:
  * Обработка 401 (redirect to login)
  * Обработка других ошибок

LOGIC:

1. JWT хранится в memory (useAuth hook) или secure cookie
2. При 401: очистка токена, редирект на /login
3. `withCredentials: true` для CORS

DONE:

* [ ] Axios instance работает
* [ ] Interceptors добавляют токен
* [ ] 401 обрабатывается

---

### TASK: API types (TypeScript)

FILE: `frontend/src/shared/types/api.types.ts`

GOAL: Общие типы для API (SPEC_FRONTEND.md п.4)

IMPLEMENT:

```typescript
interface UserProfile {
  id: string;
  email: string;
  role: 'admin' | 'editor' | 'viewer';
}

interface DashboardSummary {
  id: string;
  name: string;
  description: string | null;
  permission: 'view' | 'edit' | 'admin';
}

interface GraphData {
  graph_id: string;
  data: any;  // Plotly data format
}

interface LoginRequest {
  email: string;
  password: string;
}

interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}
// ... и другие типы
```

DONE:

* [ ] Типы определены
* [ ] Экспортируются из index.ts

---

### TASK: Shared components (Layout, ProtectedRoute)

FILE: `frontend/src/shared/components/`

GOAL: Переиспользуемые компоненты (SPEC_FRONTEND.md п.3, п.4)

IMPLEMENT:

* `Layout/AppLayout.tsx` - основной layout (header, sidebar, content)
* `Layout/Header.tsx` - header с профилем пользователя
* `Layout/Sidebar.tsx` - навигация
* `ProtectedRoute.tsx` - защита роутов (проверка auth)
* `RoleBasedAccess.tsx` - проверка роли (children только для нужных ролей)

LOGIC:

1. ProtectedRoute: проверка наличия JWT, редирект на /login
2. RoleBasedAccess: проверка роли пользователя

DONE:

* [ ] Layout рендерится
* [ ] ProtectedRoute работает
* [ ] RoleBasedAccess работает

---
