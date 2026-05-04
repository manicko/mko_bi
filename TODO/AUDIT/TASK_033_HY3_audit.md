# TASK_033_HY3: Анализ соответствия кода ТЗ и выявление архитектурных проблем

**Дата аудита:** 2026-05-03  
**Модель:** tencent/hy3-preview:free  
**Окружение:** Windows 10, Python 3.12, PostgreSQL 18, uv

---

## 1. Матрица соответствия ТЗ (SPEC.md)

| Требование SPEC.md | Статус | Комментарий |
|---|---|---|
| **1. Загрузка CSV (.csv, .csv.gz)** | ✅ | Эндпоинт `POST /upload/{dashboard_id}` реализован в `api/routes/upload.py:39-126`. Поддерживается gzip через `gzip.open()` в `data/loaders/loader.py:92-98` |
| **2. Обработка через Polars** | ✅ | Используется `polars` в `data_service.py:152-176` и `data/processing/transformations.py` |
| **3. Трансформации (groupby, YoY, доли)** | ⚠️ | YoY и доли реализованы в `transformations.py:228-360`, но интеграция с `data_service.py` неполная - используются упрощенные функции `_apply_aggregations`, `_apply_filters` вместо вызова `calculate_aggregations` |
| **4. Хранение агрегатов в PostgreSQL** | ✅ | Таблица `aggregated_data` (JSONB), репозиторий `aggregated_data_repo.py` реализован |
| **5. JWT + bcrypt** | ✅ | `core/security.py` - полная реализация. `RateLimiter` с Redis для защиты входа |
| **6. Роли (admin, editor, viewer)** | ✅ | `core/permissions.py` - иерархия ролей, проверка прав доступа |
| **7. Dash + Plotly дашборды** | ⚠️ | Dash интегрирован (`dash_app.py`), но использует заглушки вместо реальных данных (строки 622-643, 867-881) |
| **8. Типы графиков (bar, line, pie, table)** | ✅ | Компоненты в `dashboards/components/charts/` |
| **9. Фильтры (year, category, brand)** | ⚠️ | Панель фильтров создана в `dash_app.py:661-739`, но реальная фильтрация данных не реализована (callback `apply_dashboard_filters` выбрасывает `PreventUpdate` на строке 787) |
| **10. Логирование (upload, processing, errors, access)** | ✅ | Логирование настроено, `processing_logs` таблица используется |
| **11. Rate limiting** | ⚠️ | Реализован только для `/auth/login` (`auth_service.py:209`). Для upload endpoints НЕ реализован (SPEC.md п.6) |
| **12. MIME-type проверка** | ❌ | Проверяется только расширение файла (`data_service.py:60`), но НЕТ проверки MIME-type (`text/csv`, `application/gzip`) как требует SPEC.md п.6 |
| **13. Максимальный размер файла** | ✅ | Ограничение 100MB в `config.py:56` и проверка в `data_service.py:71-83` |
| **14. Удаление временных файлов** | ✅ | Файлы удаляются в `finally` блоке `data_service.py:751-757` |
| **15. SQL через parameterized queries** | ✅ | Используется SQLAlchemy ORM, raw SQL не обнаружено |
| **16. Multi-axis, комбинированные графики** | ❌ | Не найдено реализации в коде |
| **17. Layouts (UI композиция)** | ⚠️ | Таблица `layouts` есть, но интеграция с Dash не завершена |

---

## 2. Архитектурные проблемы

### 2.1. Смешение синхронного и асинхронного кода (CRITICAL)

**Проблема:** В проекте используется асинхронная конфигурация (asyncpg, async session), но значительная часть сервисов написана с синхронным кодом.

**Файлы:**
- `services/data_service.py` - использует `from sqlalchemy.orm import Session` (синхронный) в строках 16, 310, 399, 524
- `services/auth_service.py` - использует `AsyncSession` корректно, но `deps.py:77-88` создает синхронные репозитории
- `db/repositories/user_repo.py` (нужно проверить) - если репозитории синхронные, они несовместимы с async session

**Рекомендация:** Унифицировать - либо полностью async (предпочтительно для FastAPI + asyncpg), либо полностью sync.

### 2.2. Неиспользуемые абстракции (MEDIUM)

**Проблема:** Класс `CSVLoader` в `data/loaders/loader.py` не используется в `data_service.py`. Вместо этого там продублированы функции `_read_csv_safe`, `_validate_file_size`.

**Код:**
```python
# data_service.py не использует:
from mko_bi.data.loaders.loader import CSVLoader
# Вместо этого там свои функции
```

**Рекомендация:** Удалить дублирование, использовать `CSVLoader` или удалить неиспользуемый код.

### 2.3. Циклические импорты (LOW)

**Проблема:** В `deps.py` импорты репозиториев и сервисов выполняются внутри функций (ленивая загрузка), что скрывает потенциальные циклические зависимости.

**Статус:** На данный момент работает, но архитектурно это "code smell".

### 2.4. Нарушение Dependency Inversion (MEDIUM)

**Проблема:** В `deps.py` создаются конкретные реализации, а не через контейнер DI:

```python
# deps.py:86-87
def get_user_repository(...):
    from mko_bi.db.repositories.user_repo import UserRepository
    return UserRepository()  # Конкретная реализация
```

Но интерфейсы в `interfaces/service_interfaces.py` определены, что хорошо.

### 2.5. Глобальное состояние (LOW)

**Проблема:** Синглтон конфигурации в `config.py:214-229`:

```python
_settings: Settings | None = None

def get_config() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

**Риск:** В многопоточном окружении может потребоваться `threading.Lock()`.

---

## 3. Проблемы в коде

### 3.1. Дублирование кода в data_service.py (HIGH)

**Файл:** `services/data_service.py`

**Проблема:** Функция `_upload_file_logic` содержит ДВАЖДЫ повторяющийся блок кода (строки 443-476 дублируются):

```python
# Первый раз (строки 443-476):
processing_log = ProcessingLogRepository.create(db, **log_create.model_dump())
logger.info("Лог обработки создан в БД: id=%s", processing_log.id)
task_id = processing_log.id
...
return UploadResponse(...)

# Второй раз (строки 464-476) - МЕРТВЫЙ КОД:
processing_log = ProcessingLogRepository.create(db, **log_create.model_dump())
logger.info("Лог обработки создан в БД: id=%s", processing_log.id)
...
return UploadResponse(...)  # Никогда не выполнится
```

**Статус:** Dead code, потенциальная ошибка.

### 3.2. Нереализованная логика (MEDIUM)

**Файл:** `services/data_service.py:375-389`

```python
if processing_config:
    if processing_config.groupby and processing_config.aggregations:
        # Собираем агрегированные данные...
        pass  # <-- НИЧЕГО НЕ ДЕЛАЕТ!
```

**Рекомендация:** Удалить `pass` и реализовать логику или удалить весь блок.

### 3.3. Небезопасная работа с файлами (MEDIUM)

**Файл:** `services/data_service.py:596-609`

**Проблема:** Поиск файла по паттерну `*_{dashboard_id}_*.csv.gz` может найти неправильный файл, если их несколько:

```python
csv_files = list(upload_dir.glob(f"*_{dashboard_id}_*.csv.gz"))
if not csv_files:
    csv_files = list(upload_dir.glob("*.csv.gz"))  # Берет ЛЮБОЙ файл!
```

**Рекомендация:** Хранить путь к файлу в БД (в `processing_logs`).

### 3.4. Игнорирование ошибок (LOW)

**Файл:** `services/data_service.py:691-695`

```python
except Exception as save_error:
    logger.error("Ошибка при сохранении агрегированных данных: %s", save_error)
    # Не прерываем обработку из-за ошибки сохранения  <-- Игнорируем?
```

**Вопрос:** Стоит ли продолжать, если данные не сохранились?

### 3.5. Неправильная работа с транзакциями (MEDIUM)

**Файл:** `services/auth_service.py:124-143`

**Проблема:** Используется `async with db.begin():`, но при ошибке транзакция откатывается автоматически. Однако в `data_service.py` транзакции не используются явно:

```python
# data_service.py - нет явного commit/rollback
ProcessingLogRepository.create(db, **log_create.model_dump())
# Если следующая строка упадет, данные могут быть несогласованы
```

### 3.6. Утечка ресурсов (LOW)

**Файл:** `services/data_service.py:128-129`

```python
with open(file_path, "wb") as f:
    f.write(file_content)
# Файл закрывается корректно через with
```

Но в `_read_csv_safe` (строка 152-176) используется `pl.read_csv(file_path)` который читает ВЕСЬ файл в память. Для больших файлов >100MB это риск.

### 3.7. Потенциальные проблемы типизации (LOW)

**Файл:** `services/data_service.py:308`

```python
dashboard_id: int | None = None,  # В моделях dashboard_id - UUID
```

**Проблема:** Несоответствие типов `int` vs `UUID` для `dashboard_id` по всему коду.

---

## 4. Проблемы typing (mypy/ruff)

### 4.1. Результаты проверки

```bash
$ uv run ruff check .
All checks passed!  ✅

$ uv run mypy src/
Success: no issues found in 97 source files  ✅
```

**Статус:** Проверки пройдены успешно.

### 4.2. Игнорирование типов (SMELL)

**Файлы:**
- `config.py:4` - `# mypy: ignore-errors`
- `core/security.py:3` - `# mypy: ignore-errors`

**Проблема:** Игнорирование ошибок mypy вместо исправления типов.

---

## 5. Неполные/пустые файлы и заглушки

### 5.1. Dash заглушки (HIGH)

**Файл:** `dash_app.py`

- Строки 622-643: Данные дашборда захардкожены (заглушка)
- Строки 867-881: Графики используют примерные данные вместо API
- Строка 787: `raise PreventUpdate` - фильтры не работают

### 5.2. Dead code (MEDIUM)

**Файл:** `services/data_service.py`

- Строки 464-476: Повторный возврат из `_upload_file_logic` (мертвый код)
- Строка 380: `pass` в `_process_csv_file`

### 5.3. Пустые файлы

Проверка структуры показала наличие файлов, которые могут быть заглушками:
- `data/storage/manager.py` - нужно проверить содержимое
- `dashboards/implementations/dashboard_1.py` и `dashboard_2.py` - возможно пустые

---

## 6. Безопасность

### 6.1. Отсутствие проверки MIME-type (HIGH) - НАРУШЕНИЕ SPEC.md

**Файл:** `services/data_service.py:58-69`

**Проблема:** SPEC.md п.6 требует:
> "Обязательна проверка MIME-type загружаемых файлов (`text/csv`, `application/gzip`)"

**Текущая реализация:** Проверяет только расширение файла:

```python
if not any(filename.lower().endswith(ext.lower()) for ext in allowed_types):
    raise ValueError(...)
```

**Рекомендация:** Добавить проверку MIME-type через `file.content_type` или `python-magic`.

### 6.2. Rate limiting не для всех endpoints (MEDIUM) - НАРУШЕНИЕ SPEC.md

**Файл:** `core/security.py:23-37`

**Проблема:** SPEC.md п.6 требует:
> "Для upload endpoints должен использоваться rate limiting"

**Текущая реализация:** Rate limiting только для `/auth/login` (`auth_service.py:209`).

### 6.3. SQL Injection (PASS)

Проверка показала использование SQLAlchemy ORM - SQL injection невозможна.

---

## 7. Производительность

### 7.1. Загрузка всего CSV в память (MEDIUM)

**Файл:** `services/data_service.py:152-176`

Используется `pl.read_csv(file_path)` или `pl.scan_csv().collect()` - весь файл в памяти.

**Рекомендация:** Для файлов >50MB использовать lazy evaluation (уже частично реализовано через `lazy_threshold_mb`).

### 7.2. N+1 запросы (LOW)

**Файл:** `services/data_service.py:628-634`

```python
graphs = db.query(graphs_model.Graph).filter(...).all()
for graph in graphs:
    aggregates = db.query(aggregated_data_model.AggregatedData).filter(...).all()
```

**Проблема:** Для каждого графика отдельный запрос.

**Рекомендация:** Использовать `joinedload` или один запрос с JOIN.

---

## 8. Конфигурация

### 8.1. Секреты в коде (PASS)

Пароли и секреты вынесены в `app.yaml` и переменные окружения через pydantic-settings.

### 8.2. Хардкод (LOW)

**Файл:** `dash_app.py`

- Строки 682-684: Хардкоженные годы `2023, 2024`
- Строки 698-700: Хардкоженные категории
- Функции `_create_bar_chart`, `_create_line_chart` и др. - примерные данные

---

## 9. Итоговый рейтинг проблем

| Severity | Количество | Примеры |
|---|---|---|
| **CRITICAL** | 1 | Смешение sync/async кода |
| **HIGH** | 3 | Дублирование кода, отсутствие MIME check, Dash заглушки |
| **MEDIUM** | 5 | Неиспользуемые абстракции, нереализованная логика, rate limiting |
| **LOW** | 4 | Игнорирование ошибок, хардкод, утечки ресурсов |

---

## 10. Рекомендации по исправлению

### Приоритет 1 (Критические)

1. **Унифицировать sync/async код:**
   - Либо перевести все сервисы на `AsyncSession`
   - Либо использовать синхронный драйвер (psycopg2) вместо asyncpg

2. **Исправить дублирование в `data_service.py:_upload_file_logic`:**
   - Удалить мертвый код (строки 464-476)

### Приоритет 2 (Высокие)

3. **Добавить MIME-type проверку** для загружаемых файлов (REQUIRED by SPEC)
4. **Реализовать Rate limiting** для upload endpoints
5. **Удалить/реализовать заглушки в Dash** - подключить реальные API вызовы

### Приоритет 3 (Средние)

6. **Использовать `CSVLoader`** вместо дублирования функций
7. **Исправить несоответствие типов** `dashboard_id` (int vs UUID)
8. **Добавить транзакции** в `data_service.py`
9. **Реализовать фильтрацию данных** в Dash (сейчас `PreventUpdate`)

---

## 11. Заключение

Проект имеет **хорошую архитектурную основу**:
- ✅ Чистая архитектура (интерфейсы, сервисы, репозитории)
- ✅ Разделение предметных областей
- ✅ Типизация (mypy/ruff пройдены)
- ✅ Безопасность (JWT, bcrypt, parameterized queries)

**Основные проблемы:**
- ❌ Смешение синхронного и асинхронного кода
- ❌ Неполная реализация (заглушки в Dash)
- ❌ Нарушение требований SPEC.md (MIME-type, rate limiting)

**Общая оценка готовности:** ~70% (архитектура готова, требуется доработка интеграции и исправление критических ошибок).
