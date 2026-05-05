---
## BLOCK 3: AUTHENTICATION & AUTHORIZATION
---

### TASK: Password hashing (bcrypt)

FILE: `src/mko_bi/core/security.py`

GOAL: Хеширование и проверка паролей через bcrypt (SPEC.md п.5, п.29)

IMPLEMENT:

* `hash_password(password: str) -> str`
* `verify_password(plain_password: str, hashed_password: str) -> bool`
* `generate_password_hash(password: str) -> str` (alias)

LOGIC:

1. Использовать `bcrypt` библиотеку
2. `bcrypt.hashpw(password.encode(), bcrypt.gensalt())` для хеширования
3. `bcrypt.checkpw()` для проверки
4. Использовать `encoding="utf-8"` для строк

DONE:

* [ ] Хеширование работает
* [ ] Проверка пароля работает
* [ ] Тесты на hash/verify

---

### TASK: JWT token creation и validation

FILE: `src/mko_bi/core/security.py` (дополнение)

GOAL: JWT токены для аутентификации (SPEC.md п.5, п.29)

IMPLEMENT:

* `create_access_token(data: dict, expires_delta: timedelta | None = None) -> str`
* `decode_access_token(token: str) -> dict | None`
* `get_current_user(token: str) -> User | None`

LOGIC:

1. Использовать `PyJWT` библиотеку
2. Алгоритм HS256
3. Payload: `{"sub": user_id, "email": email, "role": role, "exp": expires}`
4. `jwt.decode()` с проверкой exp, signature
5. Возвращать None при невалидном токене

DONE:

* [ ] Токен создается
* [ ] Токен декодируется
* [ ] Expired token обрабатывается
* [ ] Тесты на create/decode

---

### TASK: Auth API endpoints

FILE: `src/mko_bi/api/routes/auth.py`

GOAL: Login и register-request endpoints (SPEC.md п.14.1)

IMPLEMENT:

* `POST /api/v1/auth/login`:
  * Request: `LoginRequest(email, password)`
  * Response: `AuthResponse(access_token, token_type, user)`
  * Логика: проверка email, verify password, создание JWT
* `POST /api/v1/auth/register-request`:
  * Request: `RegistrationRequestCreate(email)`
  * Response: `{"message": "Заявка отправлена"}`
  * Логика: сохранение в `registration_requests`, статус PENDING
* `GET /api/v1/auth/me`:
  * Response: `UserProfile`
  * Логика: получение текущего пользователя из JWT

LOGIC:

1. Использовать FastAPI `Depends()` для DI
2. `get_db()` dependency для сессии
3. `get_current_user()` dependency для защиты
4. HTTPException при ошибках (401 Unauthorized)
5. Логирование успешного/неуспешного входа

DONE:

* [ ] Login endpoint работает (curl test)
* [ ] Register-request endpoint работает
* [ ] Me endpoint возвращает профиль
* [ ] Тесты написаны

---

### TASK: Auth service

FILE: `src/mko_bi/services/auth_service.py`

GOAL: Бизнес-логика аутентификации

IMPLEMENT:

* `class AuthService`:
  * `async login(email: str, password: str, db: AsyncSession) -> AuthResponse | None`
  * `async register_request(email: str, ip: str | None, db: AsyncSession) -> RegistrationRequestResponse`
  * `async get_user_by_id(user_id: UUID, db: AsyncSession) -> UserResponse`
  * `async get_user_by_email(email: str, db: AsyncSession) -> User | None`

LOGIC:

1. Проверка существования пользователя/заявки
2. Валидация через Pydantic models
3. Использование UserRepository для БД операций
4. Интеграция с security.py

DONE:

* [ ] Service методы работают
* [ ] Интеграция с API
* [ ] Тесты написаны

---

### TASK: Permissions & role-based access

FILE: `src/mko_bi/core/permissions.py`

GOAL: Проверка прав доступа (SPEC.md п.4, п.15)

IMPLEMENT:

* `class RolePermissions`:
  * `CAN_CREATE_DASHBOARDS: list[UserRole] = [ADMIN]`
  * `CAN_EDIT_DASHBOARDS: list[UserRole] = [ADMIN, EDITOR]`
  * `CAN_VIEW_DASHBOARDS: list[UserRole] = [ADMIN, EDITOR, VIEWER]`
  * `CAN_MANAGE_USERS: list[UserRole] = [ADMIN]`
  * `CAN_UPLOAD_DATA: list[UserRole] = [ADMIN, EDITOR]`

* `check_permission(user_role: UserRole, required: list[UserRole]) -> bool`
* `require_role(required_roles: list[UserRole])` - FastAPI dependency
* `check_dashboard_access(user_id: UUID, dashboard_id: UUID, permission: DashboardPermission, db) -> bool`

LOGIC:

1. Декораторы или dependency injection для FastAPI
2. Проверка user ↔ dashboard доступа через DashboardAccess репозиторий
3. HTTPException(403) при отказе в доступе

DONE:

* [ ] Роли проверяются
* [ ] Dashboard access проверяется
* [ ] Тесты на permissions

---
