---
## MYPY TYPE ERRORS FIX
---

### TASK: Устранение ошибок mypy (235 ошибок)

FILE: `src/mkobi/**/*.py`, `tests/**/*.py`

GOAL: Исправить все ошибки типизации для прохождения `uv run mypy .`

FINDINGS (TASK_02 + TASK_03 + actual check):
- 235 ошибок mypy
- Категории ошибок:
  1. Return type errors: `Returning Any from function declared to return "..."`
  2. Unused "type: ignore" comments
  3. Type annotation issues: `Need type annotation for "prepared"`
  4. Argument type mismatches: UUID vs int
  5. Attr-defined errors: `YoyModeEnum` has no attribute `percent`

IMPLEMENT (по приоритету):

#### Step 1: Исправление unused type: ignore
* Найти файлы с неиспользуемыми `type: ignore`
* Удалить или заменить на корректные аннотации
* Файлы: `dashboard_filter_repo.py`, `processing_config_repo.py`, `filter_repo.py`

#### Step 2: Исправление обращения к атрибутам enum
* `YoyModeEnum.percent` → `YoyModeEnum.PERCENT`
* Проверить все обращения к enum атрибутам

#### Step 3: Исправление возвращаемых типов в репозиториях
* Добавить явное приведение типов после `execute().scalar()`
* Использовать `cast()` или проверки типов

#### Step 4: Исправление UUID vs int mismatches
* Проверить API роуты на корректность типов параметров
* Привести типы к единому виду (UUID)

#### Step 5: Добавление аннотаций типов
* Добавить аннотации для переменных с `Need type annotation`

DONE:

* [ ] `uv run mypy .` проходит без ошибок (или допустимое количество)
* [ ] Return type errors устранены
* [ ] UUID vs int mismatches исправлены
* [ ] Enum attribute access исправлен

---
