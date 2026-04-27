# Model Refactor Plan - CORRECTED (v2)

## Анализ текущего плана (TASK_027) - выявленные проблемы

### Критические недостатки текущего плана:
1. **Нарушение требования flat-структуры** - предлагается создать вложенные директории (auth/, users/, dashboards/ и т.д.), что противоречит ограничениям
2. **Создание schemas.py** - разделение на модели и схемы явно запрещено в ограничениях ("не делить на models/schemas")
3. **Оverengineering** - 6 вложенных папок вместо простых плоских файлов
4. **Дублирование сущностей** - AccessCheck/AccessGrant предлагается разнести по auth/schemas.py и оставить в access.py
5. **Отсутствие проверки импортов** - риск циклических зависимостей и сломанных импортов
6. **Нечеткий порядок миграции** - не указано, когда и как проверять работоспособность

## Целевая структура (Flat, No Overengineering)

```
src/mko_bi/models/
├── __init__.py              # Экспорт всех моделей
├── user_roles.py            # ENUM-ы (будет очищен от моделей)
├── access.py                # Модели доступа (уже хорошо, сохраняем)
├── auth.py                  # Модели аутентификации (чистый)
├── users.py                 # Модели пользователей
├── dashboards.py            # Модели дашбордов
├── charts.py                # Модели графиков + Enum-ы графиков
├── data_processing.py       # Модели обработки данных
└── analytics.py             # Модели аналитики/агрегатов
```

**Принципы:**
- Все файлы на одном уровне (flat)
- Нет вложенных директорий
- Нет разделения на models/schemas
- Четкое разделение по предметным областям
- Понятные имена файлов
- Легко масштабировать (просто добавлять новые файлы)

---

## Шаг 1: Создание пустых файлов

**Действие:** Создать новые файлы моделей (пустые)

```bash
# Создать новые файлы (touch/эквивалент)
src/mko_bi/models/auth.py          # новое
src/mko_bi/models/users.py         # новое
src/mko_bi/models/dashboards.py    # новое
src/mko_bi/models/charts.py        # новое
src/mko_bi/models/data_processing.py # новое
src/mko_bi/models/analytics.py     # новое
```

**Проверка:** Все файлы созданы, пустые (только импорты BaseModel если нужно)

---

## Шаг 2: Перенос Enum-ов (база для всех моделей)

**Действие:** Распределить Enum-ы по тематическим файлам, очистить user_roles.py

**Маппинг Enum-ов:**

| Enum | Текущий файл | Новый файл | Примечание |
|------|-------------|-----------|-----------|
| UserRoleEnum | user_roles.py | users.py | Роли пользователей |
| PermissionEnum | user_roles.py | access.py | Права доступа (уже в access.py) |
| GraphTypeEnum | user_roles.py | charts.py | Типы графиков |
| OrientationEnum | user_roles.py | charts.py | Ориентация графиков |
| BarmodeEnum | user_roles.py | charts.py | Режим столбчатых диаграмм |
| YoyModeEnum | user_roles.py | charts.py | Год-к-год сравнение |

**Операции:**
1. Скопировать UserRoleEnum в `users.py`
2. Скопировать GraphTypeEnum, OrientationEnum, BarmodeEnum, YoyModeEnum в `charts.py`
3. PermissionEnum ОСТАВИТЬ в `access.py` (уже там есть, импортируется везде)
4. Очистить `user_roles.py` - оставить ПУСТЫМ (или удалить позже)

**Проверка:** 
- Все Enum-ы доступны в новых файлах
- Старые импорты из user_roles.py еще работают (файл пока не удален)

---

## Шаг 3: Перенос моделей аутентификации

**Действие:** Перенести модели из auth.py в новый auth.py (чистый)

**Старые модели (удалить из auth.py):**
- LoginRequest
- RegisterRequest
- Token
- TokenData
- RefreshRequest

**Дублирующие модели (удалить из auth.py, оставить ТОЛЬКО в access.py):**
- AccessCheck (дублирует access.py) ❌ УДАЛИТЬ
- AccessGrant (дублирует access.py) ❌ УДАЛИТЬ

**Новый auth.py (содержимое):**
```python
from pydantic import BaseModel, ConfigDict, EmailStr
from uuid import UUID

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    # ... config ...

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: UserRoleEnum  # Импорт из users.py
    # ... config ...

class Token(BaseModel):
    access_token: str
    token_type: str
    # ... config ...

class TokenData(BaseModel):
    email: EmailStr | None = None
    user_id: UUID | None = None
    # ... config ...

class RefreshRequest(BaseModel):
    refresh_token: str
    # ... config ...
```

**Импорты в новом auth.py:**
```python
from mko_bi.models.users import UserRoleEnum  # для RegisterRequest
```

**Проверка:**
- Старый auth.py очищен (только AccessCheck/AccessGrant удалены)
- Новый auth.py содержит только аутентификационные модели
- Нет дублирования с access.py

---

## Шаг 4: Перенос моделей пользователей

**Действие:** Перенести модели из user.py в users.py

**Модели для переноса (из user.py):**
- UserBase
- UserCreate
- UserRead
- UserDB
- UserUpdate

**Новый users.py (содержимое):**
```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr
from uuid import UUID

class UserRoleEnum(StrEnum):  # Перенесен из user_roles.py
    admin = "admin"
    editor = "editor"
    viewer = "viewer"

class UserBase(BaseModel):
    email: EmailStr
    role: UserRoleEnum
    # ... config ...

class UserCreate(UserBase):
    password: str
    # ... config ...

class UserRead(UserBase):
    id: UUID
    created_at: datetime
    # ... config ...

class UserDB(UserBase):
    id: UUID
    password_hash: str
    created_at: datetime
    # ... config ...

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    role: UserRoleEnum | None = None
    password: str | None = None
    # ... config ...
```

**Старый user.py:** Очищен полностью

**Проверка:**
- Все модели пользователей в users.py
- Enum Role доступен локально
- Нет зависимости от старого user_roles.py

---

## Шаг 5: Перенос моделей дашбордов

**Действие:** Перенести модели из dashboard.py в dashboards.py

**Модели для переноса (из dashboard.py):**
- DashboardConfig
- DashboardCreate
- DashboardRead
- DashboardUpdate

**Новый dashboards.py (содержимое):**
```python
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict
from uuid import UUID

from mko_bi.models.charts import GraphTypeEnum  # Импорт из charts.py

class DashboardConfig(BaseModel):
    graph_types: list[GraphTypeEnum]
    filters: list[dict[str, Any]] | None = None
    aggregations: list[dict[str, Any]] | None = None
    charts: list[dict[str, Any]] | None = None
    title: str | None = None
    description: str | None = None
    # ... config ...

class DashboardCreate(BaseModel):
    name: str
    description: str | None = None
    config: DashboardConfig
    # ... config ...

class DashboardRead(BaseModel):
    id: UUID
    name: str
    description: str | None
    config: DashboardConfig
    created_at: datetime
    updated_at: datetime
    # ... config ...

class DashboardUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    config: DashboardConfig | None = None
    # ... config ...
```

**Старый dashboard.py:** Очищен полностью

**Проверка:**
- Импорт GraphTypeEnum из charts.py (пока файл пустой - Шаг 6)
- Все модели дашбордов в dashboards.py

---

## Шаг 6: Перенос моделей графиков

**Действие:** Перенести модели из data.py в charts.py + Enum-ы

**Enum-ы для переноса (из user_roles.py):**
- GraphTypeEnum
- OrientationEnum
- BarmodeEnum
- YoyModeEnum

**Модели для переноса (из data.py):**
- ChartConfig
- ChartData
- ChartDataRequest

**Новый charts.py (содержимое):**
```python
from enum import StrEnum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

# Enum-ы графиков
class GraphTypeEnum(StrEnum):
    bar = "bar"
    line = "line"
    pie = "pie"
    table = "table"

class OrientationEnum(StrEnum):
    vertical = "v"
    horizontal = "h"

class BarmodeEnum(StrEnum):
    group = "group"
    stack = "stack"

class YoyModeEnum(StrEnum):
    absolute = "absolute"
    percent = "percent"

# Модели графиков
class ChartConfig(BaseModel):
    x: str
    color: str | None = None
    metrics: list[str]
    orientation: OrientationEnum = OrientationEnum.vertical
    barmode: BarmodeEnum = BarmodeEnum.group
    secondary_y: list[str] = Field(default_factory=list)
    layout: dict[str, Any] = Field(default_factory=dict)
    yoy: dict[str, Any] | None = None
    # ... config ...

class ChartData(BaseModel):
    data: list[dict[str, Any]]
    # ... config ...

class ChartDataRequest(BaseModel):
    dashboard_id: UUID
    chart_ids: list[UUID] | None = None
    # ... config ...
```

**Старый user_roles.py:** Очищен (останутся только UserRoleEnum и PermissionEnum, но они перенесены)

**Проверка:**
- Все Enum-ы графиков в charts.py
- Все модели графиков в charts.py
- Нет зависимости от user_roles.py

---

## Шаг 7: Перенос моделей обработки данных

**Действие:** Перенести модели из data.py в data_processing.py

**Модели для переноса (из data.py):**
- DataUpload
- UploadResponse
- ProcessingStatus
- ProcessingConfig
- ProcessingResult
- LoaderConfig
- ValidationResult
- DataFilter

**Новый data_processing.py (содержимое):**
```python
from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from uuid import UUID

class DataUpload(BaseModel):
    file: bytes
    filename: str
    dashboard_id: int
    # ... config ...

class UploadResponse(BaseModel):
    task_id: UUID
    filename: str
    dashboard_id: int
    status: str
    message: str
    uploaded_at: datetime
    # ... config ...

class ProcessingStatus(BaseModel):
    task_id: UUID
    filename: str
    dashboard_id: int
    status: str
    progress: int = Field(0, ge=0, le=100)
    message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    # ... config ...

class ProcessingConfig(BaseModel):
    transformations: list[dict[str, Any]] | None = None
    aggregations: list[dict[str, Any]] | None = None
    groupby: list[str] | None = None
    filters: list[dict[str, Any]] | None = None
    metrics: list[dict[str, Any]] | None = None
    # ... config ...

class ProcessingResult(BaseModel):
    success: bool
    task_id: UUID
    dashboard_id: int
    rows_processed: int
    message: str
    data: dict[str, Any] | None = None
    # ... config ...

class LoaderConfig(BaseModel):
    required_columns: list[str] = Field(default_factory=list)
    column_types: dict[str, str] = Field(default_factory=dict)
    strict_schema: bool = False
    max_file_size: int = Field(default=100 * 1024 * 1024, ge=1, le=1024 * 1024 * 1024)
    allowed_file_types: list[str] = Field(default_factory=lambda: [".csv", ".csv.gz"])
    # ... config ...

class ValidationResult(BaseModel):
    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    row_count: int = Field(ge=0)
    column_count: int = Field(ge=0)
    columns: list[str] = Field(default_factory=list)
    # ... config ...

class DataFilter(BaseModel):
    dashboard_id: UUID
    filters: dict[str, Any] | None = None
    year: int | None = None
    category: str | None = None
    brand: str | None = None
    # ... config ...
```

**Старый data.py:** Очищен (останутся только AggregatedData - Шаг 8)

**Проверка:**
- Все модели обработки данных в data_processing.py
- Нет зависимости от user_roles.py

---

## Шаг 8: Перенос моделей аналитики

**Действие:** Перенести оставшиеся модели из data.py в analytics.py

**Модели для переноса (из data.py):**
- AggregatedData

**Новый analytics.py (содержимое):**
```python
from typing import Any
from pydantic import BaseModel, ConfigDict
from uuid import UUID

from mko_bi.models.charts import GraphTypeEnum  # Импорт из charts.py

class AggregatedData(BaseModel):
    dashboard_id: int
    chart_type: GraphTypeEnum
    data: list[dict[str, Any]]
    metadata: dict[str, Any] | None = None
    # ... config ...
```

**Старый data.py:** УДАЛЯТЬ полностью

**Проверка:**
- Модель AggregatedData в analytics.py
- Импорт GraphTypeEnum из charts.py

---

## Шаг 9: Обновление точки входа (__init__.py)

**Действие:** Обновить `src/mko_bi/models/__init__.py`

**Новое содержимое:**
```python
# Экспорт всех моделей по предметным областям

# Аутентификация
from .auth import (
    LoginRequest,
    RegisterRequest,
    Token,
    TokenData,
    RefreshRequest,
)

# Пользователи
from .users import (
    UserRoleEnum,
    UserBase,
    UserCreate,
    UserRead,
    UserDB,
    UserUpdate,
)

# Дашборды
from .dashboards import (
    DashboardConfig,
    DashboardCreate,
    DashboardRead,
    DashboardUpdate,
)

# Графики
from .charts import (
    GraphTypeEnum,
    OrientationEnum,
    BarmodeEnum,
    YoyModeEnum,
    ChartConfig,
    ChartData,
    ChartDataRequest,
)

# Обработка данных
from .data_processing import (
    DataUpload,
    UploadResponse,
    ProcessingStatus,
    ProcessingConfig,
    ProcessingResult,
    LoaderConfig,
    ValidationResult,
    DataFilter,
)

# Аналитика
from .analytics import (
    AggregatedData,
)

# Доступ (оставляем как есть - уже хорошо)
from .access import (
    AccessCheck,
    AccessGrant,
)

# Общий экспорт для удобства
__all__ = [
    # Auth
    "LoginRequest",
    "RegisterRequest",
    "Token",
    "TokenData",
    "RefreshRequest",
    # Users
    "UserRoleEnum",
    "UserBase",
    "UserCreate",
    "UserRead",
    "UserDB",
    "UserUpdate",
    # Dashboards
    "DashboardConfig",
    "DashboardCreate",
    "DashboardRead",
    "DashboardUpdate",
    # Charts
    "GraphTypeEnum",
    "OrientationEnum",
    "BarmodeEnum",
    "YoyModeEnum",
    "ChartConfig",
    "ChartData",
    "ChartDataRequest",
    # Data Processing
    "DataUpload",
    "UploadResponse",
    "ProcessingStatus",
    "ProcessingConfig",
    "ProcessingResult",
    "LoaderConfig",
    "ValidationResult",
    "DataFilter",
    # Analytics
    "AggregatedData",
    # Access
    "AccessCheck",
    "AccessGrant",
]
```

**Проверка:**
- Все модели доступны через `mko_bi.models`
- Четкая структура экспорта

---

## Шаг 10: Очистка старых файлов

**Действие:** Удалить или очистить старые файлы

| Файл | Действие | Примечание |
|------|----------|-----------|
| `auth.py` | ОЧИСТИТЬ | Оставить пустым или удалить (AccessCheck/AccessGrant УДАЛИТЬ, они дублируют access.py) |
| `user.py` | УДАЛИТЬ | Все модели перенесены в users.py |
| `dashboard.py` | УДАЛИТЬ | Все модели перенесены в dashboards.py |
| `data.py` | УДАЛИТЬ | Все модели перенесены в data_processing.py и analytics.py |
| `user_roles.py` | УДАЛИТЬ | Все Enum-ы перенесены (UserRoleEnum → users.py, остальные → charts.py) |
| `access.py` | ОСТАВИТЬ | Уже хорош, содержит AccessCheck и AccessGrant |

**Важно:** AccessCheck и AccessGrant в старом auth.py - ДУБЛИКАТЫ. Они уже есть в access.py. УДАЛИТЬ из auth.py, оставить только в access.py.

---

## Шаг 11: Обновление всех импортов в кодовой базе

**Действие:** Найти и заменить все импорты старых моделей на новые

**Скрипт для поиска (bash):**
```bash
# Найти все импорты из старых файлов
grep -r "from mko_bi.models\." src/mko_bi/ --include="*.py" | grep -E "(auth|user|dashboard|data)\.py" | sort -u
```

**Карта замены импортов:**

| Старый импорт | Новый импорт |
|--------------|-------------|
| `from mko_bi.models.auth import LoginRequest` | `from mko_bi.models.auth import LoginRequest` (без изменений, но из нового auth.py) |
| `from mko_bi.models.auth import AccessCheck` | `from mko_bi.models.access import AccessCheck` |
| `from mko_bi.models.auth import AccessGrant` | `from mko_bi.models.access import AccessGrant` |
| `from mko_bi.models.user import UserBase` | `from mko_bi.models.users import UserBase` |
| `from mko_bi.models.user import UserCreate` | `from mko_bi.models.users import UserCreate` |
| `from mko_bi.models.user import UserRead` | `from mko_bi.models.users import UserRead` |
| `from mko_bi.models.user import UserDB` | `from mko_bi.models.users import UserDB` |
| `from mko_bi.models.user import UserUpdate` | `from mko_bi.models.users import UserUpdate` |
| `from mko_bi.models.user_roles import UserRoleEnum` | `from mko_bi.models.users import UserRoleEnum` |
| `from mko_bi.models.user_roles import PermissionEnum` | `from mko_bi.models.access import PermissionEnum` |
| `from mko_bi.models.user_roles import GraphTypeEnum` | `from mko_bi.models.charts import GraphTypeEnum` |
| `from mko_bi.models.user_roles import OrientationEnum` | `from mko_bi.models.charts import OrientationEnum` |
| `from mko_bi.models.user_roles import BarmodeEnum` | `from mko_bi.models.charts import BarmodeEnum` |
| `from mko_bi.models.user_roles import YoyModeEnum` | `from mko_bi.models.charts import YoyModeEnum` |
| `from mko_bi.models.dashboard import DashboardConfig` | `from mko_bi.models.dashboards import DashboardConfig` |
| `from mko_bi.models.dashboard import DashboardCreate` | `from mko_bi.models.dashboards import DashboardCreate` |
| `from mko_bi.models.dashboard import DashboardRead` | `from mko_bi.models.dashboards import DashboardRead` |
| `from mko_bi.models.dashboard import DashboardUpdate` | `from mko_bi.models.dashboards import DashboardUpdate` |
| `from mko_bi.models.data import DataUpload` | `from mko_bi.models.data_processing import DataUpload` |
| `from mko_bi.models.data import UploadResponse` | `from mko_bi.models.data_processing import UploadResponse` |
| `from mko_bi.models.data import ProcessingStatus` | `from mko_bi.models.data_processing import ProcessingStatus` |
| `from mko_bi.models.data import ProcessingConfig` | `from mko_bi.models.data_processing import ProcessingConfig` |
| `from mko_bi.models.data import ProcessingResult` | `from mko_bi.models.data_processing import ProcessingResult` |
| `from mko_bi.models.data import LoaderConfig` | `from mko_bi.models.data_processing import LoaderConfig` |
| `from mko_bi.models.data import ValidationResult` | `from mko_bi.models.data_processing import ValidationResult` |
| `from mko_bi.models.data import DataFilter` | `from mko_bi.models.data_processing import DataFilter` |
| `from mko_bi.models.data import ChartConfig` | `from mko_bi.models.charts import ChartConfig` |
| `from mko_bi.models.data import ChartData` | `from mko_bi.models.charts import ChartData` |
| `from mko_bi.models.data import ChartDataRequest` | `from mko_bi.models.charts import ChartDataRequest` |
| `from mko_bi.models.data import AggregatedData` | `from mko_bi.models.analytics import AggregatedData` |

**Особые случаи:**
- Импорты из `mko_bi.models.access` остаются без изменений (уже правильные)
- Импорты через `mko_bi.models.__init__` (если есть) - продолжают работать после обновления __init__.py

---

## Шаг 12: Проверка импортов и кода

**Действие:** Проверка отсутствия циклических зависимостей и работоспособности

**1. Проверка циклических импортов:**
```bash
# Попытка импорта всех модулей
python -c "from mko_bi.models import *; print('OK')"
```

**2. Граф зависимостей (должен быть ациклическим):**
```
users.py (базовый, нет зависимостей)
  ↑
auth.py (зависит от users → UserRoleEnum)
  ↑
access.py (базовый, нет зависимостей)
  ↑
charts.py (базовый, нет зависимостей)
  ↑
dashboards.py (зависит от charts → GraphTypeEnum)
  ↑
data_processing.py (базовый, нет зависимостей)
  ↑
analytics.py (зависит от charts → GraphTypeEnum)
```

**3. Запуск тестов:**
```bash
pytest tests/test_base_models.py -v
pytest tests/test_pydantic_models.py -v
```

**4. Проверка использования в API:**
```bash
# Проверить, что все роуты работают
python -c "from mko_bi.api.routes import *; print('Routes OK')"
```

**5. Проверка отсутствия старых импортов:**
```bash
grep -r "from mko_bi.models\.user_roles import" src/ || echo "No old imports found - GOOD"
grep -r "from mko_bi.models\.user import" src/ || echo "No old imports found - GOOD"
grep -r "from mko_bi.models\.dashboard import" src/ || echo "No old imports found - GOOD"
grep -r "from mko_bi.models\.data import" src/ || echo "No old imports found - GOOD"
```

---

## Шаг 13: Удаление лишних файлов

**Действие:** Финальная очистка

**Файлы для удаления:**
- `src/mko_bi/models/auth.py` (если пустой после удаления дубликатов)
- `src/mko_bi/models/user.py`
- `src/mko_bi/models/dashboard.py`
- `src/mko_bi/models/data.py`
- `src/mko_bi/models/user_roles.py`

**Файлы для сохранения:**
- `src/mko_bi/models/access.py` (уже хорош)
- Все новые файлы (auth.py, users.py, dashboards.py, charts.py, data_processing.py, analytics.py)

---

## Резюме: Что получаем

### Проблемы, которые решены:
✅ **Смешение доменов** - каждый файл отвечает за свою предметную область  
✅ **Нарушение SRP** - каждый файл имеет одну ответственность  
✅ **Циклические зависимости** - четкая иерархия зависимостей (без циклов)  
✅ **Дублирование** - AccessCheck/AccessGrant только в access.py  
✅ **Enum-ы на своих местах** - GraphTypeEnum в charts.py, UserRoleEnum в users.py  
✅ **Flat структура** - все файлы на одном уровне, без вложенностей  
✅ **Нет overengeneering** - простые файлы, нет schemas.py, нет вложенных папок  
✅ **Понятные импорты** - `from mko_bi.models.users import UserCreate`  
✅ **Легко масштабировать** - добавить новую модель = добавить в нужный файл  

### Структура после рефакторинга:
```
src/mko_bi/models/
├── __init__.py          # Единая точка входа
├── access.py            # Модели доступа (AccessCheck, AccessGrant)
├── auth.py              # Аутентификация (Login, Register, Token)
├── users.py             # Пользователи + UserRoleEnum
├── dashboards.py        # Дашборды
├── charts.py            # Графики + все Enum-ы графиков
├── data_processing.py   # Загрузка, обработка, валидация
└── analytics.py         # Агрегированные данные
```

### Преимущества:
- **Простота** - любой разработчик сразу понимает, где что искать
- **Чистота** - нет дублирования, каждая модель на своем месте
- **Безопасность** - нет циклических зависимостей
- **Масштабируемость** - легко добавить новые модели в нужную предметную область
- **Поддерживаемость** - изменения в одной области не затрагивают другие

---

## Контрольный список для выполнения:

- [ ] Создать пустые файлы (auth.py, users.py, dashboards.py, charts.py, data_processing.py, analytics.py)
- [ ] Перенести Enum-ы (Шаг 2)
- [ ] Перенести модели аутентификации (Шаг 3)
- [ ] Перенести модели пользователей (Шаг 4)
- [ ] Перенести модели дашбордов (Шаг 5)
- [ ] Перенести модели графиков (Шаг 6)
- [ ] Перенести модели обработки данных (Шаг 7)
- [ ] Перенести модели аналитики (Шаг 8)
- [ ] Обновить __init__.py (Шаг 9)
- [ ] Удалить старые файлы (Шаг 10)
- [ ] Обновить импорты во всей кодовой базе (Шаг 11)
- [ ] Проверить работоспособность (Шаг 12)
- [ ] Финальная очистка (Шаг 13)
