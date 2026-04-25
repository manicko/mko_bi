# BI Dashboard System — Database Schema (PostgreSQL)

---

# 1. users

```sql
users (
    id              UUID PRIMARY KEY,
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('admin', 'editor', 'viewer')),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);
```

---

# 2. dashboards

```sql
dashboards (
    id              UUID PRIMARY KEY,
    name            TEXT UNIQUE NOT NULL,
    description     TEXT,
    layout_id       UUID REFERENCES layouts(id),
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);
```

---

# 3. layouts

👉 layout = **UI-композиция**, без жёсткой логики

```sql
layouts (
    id              UUID PRIMARY KEY,
    name            TEXT UNIQUE NOT NULL,

    definition      JSONB NOT NULL,
    /*
    структура:
    {
      "grid": [...],
      "graphs": [...],
      "filters": [...],
      "bindings": [
        { "filter": "year", "graphs": ["g1", "g2"] }
      ]
    }
    */

    created_at      TIMESTAMP DEFAULT NOW()
);
```

---

# 4. graphs

```sql
graphs (
    id              UUID PRIMARY KEY,
    dashboard_id    UUID NOT NULL REFERENCES dashboards(id) ON DELETE CASCADE,

    name            TEXT NOT NULL,
    type            TEXT NOT NULL CHECK (type IN ('bar', 'line', 'pie', 'table')),

    config          JSONB NOT NULL, -- оси, визуализация
    dimensions      JSONB NOT NULL, -- список dims
    metrics         JSONB NOT NULL, -- список метрик

    created_at      TIMESTAMP DEFAULT NOW(),

    UNIQUE (dashboard_id, name)
);
```

---

# 5. filters (ГЛОБАЛЬНАЯ СУЩНОСТЬ)

👉 фильтр НЕ принадлежит дашборду

```sql
filters (
    id              UUID PRIMARY KEY,
    name            TEXT UNIQUE NOT NULL,

    type            TEXT NOT NULL, 
    -- 'select' | 'multiselect' | 'range' | 'date'

    config          JSONB NOT NULL,
    /*
    пример:
    {
      "field": "year",
      "source": "dims",
      "multi": false
    }
    */

    created_at      TIMESTAMP DEFAULT NOW()
);
```

---

# 6. dashboard_access

```sql
dashboard_access (
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    dashboard_id    UUID REFERENCES dashboards(id) ON DELETE CASCADE,
    permission      TEXT NOT NULL CHECK (permission IN ('view', 'edit', 'admin')),

    PRIMARY KEY (user_id, dashboard_id)
);
```

---

# 7. processing_configs (МИНИМАЛЬНЫЙ)

👉 только настройки, НЕ логика

```sql
processing_configs (
    dashboard_id    UUID PRIMARY KEY REFERENCES dashboards(id) ON DELETE CASCADE,

    settings        JSONB NOT NULL,
    /*
    пример:
    {
      "loader": "sales_loader",
      "date_column": "event_date",
      "timezone": "UTC"
    }
    */

    updated_at      TIMESTAMP DEFAULT NOW()
);
```

---

# 8. aggregated_data (CORE)

```sql
aggregated_data (
    id              BIGSERIAL PRIMARY KEY,

    dashboard_id    UUID NOT NULL REFERENCES dashboards(id) ON DELETE CASCADE,
    graph_id        UUID NOT NULL REFERENCES graphs(id) ON DELETE CASCADE,

    dims            JSONB NOT NULL,
    metrics         JSONB NOT NULL
);
```

---

# 9. processing_logs

```sql
processing_logs (
    id              UUID PRIMARY KEY,
    dashboard_id    UUID REFERENCES dashboards(id),

    status          TEXT NOT NULL CHECK (status IN ('started', 'success', 'failed')),
    message         TEXT,

    started_at      TIMESTAMP,
    finished_at     TIMESTAMP
);
```

---

# 📌 Индексы

```sql
CREATE INDEX idx_agg_graph_id
ON aggregated_data(graph_id);

CREATE INDEX idx_agg_dashboard_id
ON aggregated_data(dashboard_id);

CREATE INDEX idx_agg_dims_gin
ON aggregated_data USING GIN (dims);

CREATE INDEX idx_access_user
ON dashboard_access(user_id);

CREATE INDEX idx_access_dashboard
ON dashboard_access(dashboard_id);
```

---

# 📌 Принципы работы

### 1. Данные

* 1 строка = 1 точка графика
* dims → фильтры / оси
* metrics → значения

---

### 2. Фильтры

* определяются в `filters`
* layout решает:

  * где отображать
  * к каким графикам применять

---

### 3. Layout

* управляет UI
* связывает:

  * filters ↔ graphs
* НЕ хранит данные

---

### 4. Processing

* логика → Python loaders
* БД хранит только настройки (`processing_configs.settings`)

---

### 5. Обновление данных

```sql
DELETE FROM aggregated_data WHERE graph_id = :graph_id;
INSERT INTO aggregated_data ...
```

---

# ✅ Итог

Схема:

* гибкая (разные данные)
* без жёстких колонок
* поддерживает переиспользуемые фильтры
* layout управляет связями UI
* готова к росту без миграций

---
