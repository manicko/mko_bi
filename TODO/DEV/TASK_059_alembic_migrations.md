TASK: Настроить Alembic миграции для управления схемой БД

FILE: alembic/, .env.example

GOAL: Настроить систему миграций для управления изменениями схемы базы данных

IMPLEMENT:

func: init_alembic()
func: create_migration()
func: upgrade()
func: downgrade()

LOGIC:

1. Инициализация Alembic:
   - alembic init alembic
   - Настройка env.py
   - Подключение к БД
2. Конфигурация:
   - alembic.ini - настройки
   - env.py - автогенерация моделей
   - script.py.mako - шаблон миграций
3. Миграции:
   - Создать миграции для существующих таблиц
   - Добавить индексы
   - Настроить downgrade
4. Процесс:
   - alembic revision --autogenerate
   - alembic upgrade head
   - Проверка миграций

CONSTRAINTS:

- Автогенерация где возможно
- Корректные downgrade
- Не терять данные при миграциях
- Документация процесса
- Скрипты для CI/CD

DONE:

- Alembic настроен
- Миграции созданы
- Можно обновлять схему
- Можно откатывать миграции
- Процесс документирован
- Интеграция с CI/CD
