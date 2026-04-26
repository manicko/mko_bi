TASK: Сервис аутентификации и регистрации

FILE: src/mko_bi/services/auth_service.py

GOAL: Реализовать бизнес-логику регистрации и входа

IMPLEMENT:

func: register_user(email: str, password: str, role: str, db: Session) -> UserRead
func: authenticate_user(email: str, password: str, db: Session) -> Optional[UserDB]
func: login_user (реализован в routes)

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
- Все функции принимают сессию БД (db) как параметр

DONE:
- Регистрация создает пользователя с захешированным паролем
- Аутентификация проверяет email и пароль
- Логин возвращает JWT токен
- Валидация ошибок работает корректно
- Тесты покрывают все сценарии

Тесты: нужны только глубоко тестирующие бизнес-логику.