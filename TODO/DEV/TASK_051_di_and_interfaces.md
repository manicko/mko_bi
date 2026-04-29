TASK: Устранить циклические зависимости и внедрить Dependency Injection

FILE: src/mko_bi/interfaces/, src/mko_bi/core/permissions.py, src/mko_bi/api/deps.py

GOAL: Устранить циклические импорты, внедрить DI для улучшения тестируемости и гибкости

IMPLEMENT:

func: IUserRepository (интерфейс)
func: IDashboardRepository (интерфейс)
func: IDataService (интерфейс)
func: get_user_repository() - DI factory

LOGIC:

1. Создать interfaces/:
   - repository_interfaces.py: ABC для всех репозиториев
   - service_interfaces.py: ABC для сервисов
2. Реализовать интерфейсы:
   - IUserRepository: методы для работы с пользователями
   - IDashboardRepository: методы для дашбордов
   - IDataRepository: методы для агрегатов
3. Внедрение зависимостей:
   - deps.py: фабрики для создания репозиториев и сервисов
   - Использовать Depends() для инъекции
   - Контекстные менеджеры для сессий
4. Разорвать циклы:
   - permissions.py → использовать интерфейсы
   - services → инжектировать репозитории
   - api/routes → инжектировать сервисы

CONSTRAINTS:

- Нет циклических импортов
- Использовать абстрактные базовые классы
- DI через FastAPI Depends
- Интерфейсы для возможности замены реализаций
- Чистая архитектура (внешние слои зависят от внутренних)

DONE:

- Нет циклических зависимостей
- Внедрены интерфейсы
- Работает DI
- Улучшена тестируемость
- Можно заменять реализации
