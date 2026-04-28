TASK: Создать базовые классы и утилиты для уменьшения дублирования

FILE: src/mko_bi/core/base_repository.py, src/mko_bi/core/base_service.py, src/mko_bi/utils/validators.py, src/mko_bi/utils/decorators.py

GOAL: Вынести общие паттерны в базовые классы и утилиты для соблюдения DRY

IMPLEMENT:

class: BaseRepository - CRUD операции
class: BaseService - общая логика сервисов
func: validate_email()
func: validate_role()
func: error_handler()

LOGIC:

1. BaseRepository:
   - Generic тип для модели
   - Методы: get, get_all, create, update, delete
   - Фильтрация, пагинация
   - Обработка ошибок
2. BaseService:
   - Репозиторий как зависимость
   - Общая логика валидации
   - Обработка транзакций
   - Кэширование (опционально)
3. Валидаторы:
   - Проверка email
   - Проверка роли
   - Проверка UUID
   - Проверка строк
4. Декораторы:
   - timing - замер времени
   - retry - повтор при ошибке
   - log_execution - логирование
   - require_role - проверка прав

CONSTRAINTS:

- Не переусложнять базовые классы
- Оставить возможность переопределения
- Документировать публичный API
- Использовать Generic типы
- Соблюдать принцип открытости/закрытости

DONE:

- Базовые классы реализованы
- Утилиты для валидации
- Декораторы для повторяющихся паттернов
- Уменьшено дублирование
- Улучшена читаемость

