TASK: Replace synchronous HTTP requests with async alternatives in Dash

FILE: src/mko_bi/dash_app.py

GOAL: Eliminate blocking HTTP calls in Dash callbacks

IMPLEMENT:

func: update Dash callbacks to use httpx.AsyncClient

LOGIC:

установить httpx (если не установлен): uv add httpx
заменить imports: remove requests, add httpx
заменить requests.get/post на httpx.AsyncClient в функциях:
  - fetch_dashboard_data()
  - login_user() callback
  - load_dashboards() callback
  - load_dashboard_data()
  - _get_available_filter_values()
использовать async with httpx.AsyncClient() as client:
обновить функции callback-ов добавив async перед def

CONSTRAINTS:

использовать httpx с async support
все HTTP вызовы должны быть неблокирующими
сохранить timeout параметры (10-30 сек)

DONE:

 requests заменен на httpx.AsyncClient
 все Dash callbacks используют async HTTP calls
 тесты проходят (если есть тесты для Dash)
