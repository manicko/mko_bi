TASK: Сервис аутентификации и регистрации

FILE: src/mko_bi/services/auth_service.py

GOAL: Реализовать бизнес-логику регистрации и входа

IMPLEMENT:

func: register_user(email: str, password: str, role: str) -> UserRead
func: authenticate_user(email: str, password: str) -> Optional[UserDB]
func: login_user(email: str, password: str) -> dict

LOGIC:
- register_user: валидация email/роли, проверка дублей, хеш пароля, сохранение
- authenticate_user: поиск по email, проверка пароля, возврат пользователя
- login_user: аутентификация + создание JWT токена
- Использовать UserRepository для операций с БД
- Использовать security для хеширования и JWT

CONSTRAINTS:
- Валидация email через pydantic EmailStr
- Роли: admin/editor/viewer
- Проверка уникальности email
- Хеширование обязательно перед сохранением
- Возврат UserRead без password_hash

DONE:
- Регистрация создает пользователя с захешированным паролем
- Аутентификация проверяет email и пароль
- Логин возвращает JWT токен
- Валидация ошибок работает корректно
- Тесты покрывают все сценарии