# BI Dashboard System Audit Task

## Цель

Провести audit FastAPI BI Dashboard System на:

* соответствие спецификации,
* корректность архитектуры,
* качество кода,
* работоспособность,
* безопасность,
* maintainability.

Фокус:

* practical engineering,
* простая поддерживаемая архитектура,
* отсутствие критичных anti-patterns.

ИЗБЕГАТЬ:

* enterprise overengineering,
* unnecessary abstractions,
* сложных паттернов без необходимости.

---

# Правила аудита

## Основные принципы

При проверке:

* сначала проверять соответствие ТЗ,
* затем корректность реализации,
* затем качество кода.

Не считать проблемой:

* простую архитектуру,
  если она:
* последовательна,
* читаема,
* тестируема,
* расширяема.

Критичными считать:

* нарушения безопасности,
* нарушения access control,
* потерю данных,
* смешивание ответственности,
* неустойчивую обработку данных,
* async/blocking issues,
* hardcoded behavior,
* отсутствие validation.

---

# BLOCK 1 — Project Structure & Architecture

## Проверить

### Структуру проекта

* разделены ли:

  * API/routes
  * services/business logic
  * repositories/db access
  * schemas/pydantic
  * processing layer
  * dashboard layer

### Проверить отсутствие

* business logic inside routes
* SQL inside controllers/routes
* global mutable state
* cyclic imports
* hidden side effects

### Проверить

* dependency injection usage
* config centralization
* env handling
* logging centralization

### Проверить processing pipeline

* upload
* parse
* transform
* aggregate
* save

Pipeline должен быть:

* явным,
* читаемым,
* разбитым по этапам.

---

# BLOCK 2 — FastAPI API Layer

## Проверить endpoints

### Auth

* login
* JWT generation
* JWT validation
* password hashing (bcrypt)

### Users

* CRUD restrictions
* role validation

### Dashboards

* CRUD
* access validation

### Upload

* file type validation
* UTF-8 validation
* temp file cleanup
* CSV.gz handling

### Processing

* trigger processing
* processing isolation
* processing errors

### Aggregated data

* filters
* pagination/limits if needed
* dashboard access validation

---

# BLOCK 3 — Access Control & Security

## Проверить

### Access control

* проверка dashboard access на каждом запросе
* editor/viewer/admin restrictions
* direct object access vulnerabilities

### JWT

* expiration validation
* invalid token handling
* missing token handling

### Passwords

* bcrypt usage
* no plaintext passwords
* no password logging

### Upload security

* path traversal
* unsafe filenames
* oversized files handling

### SQL safety

* отсутствие raw unsafe SQL
* parameterized queries

### Secrets/config

* отсутствие hardcoded secrets
* env-based configuration

---

# BLOCK 4 — Data Processing

## Проверить

### Использование Polars

* pandas не используется
* processing реализован через Polars

### Pipeline correctness

* parsing
* transformations
* aggregations
* full recalculation logic

### Aggregations

Проверить:

* groupby
* YoY
* shares
* custom metrics

### Error handling

* corrupted CSV
* invalid schema
* missing columns
* empty files

### Resource handling

* temp files cleanup
* DB transaction handling

---

# BLOCK 5 — PostgreSQL Layer

## Проверить

### Schema usage

* соответствие declared schema
* foreign keys
* cascade behavior

### Aggregated data model

* корректность JSONB usage
* фильтрация через dims
* metrics consistency

### Queries

* отсутствие N+1
* корректность joins
* index usage

### Transactions

* atomic processing
* rollback on failure

---

# BLOCK 6 — Dash / Plotly Layer

## Проверить

### Dashboard rendering

* graphs loading
* filters application
* multi-graph updates

### Graph config handling

* config-driven rendering
* graph type validation

### Supported graph types

* bar
* line
* pie
* table

### Проверить

* invalid config handling
* missing data handling

---

# BLOCK 7 — Code Quality

## Проверить

### Typing

* type hints
* pydantic usage

### Readability

* oversized functions
* duplicated logic
* unclear naming

### Error handling

* broad excepts
* swallowed exceptions
* inconsistent errors

### Async correctness

* blocking IO in async
* sync DB inside async endpoints

### Maintainability

* hardcoded logic
* magic constants
* hidden dependencies

### Logging

Проверить наличие логирования:

* uploads
* processing
* auth events
* errors

---

# BLOCK 8 — Testing

## Проверить

### pytest usage

### Coverage наличия тестов

* auth
* API
* processing
* access control

### Проверить

* edge cases
* invalid input tests
* permission tests

---

# BLOCK 9 — Performance & Stability

## Проверить

### Processing scalability

* memory-heavy operations
* full file loading issues

### API stability

* error isolation
* long-running requests

### DB

* heavy JSONB scans
* missing indexes usage

---

# Формат отчета (ОБЯЗАТЕЛЬНО)
 
Создать файл `TODO/TASK_ <number> _analysis_report.md`
вместо number - подставить номер

# 1. Executive Summary

Кратко:

* общее качество системы,
* основные риски,
* readiness level.

---

# 2. Architecture Summary

Кратко:

* сильные стороны,
* слабые стороны,
* maintainability assessment.

---

# 3. Requirements Coverage

Таблица:

| Requirement   | Status | Notes                 |
| ------------- | ------ | --------------------- |
| JWT auth      | PASS   | Correct               |
| CSV.gz upload | FAIL   | gzip handling missing |

---

# 4. Findings (основной раздел)

Для каждой проблемы ОБЯЗАТЕЛЬНО:

| Severity | File          | Line | Problem                | Impact     | Recommendation      |
| -------- | ------------- | ---- | ---------------------- | ---------- | ------------------- |
| HIGH     | api/upload.py | 84   | temp files not deleted | disk leaks | add finally cleanup |

Severity:

* CRITICAL
* HIGH
* MEDIUM
* LOW

---

# 5. File-Level Recommendations

Для каждого проблемного файла:

```text
File: processing/pipeline.py

Problems:
- oversized function
- mixed responsibilities
- transaction handling unclear

Recommendations:
- split parsing/aggregation/save stages
- isolate DB writes
- add typed intermediate models
```

---

# 6. Missing Features vs Specification

Отдельно перечислить:

* что отсутствует,
* что реализовано частично,
* что противоречит ТЗ.

---

# 7. Final Assessment

Кратко оценить:

* maintainability,
* production readiness,
* основные technical risks,
* приоритет исправлений.

---

# Важные ограничения для LLM

## НЕ считать проблемой

* простую архитектуру,
* небольшое количество abstraction layers,
* отсутствие enterprise patterns.

## Считать проблемой

* сложность поддержки,
* неявную логику,
* небезопасность,
* смешивание ответственности,
* нестабильный processing,
* слабый access control,
* плохую обработку ошибок.

## Основной критерий

Система должна быть:

* понятной,
* устойчивой,
* безопасной,
* легко поддерживаемой,
* соответствующей спецификации.
