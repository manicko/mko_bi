TASK: Подключение реальных данных к графикам Dash (цепочка)

FILE: src/mko_bi/dash_app.py
FILE: src/mko_bi/dashboards/components/charts/*.py

GOAL: Замена заглушек на реальные данные из API и активация фильтров

IMPLEMENT:

func: обновление callbacks для получения данных через API

LOGIC:

1. Создать функцию получения данных дашборда через API:
```
import requests

def fetch_dashboard_data(dashboard_id: str, token: str, filters: dict | None = None):
    """Получает данные дашборда через FastAPI API."""
    headers = {"Authorization": f"Bearer {token}"}
    params = filters or {}
    resp = requests.get(
        f"http://localhost:8000/api/v1/dashboards/{dashboard_id}/data",
        headers=headers,
        params=params,
    )
    return resp.json()
```

2. Обновить callbacks в dash_app.py:
   - `_update_dashboard_graphs()` - получать реальные данные
   - Убрать `raise PreventUpdate` в `apply_dashboard_filters` (строка 787)
   - Использовать `fetch_dashboard_data()` вместо заглушек

3. Обновить функции создания графиков:
   - `_create_bar_chart()`, `_create_line_chart()` и др.
   - Использовать реальные данные из API ответа

4. Активировать панель фильтров (строки 661-739):
   - Сделать callbacks для фильтров работающими
   - Передавать выбранные фильтры в API запрос

5. Убрать хардкоженные значения (годы, категории и т.д.)

CONSTRAINTS:

- Выполняется ПОСЛЕ TASK-005 (Dash mount) и TASK-006 (Dash auth)
- Использовать существующие API endpoints из routes/dashboards.py
- Обрабатывать ошибки API (401, 403, 404, 500)
- Callbacks должны обновлять графики при изменении фильтров

DONE:

- Графики отображают реальные данные из БД
- Фильтры работают и обновляют данные
- `raise PreventUpdate` убран из `apply_dashboard_filters`
- Хардкоженные значения заменены на динамические
- `uv run ruff check .` проходит

TEST:

# Запустить приложение и проверить:
# 1. Открыть дашборд - данные загружаются
# 2. Изменить фильтры - графики обновляются
uv run uvicorn mko_bi.main:app --reload
