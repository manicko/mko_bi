> **DEPRECATED**: This file has been moved to `docs/99-reference/run-guide.md` (translated to English). Please refer to the new location. This file is kept for backward compatibility and will be removed in a future release.

# Инструкция по запуску приложения

## Предварительные требования

- PostgreSQL установлен и запущен
- Python 3.12+
- uv (менеджер пакетов)

## Настройка через YAML конфиг

Все настройки находятся в файле: `src/mkobi/settings/app.yaml`

### Основные настройки

```yaml
# Окружение: development, staging, production, test
env: development

# Автоматические миграции (true/false)
auto_migrate: true

# Test database (опционально)
# test_database_url: "postgresql+asyncpg://postgres:1234@localhost:5432/bidb_test"
recreate_test_db: false

# Database
database:
  host: localhost
  port: 5432
  dbname: bidb
  user: postgres
  password: "1234"  # В продакшене используйте переменные окружения

# JWT
jwt:
  secret_key: "your-secret-key-change-in-production"
  algorithm: HS256
  access_token_expire_minutes: 30

# Upload
upload:
  temp_dir: "data/tmp_uploads"
  allowed_file_types:
    - ".csv.gz"
    - ".csv"
  max_file_size: 104857600  # 100MB
  lazy_threshold_mb: 10.0

# Redis
redis:
  host: localhost
  port: 6379
  db: 0

# Logging
logging:
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  level: INFO

# Charts
charts:
  default_colors:
    - "#1f77b4"
    - "#ff7f0e"
    - "#2ca02c"
    - "#d62728"
  yoy:
    current_year_style:
      line:
        dash: "solid"
        width: 3
    previous_year_style:
      line:
        dash: "dash"
        width: 2
  layout:
    template: "plotly_white"
    margin:
      l: 50
      r: 50
      t: 50
      b: 50

# CORS origins
cors_origins:
  - "https://example.com"
  - "https://app.example.com"
```

## Создание базы данных

```bash
# Через psql
set "PGPASSWORD=1234" & psql -h localhost -p 5432 -U postgres -c "CREATE DATABASE bidb;"
```

Или используйте скрипт:
```bash
set "PGPASSWORD=1234" & psql -h localhost -p 5432 -U postgres -f create_db.sql
```

## Запуск приложения

### Быстрый запуск (разработка)

```bash
uv run uvicorn mkobi.main:app --reload
```

Приложение будет доступно по адресу: http://127.0.0.1:8000

### Логи при успешном запуске

```
INFO:     Will watch for changes in these directories: ['C:\\py_exp\\mkobi']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [21368] using StatReload
Configuring CORS with allowed origins: [...]
Mounting Dash application at /dashboards
Инициализация Dash приложения
Dash приложение успешно инициализировано
Starting database initialization for ENV=development
Database exists and is accessible
Database initialization completed
```

## Доступ к Dash

После запуска Dash будет доступен по адресу:
- **Dashboards список**: http://localhost:8000/dashboards/
- **Конкретный дашборд**: http://localhost:8000/dashboards/dashboard/{dashboard_id}

## Проверка работоспособности

### API эндпоинты

```bash
# Проверка здоровья
curl http://localhost:8000/health

# Документация API
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

### Тестирование

```bash
# Запуск всех тестов
uv run pytest tests/ -v

# Запуск конкретного теста
uv run pytest tests/test_dashboards_api.py -v

# Проверка типов
uv run mypy src/mkobi/

# Проверка стиля кода
uv run ruff check .
```

## Возможные проблемы

### Ошибка подключения к PostgreSQL

**Решение**: Проверьте, что PostgreSQL запущен:
```bash
pg_isready -h localhost -p 5432
```

### Ошибка: "database 'bidb' does not exist"

**Решение**: Создайте базу данных (см. раздел "Создание базы данных").

### Ошибка миграций

**Решение**: Убедитесь, что `auto_migrate: true` в `app.yaml` или выполните миграции вручную:
```bash
uv run alembic upgrade head
```

## Структура конфигурации

Конфигурация находится в файле: `src/mkobi/settings/app.yaml`

Pydantic-settings читает настройки из YAML файла. Для чувствительных данных (пароли) рекомендуется использовать переменные окружения, переопределяя значения из YAML.

## Дополнительные команды

### Миграции базы данных (вручную)

```bash
# Применить миграции
uv run alembic upgrade head

# Создать новую миграцию
uv run alembic revision --autogenerate -m "description"

# Откатить миграцию
uv run alembic downgrade -1
```

### Пересоздание тестовой БД

Установите в `app.yaml`:
```yaml
test_database_url: "postgresql+asyncpg://postgres:1234@localhost:5432/bidb_test"
recreate_test_db: true
```

Затем запустите:
```bash
uv run python -m mkobi.db.starter --recreate-test-db
```
