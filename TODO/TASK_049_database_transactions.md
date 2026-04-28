TASK: Добавить транзакции для связанных операций БД

FILE: src/mko_bi/services/dashboard_service.py, src/mko_bi/services/data_service.py, src/mko_bi/services/auth_service.py

GOAL: Обеспечить атомарность операций, требующих изменения нескольких таблиц

IMPLEMENT:

func: create_dashboard() - с транзакцией
func: update_dashboard_access() - с транзакцией
func: process_csv_data() - с транзакцией
func: register_user() - с транзакцией

LOGIC:

1. В dashboard_service.py:
   - Создание дашборда + прав доступа в одной транзакции
   - Откат при ошибке создания прав
   - Использовать db.begin() / try-except / rollback
2. В data_service.py:
   - Удаление старых агрегатов + вставка новых в транзакции
   - Обработка ошибок сохранения
   - Полный откат при сбое
3. В auth_service.py:
   - Регистрация пользователя в транзакции
   - Создание профиля/доп. данных
4. Шаблон:
   ```python
   with db.begin():
       # операции
       # при ошибке - автоматический rollback
   ```

CONSTRAINTS:

- Использовать контекстный менеджер db.begin()
- Явный rollback при исключениях
- Логирование успешных коммитов
- Не использовать autocommit для критичных операций
- Сохранять целостность данных

DONE:

- Критические операции в транзакциях
- Нет частичных обновлений
- Откат при ошибках
- Данные всегда консистентны

