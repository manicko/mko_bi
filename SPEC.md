# BI Dashboard System 

## 1. Purpose

Веб-приложение для:

* загрузки CSV и CSV.gz данных во временную папку пользователя
* их обработки
* хранения агрегатов
* отображения в дашбордах
* управления доступом пользователей

---

## 2. Stack 

* Backend: **FastAPI**
* Dashboards: **Dash + Plotly**
* Data processing: **Polars** (запрещено использовать pandas)
* Storage: **PostgreSQL**
* Validation: **Pydantic**
* Auth: **JWT + bcrypt**
* Testing: **pytest**
* Logging: **Python logging**
* Env/deps: **uv**
* temp files - platformdirs
* SQLAlchemy (async)
* alembic для миграций
* asyncpg драйвер
---

## 3. Core Entities

### User

* id
* email
* password_hash
* role: `admin | editor | viewer`

### Dashboard

* id
* name
* config (описание структуры и графиков)

### Access

* user_id
* dashboard_id

### Data (aggregated)

* dashboard_id
* агрегированные значения (таблицы в PostgreSQL)

---

## 4. Roles & Permissions

### Admin

* CRUD dashboards
* задаёт:

  * схему данных
  * логику обработки
  * графики
* управляет пользователями
* выдаёт доступы

### Editor

* загружает CSV
* инициирует пересчёт данных

### Viewer

* только просмотр

---

## 5. Authentication

* login: email + password
* password → bcrypt hash
* auth → JWT
* все API защищены

---
## 6. Security & ограничения

* Для upload endpoints должен использоваться rate limiting
* Необходимо ограничение максимального размера загружаемых CSV-файлов
* Обязательна проверка MIME-type загружаемых файлов (`text/csv`, `application/gzip`)
* Все SQL-запросы должны выполняться через parameterized queries (SQLAlchemy ORM/Core)
* Запрещено формирование SQL через string interpolation
* Временные файлы должны удаляться после обработки
---
## 6.1 Configuration & Secrets Management

* Конфигурация загружается из нескольких источников (приоритет: env vars > Docker secrets > .env > YAML > defaults)
* Секреты (DB password, JWT key) хранятся в переменных окружения: `DATABASE__PASSWORD`, `JWT__SECRET_KEY`
* Поддержка Docker secrets через `_FILE` суффикс: `DATABASE__PASSWORD_FILE=/run/secrets/db_password`
* Поддержка `.env` файла для разработки (pydantic-settings)
* `app.yaml` содержит только нечувствительные настройки (хосты, порты, пути)
* Формат вложенных переменных: `DATABASE__HOST`, `DATABASE__PORT` (double underscore)

---
## 7. Data Flow

1. Upload CSV / CSV.gz во временную папку пользователя platformdirs
2. Parse (Polars)
3. Transform (LoaderConfig)
4. Aggregate
5. Save to PostgreSQL
6. Dashboard запрашивает данные
7. Plotly строит графики

---

## 8. Data Upload

* формат: `.csv`, `.csv.gz`
* кодировка `UTF-8`
* файл:

  * загружается
  * обрабатывается
  * удаляется
* история не хранится

---

## 9. Data Processing

* триггер: upload файла
* pipeline:
  * чтение (Polars)
  * трансформация (по конфигу dashboard)
  * агрегации:
    * groupby
    * YoY
    * доли
    * кастомные метрики
* результат:
  * **полный пересчёт**
  * запись в PostgreSQL

---

## 10. Data Storage

* хранится только агрегированное
* структура:
   единая таблица с данными графиков всех дашбордов с ипользованием JSONB 
* данные общие (не зависят от пользователя)

---


## 11. Dashboard Layer (Dash)

* читает агрегаты из backend/API
* строит графики через Plotly
* применяет фильтры

---

## 12. Dashboards

* задаются админом (config-driven)
* каждый дашборд:
  * набор графиков
  * отдельная страница

### Graph types (фиксировано)

* bar
* line
* pie
* table

### Features

* multi-axis
* комбинированные графики
* YoY

---

## 13. Filters

* глобальные:
  * year
  * category
  * brand
* применяются ко всем графикам
* реализуются через backend (SQL/Polars)

---

## 14. API Responsibilities (FastAPI)

* auth (login)
* users CRUD (admin only)
* dashboards CRUD (admin only)
* upload endpoint
* trigger processing
* get aggregated data
* access validation (user ↔ dashboard)

---

## 15. Access Control

* проверка на каждом запросе
* пользователь видит только свои dashboards

---

## 16. Database Schema (PostgreSQL)

### 16.1 Core Tables

#### `users` - Пользователи системы
```sql
users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('admin', 'editor', 'viewer')),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);
```
- **role**: `admin` | `editor` | `viewer`
- Пароли хранятся как bcrypt hash

#### `layouts` - UI композиция (без привязки к данным)
```sql
layouts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT UNIQUE NOT NULL,
    definition      JSONB NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);
```
- `definition` JSONB структура:
  ```json
  {
    "grid": [...],
    "graphs": [...],
    "filters": [...],
    "bindings": [
      { "filter": "year", "graphs": ["g1", "g2"] }
    ]
  }
  ```

#### `dashboards` - Дашборды
```sql
dashboards (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT UNIQUE NOT NULL,
    description     TEXT,
    layout_id       UUID REFERENCES layouts(id),
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);
```

#### `graphs` - Определения графиков
```sql
graphs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dashboard_id    UUID NOT NULL REFERENCES dashboards(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    type            TEXT NOT NULL CHECK (type IN ('bar', 'line', 'pie', 'table')),
    config          JSONB NOT NULL,  -- оси, цвета, настройки визуализации
    dimensions      JSONB NOT NULL,  -- список измерений
    metrics         JSONB NOT NULL,  -- список метрик
    created_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE (dashboard_id, name)
);
```
- **type**: `bar` | `line` | `pie` | `table`
- `config` содержит: axis config, colors, display options
- `dimensions`: список полей для группировки
- `metrics`: список агрегируемых полей

#### `filters` - Глобальные фильтры
```sql
filters (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT UNIQUE NOT NULL,
    type            TEXT NOT NULL,  -- 'select' | 'multiselect' | 'range' | 'date'
    config          JSONB NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);
```
- Пример `config`: `{"field": "year", "source": "dims", "multi": false}`
- Фильтры не принадлежат конкретному дашборду (переиспользуемые)

#### `dashboard_access` - Управление доступом
```sql
dashboard_access (
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    dashboard_id    UUID REFERENCES dashboards(id) ON DELETE CASCADE,
    permission      TEXT NOT NULL CHECK (permission IN ('view', 'edit', 'admin')),
    PRIMARY KEY (user_id, dashboard_id)
);
```
- **permission**: `view` | `edit` | `admin`

#### `dashboard_filters` - Связь дашбордов с фильтрами (many-to-many)
```sql
dashboard_filters (
    dashboard_id    UUID NOT NULL REFERENCES dashboards(id) ON DELETE CASCADE,
    filter_id       UUID NOT NULL REFERENCES filters(id) ON DELETE CASCADE,
    PRIMARY KEY (dashboard_id, filter_id)
);
```
- Связь многие-ко-многим между дашбордами и фильтрами
- При удалении дашборда или фильтра связь удаляется (CASCADE)

#### `processing_configs` - Настройки обработки
```sql
processing_configs (
    dashboard_id    UUID PRIMARY KEY REFERENCES dashboards(id) ON DELETE CASCADE,
    settings        JSONB NOT NULL,
    updated_at      TIMESTAMP DEFAULT NOW()
);
```
- Пример: `{"loader": "sales_loader", "date_column": "event_date", "timezone": "UTC"}`
- Только настройки, без бизнес-логики

#### `aggregated_data` - Агрегированные данные (CORE)
```sql
aggregated_data (
    id              BIGSERIAL PRIMARY KEY,
    dashboard_id    UUID NOT NULL REFERENCES dashboards(id) ON DELETE CASCADE,
    graph_id        UUID NOT NULL REFERENCES graphs(id) ON DELETE CASCADE,
    dims            JSONB NOT NULL,  -- значения измерений
    metrics         JSONB NOT NULL   -- значения метрик
);
```

- 1 строка = 1 точка графика
- `dims`: ключ-значение для фильтров и осей
- `metrics`: ключ-значение для отображения

#### `processing_logs` - Логи обработки
```sql
processing_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dashboard_id    UUID REFERENCES dashboards(id) ON DELETE SET NULL,
    status          TEXT NOT NULL CHECK (status IN ('started', 'uploaded', 'processing', 'success', 'failed', 'completed')),
    message         TEXT,
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ
);
```

### 16.2 Indexes
```sql
CREATE INDEX idx_aggregated_data_graph_id ON aggregated_data(graph_id);
CREATE INDEX idx_aggregated_data_dashboard_id ON aggregated_data(dashboard_id);
CREATE INDEX idx_aggregated_data_dashboard_graph ON aggregated_data(dashboard_id, graph_id);
CREATE INDEX idx_aggregated_data_dims_gin ON aggregated_data USING GIN (dims);
CREATE INDEX idx_dashboard_access_user ON dashboard_access(user_id);
CREATE INDEX idx_dashboard_access_dashboard ON dashboard_access(dashboard_id);
CREATE INDEX idx_graphs_dashboard ON graphs(dashboard_id);
CREATE INDEX idx_dashboard_filters_dashboard_filter ON dashboard_filters(dashboard_id, filter_id);
```

### 16.3 Data Principles
- **Гибкость**: JSONB для dims/metrics — поддержка любых данных без миграций
- **Производительность**: GIN индекс для фильтрации по dims
- **Безопасность**: ON DELETE CASCADE для связанных данных
- **Масштабируемость**: Отдельные таблицы под каждый дашборд не нужны — гибкая схема

---

## 17. Dashboard Layer (Dash)

* читает агрегаты из backend/API
* строит графики через Plotly
* применяет фильтры

---

## 18. UI (минимум)

* login page
* dashboard list
* dashboard page (graphs + filters)

---
## 19. Архитектура интеграции Dash + FastAPI

Dash встроен внутрь FastAPI-приложения.

### Архитектура

* FastAPI является основной точкой входа приложения
* Dash подключается как встроенное sub-application
* Аутентификация и проверка доступов выполняются только через FastAPI
* Dash не обращается к PostgreSQL напрямую
* Dash получает данные через внутренний service layer / API FastAPI

---

### Deployment

* Единое приложение
* Единый слой подключения к PostgreSQL
* Единая система аутентификации
* Один backend-сервис для API и Dash

---

### Поток работы

```text
Browser
   ↓
FastAPI
   ├── REST API
   ├── Auth / JWT
   ├── Upload API
   ├── Data API
   └── Embedded Dash
           ↓
      Service Layer
           ↓
      PostgreSQL
```

---

### Основные принципы

1. Вся бизнес-логика находится в FastAPI/service layer
2. Dash отвечает только за UI и визуализацию
3. Проверка прав доступа выполняется до получения данных
4. Dash не содержит собственной логики аутентификации
5. Все запросы к данным проходят через backend-сервис

### Database Initialization

При старте приложения FastAPI выполняется автоматическая проверка и инициализация схемы БД через модуль `DatabaseStarter` (lifespan). Миграции применяются согласно окружению (`ENV`) с соблюдением production-ограничений.

## 20. Logging

логируются:

* upload
* processing
* errors
* access events

уровни:

* INFO
* WARNING
* ERROR

---

## 21. Testing

* pytest
* покрытие:

  * API
  * processing
  * auth

---

## 22. Component Architecture (Dash)

### Styling Framework
* **dash-bootstrap-components** (Bootstrap 5) для всех UI компонентов
* Использовать `dbc.Container`, `dbc.Row`, `dbc.Col`, `dbc.Card` для layout
* Темизация через Bootstrap темы (DARKLY, FLATLY и др.)

### Component Types (StrEnum)
Все типы компонентов определяются через `StrEnum` в `src/mko_bi/models/enums.py`:

```python
class ButtonVariant(StrEnum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    SUCCESS = "success"
    DANGER = "danger"

class FilterType(StrEnum):
    SELECT = "select"
    MULTISELECT = "multiselect"
    RANGE = "range"
    DATE = "date"

class GraphType(StrEnum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    TABLE = "table"
```

### Pydantic Models for Styling
Конфигурация компонентов через Pydantic модели в `src/mko_bi/models/style.py`:

```python
class ComponentStyle(BaseModel):
    """Базовая модель стилей компонента."""
    width: int = 12
    height: int | None = None
    className: str = ""
    shadow: bool = True
```

### Архитектурные требования
* Маленькие функции (< 20 строк)
* Декомпозиция: каждый компонент = отдельный модуль
* Логирование всех операций рендеринга
* Использование `StrEnum` вместо констант-строк
* Pydantic модели для валидации конфигов

### Структура компонентов
```
src/mko_bi/dashboards/components/
├── charts/
│   ├── base.py          # абстрактный базовый класс
│   ├── bar.py           # график bar (маленький модуль)
│   ├── line.py          # график line
│   ├── pie.py           # график pie
│   └── table.py         # таблица
├── filters.py           # FilterPanel (декомпозированный)
├── layout.py            # DashboardLayout
└── buttons.py           # кнопки (новый модуль)
```

---


