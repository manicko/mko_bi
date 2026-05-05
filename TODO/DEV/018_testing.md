---
## BLOCK 18: TESTING
---

### TASK: Pytest configuration

FILE: `pyproject.toml` (раздел [tool.pytest.ini_options])

GOAL: Настройка pytest (SPEC.md п.21, п.2.30)

IMPLEMENT:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"
```

LOGIC:

1. Поддержка async тестов (asyncio_mode = "auto")
2. Тесты в папке tests/

DONE:

* [ ] pytest запускается
* [ ] Async тесты работают

---

### TASK: Test database setup

FILE: `tests/conftest.py`

GOAL: Fixtures для тестовой БД

IMPLEMENT:

* `async_engine_test` - тестовый engine (SQLite или PostgreSQL test DB)
* `async_session_test` - session fixture
* `client` - FastAPI TestClient с переопределенной зависимостью БД
* `test_user` - фикстура тестового пользователя
* `auth_headers` - фикстура с JWT токеном

LOGIC:

1. Использовать `pytest-asyncio`
2. Тестовая БД создается и удаляется для каждого теста (или session)
3. FastAPI TestClient для API тестов

DONE:

* [ ] Фикстуры работают
* [ ] Тестовая БД создается

---

### TASK: Auth tests

FILE: `tests/test_auth.py`

GOAL: Тесты аутентификации (SPEC.md п.21)

IMPLEMENT:

* `test_login_success` - успешный вход
* `test_login_wrong_password` - неверный пароль
* `test_login_nonexistent_user` - несуществующий юзер
* `test_register_request_success` - успешная заявка
* `test_register_request_duplicate` - дубликат email
* `test_get_me_authenticated` - получение профиля
* `test_get_me_unauthenticated` - без токена (401)

LOGIC:

1. Использовать FastAPI TestClient
2. Проверка статус кодов и ответов

DONE:

* [ ] Тесты проходят
* [ ] Покрытие > 80%

---

### TASK: Dashboard API tests

FILE: `tests/test_dashboards_api.py`

GOAL: Тесты API дашбордов

IMPLEMENT:

* `test_get_my_dashboards` - список дашбордов
* `test_get_dashboard_detail` - детали
* `test_create_dashboard_admin` - создание (admin)
* `test_create_dashboard_forbidden` - создание (не admin, 403)
* `test_update_dashboard` - обновление
* `test_delete_dashboard` - удаление
* `test_access_control` - проверка доступа

DONE:

* [ ] Тесты проходят
* [ ] Покрытие > 80%

---

### TASK: Data processing tests

FILE: `tests/test_data_processing.py`

GOAL: Тесты обработки данных (SPEC.md п.21)

IMPLEMENT:

* `test_load_csv` - загрузка CSV
* `test_load_csv_gz` - загрузка CSV.gz
* `test_apply_transformations` - трансформации
* `test_aggregate_data` - агрегации
* `test_yoy_calculation` - YoY
* `test_share_calculation` - доли

LOGIC:

1. Использовать тестовые CSV файлы (fixture)
2. Проверка DataFrame структуры

DONE:

* [ ] Тесты проходят
* [ ] Покрытие > 80%

---

### TASK: Upload API tests

FILE: `tests/test_upload_api.py`

GOAL: Тесты загрузки файлов

IMPLEMENT:

* `test_upload_csv_success` - успешная загрузка
* `test_upload_csv_gz_success` - успешная загрузка gz
* `test_upload_wrong_extension` - неверное расширение (400)
* `test_upload_wrong_mime` - неверный MIME (400)
* `test_upload_too_large` - слишком большой файл (400)
* `test_upload_no_permission` - нет прав (403)

DONE:

* [ ] Тесты проходят
* [ ] Покрытие > 80%

---

### TASK: Repository tests

FILE: `tests/test_repositories.py`

GOAL: Тесты репозиториев

IMPLEMENT:

* Тесты CRUD для каждого репозитория
* `test_user_repo_crud`
* `test_dashboard_repo_crud`
* `test_graph_repo_crud`
* и т.д.

DONE:

* [ ] Тесты проходят
* [ ] Покрытие > 80%

---

### TASK: Coverage setup

FILE: `pyproject.toml` (раздел [tool.coverage.run])

GOAL: Настройка покрытия кода

IMPLEMENT:

```toml
[tool.coverage.run]
source = ["src/mko_bi"]
omit = ["*/tests/*", "*/migrations/*"]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

LOGIC:

1. Запуск: `uv run pytest --cov`
2. Fail если покрытие < 80%

DONE:

* [ ] Coverage считается
* [ ] Fail under работает

---
