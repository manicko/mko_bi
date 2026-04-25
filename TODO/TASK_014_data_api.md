TASK: API получения агрегированных данных

FILE: src/mko_bi/api/routes/data.py

GOAL: Создать эндпоинты для получения данных для дашбордов

IMPLEMENT:

router: APIRouter с prefix="/data"

@endpoint: GET /data/{dashboard_id}
@endpoint: GET /data/{dashboard_id}/charts
@endpoint: POST /data/filter

LOGIC:
- GET /data/{id}: получить все агрегаты для дашборда
- GET /data/{id}/charts: данные для конкретных графиков
- POST /data/filter: применить фильтры к данным
- Данные запрашиваются из PostgreSQL
- Фильтры применяются на уровне SQL/Polars

CONSTRAINTS:
- Защита через Depends(get_current_user)
- Проверка доступа к дашборду
- Параметры фильтров: year, category, brand
- Ответы в формате JSON
- HTTP статусы: 200, 403, 404
- Кэширование результатов (опционально)

DONE:
- Эндпоинты возвращают агрегаты
- Фильтры работают корректно
- Проверки доступа применены
- Данные форматируются для графиков
- Тесты написаны