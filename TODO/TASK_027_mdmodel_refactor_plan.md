# Model Refactor Plan

## 1. Найденные проблемы

### 1.1 Смешение доменов
- файл: src/mko_bi/models/user_roles.py
- проблема: Смешение доменов аутентификации/авторизации и конфигурации графиков/визуализации
- пример: Enum`ы GraphTypeEnum, OrientationEnum, BarmodeEnum, YoyModeEnum находятся в файле ролей пользователей, хотя они относятся к предметной области Dashboard/Charts

- файл: src/mko_bi/models/data.py
- проблема: Слишком широкая ответственность одного файла — содержит модели для загрузки файлов, обработки данных, валидации, конфигурации графиков и фильтров
- пример: В одном файле смешаны DataUpload, ProcessingConfig, ChartConfig, FilterState — это разные bounded contexts

- файл: src/mko_bi/models/auth.py
- проблема: Дублирование моделей доступа (AccessCheck, AccessGrant) которые уже существуют в access.py
- пример: AccessCheck и AccessGrant в auth.py дублируют функционал моделей в access.py

### 1.2 Неправильное размещение Enum
- файл: src/mko_bi/models/user_roles.py
- проблема: Enum`ы графиков (GraphTypeEnum, OrientationEnum, BarmodeEnum, YoyModeEnum) не имеют отношения к ролям пользователей
- пример: GraphTypeEnum используется в dashboard.py и data.py, но определен в user_roles.py — нарушение связности

### 1.3 Нарушение SRP (Single Responsibility Principle)
- файл: src/mko_bi/models/data.py
- проблема: Один файл отвечает за 5 разных контекстов: загрузку файлов, статус обработки, конфигурацию обработки, результаты, валидацию, конфигурацию загрузчика и конфигурацию графиков
- пример: ChartConfig и ChartData находятся в файле data.py, хотя это контекст визуализации/графиков

- файл: src/mko_bi/models/user_roles.py
- проблема: Смешение ролей пользователей, прав доступа и конфигурации графиков
- пример: PermissionEnum (права доступа) и GraphTypeEnum (типы графиков) в одном файле

### 1.4 Циклические зависимости (потенциальные)
- файл: src/mko_bi/models/data.py -> импортирует из user_roles.py
- файл: src/mko_bi/models/dashboard.py -> импортирует из user_roles.py
- файл: src/mko_bi/models/auth.py -> импортирует из user_roles.py
- файл: src/mko_bi/models/user.py -> импортирует из user_roles.py
- риск: Все зависят от user_roles.py, при добавлении новых зависимостей возможны циклические импорты

### 1.5 Отсутствие группировки по сущностям
- файл: src/mko_bi/models/ — плоская структура без разделения на bounded contexts
- проблема: Нет четкого разделения на модули по предметным областям
- пример: Модели доступа (access.py) и аутентификации (auth.py) разделены, хотя относятся к одному контексту безопасности

### 1.6 Хаотичное распределение моделей по файлам
- файл: src/mko_bi/models/access.py — содержит только 2 модели доступа
- файл: src/mko_bi/models/auth.py — содержит дублирующие модели доступа + модели аутентификации
- проблема: Непоследовательное разделение, дублирование ответственности

### 1.7 Нарушение принципов модульности
- Нет четких границ между модулями
- Модели разных контекстов зависят от общих enum`ов, что создает жесткую связанность
- Отсутствует разделение на Core/Domain/Application слои

## 2. Предлагаемая структура

src/mko_bi/models/
├── __init__.py
├── auth/
│   ├── __init__.py
│   ├── models.py
│   └── schemas.py
├── users/
│   ├── __init__.py
│   ├── models.py
│   └── schemas.py
├── dashboards/
│   ├── __init__.py
│   ├── models.py
│   └── schemas.py
├── charts/
│   ├── __init__.py
│   ├── models.py
│   └── schemas.py
├── data_processing/
│   ├── __init__.py
│   ├── models.py
│   └── schemas.py
└── analytics/
    ├── __init__.py
    └── models.py

## 3. План изменений

### Шаг 1: Создание структуры каталогов
- действие: Создать новые директории для каждого bounded context
- файлы: 
  - src/mko_bi/models/auth/
  - src/mko_bi/models/users/
  - src/mko_bi/models/dashboards/
  - src/mko_bi/models/charts/
  - src/mko_bi/models/data_processing/
  - src/mko_bi/models/analytics/

### Шаг 2: Перенос моделей аутентификации
- действие: Создать auth/models.py и перенести модели аутентификации
- файлы:
  - Создать: src/mko_bi/models/auth/__init__.py
  - Создать: src/mko_bi/models/auth/models.py
  - Создать: src/mko_bi/models/auth/schemas.py
  - Удалить: AccessCheck, AccessGrant, LoginRequest, RegisterRequest, Token, TokenData, RefreshRequest из auth.py

### Шаг 3: Перенос моделей пользователей
- действие: Создать users/models.py и перенести модели пользователей
- файлы:
  - Создать: src/mko_bi/models/users/__init__.py
  - Создать: src/mko_bi/models/users/models.py
  - Создать: src/mko_bi/models/users/schemas.py
  - Удалить: UserBase, UserCreate, UserRead, UserDB, UserUpdate из user.py
  - Удалить: UserRoleEnum, PermissionEnum из user_roles.py

### Шаг 4: Перенос моделей дашбордов
- действие: Создать dashboards/models.py и перенести модели дашбордов
- файлы:
  - Создать: src/mko_bi/models/dashboards/__init__.py
  - Создать: src/mko_bi/models/dashboards/models.py
  - Создать: src/mko_bi/models/dashboards/schemas.py
  - Удалить: DashboardConfig, DashboardCreate, DashboardRead, DashboardUpdate из dashboard.py
  - Удалить: GraphTypeEnum из user_roles.py

### Шаг 5: Перенос моделей графиков
- действие: Создать charts/models.py и перенести модели графиков
- файлы:
  - Создать: src/mko_bi/models/charts/__init__.py
  - Создать: src/mko_bi/models/charts/models.py
  - Создать: src/mko_bi/models/charts/schemas.py
  - Удалить: ChartConfig, ChartData, ChartDataRequest, FilterState из data.py
  - Удалить: OrientationEnum, BarmodeEnum, YoyModeEnum из user_roles.py

### Шаг 6: Перенос моделей обработки данных
- действие: Создать data_processing/models.py и перенести модели обработки
- файлы:
  - Создать: src/mko_bi/models/data_processing/__init__.py
  - Создать: src/mko_bi/models/data_processing/models.py
  - Создать: src/mko_bi/models/data_processing/schemas.py
  - Удалить: DataUpload, UploadResponse, ProcessingStatus, ProcessingConfig, ProcessingResult, LoaderConfig, ValidationResult, DataFilter из data.py

### Шаг 7: Перенос моделей аналитики
- действие: Создать analytics/models.py
- файлы:
  - Создать: src/mko_bi/models/analytics/__init__.py
  - Создать: src/mko_bi/models/analytics/models.py
  - Удалить: AggregatedData из data.py

### Шаг 8: Обновление точки входа моделей
- действие: Обновить src/mko_bi/models/__init__.py
- файлы:
  - Обновить: Импорт всех моделей из новых модулей

### Шаг 9: Очистка старых файлов
- действие: Удалить или очистить старые файлы моделей
- файлы:
  - Очистить: auth.py
  - Очистить: user.py
  - Очистить: dashboard.py
  - Очистить: data.py
  - Переименовать: user_roles.py -> удалить
  - Оставить: access.py

### Шаг 10: Обновление импортов в кодовой базе
- действие: Обновить все импорты в проекте
- файлы: Все Python файлы в src/mko_bi/
- задача: Заменить старые импорты на новые пути

## 4. Маппинг моделей

| Старая модель | Новый файл |
|--------------|-----------|
| LoginRequest | models/auth/models.py |
| RegisterRequest | models/auth/models.py |
| Token | models/auth/models.py |
| TokenData | models/auth/models.py |
| RefreshRequest | models/auth/models.py |
| AccessCheck (auth.py) | models/auth/schemas.py |
| AccessGrant (auth.py) | models/auth/schemas.py |
| UserBase | models/users/models.py |
| UserCreate | models/users/models.py |
| UserRead | models/users/models.py |
| UserDB | models/users/models.py |
| UserUpdate | models/users/models.py |
| UserRoleEnum | models/users/schemas.py |
| PermissionEnum | models/users/schemas.py |
| DashboardConfig | models/dashboards/models.py |
| DashboardCreate | models/dashboards/models.py |
| DashboardRead | models/dashboards/models.py |
| DashboardUpdate | models/dashboards/models.py |
| GraphTypeEnum | models/dashboards/schemas.py |
| ChartConfig | models/charts/models.py |
| ChartData | models/charts/models.py |
| ChartDataRequest | models/charts/models.py |
| OrientationEnum | models/charts/schemas.py |
| BarmodeEnum | models/charts/schemas.py |
| YoyModeEnum | models/charts/schemas.py |
| FilterState | models/charts/schemas.py |
| DataUpload | models/data_processing/models.py |
| UploadResponse | models/data_processing/models.py |
| ProcessingStatus | models/data_processing/models.py |
| ProcessingConfig | models/data_processing/models.py |
| ProcessingResult | models/data_processing/models.py |
| LoaderConfig | models/data_processing/schemas.py |
| ValidationResult | models/data_processing/schemas.py |
| DataFilter | models/data_processing/schemas.py |
| AggregatedData | models/analytics/models.py |
| AccessCheck (access.py) | models/access.py |
| AccessGrant (access.py) | models/access.py |

## CONSTRAINTS

* НЕ писать код — только планирование
* НЕ изменять файлы — только анализ и план
* использовать существующие модели — не придумывать новые сущности
* не придумывать новые сущности без необходимости

## CRITERIA

План должен:

* быть конкретным (с указанием файлов) ✅
* устранять смешение доменов ✅
* упрощать навигацию по проекту ✅
* быть применимым пошагово ✅
