TASK: Убрать хардкод секретов и сделать обязательными env-переменные

FILE: src/mko_bi/config.py, src/mko_bi/db/session.py, .env.example

GOAL: Удалить все дефолтные секреты, сделать обязательными переменные окружения для безопасности

IMPLEMENT:

func: Config - использовать pydantic-settings с валидацией

LOGIC:

1. В config.py:
   - Удалить JWT_SECRET_KEY по умолчанию
   - Сделать обязательным os.getenv("JWT_SECRET_KEY")
   - Выбрасывать ошибку если переменная не задана
2. В db/session.py:
   - Убрать хардкод пароля "1234"
   - Читать из DATABASE_URL или отдельных переменных
3. Создать .env.example:
   - JWT_SECRET_KEY=change-me
   - DATABASE_URL=postgresql://user:password@localhost/db
   - REDIS_URL=redis://localhost:6379
   - LOG_LEVEL=INFO
4. Использовать pydantic-settings:
   - Валидация типов
   - Обязательные поля
   - Преобразование значений

CONSTRAINTS:

- Нет дефолтных секретов в коде
- Приложение не должно запускаться без обязательных переменных
- Четкие сообщения об ошибках при отсутствии переменных
- Документация в .env.example

DONE:

- Нет хардкода секретов
- Приложение требует env-переменные
- .env.example создан
- Приложение падает с понятной ошибкой если нет переменных
