# Единый план рефакторинга моделей (финальный)

## Целевая структура (плоская)

```
src/mko_bi/models/
├── __init__.py
├── access.py          # оставляем как есть (AccessCheck, AccessGrant, PermissionEnum)
├── auth.py            # модели аутентификации (LoginRequest, RegisterRequest, Token, TokenData, RefreshRequest)
├── users.py           # пользователи + UserRoleEnum
├── dashboards.py      # дашборды (DashboardConfig, DashboardCreate, DashboardRead, DashboardUpdate)
├── charts.py          # графики + все enum-ы графиков (GraphTypeEnum, OrientationEnum, BarmodeEnum, YoyModeEnum, ChartConfig, ChartData, ChartDataRequest)
├── data_processing.py # загрузка, обработка, валидация, фильтры (DataUpload, UploadResponse, ProcessingStatus, ProcessingConfig, ProcessingResult, LoaderConfig, ValidationResult, DataFilter)
└── analytics.py       # агрегированные данные (AggregatedData)
```

## Последовательность шагов

### Шаг 1. Создание новых файлов (пустых)
```bash
src/mko_bi/models/new_access.py  
src/mko_bi/models/new_auth.py
src/mko_bi/models/new_users.py
src/mko_bi/models/new_dashboards.py
src/mko_bi/models/new_charts.py
src/mko_bi/models/new_data_processing.py
src/mko_bi/models/new_analytics.py
```

### Шаг 2. Перенос Enum-ов (база для всех моделей)
- **Из `user_roles.py` в `new_users.py`**  
  Скопировать `UserRoleEnum`
- **Из `user_roles.py` в `new_charts.py`**  
  Скопировать `GraphTypeEnum`, `OrientationEnum`, `BarmodeEnum`, `YoyModeEnum`
- **`PermissionEnum`** –  в `new_access.py` 
- **`user_roles.py`** после копирования очистить (позже удалить)

### Шаг 3. Перенос моделей аутентификации
**Из `auth.py` в `new_auth.py` (новый):**
- `LoginRequest`
- `RegisterRequest`
- `Token`
- `TokenData`
- `RefreshRequest`
- перенос импортов, кроме mko_bi.models

**Новый `new_auth.py` должен импортировать `UserRoleEnum` из `new_users.py` для `RegisterRequest`.**

### Шаг 4. Перенос моделей пользователей
**Из `user.py` в `new_users.py`:**
- `UserBase`
- `UserCreate`
- `UserRead`
- `UserDB`
- `UserUpdate`
- перенос импортов кроме mko_bi.models

### Шаг 5. Перенос моделей дашбордов
**Из `dashboard.py` в `new_dashboards.py`:**
- `DashboardConfig`
- `DashboardCreate`
- `DashboardRead`
- `DashboardUpdate`
-  перенос импортов кроме mko_bi.models

**В `new_dashboards.py` импортировать `GraphTypeEnum` из `new_charts.py` (для `DashboardConfig.graph_types`).**

### Шаг 6. Перенос моделей графиков
**Из `data.py` в `new_charts.py`:**
- `ChartConfig`
- `ChartData`
- `ChartDataRequest`
- перенос импортов кроме mko_bi.models

### Шаг 7. Перенос моделей обработки данных
**Из `data.py` в `new_data_processing.py`:**
- `DataUpload`
- `UploadResponse`
- `ProcessingStatus`
- `ProcessingConfig`
- `ProcessingResult`
- `LoaderConfig`
- `ValidationResult`
- `DataFilter`
- перенос импортов кроме mko_bi.models

### Шаг 8. Перенос моделей аналитики
**Из `data.py` в `new_analytics.py`:**
- `AggregatedData`

**В `analytics.py` импортировать `GraphTypeEnum` из `charts.py` (если нужно).
- перенос импортов кроме mko_bi.models

### Шаг 9. Перенос моделей доступа
**Из `access.py` в `new_access.py`:**
- `AccessCheck`
- `AccessGrant`
- перенос импортов кроме mko_bi.models

### Шаг 10. Очистка и удаление старых файлов
- **Удалить** (после переноса всех моделей):
  - `user_roles.py`
  - `user.py`
  - `dashboard.py`
  - `data.py`
  - `auth.py`
  - `access.py`

### Шаг 11. Переименование файлов
- `new_auth.py` → `auth.py`
- `new_users.py` → `users.py`
- `new_dashboards.py` → `dashboards.py`
- `new_charts.py` → `charts.py`
- `new_data_processing.py` → `data_processing.py`
- `new_analytics.py` → `analytics.py`
- `new_access.py` → `access.py`

## Шаг 12: Обновление точки входа (__init__.py)

**Действие:** Обновить `src/mko_bi/models/__init__.py`

**Новое содержимое:**
```python
# Экспорт всех моделей по предметным областям

# Аутентификация
 .auth 
# Пользователи
.users 

# Дашборды
.dashboards

# Графики
 .charts 
# Обработка данных
 .data_processing

# Аналитика
.analytics 

# Доступ (оставляем как есть - уже хорошо)
 .access 

# Общий экспорт для удобства
__all__ = [
    # Auth
   ....
    # Users
    ...
    # Dashboards
  ..
    # Charts
    ..
    # Data Processing
   ..
    # Analytics
  ..
    # Access
    ...
]
```

**Проверка:**
- Все модели доступны через `mko_bi.models`
- Четкая структура экспорта

---
### Шаг 13. Обновление импортов во всей кодовой базе

**Действие:** Найти и заменить все импорты старых моделей на новые

**Скрипт для поиска (bash):**
```bash
# Найти все импорты из старых файлов
grep -r "from mko_bi.models\." src/mko_bi/ --include="*.py" | grep -E "(auth|user|dashboard|data)\.py" | sort -u
```

**Рекомендация:** использовать grep + sed для автоматической замены, но с осторожностью.

### Шаг 14. Проверка работоспособности
- **Проверка циклических импортов:**  
  `python -c "from mko_bi.models import *"`
- **Запуск тестов:**  
  `pytest tests/`
- **Проверка отсутствия старых импортов:**  
  ```bash
  grep -r "from mko_bi.models\.user_roles" src/ || echo "OK"
  grep -r "from mko_bi.models\.user import" src/ || echo "OK"
  grep -r "from mko_bi.models\.dashboard import" src/ || echo "OK"
  grep -r "from mko_bi.models\.data import" src/ || echo "OK"
  ```

### Шаг 15. Финальная очистка
- Убедиться, что старые файлы удалены.
- Убедиться, что все импорты ведут в новые файлы.

### Шаг 16. Проверка работоспособности

### Шаг 17. Переименование файла плана в *_done.md

## Контрольные точки выполнения

- [ ] Шаг 1 – новые файлы созданы.
- [ ] Шаг 2 – Enum-ы перенесены, `user_roles.py` очищен.
- [ ] Шаг 3 – модели аутентификации перенесены, дубликаты удалены.
- [ ] Шаг 4 – модели пользователей перенесены.
- [ ] Шаг 5 – модели дашбордов перенесены.
- [ ] Шаг 6 – модели графиков перенесены.
- [ ] Шаг 7 – модели обработки данных перенесены.
- [ ] Шаг 8 – модели аналитики перенесены.
- [ ] Шаг 9 – `__init__.py` обновлён.
- [ ] Шаг 10 – старые файлы удалены.
- [ ] Шаг 11 – все импорты обновлены.
- [ ] Шаг 12 – тесты проходят, циклических импортов нет.
- [ ] Шаг 13 – код готов к слиянию.

## Ожидаемые результаты

- **Нет смешения доменов** – каждая предметная область в своём файле.
- **Нет дубликатов** – `AccessCheck` / `AccessGrant` только в `access.py`.
- **Плоская структура** – без вложенных папок и `schemas.py`.
- **Простота навигации** – разработчик сразу понимает, где искать нужную модель.
- **Все тесты проходят** – рефакторинг не ломает бизнес-логику.