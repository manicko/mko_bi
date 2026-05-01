TASK: исправить UUID в тестах сервиса пользователей

FILE: tests/services/test_user_service.py

GOAL: заменить Integer ID на UUID во всех тестах сервиса

IMPLEMENT:

func: test_get_user_by_id()
func: test_validate_user_exists()
func: все вызовы с параметром user_id

LOGIC:

найти все использования int ID (1, 999, и т.д.)
заменить на uuid.uuid4() для генерации UUID
обновить моки и фикстуры для работы с UUID
проверить что типы данных соответствуют src/mko_bi/db/models/user.py (UUID)

CONSTRAINTS:

user_id должен быть типа UUID (как в модели User)
не использовать int для ID
все вызовы _validate_user_exists, get_user_by_id должны получать UUID

DONE:

все user_id в test_user_service.py используют UUID
тесты проходят: uv run pytest tests/services/test_user_service.py
