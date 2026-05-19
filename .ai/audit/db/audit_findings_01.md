C:\py_dev\mkobi\src\mkobi\db\starter.py есть несколько архитектурных и production-проблем, которые стоит исправить.

## Что хорошо

* Четкое разделение startup/shutdown lifecycle.
* Async SQLAlchemy используется корректно.
* Alembic запускается через `asyncio.to_thread`.
* Идемпотентный `ensure_admin_user`.
* Есть cleanup старых логов и temp files.
* Хорошая типизация.
* Нормальные custom exceptions.
* Конфиг вынесен отдельно.

---

# Основные проблемы

## 1. Жестко захардкожено имя test DB

Сейчас:

```python
WHERE datname = 'bidb_test'
DROP DATABASE IF EXISTS bidb_test
CREATE DATABASE bidb_test
```

Это ломает универсальность.

Нужно парсить database name из URL.

Например:

```python
from sqlalchemy.engine.url import make_url

url = make_url(test_url)
db_name = url.database
```

И дальше использовать bind parameters либо безопасное quoting.

---

## 2. SQL injection risk через DB name

Вот это:

```python
text(f"DROP DATABASE IF EXISTS {db_name}")
```

делать нельзя даже для internal tooling.

Для PostgreSQL database name нельзя parameterize через bind params напрямую.

Используй:

```python
from sqlalchemy.sql import quoted_name
```

или psycopg sql.Identifier.

---

## 3. `_test_engine` никогда не используется

Ты создаешь:

```python
self._test_engine: AsyncEngine | None = None
```

Но:

* нигде не присваиваешь
* нигде не используешь

Это dead state.

Либо удалить, либо реально хранить engine.

---

## 4. Проверка schema existence ненадежная

Сейчас:

```python
WHERE table_name = 'alembic_version'
```

Проблемы:

* не проверяется schema
* может существовать table с таким именем не там
* не гарантирует актуальность миграций

Лучше:

```python
command.current(config)
```

или проверка head/current revision.

---

## 5. `except Exception` слишком широкие

Например:

```python
except Exception as e:
```

в startup.

Это скрывает реальные ошибки:

* auth failures
* DNS
* SSL
* timeout
* migration corruption

Лучше ловить:

```python
from sqlalchemy.exc import OperationalError
```

---

## 6. Race condition в ensure_admin_user

Сейчас:

```python
user = await get_by_email()

if user is None:
    create()
```

При двух parallel startup возможен race.

Ты partially mitigated через:

```python
except IntegrityError
```

Но лучше сразу делать UPSERT.

Например через PostgreSQL:

```sql
INSERT ...
ON CONFLICT DO NOTHING
```

---

## 7. Нет timeout для startup DB checks

Вот тут:

```python
await conn.execute(text("SELECT 1"))
```

может зависнуть.

Лучше:

```python
await asyncio.wait_for(...)
```

или через connect_args/connect_timeout.

---

## 8. `cleanup_old_logs()` никогда не вызывается

Метод есть, но lifecycle его не использует.

---

## 9. Потенциальная проблема с connection disposal

Тут:

```python
migration_engine = create_async_engine(test_url)
await self._apply_migrations(test_url)
await migration_engine.dispose()
```

`migration_engine` вообще не используется.

Лишний объект.

---

## 10. Startup делает слишком много

Сейчас startup:

* DB validation
* migrations
* schema validation
* admin bootstrap
* file cleanup
* test DB recreation

Это уже orchestration service.

Лучше разделить:

* MigrationService
* AdminBootstrapService
* CleanupService
* TestDatabaseService

---

# Очень важная production-проблема

## Alembic concurrent startup

Если у тебя несколько FastAPI instances стартуют одновременно:

* Kubernetes
* Docker replicas
* Gunicorn workers

то:

```python
command.upgrade(config, "head")
```

может выполняться параллельно.

Это опасно.

Нужен distributed lock.

Для PostgreSQL:

```sql
SELECT pg_advisory_lock(...)
```

перед миграцией.

---

# Архитектурное улучшение

## Сделать state machine startup

Сейчас linear script-style startup.

Лучше:

```python
class StartupStage(Enum):
    CONNECT_DB
    RUN_MIGRATIONS
    VERIFY_SCHEMA
    ENSURE_ADMIN
    CLEANUP
```

Тогда:

* лучше observability
* retry support
* metrics
* structured logging

---

# Логирование можно улучшить

Сейчас:

```python
logger.info("Running migrations for %s...", db_url)
```

Но URL может содержать credentials.

Нельзя логировать raw DB URL.

Используй sanitized URL:

```python
url.render_as_string(hide_password=True)
```

---

# Хороший production-grade вариант recreate DB

Сейчас rebuild через postgres DB — это норм.

Но лучше:

```sql
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = :db_name
AND pid <> pg_backend_pid()
```

Ты сейчас можешь terminate self connection indirectly.

---

# Minor issues

## Не нужен cast

```python
cast(AsyncEngine, self._main_engine)
```

Лучше:

```python
assert self._main_engine is not None
```

до блока.

---

## Неиспользуемый import

```python
from typing import cast
```

если убрать cast.

---

## create_async_engine без pooling config

Production обычно требует:

```python
pool_pre_ping = True
pool_recycle = 300
```

---

# Что я бы изменил в первую очередь

Приоритет:

1. Убрать hardcoded `bidb_test`
2. Добавить advisory lock на migrations
3. Sanitized logging
4. Исправить schema validation
5. Удалить unused engines/state
6. Сделать UPSERT admin creation
7. Добавить timeout/connect config

---

# Общая оценка

Для internal/backend service:

* code quality: 8/10
* production readiness: 6.5/10
* architecture: 7/10
* reliability under scale: 5/10

Главная проблема — concurrency + orchestration complexity при multi-instance deployment.
