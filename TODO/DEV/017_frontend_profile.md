---
## BLOCK 17: FRONTEND PROFILE
---

### TASK: User profile page

FILE: `frontend/src/features/users/ui/UserProfile.tsx`

GOAL: Профиль пользователя (SPEC_FRONTEND.md п.4.4)

IMPLEMENT:

* Email пользователя (read-only)
* Роль (read-only)
* Кнопка "Удалить аккаунт" (только для НЕ-админов)
* Модальное окно подтверждения удаления

LOGIC:

1. GET /api/v1/auth/me (текущий пользователь)
2. DELETE /api/v1/users/me (самоудаление)
3. После удаления: редирект на /login, очистка JWT
4. Админ не видит кнопку удаления

DONE:

* [ ] Профиль загружается
* [ ] Данные read-only
* [ ] Удаление работает
* [ ] Админ не видит кнопку удаления

---

### TASK: User API (frontend)

FILE: `frontend/src/features/users/api/userApi.ts`

GOAL: API функции для пользователя

IMPLEMENT:

* `getProfile(): Promise<UserProfile>`
* `deleteAccount(): Promise<void>`

LOGIC:

1. Использовать axiosInstance
2. После удаления - logout (очистка JWT)

DONE:

* [ ] API функции работают

---
