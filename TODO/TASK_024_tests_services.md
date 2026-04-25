TASK: Тесты сервисов (бизнес-логика)

FILE: tests/services/test_auth_service.py
FILE: tests/services/test_user_service.py
FILE: tests/services/test_dashboard_service.py
FILE: tests/services/test_data_service.py

GOAL: Написать unit тесты для бизнес-логики

IMPLEMENT:

test: test_register_user
test: test_authenticate_user
test: test_create_dashboard
test: test_data_processing
test: test_access_control

LOGIC:
- Тесты регистрации с валидными/невалидными данными
- Тесты аутентификации (успех/неудача)
- Тесты создания дашбордов
- Тесты обработки данных
- Тесты проверки прав доступа

CONSTRAINTS:
- Использовать pytest
- Мокирование внешних зависимостей
- Изоляция тестов
- Параметризация тестов
- Покрытие: 90%+ бизнес-логики

DONE:
- Сервисы протестированы
- Мокирование настроено
- Тесты покрывают edge cases
- Покрытие 90%+
- CI/CD запускает тесты