# Model Refactor Plan - CORRECTED (Flat Structure)

## Анализ текущей ситуации

### Проблемы (выявленные в TASK_027):
1. **Смешение доменов в user_roles.py**: GraphTypeEnum, OrientationEnum, BarmodeEnum, YoyModeEnum — это не роли пользователей, а типы графиков
2. **data.py — слишком большой**: содержит модели загрузки, обработки, графиков, фильтров и аналитики
3. **Дублирование в auth.py**: AccessCheck и AccessGrant дублируют access.py
4. **Жесткая связанность**: Все зависят от user_roles.py
5. **Нарушение SRP**: Один файл — слишком много ответственностей

### Ошибки в оригинальном плане (TASK_027):
- Создает вложенные директории (violates flat structure constraint)
- Создает schemas.py везде (избыточно — Pydantic модели уже схемы)
- Оverengineering: 6 пакетов для текущего масштаба
- Нарушает ограничение: "Файлы моделей должны оставться в папке models"

---

## Целевая структура (FLAT - без вложенностей)

```
src/mko_bi/models/
├── __init__.py                    # Экспорт всех моделей
├── access.py                      # Модели доступа (уже хорошо)
├── auth_models.py                 # Аутентификация: LoginRequest, Token и т.д.
├── user_models.py                 # Пользователи: UserBase, UserCreate и т.д.
├── role_enums.py                  # Роли и права: UserRoleEnum, PermissionEnum
├── chart_enums.py                 # Типы графиков: GraphTypeEnum, OrientationEnum, BarmodeEnum, YoyModeEnum
├── dashboard_models.py            # Дашборды: DashboardConfig, DashboardCreate и т.д.
├── chart_models.py                # Графики: ChartConfig, ChartData, ChartDataRequest, FilterState
├── upload_models.py               # Загрузка файлов: DataUpload, UploadResponse
├── processing_models.py           # Обработка: ProcessingStatus, ProcessingConfig, ProcessingResult
├── loader_models.py               # Загрузчик/валидация: LoaderConfig, ValidationResult
├── analytics_models.py            # Аналитика: AggregatedData
└── filter_models.py               # Фильтры: DataFilter
```

**Принципы:**
- Все файлы плоские (flat) — нет вложенных директорий
- Нет избыточных schemas.py — Pydantic модели уже выполняют эту роль
- Четкое разделение по предметным областям
- Минимум изменений, максимум пользы

---

## План изменений (последовательность)

### Шаг 1: Создание новых файлов моделей (пустых)
Создать следующие файлы в `src/mko_bi/models/`:
- `auth_models.py`
- `user_models.py`
- `role_enums.py`
- `chart_enums.py`
- `dashboard_models.py`
- `chart_models.py`
- `upload_models.py`
- `processing_models.py`
- `loader_models.py`
- `analytics_models.py`
- `filter_models.py`

### Шаг 2: Перенос Enum типов
**Из user_roles.py → chart_enums.py:**
- GraphTypeEnum
- OrientationEnum
- BarmodeEnum
- YoyModeEnum

**Из user_roles.py → role_enums.py:**
- UserRoleEnum (остается)
- PermissionEnum (остается)

**Результат:** user_roles.py удаляется (весь контент перенесен)

### Шаг 3: Перенос моделей аутентификации
**Из auth.py → auth_models.py:**
- LoginRequest
- RegisterRequest
- Token
- TokenData
- RefreshRequest

**Из auth.py удалить:**
- AccessCheck (дубликат из access.py)
- AccessGrant (дубликат из access.py)

**auth.py после изменений:** Очищается полностью (все модели перенесены)

### Шаг 4: Перенос моделей пользователей
**Из user.py → user_models.py:**
- UserBase
- UserCreate
- UserRead
- UserDB
- UserUpdate

**user.py после изменений:** Очищается полностью

### Шаг 5: Перенос моделей дашбордов
**Из dashboard.py → dashboard_models.py:**
- DashboardConfig
- DashboardCreate
- DashboardRead
- DashboardUpdate

**dashboard.py после изменений:** Очищается полностью

### Шаг 6: Перенос моделей графиков и фильтров
**Из data.py → chart_models.py:**
- ChartConfig
- ChartData
- ChartDataRequest
- FilterState

**Из data.py → filter_models.py:**
- DataFilter

### Шаг 7: Перенос моделей загрузки
**Из data.py → upload_models.py:**
- DataUpload
- UploadResponse

### Шаг 8: Перенос моделей обработки
**Из data.py → processing_models.py:**
- ProcessingStatus
- ProcessingConfig
- ProcessingResult

### Шаг 9: Перенос моделей загрузчика/валидации
**Из data.py → loader_models.py:**
- LoaderConfig
- ValidationResult

### Шаг 10: Перенос моделей аналитики
**Из data.py → analytics_models.py:**
- AggregatedData

### Шаг 11: Очистка data.py
**data.py после изменений:** Удаляется (все модели перенесены)

### Шаг 12: Обновление __init__.py
Обновить `src/mko_bi/models/__init__.py`:
- Импортировать все модели из новых файлов
- Обновить __all__ список
- Удалить импорты из старых файлов (user_roles, data, auth, user, dashboard)

### Шаг 13: Обновление импортов в кодовой базе
Обновить импорты во всех Python файлах проекта:

| Старый импорт | Новый импорт |
|---------------|-------------|
| `from mko_bi.models.user_roles import ...` | `from mko_bi.models.role_enums import ...` или `from mko_bi.models.chart_enums import ...` |
| `from mko_bi.models.data import ...` | Соответствующий файл (chart_models, upload_models и т.д.) |
| `from mko_bi.models.auth import ...` | `from mko_bi.models.auth_models import ...` |
| `from mko_bi.models.user import ...` | `from mko_bi.models.user_models import ...` |
| `from mko_bi.models.dashboard import ...` | `from mko_bi.models.dashboard_models import ...` |
| `from mko_bi.models.access import ...` | Остается без изменений |

### Шаг 14: Удаление старых файлов
Удалить следующие файлы:
- `src/mko_bi/models/user_roles.py` (перенесено в role_enums.py и chart_enums.py)
- `src/mko_bi/models/data.py` (перенесено в специализированные файлы)
- `src/mko_bi/models/auth.py` (перенесено в auth_models.py)
- `src/mko_bi/models/user.py` (перенесено в user_models.py)
- `src/mko_bi/models/dashboard.py` (перенесено в dashboard_models.py)

### Шаг 15: Проверка и валидация
- Запустить тесты: `pytest`
- Проверить импорты: `python -c "from mko_bi.models import *"`
- Проверить циклические зависимости
- Убедиться, что все API эндпоинты работают

---

## Маппинг моделей (детальный)

| Модель | Старый файл | Новый файл |
|--------|-------------|------------|
| UserRoleEnum | user_roles.py | role_enums.py |
| PermissionEnum | user_roles.py | role_enums.py |
| GraphTypeEnum | user_roles.py | chart_enums.py |
| OrientationEnum | user_roles.py | chart_enums.py |
| BarmodeEnum | user_roles.py | chart_enums.py |
| YoyModeEnum | user_roles.py | chart_enums.py |
| LoginRequest | auth.py | auth_models.py |
| RegisterRequest | auth.py | auth_models.py |
| Token | auth.py | auth_models.py |
| TokenData | auth.py | auth_models.py |
| RefreshRequest | auth.py | auth_models.py |
| AccessCheck (auth.py) | auth.py | УДАЛИТЬ (дубликат) |
| AccessGrant (auth.py) | auth.py | УДАЛИТЬ (дубликат) |
| UserBase | user.py | user_models.py |
| UserCreate | user.py | user_models.py |
| UserRead | user.py | user_models.py |
| UserDB | user.py | user_models.py |
| UserUpdate | user.py | user_models.py |
| DashboardConfig | dashboard.py | dashboard_models.py |
| DashboardCreate | dashboard.py | dashboard_models.py |
| DashboardRead | dashboard.py | dashboard_models.py |
| DashboardUpdate | dashboard.py | dashboard_models.py |
| ChartConfig | data.py | chart_models.py |
| ChartData | data.py | chart_models.py |
| ChartDataRequest | data.py | chart_models.py |
| FilterState | data.py | chart_models.py |
| DataUpload | data.py | upload_models.py |
| UploadResponse | data.py | upload_models.py |
| ProcessingStatus | data.py | processing_models.py |
| ProcessingConfig | data.py | processing_models.py |
| ProcessingResult | data.py | processing_models.py |
| LoaderConfig | data.py | loader_models.py |
| ValidationResult | data.py | loader_models.py |
| AggregatedData | data.py | analytics_models.py |
| DataFilter | data.py | filter_models.py |
| AccessCheck (access.py) | access.py | access.py (остается) |
| AccessGrant (access.py) | access.py | access.py (остается) |

---

## Ожидаемые результаты

### Улучшения:
1. ✅ **Нет смешения доменов**: Каждый файл — одна ответственность
2. ✅ **Простая структура**: Flat, без избыточных вложенностей
3. ✅ **Понятные импорты**: Четкое соответствие файл-сущность
4. ✅ **Легче масштабировать**: Добавление новых моделей не усложняет существующие файлы
5. ✅ **Устранены дубликаты**: AccessCheck/AccessGrant только в access.py
6. ✅ **Нет overengenerinng**: Только необходимое разделение

### Сохранено:
- Все модели на месте (только перемещены)
- Бизнес-логика не изменена
- API интерфейсы не изменены
- Структура БД не изменена
- Все тесты должны проходить

---

## Контрольные точки

1. После Шага 2: Проверить, что chart_enums.py и role_enums.py корректно импортируются
2. После Шага 12: Проверить __init__.py — все экспорты должны работать
3. После Шага 13: Запустить тесты — импорты во всех файлах должны быть исправлены
4. После Шага 15: `pytest` должен пройти успешно

---

## Важные замечания

### Почему НЕ создаем вложенные директории:
1. Нарушает ограничение задачи: "Файлы моделей должны оставться в папке models"
2. Избыточно для текущего масштаба (11 файлов — это не много)
3. Усложняет импорты: `from mko_bi.models.charts.models import ...` вместо `from mko_bi.models.chart_models import ...`
4. Противоречит принципу KISS

### Почему НЕ создаем schemas.py:
1. Pydantic BaseModel уже является схемой
2. Дублирование файлов без необходимости
3. Усложняет поддержку (нужно поддерживать две сущности вместо одной)
4. В текущей кодовой базе нет потребности в разделении models/schemas

### Почему access.py остается без изменений:
1. Уже имеет четкую ответственность (только доступ)
2. Только 2 простые модели
3. Нет признаков domain mixing
4. Импортируется в DB моделей — лучше не трогать

### Почему удаляем user_roles.py полностью:
1. Весь контент (роли и типы графиков) разделен по правильным файлам
2. Не остается причин для его существования
3. Упрощает навигацию

---

## Риски и Mitigation

| Риск | Вероятность | Уровень | Mitigation |
|------|-------------|---------|------------|
| Циклические импорты | Низкая | 🟢 | Проверить после каждого шага |
| Неправильные импорты в DB моделях | Средняя | 🟡 | Внимательно проверить все TYPE_CHECKING импорты |
| Битые тесты | Средняя | 🟡 | Запустить pytest после каждого этапа |
| Забыть обновить импорт в каком-то файле | Высокая | 🟠 | Использовать grep для поиска всех импортов перед началом |

---

## Метрики успеха

- [ ] 0 дубликатов моделей
- [ ] 0 файлов со смешением доменов
- [ ] Все файлы в папке models/ (без вложенностей)
- [ ] Нет избыточных schemas.py
- [ ] Все тесты проходят (pytest)
- [ ] Импорты в порядке (mypy/pyright если есть)
- [ ] DB модели работают корректно
- [ ] API эндпоинты функционируют

---

## Примечания по импорту в DB моделях

Особое внимание нужно уделить TYPE_CHECKING импортам в `db/models/`:
- `db/models/user.py` импортирует из `mko_bi.models.user_roles` и `mko_bi.models.access`
- `db/models/dashboard.py` импортирует из `mko_bi.models.access`, `mko_bi.models.layout`, `mko_bi.models.graphs`, `mko_bi.models.aggregated_data`
- `db/models/access.py` импортирует из `mko_bi.models.user_roles`

Эти импорты нужно обновить:
- `user_roles` → `role_enums` или `chart_enums` (в зависимости от конкретного Enum)
- Остальные остаются без изменений (это DB модели, а не Pydantic)

---

*План разработан с учетом ограничений: flat структура, без overengenerinng, без изменения бизнес-логики.*
