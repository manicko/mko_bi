TASK: исправить UUID в тестах сервиса дашбордов

FILE: tests/services/test_dashboard_service.py

GOAL: заменить Integer ID на UUID во всех тестах сервиса дашбордов

IMPLEMENT:

func: test_validate_dashboard_exists()
func: test_check_owner_permission()
func: test_grant_access()
func: все вызовы с параметрами dashboard_id, user_id

LOGIC:

найти все использования int ID (1, 2, 999, и т.д.)
заменить на uuid.uuid4() для генерации UUID
обновить моки и фикстуры для работы с UUID
проверить что типы данных соответствуют src/mko_bi/db/models/dashboard.py (UUID)

CONSTRAINTS:

dashboard_id и user_id должны быть типа UUID (как в моделях)
не использовать int для ID
все вызовы _validate_dashboard_exists, _check_owner_permission, grant_access должны получать UUID

DONE:

все ID в test_dashboard_service.py используют UUID
тесты проходят: uv run pytest tests/services/test_dashboard_service.py
