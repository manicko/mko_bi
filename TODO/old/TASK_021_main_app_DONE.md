TASK: FastAPI Application Setup

FILES:
- src/mko_bi/main.py
- src/mko_bi/app.py

GOAL:
Создать FastAPI приложение через factory pattern

IMPLEMENT:

1. В app.py:
- функция create_app() -> FastAPI
- НЕ создавать глобальный app

2. В main.py:
- создать app = create_app()

LOGIC:

create_app:
- создать FastAPI(
    title="mko_bi API",
    version="1.0.0"
)

- добавить middleware:
    - CORS (allow_origins=["*"])
    - GZip (minimum_size=1000)

- зарегистрировать роутеры через include_router()
    (предположить, что routers находятся в mko_bi.api)

- добавить exception handlers:
    - HTTPException
    - RequestValidationError (FastAPI)
    - ValidationError (Pydantic)

- включить docs:
    - /docs (Swagger)
    - /redoc

CONSTRAINTS:
- использовать factory pattern
- не дублировать app
- код должен быть production-ready
- Тесты: нужны только глубоко тестирующие бизнес-логику.


DONE:
- FastAPI приложение создано
- Все роуты зарегистрированы
- Middleware настроены
- Swagger доступен
- Обработка ошибок работает
