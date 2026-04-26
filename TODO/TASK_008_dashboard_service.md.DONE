TASK: Сервис управления дашбордами

FILE: src/mko_bi/services/dashboard_service.py

GOAL: Реализовать бизнес-логику для CRUD операций с дашбордами

IMPLEMENT:

func: create_dashboard(name: str, config: dict, owner_id: int, db: Session) -> DashboardRead
func: get_dashboard(dashboard_id: int, user_id: int, db: Session) -> Optional[DashboardRead]
func: get_user_dashboards(user_id: int) -> List[DashboardRead]
func: update_dashboard(dashboard_id: int, config: dict, db: Session) -> Optional[DashboardRead]
func: delete_dashboard(dashboard_id: int) -> bool
func: grant_access(dashboard_id: int, user_id: int, permission: str, db: Session) -> bool

LOGIC:
- create_dashboard: создание дашборда с владельцем
- get_dashboard: проверка доступа перед возвратом
- get_user_dashboards: фильтрация по доступам
- update_dashboard: обновление конфигурации
- delete_dashboard: каскадное удаление доступов
- grant_access: выдача прав пользователю на дашборд

CONSTRAINTS:
- Проверка прав доступа для всех операций
- Только владелец может обновлять/удалять
- Конфигурация в формате JSON
- permission: read/write/admin
- Логирование всех операций
- create_dashboard, get_dashboard, update_dashboard, grant_access принимают сессию БД (db) как параметр

DONE:
- CRUD для дашбордов реализован
- Управление доступами работает
- Проверки прав применены
- Логирование добавлено
- Тесты написаны

Тесты: нужны только глубоко тестирующие бизнес-логику.