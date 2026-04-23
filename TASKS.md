
---

## AUTH

---

### TASK: реализовать хеширование пароля

FILE: src/mko_bi/core/security.py

GOAL: безопасное хранение паролей через bcrypt

IMPLEMENT:

* func: hash_password(password: str) -> str
* func: verify_password(password: str, hash: str) -> bool

INPUT:

"password123"

OUTPUT:

"$2b$..."

LOGIC:

1. использовать bcrypt
2. salt генерируется автоматически
3. verify сравнивает пароль с хешем

CONSTRAINTS:

* использовать bcrypt
* не хранить plain password

DONE:

* [ ] hash возвращает строку
* [ ] verify возвращает bool
* [ ] есть тест

---

### TASK: реализовать JWT

FILE: src/mko_bi/core/security.py

GOAL: аутентификация через JWT

IMPLEMENT:

* func: create_access_token(data: dict) -> str
* func: decode_token(token: str) -> dict

INPUT:

{"user_id": 1}

OUTPUT:

"eyJhbGciOi..."

LOGIC:

1. использовать secret из config
2. добавить exp
3. декодировать и валидировать

CONSTRAINTS:

* срок жизни токена обязателен
* алгоритм HS256

DONE:

* [ ] токен создаётся
* [ ] токен валидируется
* [ ] есть тест

---

### TASK: login endpoint

FILE: src/mko_bi/api/routes/auth.py

GOAL: авторизация пользователя

IMPLEMENT:

* POST /login

INPUT:

{
"email": "[test@test.com](mailto:test@test.com)",
"password": "123"
}

OUTPUT:

{
"access_token": "..."
}

LOGIC:

1. найти пользователя
2. проверить пароль
3. выдать JWT

CONSTRAINTS:

* 401 при ошибке
* не раскрывать причину

DONE:

* [ ] успешный логин
* [ ] ошибка при неверных данных
* [ ] тест есть

---

## USERS

---

### TASK: создать пользователя

FILE: src/mko_bi/services/user_service.py

GOAL: создание пользователя с ролью

IMPLEMENT:

* func: create_user(email, password, role)

LOGIC:

1. проверить уникальность email
2. захешировать пароль
3. сохранить

CONSTRAINTS:

* роли: admin/editor/viewer

DONE:

* [ ] пользователь создаётся
* [ ] пароль захеширован
* [ ] тест

---

### TASK: users CRUD API

FILE: src/mko_bi/api/routes/users.py

GOAL: управление пользователями (admin only)

IMPLEMENT:

* GET /users
* POST /users
* DELETE /users/{id}

LOGIC:

1. проверить роль admin
2. вызвать service

CONSTRAINTS:

* доступ только admin

DONE:

* [ ] CRUD работает
* [ ] проверка роли
* [ ] тесты

---

## DASHBOARDS

---

### TASK: CRUD dashboards

FILE: src/mko_bi/services/dashboard_service.py

GOAL: управление дашбордами

IMPLEMENT:

* create_dashboard
* get_dashboard
* delete_dashboard

LOGIC:

1. работать через repo
2. хранить config JSON

DONE:

* [ ] CRUD работает
* [ ] тест

---

### TASK: dashboards API

FILE: src/mko_bi/api/routes/dashboards.py

GOAL: API для дашбордов

IMPLEMENT:

* GET /dashboards
* POST /dashboards

LOGIC:

1. проверка роли
2. фильтр по доступу

DONE:

* [ ] возвращаются только доступные
* [ ] тест

---

## ACCESS CONTROL

---

### TASK: проверка доступа к дашборду

FILE: src/mko_bi/core/permissions.py

GOAL: ограничить доступ

IMPLEMENT:

* func: check_access(user_id, dashboard_id)

LOGIC:

1. проверить запись в access таблице
2. admin всегда имеет доступ

DONE:

* [ ] доступ работает
* [ ] тест

---

### TASK: middleware зависимости доступа

FILE: src/mko_bi/api/deps.py

GOAL: внедрение проверки в API

IMPLEMENT:

* dependency: get_current_user
* dependency: check_dashboard_access

LOGIC:

1. извлечь user из JWT
2. проверить доступ

DONE:

* [ ] dependency работает
* [ ] используется в endpoints

---

## DATA UPLOAD

---

### TASK: upload endpoint

FILE: src/mko_bi/api/routes/upload.py

GOAL: загрузка CSV

IMPLEMENT:

* POST /upload

INPUT:

file: .csv.gz

LOGIC:

1. сохранить во временную папку
2. вызвать processing
3. удалить файл

CONSTRAINTS:

* только .csv.gz

DONE:

* [ ] файл сохраняется
* [ ] удаляется после обработки
* [ ] тест

---

## DATA LOADING

---

### TASK: загрузка CSV через Polars

FILE: src/mko_bi/data/loaders/loader.py

GOAL: чтение данных

IMPLEMENT:

* func: load_csv(path: str) -> DataFrame

LOGIC:

1. использовать polars.read_csv
2. поддержка gzip

DONE:

* [ ] DataFrame возвращается
* [ ] тест

---

### TASK: валидация данных

FILE: src/mko_bi/data/loaders/validator.py

GOAL: проверка структуры

IMPLEMENT:

* func: validate(df, schema)

LOGIC:

1. проверка колонок
2. типы данных

DONE:

* [ ] ошибки валидируются
* [ ] тест

---

## DATA PROCESSING

---

### TASK: базовый pipeline

FILE: src/mko_bi/data/processing/base.py

GOAL: оркестрация обработки

IMPLEMENT:

* class DataPipeline
* method: run(df, config)

LOGIC:

1. transform
2. aggregate
3. вернуть результат

DONE:

* [ ] pipeline работает
* [ ] тест

---

### TASK: трансформации

FILE: src/mko_bi/data/processing/transformations.py

GOAL: преобразование данных

IMPLEMENT:

* func: apply_transformations(df, config)

LOGIC:

1. фильтры
2. вычисляемые поля

DONE:

* [ ] трансформации применяются
* [ ] тест

---

### TASK: агрегации

FILE: src/mko_bi/data/processing/registry.py

GOAL: агрегаты

IMPLEMENT:

* groupby
* YoY
* share

LOGIC:

1. группировка
2. расчет метрик

DONE:

* [ ] агрегаты считаются
* [ ] тест

---

## DATA STORAGE

---

### TASK: сохранение агрегатов

FILE: src/mko_bi/data/storage/manager.py

GOAL: запись в PostgreSQL

IMPLEMENT:

* func: save_aggregates(dashboard_id, df)

LOGIC:

1. создать таблицу если нет
2. overwrite данные

DONE:

* [ ] данные сохраняются
* [ ] тест

---

### TASK: получение агрегатов

FILE: src/mko_bi/services/data_service.py

GOAL: выдача данных для дашборда

IMPLEMENT:

* func: get_data(dashboard_id, filters)

LOGIC:

1. SQL запрос
2. применить фильтры

DONE:

* [ ] фильтры работают
* [ ] тест

---

## DASHBOARD ENGINE

---

### TASK: базовый класс дашборда

FILE: src/mko_bi/dashboards/base.py

GOAL: структура дашборда

IMPLEMENT:

* class BaseDashboard

LOGIC:

1. config-driven
2. методы получения данных

DONE:

* [ ] базовый класс есть

---

### TASK: registry дашбордов

FILE: src/mko_bi/dashboards/registry.py

GOAL: хранение доступных дашбордов

IMPLEMENT:

* dict registry

LOGIC:

1. регистрация классов

DONE:

* [ ] можно получить dashboard по id

---

### TASK: график bar

FILE: src/mko_bi/dashboards/components/charts/bar.py

GOAL: построение bar chart

IMPLEMENT:

* func: build_bar_chart(data)

LOGIC:

1. использовать plotly

DONE:

* [ ] график строится

---

### TASK: график dot

FILE: src/mko_bi/dashboards/components/charts/dot.py

GOAL: dot chart

IMPLEMENT:

* func: build_dot_chart

DONE:

* [ ] работает

---

### TASK: фильтры

FILE: src/mko_bi/dashboards/components/filters.py

GOAL: глобальные фильтры

IMPLEMENT:

* year, category, brand

LOGIC:

1. применяются к данным

DONE:

* [ ] фильтры работают

---

## SERVICES

---

### TASK: auth service

FILE: src/mko_bi/services/auth_service.py

GOAL: логика авторизации

IMPLEMENT:

* login()

LOGIC:

1. проверить пользователя
2. вернуть токен

DONE:

* [ ] сервис работает

---

### TASK: access service

FILE: src/mko_bi/services/access_service.py

GOAL: управление доступами

IMPLEMENT:

* grant_access
* revoke_access

DONE:

* [ ] доступы управляются

---

## LOGGING

---

### TASK: настройка логирования

FILE: src/mko_bi/logging_config.py

GOAL: централизованные логи

IMPLEMENT:

* logging config

LOGIC:

1. уровни INFO/WARNING/ERROR
2. вывод в stdout

DONE:

* [ ] логирование работает

---

## TESTING

---

### TASK: тест auth

FILE: tests/api/test_auth.py

GOAL: покрыть login

DONE:

* [ ] успешный логин
* [ ] ошибка

---

### TASK: тест pipeline

FILE: tests/data/test_pipeline.py

GOAL: проверить обработку

DONE:

* [ ] pipeline работает

---

### TASK: тест dashboard service

FILE: tests/services/test_dashboard_service.py

GOAL: проверить CRUD

DONE:

* [ ] тесты проходят

---
