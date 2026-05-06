---
## ENUM CONSISTENCY & CLEANUP
---

### TASK: Унификация использования StrEnum

FILE: `src/mkobi/models/enums.py`, `src/mkobi/models/user_roles.py`, `src/mkobi/core/permissions.py`

GOAL: Перейти на единый источник истины для enum (enums.py), убрать путаницу с user_roles.py

FINDINGS (TASK_02 + TASK_03):
- `user_roles.py` создает алиасы (UserRoleEnum, PermissionEnum и др.)
- 39 файлов импортируют из `user_roles.py` вместо `enums.py`
- `permissions.py` импортирует из `mkobi.models.user_roles` (строка 29)
- Используется `ROLE_LEVELS` словарь вместо прямого сравнения StrEnum

DECISION: Сохранить `user_roles.py` для обратной совместимости, но:
- Перенести все импорты на `enums.py` в новом коде
- `user_roles.py` оставить как re-export (уже реализовано корректно)
- В `permissions.py` исправить импорт для консистентности

IMPLEMENT:

* В `permissions.py` заменить импорт на `from mkobi.models.enums import UserRole, UserRoleEnum`
* Обновить типы аргументов функций на `UserRole` вместо `str`
* Документировать в коде, что `user_roles.py` - для обратной совместимости

DONE:

* [ ] Импорты в `permissions.py` исправлены
* [ ] Типы аргументов обновлены на `UserRole`
* [ ] Код использует единый стиль enum

---

### TASK: Исправление использования FilterOperatorEnum

FILE: `src/mkobi/data/processing/transformations.py`

GOAL: Использовать FilterOperatorEnum вместо строковых литералов

FINDINGS (TASK_03):
- Строка 137: используются строковые литералы `"eq"` и `"ne"` вместо `FilterOperatorEnum.EQ.value`

IMPLEMENT:

* Заменить `"eq"` на `FilterOperatorEnum.EQ.value`
* Заменить `"ne"` на `FilterOperatorEnum.NE.value`
* Проверить другие места на использование строковых литералов для enum

DONE:

* [ ] FilterOperatorEnum используется последовательно
* [ ] Строковые литералы заменены

---
