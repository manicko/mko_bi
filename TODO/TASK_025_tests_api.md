TASK: Интеграционные тесты API

FILE: tests/api/test_auth.py
FILE: tests/api/test_users.py
FILE: tests/api/test_dashboards.py
FILE: tests/api/test_upload.py

GOAL: Написать интеграционные тесты для эндпоинтов

IMPLEMENT:

test: test_login_endpoint
test: test_register_endpoint
test: test_users_crud
test: test_dashboards_crud
test: test_upload_endpoint

LOGIC:
- Тесты POST /auth/login
- Тесты POST /auth/register
- Тесты CRUD /users
- Тесты CRUD /dashboards
- Тесты POST /upload
- Проверка кодов ответов
- Проверка ответов JSON

CONSTRAINTS:
- Использовать TestClient от FastAPI
- Аутентификация через JWT в тестах
- Изоляция тестов
- Покрытие: все эндпоинты
- Тесты производительности (опционально)

DONE:
- Все эндпоинты протестированы
- JWT аутентификация работает
- Коды ответов корректны
- Ответы валидны
- CI/CD запускает тесты