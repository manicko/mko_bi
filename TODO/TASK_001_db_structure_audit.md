# Задание: аудит баз данных PostgreSQL в проекте (FastAPI)

## Состав команды для выполнения задания

- **Backend Architect** – определяет перечень требуемых баз (основная, тестовая, иные), архитектурные риски, требования масштабируемости и maintainability.
- **Senior Python Developer** – выполняет поиск и анализ кода (репозитории, модели, миграции, конфиги), документирует схему БД и выявляет технический долг.
- **DevOps / DB Admin** – проверяет окружения (dev/stage/prod), права, переменные окружения, reproducibility, backup/recovery и deployment constraints.
- **QA Engineer** – проверяет изоляцию test DB, соответствие схемы тестовой среде, reproducibility и отсутствие environment leakage.

---

# 1. Цель задания

На основе анализа существующего кода, миграций, конфигурации и реальных PostgreSQL баз:

1. **Перечислить все требуемые базы данных PostgreSQL**, используемые системой.
2. Для каждой базы – **извлечь и задокументировать полную структуру**:
   - таблицы;
   - типы данных;
   - связи;
   - индексы;
   - ограничения;
   - триггеры;
   - расширения;
   - роли и права.
3. Выявить:
   - архитектурные проблемы;
   - schema drift;
   - migration drift;
   - проблемы масштабируемости;
   - проблемы maintainability;
   - потенциальные точки деградации при росте системы.
4. Составить рекомендации:
   - что необходимо исправить;
   - что нужно упростить;
   - что нужно стандартизировать;
   - что необходимо подготовить заранее для роста системы.

> Важно:
> - не описывать бизнес-логику приложения;
> - не анализировать UI/API behavior;
> - фокус только на database architecture, schema lifecycle и reproducibility.
- структура базы может расходиться с кодом, т.к. приложение еще в разработке

---

# 2. Этапы выполнения

---

# 2.1. Аудит кода и окружения – поиск по файлам

Необходимо просканировать репозиторий и окружения (dev/stage/prod).

---

## 2.1.1. Перечень баз данных

Искать в:

- `.env`
- `docker-compose.yml`
- `k8s secrets`
- CI/CD конфигурациях
- `config.py`
- `settings.py`
- `init_db.sh`
- `create_dbs.sql`
- `conftest.py`
- pytest fixtures

Проверять:
- `DATABASE_URL`
- `TEST_DATABASE_URL`
- `MIGRATION_DATABASE_URL`
- дополнительные PostgreSQL DSN

### Результат

Список баз с указанием:

| Logical Name | DSN Variable | Environment | Purpose | Creation Method |
|---|---|---|---|---|

---

## 2.1.2. Схема таблиц, связей, индексов для каждой базы

Источники:

- `alembic/versions/*.py`
- SQLAlchemy модели
- raw SQL миграции
- init scripts
- fixtures
- интерактивный аудит PostgreSQL

Для каждой таблицы задокументировать:

- schema/table name
- columns/types
- constraints
- indexes
- FK
- triggers
- sequences
- extensions
- comments

### Особое внимание

Проверять:

- UUID consistency
- JSONB usage
- timezone-aware timestamps
- nullable correctness
- async-compatible types/drivers

### Результат

Markdown-документ со структурой БД.

---

## 2.1.2.1. Проверка расхождений между ORM, миграциями и реальной БД

Проверить согласованность:

- ORM;
- Alembic;
- реальной PostgreSQL схемы.

Выявлять:

- отсутствующие таблицы;
- отсутствующие поля;
- несовпадения типов;
- расхождения constraints;
- расхождения индексов;
- manual DB changes;
- legacy columns/tables.

### Особое внимание

- UUID vs INTEGER
- JSONB vs JSON/TEXT
- timezone-aware timestamps
- async-compatible DB drivers

### Результат

Schema Drift Report.

---

## 2.1.2.2. Аудит миграций и reproducibility схемы

Проверить:

- целостность migration chain;
- reproducibility с нуля;
- отсутствие broken revisions;
- отсутствие циклических зависимостей;
- возможность выполнить:
  - `alembic upgrade head`
  - на полностью пустой БД.

Выявлять:

- manual SQL changes;
- non-idempotent migrations;
- state-dependent migrations;
- migration drift;
- смешивание schema/data migrations.

### Результат

Migration Audit Report.

---

## 2.1.3. Роли и права доступа

Искать в:

- SQL scripts;
- Docker init scripts;
- Terraform/Ansible;
- PostgreSQL grants.

Документировать:

- роли;
- права;
- ownership;
- migration users;
- runtime users.

### Проверить

- separation of privileges;
- least privilege principle;
- отсутствие superuser usage приложением.

### Результат

Role & Permissions Report.

---

## 2.1.4. Особенности test database

Проверить:

- isolation;
- recreate strategy;
- fixtures;
- schema cleanup;
- reuse-db;
- transactional tests.

### Проверить

- test DB физически отделена;
- отдельный DSN;
- нет доступа к prod/dev;
- migrations не затрагивают production.

### Результат

Test Isolation Report:
- SAFE
- RISKY
- UNSAFE

---

# 2.2. Архитектурный аудит database layer

## Цель

Не только описать текущую структуру,
но и определить:

- что сломается при росте системы;
- что усложнит поддержку;
- где architecture bottlenecks;
- какие решения уже сейчас создают technical debt.

---

## 2.2.1. Audit maintainability

Проверить:

- consistency naming;
- consistency UUID strategy;
- consistency timestamp strategy;
- consistency FK strategy;
- consistency index naming;
- schema organization;
- migration organization.

Выявлять:

- хаотичные naming conventions;
- mixed ID strategies;
- inconsistent defaults;
- duplicate structures;
- hardcoded schema assumptions;
- hidden coupling между таблицами.

---

## 2.2.2. Audit scalability

Проверить:

- потенциальные bottlenecks;
- heavy JSONB overuse;
- отсутствие нужных индексов;
- full table scans;
- oversized tables;
- отсутствие partitioning strategy (если объёмы предполагаются большие);
- aggregation hotspots;
- growth risks.

### Проверять особенно

- таблицы логов;
- aggregated data;
- event/history tables;
- processing tables.

### Выявлять

- потенциальные N+1 patterns;
- expensive joins;
- unbounded growth;
- missing archival strategy.

---

## 2.2.3. Audit schema design quality

Проверить:

- нормализацию;
- justified denormalization;
- consistency constraints;
- nullable correctness;
- FK correctness;
- cascade behavior.

Выявлять:

- weak integrity;
- orphan risks;
- missing constraints;
- duplicated data;
- incompatible data types;
- dangerous cascade deletes.

---

## 2.2.4. Audit operational stability

Проверить:

- reproducibility;
- backup compatibility;
- restore compatibility;
- migration safety;
- rollback safety;
- startup safety.

Выявлять:

- schema states impossible to recreate;
- manual-only steps;
- hidden runtime dependencies;
- environment-dependent behavior.

---

## 2.2.5. Audit async compatibility

Для FastAPI async architecture проверить:

- async DB drivers;
- sync engine usage;
- blocking DB access;
- connection lifecycle;
- pool configuration;
- transaction handling.

Выявлять:

- sync SQLAlchemy inside async runtime;
- blocking migrations during requests;
- leaked sessions/connections.

---

## 2.2.6. Audit future extensibility

Проверить:

- насколько схема готова к:
  - новым dashboards;
  - новым aggregation types;
  - multi-tenant support;
  - росту объёмов данных;
  - новым environments.

### Выявлять

- schema rigidity;
- hardcoded assumptions;
- tightly coupled structures;
- migration fragility;
- невозможность безопасного refactoring.

---

# 3. Результаты выполнения задания Файл `C:\py_exp\mko_bi\TODO\DATABASES_AUDIT_REPORT_<number>.md` cодержит:

### 1. Database Inventory

| Database | Environment | Purpose | DSN Variable | Creation Strategy |
|---|---|---|---|---|

---

### 2. Schema Documentation

Для каждой базы:
- таблицы;
- типы;
- FK;
- индексы;
- triggers;
- extensions;
- sequences;
- roles.

---

### 3. Schema Drift Report

| Object | Problem | ORM | Alembic | Real DB | Recommended Source of Truth |
|---|---|---|---|---|---|

---

### 4. Migration Audit

| Check | Status | Notes |
|---|---|---|

---

### 5. Environment Isolation Audit

| Environment | DB | Isolation Status | Risk |
|---|---|---|---|

---

### 6. Architectural Problems

Таблица:

| Severity | Area | Problem | Risk | Recommendation |
|---|---|---|---|---|

Severity:
- CRITICAL
- HIGH
- MEDIUM
- LOW

---

### 7. Scalability Risks

| Area | Risk | Expected Failure Mode | Recommendation |
|---|---|---|---|

---

### 8. Technical Debt

| Area | Debt | Impact | Refactoring Priority |
|---|---|---|---|

---

### 9. Required Architectural Improvements

Цель:
- простая;
- понятная;
- предсказуемая;
- поддерживаемая;
- расширяемая архитектура.
- не максимальная “enterprise architecture”;
- не внедрение сложных паттернов;
- не абстракции ради абстракций.

### Рекомендации должны предлагаться ТОЛЬКО если они:

- уменьшают вероятность ошибок;
- упрощают поддержку;
- уменьшают связность;
- упрощают развитие системы;
- устраняют реальный bottleneck;
- устраняют реальный architectural risk;
- устраняют schema drift;
- улучшают reproducibility;
- делают поведение системы более предсказуемым.

---

### НЕ считать проблемой

- небольшое количество таблиц;
- простую структуру;
- отсутствие microservices;
- отсутствие CQRS;
- отсутствие event sourcing;
- отсутствие repository pattern;
- отсутствие сложных abstraction layers;
- отсутствие premature partitioning/sharding;
- отсутствие сложной caching architecture;
- отсутствие premature optimization.

---

### Считать проблемой только если это реально влияет на:

- maintainability;
- reproducibility;
- scalability;
- integrity;
- operational stability;
- migration safety;
- debugging complexity;
- onboarding complexity;
- test isolation;
- predictable behavior.

---

### Запрещено рекомендовать без явной причины

- partitioning;
- sharding;
- message brokers;
- distributed systems;
- CQRS;
- event sourcing;
- multi-database split;
- сложные abstraction layers;
- generic repositories;
- unnecessary normalization;
- premature denormalization;
- async rewrite без необходимости.

---

### Каждая рекомендация должна отвечать на вопрос:

Что конкретно станет:
- проще поддерживать,
- проще расширять,
- безопаснее изменять,
- стабильнее эксплуатировать

после внедрения изменения.

Если ответа нет — рекомендацию не добавлять.

### Формат 
Для каждой проблемы ОБЯЗАТЕЛЬНО указать:

| Severity | Category | Object | Current Problem | Failure Risk | Required Change | Why It Matters |
|---|---|---|---|---|---|---|

Где:

- `Severity`
  - CRITICAL
  - HIGH
  - MEDIUM
  - LOW

- `Category`
  - Schema Design
  - Migrations
  - Indexing
  - Constraints
  - Scaling
  - Maintainability
  - Async Compatibility
  - Test Isolation
  - Environment Separation
  - Security
  - Reproducibility

- `Object`
  Конкретный объект:
  - таблица,
  - индекс,
  - migration,
  - role,
  - schema,
  - env config,
  - DB connection layer.

---

### Требования к рекомендациям

Каждая рекомендация должна:

- быть привязана к конкретному объекту;
- описывать реальную проблему;
- объяснять:
  - почему это проблема;
  - когда система начнёт деградировать;
  - какой риск создаётся;
- содержать конкретное изменение;
- не содержать абстрактных советов.

---

### Запрещено писать рекомендации вида:

- “улучшить архитектуру”
- “добавить scalability”
- “использовать best practices”
- “рассмотреть оптимизацию”
- “сделать код чище”

---

### Разрешены только конкретные рекомендации

Пример хорошей рекомендации:

| Severity | Category | Object | Current Problem | Failure Risk | Required Change | Why It Matters |
|---|---|---|---|---|---|---|
| HIGH | Indexing | aggregated_data | отсутствует индекс по dashboard_id + graph_id | full table scan при росте данных | добавить composite btree index | запросы dashboard aggregation начнут деградировать после роста таблицы |

---

### Для scalability-проблем обязательно указывать

- что именно станет bottleneck;
- при каком типе роста:
  - рост строк,
  - рост dashboards,
  - рост concurrent users,
  - рост aggregation volume;
- какой компонент пострадает:
  - inserts,
  - filtering,
  - joins,
  - migrations,
  - startup,
  - backup/restore.

---

### Для maintainability-проблем обязательно указывать

- что усложняет поддержку;
- почему это создаёт technical debt;
- что затруднит:
  - migrations,
  - debugging,
  - onboarding,
  - schema evolution,
  - refactoring.

---

### Для migration-проблем обязательно указывать

- возможно ли восстановление БД с нуля;
- какие migrations non-reproducible;
- какие migrations зависят от runtime state;
- какие migrations опасны для production.

---

### Для environment/test isolation обязательно указывать

- может ли test environment повредить dev/prod;
- есть ли shared DB usage;
- есть ли shared credentials;
- возможны ли accidental destructive operations.
---

# 4. Критерии приёмки аудита

Аудит считается выполненным, если:

- выявлены и описаны все PostgreSQL базы;
- восстановлена структура всех схем;
- выявлены расхождения между ORM / Alembic / реальной БД;
- проверена reproducibility схемы;
- выявлены архитектурные проблемы;
- выявлены scalability risks;
- задокументированы migration risks;
- описаны technical debt и maintainability risks;
- предоставлены конкретные рекомендации по улучшению;
- рекомендации не содержат unnecessary enterprise overengineering;
- выводы основаны на фактическом коде, миграциях и структуре БД.