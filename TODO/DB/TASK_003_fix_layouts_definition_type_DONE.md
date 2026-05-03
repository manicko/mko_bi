TASK: Исправить тип layouts.definition в ORM модели и базе данных с JSON на JSONB

FILE: src/mko_bi/alembic/versions/fix_layouts_definition_type.py

GOAL: Изменить тип столбца definition в таблице layouts с json на jsonb согласно SPEC.md, а также обновить ORM модель для использования JSONB вместо JSON.

IMPLEMENT:
- Обновить ORM модель в src/mko_bi/db/models/layout.py: заменить JSON на JSONB из sqlalchemy.dialects.postgresql
- Создать миграцию, которая изменяет тип столбца definition в таблице layouts на jsonb с использованием USING definition::jsonb
- Убедиться, что миграция применяется чисто на пустой базе данных (после истинной начальной миграции и миграции fixing aggregated_data.id)
- Добавить зависимость от предыдущих миграций в файл миграции

LOGIC:
- ORM модель должна использовать SQLAlchemy тип JSONB для столбца definition
- Миграция должна использовать ALTER TABLE для изменения типа столбца с json на jsonb
- После применения миграции, таблица layouts должна иметь столбец definition типа jsonb
- ORM модель должна соответствовать типу в базе данных

CONSTRAINTS:
- Миграция должна быть совместима с текущими моделями ORM (после обновления)
- Миграция не должна ломать существующие данные при применении
- Миграция должна быть откатной (предусмотреть downgrade)

DONE:
- ORM модель layouts.py использует JSONB вместо JSON
- Таблица layouts имеет столбец definition типа jsonb
- Миграция применяется чисто на пустой базе данных после предыдущих миграций
- Миграция имеет рабочий downgrade
- Все существующие тесты продолжают проходить после применения миграции