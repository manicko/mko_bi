TASK: исправить UUID в тестах API загрузки данных

FILE: tests/test_upload_api.py

GOAL: заменить Integer ID на UUID в тестах загрузки

IMPLEMENT:

func: test_upload_file()
func: test_upload_response()
func: все моки mock_user, dashboard_id

LOGIC:

заменить mock_user.id = 1 на mock_user.id = uuid.uuid4()
заменить dashboard_id=1 на dashboard_id=uuid.uuid4()
обновить UploadResponse с UUID полями
проверить что вызовы сервисов получают UUID

CONSTRAINTS:

mock_user.id должен быть UUID
dashboard_id должен быть UUID
не использовать int для ID

DONE:

все ID в test_upload_api.py используют UUID
тесты проходят: uv run pytest tests/test_upload_api.py
