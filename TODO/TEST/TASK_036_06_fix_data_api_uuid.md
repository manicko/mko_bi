TASK: исправить UUID в тестах API данных

FILE: tests/test_data_api.py

GOAL: заменить Integer ID на UUID и удалить приведение типов

IMPLEMENT:

func: test_get_aggregate_data()
func: test_data_response()
func: все моки mock_user, mock_aggregate

LOGIC:

заменить mock_user.id = 1 на mock_user.id = uuid.uuid4()
удалить строку mock_aggregate.dashboard_id = int(dashboard_id)
использовать UUID напрямую без приведения типов
обновить dashboard_id в моках на uuid.uuid4()

CONSTRAINTS:

mock_user.id должен быть UUID
dashboard_id должен быть UUID
удалить int(dashboard_id) - грубая ошибка
не использовать приведение типов

DONE:

все ID в test_data_api.py используют UUID
удалено приведение int(dashboard_id)
тесты проходят: uv run pytest tests/test_data_api.py
