# BI Dashboard System 

## 1. Purpose

Веб-приложение для:

* загрузки CSV данных
* их обработки
* хранения агрегатов
* отображения в дашбордах
* управления доступом пользователей

---

## 2. Stack 

* Backend: **FastAPI**
* Dashboards: **Dash + Plotly**
* Data processing: **Polars**
* Storage: **PostgreSQL**
* Validation: **Pydantic**
* Auth: **JWT + bcrypt**
* Testing: **pytest**
* Logging: **Python logging**
* Env/deps: **uv**

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
## 6. Data Flow

1. Upload CSV
2. Parse (Polars)
3. Transform (LoaderConfig)
4. Aggregate
5. Save to PostgreSQL
6. Dashboard запрашивает данные
7. Plotly строит графики

---

## 7. Data Upload

* формат: `.csv.gz`
* файл:

  * загружается
  * обрабатывается
  * удаляется
* история не хранится

---

## 8. Data Processing

* триггер: upload файла
* pipeline:

  * чтение CSV (Polars)
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

## 9. Data Storage

* хранится только агрегированное
* структура:

  * отдельные таблицы/схемы per dashboard
* данные общие (не зависят от пользователя)

---


## 10. Dashboard Layer (Dash)

* читает агрегаты из backend/API
* строит графики через Plotly
* применяет фильтры

---

## 11. Dashboards

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

## 12. Filters

* глобальные:

  * year
  * category
  * brand
* применяются ко всем графикам
* реализуются через backend (SQL/Polars)

---

## 13. API Responsibilities (FastAPI)

* auth (login)
* users CRUD (admin only)
* dashboards CRUD (admin only)
* upload endpoint
* trigger processing
* get aggregated data
* access validation (user ↔ dashboard)

---

## 14. Access Control

* проверка на каждом запросе
* пользователь видит только свои dashboards

---

## 15. UI (минимум)

* login page
* dashboard list
* dashboard page (graphs + filters)

---

## 16. Logging

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

## 17. Testing

* pytest
* покрытие:

  * API
  * processing
  * auth

---


