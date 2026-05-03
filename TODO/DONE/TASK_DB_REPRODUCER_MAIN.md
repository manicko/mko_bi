# Техническое задание: Модуль воспроизведения структуры БД

**Версия**: 1.1 (объединенная)
**Дата**: 2026-05-03
**Статус**: Ready for development
**Автор**: Lead Python Architect

---

## 1. Цель модуля

Создать Python-модуль для автоматического воспроизведения структуры базы данных на целевом сервере. Модуль должен:

- Проверять наличие и состояние БД при старте FastAPI приложения
- Применять миграции Alembic в соответствии с окружением
- Обеспечивать идемпотентность (повторный запуск не меняет схему)
- Безопасно работать в production (без автоматических destructive операций)
- Корректно работать в async контексте FastAPI (lifespan)

---

## 2. Архитектура модуля

### 2.1 Расположение

```
src/mko_bi/db/
├── base.py              # SQLAlchemy Base (существует)
├── models/             # SQLAlchemy модели (существует)
├── repositories/       # Репозитории (существует)
├── session.py          # Session maker (существует)
└── starter.py          # <-- НОВЫЙ МОДУЛЬ
```

### 2.2 Интеграция с FastAPI

Модуль вызывается из `src/mko_bi/app.py` через lifespan context manager:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from mko_bi.db.starter import DatabaseStarter


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения."""
    starter = DatabaseStarter()
    await starter.startup()
    yield
    await starter.shutdown()
```

---

## 3. Функциональные требования

### 3.1 Определение окружения

Модуль определяет окружение через переменную `ENV` с использованием `EnvironmentEnum` из `mko_bi/models/types.py`:

Приоритет определения:
1. Переменная окружения `ENV`
2. Значение по умолчанию: `development`

### 3.2 Проверка существования БД

Для основной БД (`MAIN_DATABASE_URL`):
- Если БД не существует → выбросить исключение `DatabaseNotFoundError`
- Автоматическое создание БД **запрещено** (кроме тестовой)

Для тестовой БД (`TEST_DATABASE_URL`):
- Если флаг `RECREATE_TEST_DB=true` → DROP + CREATE
- DROP выполняется через `WITH (FORCE)` для завершения активных соединений

### 3.3 Проверка схемы (миграций)

Проверка наличия применённых миграций:
- Проверка таблицы `alembic_version`
- Если таблица отсутствует → схема не применена

Логика по окружениям:

| Окружение | Схема есть | Схема отсутствует |
|-----------|-----------|-------------------|
| production | Продолжить | Исключение + инструкция |
| staging | Продолжить | AUTO_MIGRATE=true → migrate |
| development | Продолжить | AUTO_MIGRATE=true → migrate |
| test | Пересоздать | Создать + migrate |

### 3.4 Применение миграций

Миграции выполняются через Alembic API (не subprocess):

```python
from alembic import command
from alembic.config import Config

def run_migrations(alembic_cfg_path: str) -> None:
    """Применение миграций через Alembic API."""
    alembic_cfg = Config(alembic_cfg_path)
    command.upgrade(alembic_cfg, "head")
```

Для async Alembic (`env.py` уже настроен на async):
- Выполняется в отдельном thread через `asyncio.to_thread()`
- Не блокирует event loop

### 3.5 Идемпотентность

- Повторный запуск не применяет уже применённые миграции
- Alembic сам отслеживает состояние через `alembic_version`

---

## 4. Конфигурация

### 4.1 Переменные окружения

| Переменная | Описание | По умолчанию | Обязательная |
|-----------|----------|--------------|--------------|
| `ENV` | Окружение | `development` | Нет |
| `MAIN_DATABASE_URL` | URL основной БД | - | Да |
| `TEST_DATABASE_URL` | URL тестовой БД | - | Нет |
| `AUTO_MIGRATE` | Авто-миграции | `false` (prod), `true` (dev) | Нет |
| `MIGRATION_SCRIPT_PATH` | Путь к миграциям | `alembic` | Нет |
| `ALEMBIC_INI_PATH` | Путь к alembic.ini | `alembic.ini` | Нет |
| `RECREATE_TEST_DB` | Пересоздание тестовой БД | `false` | Нет |

### 4.2 Pydantic модель конфигурации

```python
from pydantic import BaseModel
from mko_bi.models.types import EnvironmentEnum

class DatabaseStarterConfig(BaseModel):
    """Конфигурация модуля воспроизведения БД."""

    env: EnvironmentEnum = EnvironmentEnum.DEVELOPMENT
    main_database_url: str
    test_database_url: str | None = None
    auto_migrate: bool = False
    migration_script_path: str = "alembic"
    alembic_ini_path: str = "alembic.ini"
    recreate_test_db: bool = False

    model_config = {"extra": "ignore"}
```

---

## 5. Требования безопасности (Production)

Модуль **НЕ должен**:

1. Автоматически создавать production БД
2. Выполнять destructive миграции без подтверждения
3. DROP/RESET production схему
4. Менять структуру production без явного указания

В production при отсутствии схемы:

```python
class SchemaNotFoundError(Exception):
    """Схема БД не найдена."""

    def __init__(self, db_url: str):
        super().__init__(
            f"Database schema not found. "
            f"Please run migrations manually: "
            f"alembic upgrade head"
        )
```

---

## 6. Требования к реализации

### 6.1 Структура класса DatabaseStarter

```python
import logging
from asyncio import to_thread
from enum import StrEnum
from typing import Any

from sqlalchemy import Engine, text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

logger = logging.getLogger(__name__)


class DatabaseStarter:
    """Модуль воспроизведения структуры БД."""

    def __init__(self) -> None:
        self._config = self._load_config()
        self._engine: AsyncEngine | None = None

    def _load_config(self) -> DatabaseStarterConfig:
        """Загрузка конфигурации из переменных окружения."""
        ...

    async def startup(self) -> None:
        """Действия при старте приложения."""
        logger.info(f"Starting database initialization for ENV={self._config.env}")

        # 1. Проверка существования БД
        await self._check_database_exists()

        # 2. Проверка схемы
        schema_exists = await self._check_schema_exists()

        # 3. Применение миграций (если нужно)
        if not schema_exists:
            await self._handle_missing_schema()

        logger.info("Database initialization completed")

    async def shutdown(self) -> None:
        """Действия при завершении приложения."""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database engine disposed")

    async def _check_database_exists(self) -> None:
        """Проверка существования БД."""
        ...

    async def _check_schema_exists(self) -> bool:
        """Проверка наличия таблицы alembic_version."""
        ...

    async def _handle_missing_schema(self) -> None:
        """Обработка отсутствия схемы."""
        ...
```

### 6.2 Проверка существования БД

Использовать SQLAlchemy async engine для проверки:

```python
async def _check_database_exists(self) -> None:
    """Проверка существования БД через попытку подключения."""
    try:
        engine = create_async_engine(self._config.main_database_url)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        logger.info("Database exists and is accessible")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise DatabaseNotFoundError() from e
```

### 6.3 Async-безопасность

- Запуск Alembic миграций через `asyncio.to_thread()`
- Не использовать sync SQLAlchemy engine внутри async runtime
- Корректное закрытие соединений через context manager

```python
async def _run_migrations(self) -> None:
    """Запуск миграций в отдельном thread."""
    logger.info("Running Alembic migrations...")

    def _sync_migrate() -> None:
        alembic_cfg = Config(self._config.alembic_ini_path)
        command.upgrade(alembic_cfg, "head")

    await to_thread(_sync_migrate)
    logger.info("Migrations applied successfully")
```

---

## 7. Тестовая БД

### 7.1 Пересоздание тестовой БД

```python
async def recreate_test_database(self) -> None:
    """Полное пересоздание тестовой БД."""
    if not self._config.test_database_url:
        raise ValueError("TEST_DATABASE_URL not configured")

    # Парсинг URL для получения имени БД
    db_name = self._extract_db_name(self._config.test_database_url)

    # DROP WITH FORCE
    sys_db_url = self._get_system_db_url(self._config.test_database_url)
    engine = create_async_engine(sys_db_url)

    async with engine.connect() as conn:
        await conn.execute(text(f"DROP DATABASE IF EXISTS {db_name} WITH (FORCE)"))
        await conn.execute(text(f"CREATE DATABASE {db_name}"))

    await engine.dispose()

    # Применение миграций
    await self._run_migrations_for_url(self._config.test_database_url)
```

---

## 8. Логирование

Все шаги должны логироваться через стандартный `logging`:

Уровни логирования:
- `INFO` — штатные операции (проверка БД, применение миграций)
- `WARNING` — некритичные проблемы (схема отсутствует, но будет применена)
- `ERROR` — критические ошибки (БД недоступна, миграция упала)

---

## 9. Используемые Enum

Все перечисления должны использовать `StrEnum` из `mko_bi/models/types.py`:

Запрещено использовать:
- `dict` для маппинга констант (используйте Enum)
- `list` для валидации допустимых значений (используйте Enum)

---

## 10. Критерии приёмки

1. ✅ Модуль расположен в `src/mko_bi/db/starter.py`
2. ✅ Использует `asyncio.to_thread()` для Alembic миграций
3. ✅ Интегрирован с FastAPI через `lifespan`
4. ✅ Поддерживает переменную `ENV` (production/staging/development/test)
5. ✅ В production не создаёт БД и не делает destructive operations
6. ✅ В test окружении разрешено пересоздание БД
7. ✅ Идемпотентность соблюдена
8. ✅ Все шаги логируются (INFO/ERROR)
9. ✅ Использует StrEnum вместо dict/list для констант
10. ✅ Конфигурация через Pydantic модель
11. ✅ Написаны unit-тесты
12. ✅ Проверки mypy и ruff пройдены

---

## 11. Дополнительные замечания

- Не использовать `subprocess` для запуска Alembic (только API)
- Обрабатывать исключения с информативными сообщениями
- Закрывать все connections/engines через `async with` или `try/finally`
- Использовать типизацию (`-> None`, `async -> bool`, etc.)
- Функции должны быть маленькими (до 20 строк)
- Использовать декомпозицию: `_check_*`, `_handle_*`, `_run_*`

---

**Конец технического задания**
