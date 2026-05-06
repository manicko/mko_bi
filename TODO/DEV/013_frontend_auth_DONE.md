---
## BLOCK 13: FRONTEND AUTH
---

### TASK: Auth hook (useAuth)

FILE: `frontend/src/features/auth/model/useAuth.ts`

GOAL: Хук для управления аутентификацией (SPEC_FRONTEND.md п.4.1, п.4.2)

IMPLEMENT:

* `useAuth()` hook:
  * `user: UserProfile | null`
  * `isLoading: boolean`
  * `login(email, password) -> Promise<void>`
  * `logout() -> void`
  * `registerRequest(email) -> Promise<void>`
  * `getProfile() -> Promise<void>`

LOGIC:

1. JWT хранится в React state (memory) или sessionStorage
2. При login: POST /api/v1/auth/login, сохранение токена
3. При logout: очистка токена, редирект
4. Валидация токена при загрузке (GET /api/v1/auth/me)

DONE:

* [ ] Hook работает
* [ ] Login сохраняет токен
* [ ] Logout очищает состояние

---

### TASK: Login page

FILE: `frontend/src/features/auth/ui/LoginForm.tsx`

GOAL: Страница входа (SPEC_FRONTEND.md п.4.1)

IMPLEMENT:

* Поле email (React Hook Form + Zod validation)
* Поле password (type="password")
* Кнопка "Войти"
* Ссылка "Зарегистрироваться" → /register
* Сообщение об ошибке

LOGIC:

1. Валидация формы через Zod: email format
2. POST /api/v1/auth/login
3. При успехе: сохранить JWT, редирект на /dashboards
4. При ошибке: показать "Неверный email или пароль"

DONE:

* [ ] Форма рендерится
* [ ] Валидация работает
* [ ] Login делает редирект

---

### TASK: Registration page

FILE: `frontend/src/features/auth/ui/RegisterForm.tsx`

GOAL: Страница заявки на регистрацию (SPEC_FRONTEND.md п.4.2)

IMPLEMENT:

* Поле email (Zod validation: regex + blocked domains)
* Кнопка "Отправить заявку"
* Ссылка "Уже есть аккаунт?" → /login

LOGIC:

1. Zod schema: `z.string().email()` + blocked domains check
2. POST /api/v1/auth/register-request
3. При успехе: сообщение "Заявка отправлена администратору"

DONE:

* [ ] Форма рендерится
* [ ] Валидация работает
* [ ] Заявка отправляется

---

### TASK: Auth API

FILE: `frontend/src/features/auth/api/authApi.ts`

GOAL: API функции для аутентификации

IMPLEMENT:

* `login(email: string, password: string): Promise<AuthResponse>`
* `registerRequest(email: string): Promise<RegistrationResponse>`
* `getProfile(): Promise<UserProfile>`
* `logout(): void` (client-side)

LOGIC:

1. Использовать axiosInstance
2. Типизированные ответы

DONE:

* [ ] API функции работают
* [ ] Типы корректны

---
