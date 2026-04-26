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
    - UserRepository: get, get_by_email, create, update, delete
    - DashboardRepository: get, get_by_user, create, update, delete
    - AccessRepository: grant_access, revoke_access, check_access, get_user_dashboards
    - Все методы используют SessionLocal для сессий
    - Сессии создаются внутри каждого метода и закрываются в блоке finally
    - Обработка ошибок и возврат None при отсутствии записей
    
    CONSTRAINTS:
    - Использовать классовые методы (@classmethod)
    - Сессии создавать внутри каждого метода
    - Возвращать SQLAlchemy модели или None
    - Для create возвращать созданную модель с id
    - commit/rollback в соответствующих блоках
    - Корректное закрытие сессий в блоке finally

DONE:
- UserRepository с полным CRUD
- DashboardRepository с фильтрацией по пользователю
- AccessRepository для управления правами
- Все методы работают с сессиями корректно
- Тесты для репозиториев написаны

Тесты: нужны только глубоко тестирующие бизнес-логику.