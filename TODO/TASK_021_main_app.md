TASK: Основное приложение FastAPI

FILE: src/mko_bi/main.py
FILE: src/mko_bi/app.py

GOAL: Создать точку входа и настроить FastAPI приложение

IMPLEMENT:

func: create_app()
class: FastAPI app

LOGIC:
- create_app: factory function для создания приложения
- Настройка CORS middleware
- Настройка GZip middleware
- Регистрация всех роутов
- Обработчики исключений
- Swagger/ReDoc документация

CONSTRAINTS:
- Использовать FastAPI
- Title: "mko_bi API"
- Version: "1.0.0"
- CORS: allow_origins=["*"]
- GZip: минимальный размер 1000
- Обработка HTTPException и ValidationError

DONE:
- FastAPI приложение создано
- Все роуты зарегистрированы
- Middleware настроены
- Swagger доступен
- Обработка ошибок работает

Тесты: нужны только глубоко тестирующие бизнес-логику.