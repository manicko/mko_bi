TASK: исправить UUID в тестах API дашбордов

FILE: tests/test_dashboards_api.py

GOAL: заменить Integer ID на UUID и подготовить к httpx.AsyncClient

IMPLEMENT:

func: test_create_dashboard()
func: test_get_dashboard()
func: все моки mock_user, dashboard_id

LOGIC:

заменить mock_user.id = 1 на mock_user.id = uuid.uuid4()
заменить все dashboard_id=1 на dashboard_id=uuid.uuid4()
обновить assert проверки (owner_id == UUID, а не int)
убедиться что моки возвращают объекты с UUID полями

CONSTRAINTS:

mock_user.id должен быть UUID
dashboard_id должен быть UUID
не использовать int(dashboard_id) или приведение типов
убрать assert с == 1 или == int

DONE:

все ID в test_dashboards_api.py используют UUID
тесты проходят: uv run pytest tests/test_dashboards_api.py
