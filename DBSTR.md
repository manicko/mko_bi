# Database Structure Reference — Quick Guide for Development

## Overview
База данных bidb (PostgreSQL 18) — гибкая JSONB-ориентированная схема для BI дашбордов.
Все таблицы используют UUID, ON DELETE CASCADE, GIN-индексы для JSONB.

---

## Tables Quick Reference

### 1. users — Пользователи системы
**Purpose:** Аутентификация и авторизация
**Key fields:** id, email, password_hash, role
**Roles:** admin, editor, viewer

**Columns:**
- id (UUID, PK) — идентификатор
- email (TEXT, UNIQUE) — email для входа
- password_hash (TEXT) — bcrypt hash пароля
- role (TEXT, CHECK) — роль доступа (admin/editor/viewer)
- is_active (BOOLEAN) — флаг активности
- created_at (TIMESTAMP) — дата создания

**Indexes:** users_pkey, users_email_key
**Use in modules:** Регистрация, login, проверка прав доступа

---

### 2. layouts — UI Компоновка (без данных)
**Purpose:** Хранение структуры UI дашборда (grid, graphs, filters, bindings)
**Key fields:** id, name, definition (JSONB)

**Columns:**
- id (UUID, PK) — идентификатор
- name (TEXT, UNIQUE) — имя layout
- definition (JSONB) — структура UI
- created_at (TIMESTAMP)

**Indexes:** layouts_pkey, layouts_name_key
**Use in modules:** Рендеринг дашборда, привязка фильтров к графикам

---

### 3. dashboards — Дашборды
**Purpose:** Основная сущность дашборда
**Key fields:** id, name, layout_id, created_by

**Columns:**
- id (UUID, PK) — идентификатор
- name (TEXT, UNIQUE) — имя дашборда
- description (TEXT) — описание
- layout_id (UUID, FK→layouts) — ссылка на layout
- created_by (UUID, FK→users) — создатель
- created_at (TIMESTAMP) — дата создания
- updated_at (TIMESTAMP) — дата обновления

**Indexes:** dashboards_pkey, dashboards_name_key
**Use in modules:** CRUD дашбордов, проверка владельца

---

### 4. graphs — Определения графиков
**Purpose:** Хранение конфигураций графиков для дашборда
**Key fields:** id, dashboard_id, type, config, dimensions, metrics

**Columns:**
- id (UUID, PK) — идентификатор
- dashboard_id (UUID, FK→dashboards, CASCADE) — родительский дашборд
- name (TEXT) — имя графика
- type (TEXT, CHECK) — тип: bar, line, pie, table
- config (JSONB) — настройки визуализации
- dimensions (JSONB) — измерения для группировки
- metrics (JSONB) — метрики для агрегации
- created_at (TIMESTAMP)

**Indexes:** graphs_pkey, graphs_dashboard_id_name_key
**Use in modules:** Построение SQL/Polars запросов, рендеринг графиков

---

### 5. filters — Глобальные фильтры
**Purpose:** Переиспользуемые фильтры (не привязаны к конкретному дашборду)
**Key fields:** id, name, type, config

**Columns:**
- id (UUID, PK) — идентификатор
- name (TEXT, UNIQUE) — имя фильтра
- type (TEXT) — тип фильтра: select, multiselect, range, date
- config (JSONB) — конфигурация
- created_at (TIMESTAMP)

**Indexes:** filters_pkey, filters_name_key
**Use in modules:** Применение фильтров к данным (SQL WHERE / Polars filter)

---

### 6. dashboard_access — Управление доступом
**Purpose:** Права пользователей на дашборды
**Key fields:** user_id, dashboard_id, permission

**Columns:**
- user_id (UUID, FK→users, CASCADE) — пользователь
- dashboard_id (UUID, FK→dashboards, CASCADE) — дашборд
- permission (TEXT, CHECK) — право: view, edit, admin

**Indexes:** dashboard_access_pkey, idx_access_user, idx_access_dashboard
**Use in modules:** Проверка доступа (middleware), список доступных дашбордов

---

### 7. processing_configs — Настройки обработки
**Purpose:** Конфигурация data pipeline для каждого дашборда
**Key fields:** dashboard_id, settings (JSONB)

**Columns:**
- dashboard_id (UUID, PK, FK→dashboards, CASCADE) — дашборд
- settings (JSONB) — настройки data pipeline
- updated_at (TIMESTAMP)

**Indexes:** processing_configs_pkey
**Use in modules:** Загрузка CSV, трансформация данных (Polars)

---

### 8. aggregated_data — Агрегированные данные (CORE)
**Purpose:** Хранение готовых данных для графиков
**Key fields:** dashboard_id, graph_id, dims, metrics

**Columns:**
- id (BIGSERIAL, PK) — идентификатор
- dashboard_id (UUID, FK→dashboards, CASCADE) — дашборд
- graph_id (UUID, FK→graphs, CASCADE) — график
- dims (JSONB) — значения измерений (точка графика)
- metrics (JSONB) — значения метрик

**Indexes:** aggregated_data_pkey, idx_agg_graph_id, idx_agg_dashboard_id, idx_agg_dims_gin
**Use in modules:** Запрос данных для графиков, фильтрация по dims (GIN индекс)

---

### 9. processing_logs — Логи обработки
**Purpose:** Аудит и отладка data pipeline
**Key fields:** id, dashboard_id, status, message

**Columns:**
- id (UUID, PK) — идентификатор
- dashboard_id (UUID, FK→dashboards) — дашборд
- status (TEXT, CHECK) — статус: started, success, failed
- message (TEXT) — сообщение/ошибка
- started_at (TIMESTAMP) — начало обработки
- finished_at (TIMESTAMP) — окончание обработки

**Indexes:** processing_logs_pkey
**Use in modules:** Логирование, мониторинг, алерты

---

## Common Query Patterns

### Получить дашборды пользователя с правами
SELECT d.*, da.permission
FROM dashboards d
JOIN dashboard_access da ON d.id = da.dashboard_id
WHERE da.user_id = :user_id;

### Получить данные для графика с фильтром
SELECT dims, metrics
FROM aggregated_data
WHERE graph_id = :graph_id
  AND dims @> '{"year": 2024}'::jsonb;

### Получить конфиг дашборда с графиками
SELECT d.*, l.definition as layout, array_agg(g.*) as graphs
FROM dashboards d
JOIN layouts l ON d.layout_id = l.id
LEFT JOIN graphs g ON g.dashboard_id = d.id
WHERE d.id = :dashboard_id
GROUP BY d.id, l.id;

### Проверка прав доступа
SELECT permission
FROM dashboard_access
WHERE user_id = :user_id
  AND dashboard_id = :dashboard_id;

---

## Module Development Tips

1. Auth Module -> users, dashboard_access
2. Dashboard Module -> dashboards, layouts, graphs
3. Data Module -> processing_configs, aggregated_data, processing_logs
4. Filter Module -> filters, aggregated_data (GIN queries)
5. Upload Module -> processing_logs, processing_configs

## JSONB Field Conventions

- dims: {"field": value} — для фильтрации и группировки
- metrics: {"field": value} — числовые значения
- config: {"visual": {...}, "axis": {...}} — настройки отображения
- definition: {"grid": [...], "bindings": [...]} — структура UI

## Performance Notes

- GIN индекс на dims ускоряет фильтрацию: WHERE dims @> '{"year": 2024}'
- CASCADE удаляет графики -> данные при удалении дашборда
- UUID генерируется БД: uuid_generate_v4()
- BCrypt hash для паролей (не хранить plaintext!)

---
