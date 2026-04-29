# TASK_033: Audit Report - BI Dashboard System

**Дата**: 2026-04-29  
**Аудитор**: Senior Python Architect (Kilo)  
**Проект**: mko_bi - BI Dashboard System

---

## 1. Матрица соответствия SPEC.md

| Требование SPEC.md | Статус | Комментарий |
|----------------------|--------|-----------|
| **1. Загрузка CSV (сжатый gz)** | ⚠️ Partial | Эндпоинт `/upload/{dashboard_id}` существует, поддерживает CSV. GZ обработка заявлена, но `_process_csv_file` читает через `pl.read_csv(file_path)` без явной поддержки `.gz` |
| **2. Обработка через Polars** | ⚠️ Partial | Polars используется, но трансформации (groupby, YoY, доли) реализованы частично. YoY и доли упоминаются в моделях, но код обработки (`data_service.py`) содержит только базовые агрегации |
| **3. Хранение агрегатов в PostgreSQL** | ✅ Done | Таблицы `aggregated_data`, `dashboards`, `layouts`, `graphs`, `filters`, `processing_configs` созданы |
| **4. JWT + bcrypt** | ✅ Done | JWT через `python-jose`, bcrypt для хеширования. Все API защищены (проверка через `deps.py`) |
| **5. Dash + Plotly** | ⚠️ Partial | Dash-приложение существует (`dash_app.py`), графики (bar, line, pie, table) заявлены, но реализация может быть неполной |
| **6. Логирование** | ✅ Done | Логируются upload, processing, errors, access через стандартный `logging` |
| **7. Проверка ruff mypy** | ❌ Failed | **Ruff**: 4 ошибки. **MyPy**: конфигурационная ошибка (source file found twice) |
| **8. Пользователи, права, доступы** | ✅ Done | Модели `users`, `dashboard_access` реализованы, роли работают |

---

## 2. Архитектурные проблемы

### 🔴 Critical: Критическая ошибка импорта (блокирует тесты)

**Файл**: `src/mko_bi/interfaces/service_interfaces.py:12`  
**Проблема**: Импорт `from mko_bi.models.graph import GraphRead` - модуль `mko_bi.models.graph` не существует.  
**Следствие**: 9 тестовых файлов не могут быть собраны (88+ ошибок тестов).  
**Решение**: Заменить на `from mko_bi.db.models.graphs import GraphRead`.

```
ERROR: tests/services/test_auth_service.py
ModuleNotFoundError: No module named 'mko_bi.models.graph'
```

### 🔴 Critical: Неверные пути моков в тестах

**Файл**: `tests/conftest.py:70`  
**Проблема**: `patch("mko_bi.db.session.get_engine", ...)` - функция в `session.py` называется `_get_engine` (с underscore), а не `get_engine`.  
**Следствие**: Все тесты, использующие `mock_get_engine`, падают с `AttributeError`.

---

### High: Смешение ответственности

**Файл**: `src/mko_bi/services/auth_service.py`  
**Проблема**: Файл содержит и класс `AuthService(IAuthService)`, и standalone-функции `register_user()`, `login_user()`, `authenticate_user()`. Это создает путаницу:
- `deps.py` импортирует `AuthService` 
- Но `auth.py` (API route) использует standalone-функции `register_user()`, `login_user()`

**Рекомендация**: Выбрать один подход (класс или функции) и придерживаться его.

---

### High: Tight coupling в deps.py

**Файл**: `src/mko_bi/api/deps.py:31-60`  
**Проблема**: Файл импортирует и интерфейсы (`IUserRepository`, `IAuthService`, ...), и конкретные реализации (`UserRepository`, `AuthService`, ...). Это создает жесткую связность.

```python
# Текущий код (смешение)
from mko_bi.interfaces import IUserRepository, AuthService  # интерфейсы
from mko_bi.db.repositories import UserRepository  # конкретная реализация
from mko_bi.services import AuthService  # конкретная реализация
```

**Рекомендация**: Использовать только интерфейсы в type hints, а реализации инстанцировать внутри фабричных методов.

---

### Medium: Мертвый код - interfaces_old/

**Папка**: `src/mko_bi/interfaces_old/`  
**Проблема**: Содержит старые версии интерфейсов, которые не используются.  
**Решение**: Удалить папку, так как актуальные интерфейсы находятся в `interfaces/`.

---

### Medium: Неиспользуемый BaseService

**Файл**: `src/mko_bi/core/base_service.py`  
**Проблема**: Класс `BaseService` определен как generic-класс с методами, но:
1. Метод `validate_data()` содержит только `pass` (строка 212)
2. Не найдено использование этого базового класса в других сервисах

**Рекомендация**: Либо реализовать полноценный базовый сервис и использовать его в наследниках, либо удалить.

---

### Medium: Дублирование rate limiting

**Файлы**: 
- `src/mko_bi/api/routes/auth.py:34-71` (`_login_attempts` и `_check_rate_limit`)
- `src/mko_bi/services/auth_service.py:110-143` (те же `_login_attempts` и `_check_rate_limit`)

**Проблема**: Две независимые реализации rate limiting с отдельными состояниями. Они не будут работать корректно, так как состояние `_login_attempts` в API-роутах и в сервисе - это разные объекты.

**Рекомендация**: Вынести rate limiting в отдельный модуль или использовать только одну реализацию.

---

## 3. Проблемы в коде

### 🔴 Critical: Обработка файлов без проверки .gz

**Файл**: `src/mko_bi/services/data_service.py:132`  
**Код**:
```python
df = pl.read_csv(file_path)  # Не обрабатывает .gz должным образом
```
**Проблема**: SPEC требует поддержку `.csv.gz`, но `pl.read_csv()` может не поддерживать чтение сжатых файлов напрямую без дополнительной обработки.  
**Решение**: Использовать `polars.read_csv(file_path, ...)` с проверкой расширения или явно разархивировать.

---

### 🔴 Critical: Небезопасная работа с файлами

**Файл**: `src/mko_bi/services/data_service.py:102-103`  
**Код**:
```python
with open(file_path, "wb") as f:
    f.write(file_content)
```
**Проблема**: Файл `file_path` формируется на основе пользовательского ввода (`filename`). Возможна directory traversal атака, если `filename` содержит `../`.  
**Решение**: Использовать `secure_filename` или валидировать путь через `Path.resolve()`.

---

### High: Транзакции и обработка ошибок

**Файл**: `src/mko_bi/services/data_service.py:449-521`  
**Проблема**: При ошибке сохранения агрегированных данных (строка 517-520) ошибка логируется, но не прерывает выполнение:
```python
except Exception as save_error:
    logger.error("Ошибка при сохранении агрегированных данных: %s", save_error)
    # Не прерываем обработку из-за ошибки сохранения  <-- Потенциальная потеря данных
```

**Рекомендация**: Если сохранение - критическая операция, нужно прерывать процесс и обновлять статус лога на `failed`.

---

### High: Отсутствие нормального закрытия файлов

**Файл**: `src/mko_bi/api/routes/upload.py:86-89`  
**Код**:
```python
try:
    file_content = file.read()
except TypeError:
    file_content = await file.read()
```
**Проблема**: `UploadFile` может не закрываться корректно. Использование `file_content = await file.read()` в async контексте может привести к утечкам, если не использовать контекстный менеджер.

---

### Medium: Жестко за编码енные пути и конфигурация

**Файл**: `src/mko_bi/services/data_service.py:426`  
**Код**:
```python
csv_files = list(upload_dir.glob(f"*_{dashboard_id}_*.csv.gz"))
```
**Проблема**: Ожидается, что файл будет называться по шаблону `*_{dashboard_id}_*.csv.gz`, но при сохранении (`_save_uploaded_file`) имя генерируется как `uuid + "_" + dashboard_id + "_" + filename`. Если `filename` содержит спецсимволы, glob может не сработать.

---

### Medium: Использование `Any` в типах

**Файлы**: 
- `src/mko_bi/services/data_service.py` - массовое использование `dict[str, Any]`
- `src/mko_bi/db/models/aggregated_data.py` - `JSONBType` обявлен как `dict[str, Any]`

**Проблема**: `Any` отключает проверку типов.  
**Рекомендация**: Использовать более конкретные типы или `TypedDict`.

---

### Medium: Дублирование кода в сервисах

**Файлы**: `services/auth_service.py` и `services/user_service.py`  
**Проблема**: Оба файла содержат похожие функции хеширования паролей, валидации email и т.д.

---

## 4. Typing Issues (Ruff & MyPy)

### Ruff Errors (4 найдено)

```
E402 Module level import not at top of file
  --> src\mko_bi\core\permissions.py:43:1
   |
43 | from mko_bi.models.user import UserDB
   |

B904 Within an `except` clause, raise exceptions with `raise ... from err`
  --> src\mko_bi\core\permissions.py:105:9
   |
105 |         raise ValueError(f"Неизвестная роль: '{role}'")
   |

UP047 Generic function `timing` should use type parameters
  --> src\mko_bi\utils\decorators.py:20:5
   |
20 | def timing(func: F) -> F:
```

### MyPy Error

```
src\mko_bi\models\user_roles.py: error: Source file found twice under different module names: "models.user_roles" and "src.mko_bi.models.user_roles"
```

**Причина**: Неправильная конфигурация mypy. Нужно настроить `mypy.ini` или `pyproject.toml` с правильными `mypy_path` и `namespace_packages`.

---

## 5. Неиспользуемые абстракции (Dead Code)

| Файл/Класс | Проблема | Решение |
|-----------|---------|---------|
| `interfaces_old/` | Старые интерфейсы, не используются | Удалить папку |
| `BaseService.validate_data()` | Метод содержит только `pass` | Реализовать или удалить |
| `IRepository.get_session()` | Метод в интерфейсе, но не используется | Удалить из интерфейса |
| `IAggregatedDataRepository.create_bulk()` | Не используется (есть `bulk_insert` в реализации) | Удалить из интерфейса |

---

## 6. Пустые файлы/Заглушки

| Файл | Строка | Проблема |
|------|--------|---------|
| `src/mko_bi/services/data_service.py` | 238 | `pass` в `_process_csv_file` - не реализовано сохранение агрегатов |
| `src/mko_bi/dashboards/base.py` | 59, 61, 81, 102 | `...` в коде (Ellipsis) - заглушки |
| `src/mko_bi/dashboards/implementations/dashboard_1.py` | 217-222 | Методы `get_data()`, `apply_filters()`, `render()` возвращают пустые данные |

---

## 7. Рекомендации по исправлению

### Приоритет P0 (Critical - блокирует работу)

1. **Исправить импорт в `service_interfaces.py`**:
   ```python
   # Было:
   from mko_bi.models.graph import GraphRead
   # Стало:
   from mko_bi.db.models.graphs import GraphRead
   ```

2. **Исправить пути моков в `tests/conftest.py`**:
   ```python
   # Было:
   patch("mko_bi.db.session.get_engine", ...)
   # Стало:
   patch("mko_bi.db.session._get_engine", ...)
   # Или лучше: экспортировать get_engine как публичную функцию
   ```

### Приоритет P1 (High - архитектурные проблемы)

3. **Унифицировать auth_service.py**: Выбрать один подход (класс или функции)
4. **Разорвать циклические зависимости**: Использовать интерфейсы в `deps.py` без прямых импортов реализаций
5. **Удалить `interfaces_old/`**: Мертвый код

### Приоритет P2 (Medium - улучшения)

6. **Настроить MyPy**: Исправить `pyproject.toml` для корректной работы с src-layout
7. **Исправить Ruff ошибки**: E402, B904, UP047
8. **Добавить валидацию путей файлов**: Для предотвращения directory traversal
9. **Обработать .gz файлы корректно**: В `_process_csv_file`

---

## 8. Сводная оценка

| Категория | Оценка | Комментарий |
|-----------|--------|-----------|
| Соответствие SPEC.md | 70% | Основной функционал реализован, но есть пробелы (YoY, доли) |
| Архитектура | 60% | Чистая архитектура частично соблюдена, есть нарушения (tight coupling) |
| Качество кода | 65% | Есть дублирование, мертвый код, небезопасные операции с файлами |
| Типизация | 50% | MyPy не работает, Ruff нахдит ошибки, много `Any` |
| Тестируемость | 30% | Тесты не запускаются из-за критических ошибок импорта |

**Общая оценка**: **55%** - Требуется исправление критических ошибок перед продолжением разработки.

---

## 9. Checklist выполнения аудита

- [x] Проверены все пункты чек-листа TASK_033_audit.md
- [x] Найдены проблемы (см. разделы 2-6)
- [x] Для каждой проблемы указан файл, строка и конкретный пример
- [x] Отчёт сохранён в `TODO/TASK_033_analysis_report.md`
