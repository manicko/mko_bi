---
name: Agent Guidelines
description: Обязательные правила и контекст для работы над проектом
alwaysApply: true
---

#Key links
[Project Structure](C:\py_dev\mkobi\.ai\structure\map.md)
[Full Project Structure including dependencies and semantic for audit and development)](C:\py_dev\mkobi\.ai\structure**)
[Important project specification](C:\py_dev\mkobi\docs\**)
[Docker specification](C:\py_dev\mkobi\docs\README_DOCKER.md)
[Important project commands](C:\py_dev\mkobi\.ai\context\commands.md)
[Important context](C:\py_dev\mkobi\.ai\context)


# Agent Guidelines — mkobi BI Dashboard

## 1. Основные принципы

- **Production-код — главный источник истины**.
- Предпочтение отдаётся **простоте, читаемости и поддерживаемости**.
- Соблюдать **Clean Architecture** (backend) и **Feature-Sliced Design** (frontend).
- Все комментарии, логи и docstring — **только на английском**.
- Избегать overengineering и ненужных абстракций.

## 2. Структура проекта

**Backend:**
- `src/mkobi/` — основной пакет
  - `api/` — HTTP-слой (роуты + deps)
  - `services/` — бизнес-логика
  - `db/` — модели SQLAlchemy + repositories
  - `models/` — Pydantic модели + enums
  - `data/` — загрузка, обработка (Polars) и сохранение данных
  - `core/` — security, permissions, logging, config
  - `interfaces/` — абстракции для DI
  - `utils/` — вспомогательные функции
  - `workers/` — фоновые задачи

**Frontend:**
- `frontend/src/`
  - `app/` — провайдеры и роутинг
  - `features/` — бизнес-фичи (auth, dashboards, upload, admin и т.д.)
  - `shared/` — переиспользуемый код (api, components, types)

**Другое:**
- `tests/` — все тесты (pytest)
- `alembic/` — миграции БД
- `docker-compose*.yml` + `Dockerfile`

## 3. Технологический стек (обязательно соблюдать)

- **Backend**: FastAPI, Pydantic v2, SQLAlchemy 2.0 (async), asyncpg, Polars, StrEnum
- **Frontend**: React 18 + TypeScript, TanStack Query, React Hook Form + Zod, Plotly.js React
- **БД**: PostgreSQL + JSONB, Alembic
- **Инструменты**: uv, ruff, mypy

**Запрещено:**
- pandas
- `print()`
- raw SQL через f-strings
- русский язык в коде, логах и комментариях

## 4. Критические правила

### Backend
- Чёткое разделение слоёв: **API → Service → Repository**
- Все публичные функции и методы — с type hints
- Все константы и статусы — через `StrEnum` (`src/mkobi/models/enums.py`)
- Логирование: `logger = logging.getLogger(__name__)`
- Временные файлы после обработки **обязательно удалять**
- Access control проверяется на каждом запросе к дашборду

### Data Processing
- Использовать только **Polars**
- При загрузке файла — **полный пересчёт** агрегатов для дашборда
- Данные хранятся в `aggregated_data` (JSONB `dims` + `metrics`)

### Code Quality
- Ruff + mypy должны проходить без ошибок
- Маленькие функции, понятные имена
- Комментарии — только к нетривиальной логике

### Security
- JWT + bcrypt
- Rate limiting + MIME-type + размер файла на upload
- Secrets только через окружение (поддержка `_FILE`)

## 5. Основной Data Flow

1. Upload (`POST /upload/{dashboard_id}`)
2. Сохранение во временную папку (`platformdirs`)
3. Валидация → Parse (Polars)
4. Transform + Aggregate (по `processing_configs`)
5. Сохранение в `aggregated_data`
6. Frontend получает данные через `/data/aggregated`

## 6. Что всегда проверять

- Соответствие архитектуре (не смешивать слои)
- Использование `StrEnum`
- Корректный cleanup временных файлов
- Наличие type hints
- Английский язык в логах и комментариях
- Соответствие спецификации (`SPEC.md`)

---

**Главный девиз:**

> Пиши явно, просто и надёжно.  
> Код должен быть понятен через 6 месяцев без дополнительных объяснений.

