---
## BLOCK 10: USER MANAGEMENT (ADMIN)
---

### TASK: Users CRUD (admin)

FILE: `src/mko_bi/api/routes/users.py`

GOAL: Управление пользователями (SPEC.md п.14.4, п.14.2)

IMPLEMENT:

* `GET /api/v1/admin/users` (admin) - список пользователей
* `PATCH /api/v1/admin/users/{user_id}/role` (admin) - изменение роли
  * Body: `{"role": "admin" | "editor" | "viewer"}`
* `DELETE /api/v1/admin/users/{user_id}` (admin) - удаление
* `GET /api/v1/auth/me` - профиль текущего пользователя
* `DELETE /api/v1/users/me` - самоудаление (только не-админ)

LOGIC:

1. Только admin может менять роли
2. Admin не может удалить свой аккаунт (проверка в API)
3. Самоудаление: только для не-админов
4. Удаление пользователя → CASCADE удаление access, logs

DONE:

* [ ] Users list endpoint работает
* [ ] Role change работает
* [ ] Delete работает (с проверками)
* [ ] Тесты написаны

---

### TASK: Registration requests management

FILE: `src/mko_bi/api/routes/auth.py` (дополнение)

GOAL: Управление заявками на регистрацию (SPEC.md п.14.4)

IMPLEMENT:

* `GET /api/v1/admin/registration-requests` (admin) - список заявок
* `POST /api/v1/admin/registration-requests/{request_id}/approve` (admin) - одобрение
  * Создание user в БД
  * Установка статуса APPROVED
  * Запись reviewed_by, reviewed_at
* `POST /api/v1/admin/registration-requests/{request_id}/reject` (admin) - отклонение

LOGIC:

1. При approve: генерация временного пароля (или приглашение по email)
2. Заявки только в статусе PENDING
3. reviewer = current_user (admin)

DONE:

* [ ] List requests работает
* [ ] Approve создает user
* [ ] Reject работает
* [ ] Тесты написаны

---

### TASK: User service

FILE: `src/mko_bi/services/user_service.py`

GOAL: Бизнес-логика пользователей

IMPLEMENT:

* `class UserService`:
  * `async def get_all(self, db: AsyncSession) -> list[UserResponse]`
  * `async def change_role(self, user_id: UUID, new_role: UserRole, db: AsyncSession) -> UserResponse`
  * `async def delete_user(self, user_id: UUID, db: AsyncSession) -> bool`
  * `async def get_registration_requests(self, db: AsyncSession) -> list[RegistrationRequestResponse]`
  * `async def approve_request(self, request_id: UUID, reviewer_id: UUID, db: AsyncSession) -> UserResponse`
  * `async def reject_request(self, request_id: UUID, reviewer_id: UUID, db: AsyncSession) -> bool`
  * `async def self_delete(self, user_id: UUID, db: AsyncSession) -> bool`

LOGIC:

1. Использовать UserRepository, RegistrationRequestRepository
2. Проверки прав доступа
3. Транзакционность операций

DONE:

* [ ] Service методы работают
* [ ] Интеграция с API
* [ ] Тесты написаны

---
