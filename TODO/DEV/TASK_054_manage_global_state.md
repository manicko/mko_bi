TASK: Управление глобальным состоянием и сессиями БД

FILE: src/mko_bi/config.py, src/mko_bi/db/session.py, src/mko_bi/services/data_service.py

GOAL: Убрать глобальное состояние, использовать контекстный менеджмент для сессий БД

IMPLEMENT:

func: get_config() - использовать pydantic-settings
func: get_db_session() - контекстный менеджер
func: Удалить _task_statuses - перенести в БД

LOGIC:

1. В config.py:
   - Использовать pydantic-settings
   - Валидация всех переменных
   - Обязательные поля
   - Преобразование типов
2. В db/session.py:
   - Контекстный менеджер для сессий
   - Гарантированное закрытие
   - Использовать with get_db_session() as db:
3. В data_service.py:
   - Удалить глобальный _task_statuses
   - Использовать таблицу processing_logs
   - Сохранять статусы в БД
4. Удалить глобальные переменные:
   - config = Config() → использовать get_config()
   - _task_statuses → использовать БД
   - engine, SessionLocal → через контекст

CONSTRAINTS:

- Нет глобального состояния
- Сессии БД в контекстных менеджерах
- 100% гарантия закрытия сессий
- Конфигурация через env-переменные
- Потокобезопасность
- Нет race conditions

DONE:

- Нет глобальных переменных
- Сессии гарантированно закрываются
- Конфигурация через env
- Статусы в БД
- Нет утечек памяти
- Потокобезопасно
