TASK: Реализация репозиториев для работы с БД

FILE: src/mko_bi/db/repositories/user_repo.py
FILE: src/mko_bi/db/repositories/dashboard_repo.py
FILE: src/mko_bi/db/repositories/access_repo.py

GOAL: Реализовать паттерн Repository для CRUD операций

IMPLEMENT:

class: UserRepository
class: DashboardRepository
class: AccessRepository

LOGIC:
- UserRepository: get, get_by_email, create, update, delete, get_session
- DashboardRepository: get, get_by_user, create, update, delete
- AccessRepository: grant_access, revoke_access, check_access, get_user_dashboards
- Все методы использовать SessionLocal для сессий
- Контекстный менеджер для автоматического закрытия сессий
- Обработка ошибок и возврат None при отсутствии записей

CONSTRAINTS:
- Использовать классовые методы (@classmethod)
- Сессии создавать внутри каждого метода
- Возвращать SQLAlchemy модели или None
- Для create возвращать созданную модель с id
- commit/rollback в соответствующих блоках

DONE:
- UserRepository с полным CRUD
- DashboardRepository с фильтрацией по пользователю
- AccessRepository для управления правами
- Все методы работают с сессиями корректно
- Тесты для репозиториев написаны