TASK: API управления дашбордами

FILE: src/mko_bi/api/routes/dashboards.py

GOAL: Создать эндпоинты для CRUD операций с дашбордами

IMPLEMENT:

router: APIRouter с prefix="/dashboards"

@endpoint: POST /dashboards
@endpoint: GET /dashboards
@endpoint: GET /dashboards/{dashboard_id}
@endpoint: PUT /dashboards/{dashboard_id}
@endpoint: DELETE /dashboards/{dashboard_id}
@endpoint: POST /dashboards/{dashboard_id}/access

LOGIC:
- POST /dashboards: создать дашборд (автор = текущий пользователь)
- GET /dashboards: список доступных пользователю дашбордов
- GET /dashboards/{id}: получить дашборд с проверкой доступа
- PUT /dashboards/{id}: обновить конфигурацию
- DELETE /dashboards/{id}: удалить дашборд
- POST /dashboards/{id}/access: выдать доступ пользователю

CONSTRAINTS:
- Защита через Depends(get_current_user)
- Проверка доступа для всех операций
- Только владелец может обновлять/удалять
- Конфигурация в формате JSON
- HTTP статусы: 200, 201, 204, 403, 404

DONE:
- Эндпоинты созданы
- CRUD операции работают
- Проверки доступа реализованы
- Управление правами работает
- Тесты покрывают все сценарии

Тесты: нужны только глубоко тестирующие бизнес-логику.