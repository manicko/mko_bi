TASK: мигрировать API тесты на httpx.AsyncClient

FILE: tests/test_dashboards_api.py, tests/test_upload_api.py, tests/test_data_api.py

GOAL: переписать тесты с прямых вызовов функций на httpx.AsyncClient

IMPLEMENT:

func: переписать все тесты с await create_dashboard_endpoint(...) на httpx запросы
func: использовать фикстуру async_client из conftest.py

LOGIC:

найти прямые вызовы функций роутов (create_dashboard_endpoint, get_dashboard_endpoint и т.д.)
заменить на httpx.AsyncClient запросы (client.post, client.get и т.д.)
настроить правильные URL пути
использовать фикстуру async_client для авторизации и заголовков
проверить middleware и зависимости (Depends) через реальные HTTP запросы

CONSTRAINTS:

не вызывать handler-функции напрямую
использовать httpx.AsyncClient для всех API тестов
тесты должны проходить через реальный FastAPI stack (middleware, Depends)

DONE:

API тесты используют httpx.AsyncClient
прямые вызовы функций роутов удалены
тесты проходят: uv run pytest tests/test_dashboards_api.py tests/test_upload_api.py tests/test_data_api.py
