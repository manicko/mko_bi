TASK: Расширение модуля безопасности

FILE: src/mko_bi/core/security.py

GOAL: Реализовать хеширование паролей и JWT токены

IMPLEMENT:

func: hash_password(password: str) -> str
func: verify_password(password: str, hash_value: str) -> bool
func: create_access_token(data: dict) -> str
func: decode_token(token: str) -> dict

LOGIC:
- hash_password: bcrypt.hashpw с ограничением 72 байт
- verify_password: bcrypt.checkpw с тем же ограничением
- create_access_token: JWT с exp временем из config
- decode_token: валидация и декодирование JWT
- Использовать SECRET_KEY и ALGORITHM из config

CONSTRAINTS:
- bcrypt для хеширования (SALT_ROUNDS=12)
- JWT с алгоритмом HS256
- Время жизни токена: 30 минут
- Обрезать пароли длиннее 72 байт для bcrypt
- Обработка JWTError при декодировании

DONE:
- Пароли хешируются корректно
- Проверка паролей работает
- JWT токены создаются с exp
- Декодирование валидирует токены
- Токены содержат user_id

Тесты: нужны только глубоко тестирующие бизнес-логику.