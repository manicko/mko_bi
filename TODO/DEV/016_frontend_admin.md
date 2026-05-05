---
## BLOCK 16: FRONTEND ADMIN
---

### TASK: Admin panel layout

FILE: `frontend/src/features/admin/ui/AdminPanel.tsx`

GOAL: Панель администратора (SPEC_FRONTEND.md п.4.5)

IMPLEMENT:

* Tabs для навигации:
  1. User Management (/admin/users)
  2. Registration Requests (/admin/requests)
  3. Dashboard Management (/admin/dashboards)
  4. Log Viewer (/admin/logs)
* Права: только для admin role

LOGIC:

1. MUI Tabs или Ant Design Tabs
2. Защита через `RoleBasedAccess` компонент
3. Роутинг на подстраницы

DONE:

* [ ] Tabs рендерятся
* [ ] Навигация работает
* [ ] Доступ только для admin

---

### TASK: User management tab

FILE: `frontend/src/features/admin/ui/UserManagement.tsx`

GOAL: Управление пользователями (SPEC_FRONTEND.md п.4.5)

IMPLEMENT:

* Таблица пользователей (MUI DataGrid или Ant Table)
  * Колонки: email, role, status, created_at
* Кнопки: "Изменить роль", "Заблокировать", "Удалить"
* Форма создания пользователя (для админа)

LOGIC:

1. GET /api/v1/admin/users
2. PATCH /api/v1/admin/users/:id/role
3. DELETE /api/v1/admin/users/:id
4. Модальное окно для редактирования

DONE:

* [ ] Таблица рендерится
* [ ] Изменение роли работает
* [ ] Удаление работает

---

### TASK: Registration requests tab

FILE: `frontend/src/features/admin/ui/RegistrationRequests.tsx`

GOAL: Управление заявками (SPEC_FRONTEND.md п.4.5)

IMPLEMENT:

* Список заявок на регистрацию
* Статусы: pending, approved, rejected
* Кнопки: "Одобрить", "Отклонить"

LOGIC:

1. GET /api/v1/admin/registration-requests
2. POST /api/v1/admin/registration-requests/:id/approve
3. POST /api/v1/admin/registration-requests/:id/reject

DONE:

* [ ] Список загружается
* [ ] Одобрение работает
* [ ] Отклонение работает

---

### TASK: Dashboard management tab

FILE: `frontend/src/features/admin/ui/DashboardManagement.tsx`

GOAL: CRUD дашбордов (SPEC_FRONTEND.md п.4.5)

IMPLEMENT:

* Таблица дашбордов
* CRUD операции (через модальные окна)
* Назначение доступов (user ↔ dashboard)

LOGIC:

1. GET /api/v1/dashboards (все, для админа)
2. POST /api/v1/dashboards - создание
3. PUT /api/v1/dashboards/:id - обновление
4. DELETE /api/v1/dashboards/:id - удаление
5. POST /api/v1/dashboards/:id/access - выдача доступа

DONE:

* [ ] CRUD дашбордов работает
* [ ] Управление доступами работает

---

### TASK: Log viewer tab

FILE: `frontend/src/features/admin/ui/LogViewer.tsx`

GOAL: Просмотр логов (SPEC_FRONTEND.md п.4.5)

IMPLEMENT:

* Таблица логов (processing_logs)
* Фильтры по dashboard_id, status, date range
* Пагинация

LOGIC:

1. GET /api/v1/admin/logs?dashboard_id=&status=&date_from=&date_to=
2. Обновление таблицы при изменении фильтров

DONE:

* [ ] Логи загружаются
* [ ] Фильтры работают
* [ ] Пагинация работает

---

### TASK: Admin API

FILE: `frontend/src/features/admin/api/adminApi.ts`

GOAL: API функции для админки

IMPLEMENT:

* `getUsers(): Promise<User[]>`
* `changeUserRole(userId: string, role: string): Promise<User>`
* `deleteUser(userId: string): Promise<void>`
* `getRegistrationRequests(): Promise<RegistrationRequest[]>`
* `approveRequest(requestId: string): Promise<void>`
* `rejectRequest(requestId: string): Promise<void>`
* `getLogs(filters?: LogFilters): Promise<ProcessingLog[]>`

DONE:

* [ ] API функции работают
* [ ] Типизация корректна

---
