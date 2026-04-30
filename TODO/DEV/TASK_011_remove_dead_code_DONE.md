TASK: удаление мертвого кода

FILE: interfaces_old/, src/mko_bi/core/base_service.py, src/mko_bi/data/processing/base.py

GOAL: очистка от неиспользуемого кода

IMPLEMENT:

1. удалить папку interfaces_old/
2. удалить BaseService или реализовать validate_data()
3. проверить использование data/processing/base.py
   - если не используется - удалить
   - если используется - интегрировать
4. удалить неиспользуемые методы из интерфейсов:
   - IRepository.get_session()
   - IAggregatedDataRepository.create_bulk()

LOGIC:

найти все неиспользуемые файлы и код
удалить или интегрировать
проверить что ничего не сломалось

CONSTRAINTS:

удалять только неиспользуемый код
проверить все импорты

DONE:

мертвый код удален
нет неиспользуемых файлов
все тесты проходят
