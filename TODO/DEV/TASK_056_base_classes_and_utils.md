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

- [x] Создан src/mko_bi/core/base_repository.py с классом BaseRepository (Generic)
  - CRUD операции: get, get_all, create, update, delete
  - Фильтрация через filter_by
  - Пагинация в get_all
  - Обработка ошибок SQLAlchemy
- [x] Создан src/mko_bi/core/base_service.py с классом BaseService (Generic)
  - Репозиторий как зависимость
  - Общие методы: get_by_id, get_all, create, update, delete
  - Метод _to_dict для преобразования в словарь
  - Метод validate_data для переопределения
- [x] Создан src/mko_bi/utils/validators.py с функциями валидации:
  - validate_email() - проверка формата email
  - validate_role() - проверка роли через UserRoleEnum
  - validate_uuid() - проверка UUID
  - validate_string() - проверка строк с параметрами min/max length
  - validate_password() - проверка сложности пароля
  - raise_if_invalid() - выброс исключения при невыполнении условия
- [x] Создан src/mko_bi/utils/decorators.py с декораторами:
  - @timing - замер времени выполнения
  - @retry - повтор при ошибке с настраиваемыми параметрами
  - @log_execution - логирование выполнения
  - @require_role - проверка прав доступа
  - @error_handler - обработка ошибок с fallback значением
- [x] Уменьшено дублирование через базовые классы
- [x] Улучшена читаемость и поддерживаемость кода

