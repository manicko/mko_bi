TASK: Интеграция Layouts (UI композиция)

FILE: src/mko_bi/dashboards/
FILE: src/mko_bi/db/models/layout.py
FILE: src/mko_bi/dash_app.py

GOAL: Использование сохраненных layout-ов для компоновки дашбордов (SPEC.md)

IMPLEMENT:

func: загрузка и применение layout конфигурации

LOGIC:

1. Проверить таблицу layouts в БД:
   - Модель уже существует в db/models/layout.py
   - Repository в db/repositories/

2. Создать сервис для работы с layouts:
   - `services/layout_service.py` (или добавить в dashboard_service)
   - CRUD операции для layout-ов

3. Обновить Dash для использования сохраненных layout-ов:
   - Загружать конфигурацию layout при открытии дашборда
   - Применять порядок и расположение графиков согласно layout

4. Пример структуры layout:
```
{
    "dashboard_id": "uuid",
    "layout_config": {
        "rows": [
            {"columns": [{"graph_id": 1, "width": 12}]},
            {"columns": [{"graph_id": 2, "width": 6}, {"graph_id": 3, "width": 6}]}
        ]
    }
}
```

5. UI для редактирования layout (опционально, может быть в следующей версии)

CONSTRAINTS:

- Выполняется ПОСЛЕ TASK-007 (Dash real data)
- Таблица layouts уже существует - использовать её
- Не делать overengineering - простая сетка (rows/columns) достаточно
- Интеграция с существующими Dash компонентами (dbc.Row, dbc.Col)

DONE:

- Layout-ы загружаются из БД при открытии дашборда
- Графики располагаются согласно layout конфигурации
- Сохранение нового layout работает (API endpoint)
- `uv run ruff check .` проходит

TEST:

# Создать layout через API
# Проверить отображение в Dash
uv run pytest tests/ -k "layout" -v
