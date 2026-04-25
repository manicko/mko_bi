TASK: Тесты моделей и репозиториев

FILE: tests/test_models.py
FILE: tests/test_repositories.py

GOAL: Написать unit тесты для моделей и репозиториев

IMPLEMENT:

test: test_user_model_creation
test: test_dashboard_model_creation
test: test_access_model_creation
test: test_user_repository_crud
test: test_dashboard_repository_crud
test: test_access_repository_operations

LOGIC:
- Тесты создания моделей с валидными данными
- Тесты связей между моделями
- Тесты CRUD операций через репозитории
- Тесты уникальных ограничений
- Тесты каскадного удаления

CONSTRAINTS:
- Использовать pytest
- База данных: SQLite in-memory
- Изоляция тестов (каждый тест с чистой БД)
- fixtures для setup/teardown
- Покрытие: 100% моделей и репозиториев

DONE:
- Все модели протестированы
- Все репозитории протестированы
- Тесты изолированы
- Покрытие 100%
- CI/CD интеграция настроена