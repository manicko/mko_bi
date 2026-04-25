# Разработка BI Dashboard System - Поэтапный план

## Общие принципы
- Соблюдение PEP8 и стандартов качества кода
- Короткие функции, чёткое разделение на блоки
- Использование logging для всех ключевых операций
- Pydantic для валидации данных
- Архитектура: Repository Pattern + Service Layer + FastAPI

---

## Этап 1: Базовая настройка и конфигурация

### 1.1 Настройка конфигурации приложения
**Цель:** Настроить подключение к PostgreSQL и базовые параметры

**Файлы:**
- `src/mko_bi/config.py` - расширение конфигурации
- `src/mko_bi/settings/app.yaml` - настройки подключения к БД
- `src/mko_bi/logging_config.py` - конфигурация логирования

**Задачи:**
- Настроить DATABASE_URL для PostgreSQL 18
- Добавить настройки логирования (INFO, WARNING, ERROR)
- Настроить JWT параметры (SECRET_KEY, ALGORITHM, срок жизни токена)
- Настроить параметры загрузки файлов (UPLOAD_TEMP_DIR, ALLOWED_FILE_TYPES, MAX_FILE_SIZE)

**Классы/Функции:**
- Константы конфигурации в config.py
- Функция загрузки настроек из app.yaml
- Инициализация логгера приложения

---

## Этап 2: Слой данных (Data Layer)

### 2.1 Базовые модели SQLAlchemy
**Цель:** Создать таблицы для пользователей, дашбордов и доступа

**Файлы:**
- `src/mko_bi/db/models/user.py` - модель пользователя
- `src/mko_bi/db/models/dashboard.py` - модель дашборда
- `src/mko_bi/db/models/access.py` - модель доступа
- `src/mko_bi/db/base.py` - базовый класс и сессия

**Задачи:**
- Создать модель User (id, email, password_hash, role)
- Создать модель Dashboard (id, name, config, created_at)
- Создать модель Access (user_id, dashboard_id, permission_level)
- Настроить связи (relationships) между моделями
- Создать engine и SessionLocal для PostgreSQL

**Классы:**
- `User` (SQLAlchemy model)
- `Dashboard` (SQLAlchemy model)
- `Access` (SQLAlchemy model)
- `Base` (declarative_base)

---

### 2.2 Pydantic модели
**Цель:** Создать схемы для валидации входящих/исходящих данных

**Файлы:**
- `src/mko_bi/models/user.py` - схемы пользователя
- `src/mko_bi/models/dashboard.py` - схемы дашборда
- `src/mko_bi/models/data.py` - схемы данных
- `src/mko_bi/models/auth.py` - схемы аутентификации

**Задачи:**
- Создать UserCreate, UserRead, UserDB схемы
- Создать DashboardCreate, DashboardRead, DashboardConfig схемы
- Создать схемы для загрузки данных (DataUpload, ProcessingConfig)
- Создать схемы для аутентификации (LoginRequest, Token)

**Классы:**
- Pydantic BaseModel для каждой сущности
- Валидаторы полей (EmailStr, Literal для ролей)

---

### 2.3 Репозитории (Data Access Layer)
**Цель:** Реализовать паттерн Repository для работы с БД

**Файлы:**
- `src/mko_bi/db/repositories/user_repo.py`
- `src/mko_bi/db/repositories/dashboard_repo.py`
- `src/mko_bi/db/repositories/access_repo.py`

**Задачи:**
- Реализовать CRUD операции для User
- Реализовать CRUD операции для Dashboard
- Реализовать управление доступами (Access)
- Добавить методы фильтрации и поиска

**Классы:**
- `UserRepository` (get, create, update, delete, get_by_email)
- `DashboardRepository` (CRUD + get_by_user)
- `AccessRepository` (grant, revoke, check_access)

---

## Этап 3: Сервисный слой (Business Logic)

### 3.1 Сервис аутентификации
**Цель:** Реализовать логику регистрации, входа и JWT

**Файлы:**
- `src/mko_bi/services/auth_service.py`
- `src/mko_bi/core/security.py` - расширение

**Задачи:**
- Реализовать функцию регистрации пользователя
- Реализовать функцию аутентификации (login)
- Реализовать создание и валидацию JWT токенов
- Реализовать хеширование паролей (bcrypt)

**Функции:**
- `register_user(email, password, role)`
- `authenticate_user(email, password)`
- `create_access_token(data)`
- `verify_password(password, hash)`
- `hash_password(password)`

---

### 3.2 Сервис управления пользователями
**Цель:** Реализовать бизнес-логику для работы с пользователями

**Файлы:**
- `src/mko_bi/services/user_service.py`

**Задачи:**
- Реализовать создание пользователя (с валидацией)
- Реализовать получение пользователя по email
- Реализовать обновление роли пользователя
- Реализовать удаление пользователя

**Функции:**
- `create_user(email, password, role)`
- `get_user_by_email(email)`
- `update_user_role(user_id, new_role)`
- `delete_user(user_id)`

---

### 3.3 Сервис управления дашбордами
**Цель:** Реализовать бизнес-логику для CRUD дашбордов

**Файлы:**
- `src/mko_bi/services/dashboard_service.py`

**Задачи:**
- Реализовать создание дашборда
- Реализовать получение дашбордов пользователя
- Реализовать обновление конфигурации дашборда
- Реализовать удаление дашборда
- Реализовать управление доступом к дашбордам

**Функции:**
- `create_dashboard(name, config, owner_id)`
- `get_dashboard(dashboard_id, user_id)`
- `update_dashboard(dashboard_id, config)`
- `delete_dashboard(dashboard_id)`
- `grant_access(dashboard_id, user_id, permission)`

---

### 3.4 Сервис обработки данных
**Цель:** Реализовать пайплайн загрузки и обработки CSV данных

**Файлы:**
- `src/mko_bi/services/data_service.py`
- `src/mko_bi/data/loaders/loader.py`
- `src/mko_bi/data/processing/base.py`

**Задачи:**
- Реализовать загрузку CSV файлов
- Реализовать парсинг данных (Polars)
- Реализовать трансформацию по конфигу дашборда
- Реализовать агрегацию данных (groupby, YoY, доли)
- Реализовать сохранение агрегатов в PostgreSQL

**Функции:**
- `upload_csv(file, dashboard_id)`
- `process_data(dashboard_id, raw_data)`
- `aggregate_data(data, config)`
- `save_aggregates(dashboard_id, aggregates)`

---

## Этап 4: Слой доступа и безопасность

### 4.1 Управление доступом
**Цель:** Реализовать проверку прав доступа

**Файлы:**
- `src/mko_bi/core/permissions.py`
- `src/mko_bi/api/deps.py` - зависимости FastAPI

**Задачи:**
- Реализовать проверку роли пользователя
- Реализовать проверку доступа к дашборду
- Реализовать dependency для FastAPI (get_current_user)
- Реализовать проверку прав на уровне API

**Функции:**
- `check_role(user, required_role)`
- `check_dashboard_access(user_id, dashboard_id)`
- `get_current_user(token)` - FastAPI dependency

---

## Этап 5: API уровень (FastAPI)

### 5.1 Аутентификация API
**Цель:** Создать эндпоинты для auth

**Файлы:**
- `src/mko_bi/api/routes/auth.py`

**Задачи:**
- Эндпоинт /auth/login (POST)
- Эндпоинт /auth/register (POST)
- Эндпоинт /auth/refresh (POST)
- Защита всех эндпоинтов JWT

**Маршруты:**
- POST /auth/login
- POST /auth/register
- POST /auth/refresh

---

### 5.2 Пользователи API
**Цель:** Создать эндпоинты для управления пользователями

**Файлы:**
- `src/mko_bi/api/routes/users.py`

**Задачи:**
- Эндпоинт GET /users (список пользователей, admin only)
- Эндпоинт GET /users/{id} (получить пользователя)
- Эндпоинт PUT /users/{id} (обновить пользователя)
- Эндпоинт DELETE /users/{id} (удалить пользователя)

**Маршруты:**
- GET /users
- GET /users/{user_id}
- PUT /users/{user_id}
- DELETE /users/{user_id}

---

### 5.3 Дашборды API
**Цель:** Создать эндпоинты для CRUD дашбордов

**Файлы:**
- `src/mko_bi/api/routes/dashboards.py`

**Задачи:**
- Эндпоинт POST /dashboards (создать)
- Эндпоинт GET /dashboards (список доступных)
- Эндпоинт GET /dashboards/{id} (получить)
- Эндпоинт PUT /dashboards/{id} (обновить)
- Эндпоинт DELETE /dashboards/{id} (удалить)
- Эндпоинт POST /dashboards/{id}/access (управление доступом)

**Маршруты:**
- POST /dashboards
- GET /dashboards
- GET /dashboards/{dashboard_id}
- PUT /dashboards/{dashboard_id}
- DELETE /dashboards/{dashboard_id}
- POST /dashboards/{dashboard_id}/access

---

### 5.4 Загрузка данных API
**Цель:** Создать эндпоинты для загрузки CSV

**Файлы:**
- `src/mko_bi/api/routes/upload.py`

**Задачи:**
- Эндпоинт POST /upload (загрузка CSV)
- Эндпоинт POST /upload/{dashboard_id}/process (триггер обработки)
- Эндпоинт GET /upload/status/{task_id} (статус обработки)

**Маршруты:**
- POST /upload
- POST /upload/{dashboard_id}/process
- GET /upload/status/{task_id}

---

### 5.5 Данные API
**Цель:** Создать эндпоинты для получения агрегированных данных

**Файлы:**
- `src/mko_bi/api/routes/data.py`

**Задачи:**
- Эндпоинт GET /data/{dashboard_id} (получить агрегаты)
- Эндпоинт GET /data/{dashboard_id}/charts (данные для графиков)
- Эндпоинт POST /data/filter (применить фильтры)

**Маршруты:**
- GET /data/{dashboard_id}
- GET /data/{dashboard_id}/charts
- POST /data/filter

---

## Этап 6: Слой дашбордов (Dash + Plotly)

### 6.1 Базовая инфраструктура дашбордов
**Цель:** Создать базовый класс и реестр дашбордов

**Файлы:**
- `src/mko_bi/dashboards/base.py`
- `src/mko_bi/dashboards/registry.py`

**Задачи:**
- Создать базовый класс DashboardBase
- Реализовать реестр для регистрации дашбордов
- Реализовать фабрику создания дашбордов

**Классы:**
- `DashboardBase` (абстрактный базовый класс)
- `DashboardRegistry` (реестр дашбордов)

---

### 6.2 Компоненты дашбордов
**Цель:** Создать компоненты для графиков и фильтров

**Файлы:**
- `src/mko_bi/dashboards/components/charts/bar.py`
- `src/mko_bi/dashboards/components/charts/dot.py`
- `src/mko_bi/dashboards/components/filters.py`
- `src/mko_bi/dashboards/components/layout.py`

**Задачи:**
- Реализовать компонент Bar Chart
- Реализовать компонент Line Chart (dot.py)
- Реализовать компонент Pie Chart
- Реализовать компонент Table
- Реализовать компонент Filters (глобальные фильтры)
- Реализовать компонент Layout (компоновка)

**Классы:**
- `BarChart`
- `LineChart`
- `PieChart`
- `DataTable`
- `FilterPanel`
- `DashboardLayout`

---

### 6.3 Конкретные реализации дашбордов
**Цель:** Создать примеры реализации конкретных дашбордов

**Файлы:**
- `src/mko_bi/dashboards/implementations/dashboard_1.py`
- `src/mko_bi/dashboards/implementations/dashboard_2.py`

**Задачи:**
- Реализовать Dashboard1 (пример с bar и line)
- Реализовать Dashboard2 (пример с pie и table)
- Настроить конфигурацию графиков
- Настроить фильтры

**Классы:**
- `Dashboard1`
- `Dashboard2`

---

## Этап 7: Основное приложение

### 7.1 Точка входа FastAPI
**Цель:** Создать основное приложение FastAPI

**Файлы:**
- `src/mko_bi/main.py`
- `src/mko_bi/app.py`

**Задачи:**
- Создать FastAPI приложение
- Зарегистрировать все роуты
- Настроить middleware (CORS, GZip)
- Настроить обработку ошибок
- Добавить документацию Swagger/ReDoc

**Классы/Функции:**
- `FastAPI` app конфигурация
- `include_router` для всех модулей
- Обработчики исключений

---

### 7.2 Утилиты
**Цель:** Создать вспомогательные утилиты

**Файлы:**
- `src/mko_bi/utils/exceptions.py`
- `src/mko_bi/utils/file_utils.py`
- `src/mko_bi/utils/time_utils.py`

**Задачи:**
- Создать кастомные исключения
- Реализовать утилиты для работы с файлами
- Реализовать утилиты для работы со временем

**Классы:**
- `HTTPException` обертки
- `FileUtils` (чтение/запись/удаление файлов)
- `TimeUtils` (форматирование дат)

---

## Этап 8: Тестирование

### 8.1 Тесты моделей и репозиториев
**Цель:** Написать unit тесты для моделей и репозиториев

**Файлы:**
- `tests/test_models.py`
- `tests/test_repositories.py`

**Задачи:**
- Тесты создания моделей
- Тесты CRUD операций
- Тесты связей между моделями

---

### 8.2 Тесты сервисов
**Цель:** Написать unit тесты для бизнес-логики

**Файлы:**
- `tests/services/test_auth_service.py`
- `tests/services/test_user_service.py`
- `tests/services/test_dashboard_service.py`
- `tests/services/test_data_service.py`

**Задачи:**
- Тесты аутентификации
- Тесты управления пользователями
- Тесты управления дашбордами
- Тесты обработки данных

---

### 8.3 Тесты API
**Цель:** Написать интеграционные тесты для API

**Файлы:**
- `tests/api/test_auth.py`
- `tests/api/test_users.py`
- `tests/api/test_dashboards.py`
- `tests/api/test_upload.py`

**Задачи:**
- Тесты эндпоинтов аутентификации
- Тесты эндпоинтов пользователей
- Тесты эндпоинтов дашбордов
- Тесты эндпоинтов загрузки

---

### 8.4 Тесты данных
**Цель:** Написать тесты для пайплайна данных

**Файлы:**
- `tests/data/test_pipeline.py`
- `tests/data/test_processing.py`

**Задачи:**
- Тесты загрузки CSV
- Тесты трансформации данных
- Тесты агрегации
- Тесты сохранения в БД

---

## Этап 9: Деплой и CI/CD

### 9.1 Настройка окружения
**Цель:** Подготовить окружение для деплоя

**Файлы:**
- `docker-compose.yml`
- `Dockerfile`
- `nginx/nginx.conf`

**Задачи:**
- Настроить Docker контейнеры
- Настроить PostgreSQL контейнер
- Настроить Nginx реверс-прокси
- Настроить переменные окружения

---

## Приоритеты реализации:

### Высокий приоритет (MVP):
1. Этап 1 - Базовая настройка
2. Этап 2 - Слой данных (модели, схемы, репозитории)
3. Этап 3.1-3.2 - Сервисы аутентификации и пользователей
4. Этап 4 - Слой доступа
5. Этап 5.1-5.2 - API аутентификации и пользователей
6. Этап 7 - Основное приложение
7. Этап 8 - Базовые тесты

### Средний приоритет:
1. Этап 3.3-3.4 - Сервисы дашбордов и данных
2. Этап 5.3-5.5 - Остальные API
3. Этап 6 - Слой дашбордов
4. Этап 8 - Продвинутые тесты

### Низкий приоритет:
1. Этап 9 - Деплой и CI/CD
2. Дополнительные фичи и оптимизации