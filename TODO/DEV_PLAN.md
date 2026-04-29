# DEV_PLAN: План доработки системы mko_bi

**Дата**: 2026-04-29  
**Архитектор**: Senior Python Architect (Kilo)  
**Версия**: 1.0

---

## Матрица группировки аудитов по темам

### Тема 1: 🔴 Critical - Блокирующие проблемы (P0)
| Проблема | Источник | Файлы |
|----------|----------|-------|
| Неверный импорт `mko_bi.models.graph` | TASK_033, TASK_036 | `interfaces/service_interfaces.py:12` |
| Тесты не работают (337 тестов заблокированы) | TASK_033, TASK_036 | `interfaces/service_interfaces.py`, `tests/conftest.py` |
| Несуществующий класс `GraphRead` | TASK_036 | Требует создания Pydantic моделей |
| MyPy конфигурация (source file found twice) | TASK_033 | `pyproject.toml` |

### Тема 2: 🟠 Architecture - Архитектурные проблемы (P1)
| Проблема | Источник | Файлы |
|----------|----------|-------|
| Смешение ответственности (SQL в сервисах) | TASK_033 | `services/data_service.py:45-50` |
| Tight coupling в deps.py | TASK_033 | `api/deps.py:31-60` |
| Прямой доступ к БД из API роутов | TASK_033 | `api/upload.py:30-35` |
| Дублирование auth (класс + функции) | TASK_033 | `services/auth_service.py` |
| Множественные сессии в одной операции | TASK_036 | `services/data_service.py` |
| Отсутствие реализации GraphService | TASK_036 | `interfaces/service_interfaces.py:110-142` |

### Тема 3: 🟡 Code Quality - Качество кода и типизация (P2)
| Проблема | Источник | Файлы |
|----------|----------|-------|
| Ruff ошибки (E402, B904, UP047, F401) | TASK_033, TASK_036 | Множественные файлы |
| Массовое использование `Any` | TASK_033, TASK_036 | `interfaces/service_interfaces.py`, `services/data_service.py` |
| MyPy не работает корректно | TASK_033 | `pyproject.toml` |
| Дублирование кода (хеширование, валидация) | TASK_033 | `services/auth_service.py`, `services/user_service.py` |
| Мертвый код (`interfaces_old/`, `BaseService`) | TASK_033, TASK_036 | `interfaces_old/`, `core/base_service.py` |
| Использование `any` вместо `Any` | TASK_036 | `services/auth_service.py:29` |

### Тема 4: 📊 Data Processing - Обработка данных и SPEC (P3)
| Проблема | Источник | Файлы |
|----------|----------|-------|
| YoY расчет некорректен (нет группировки) | TASK_036 | `data/processing/transformations.py:262-293` |
| GZ файлы обрабатываются некорректно | TASK_033, TASK_036 | `services/data_service.py:132` |
| Доли (shares) реализованы частично | TASK_033 | `data/processing/transformations.py` |
| Загрузка всего CSV в память | TASK_033 | `services/data_service.py:20` |
| Агрегаты создаются по preview (10 строк) | TASK_036 | `services/data_service.py:470-496` |
| Обработка пустых/битых CSV | TASK_036 | `data/processing/base.py:50-67` |

### Тема 5: 🔒 Security - Безопасность (P4)
| Проблема | Источник | Файлы |
|----------|----------|-------|
| Directory traversal в upload | TASK_033 | `services/data_service.py:102-103` |
| Rate limiting в памяти (не persistent) | TASK_036 | `api/routes/auth.py:36`, `services/auth_service.py:110` |
| JWT без механизма отзыва | TASK_036 | `core/security.py` |
| Пароли обрезаются до 72 байт | TASK_036 | `core/security.py:20-41` |
| CORS `allow_origins=["*"]` | TASK_036 | `app.py:44-50` |
| Нет ограничения размера загружаемых файлов | TASK_036 | `services/data_service.py:132` |

### Тема 6: ⚠️ Error Handling - Обработка ошибок (P5)
| Проблема | Источник | Файлы |
|----------|----------|-------|
| Голые `except:` | TASK_033 | `services/data_service.py:68` |
| Отсутствие логирования ошибок | TASK_033 | `api/upload.py:40-45` |
| Нет явных транзакций (commit/rollback) | TASK_033 | `services/data_service.py:55-60` |
| Незакрытые файловые дескрипторы | TASK_033 | `api/upload.py:30` |
| Временные файлы не удаляются при ошибке | TASK_033 | `api/upload.py:50` |
| Исключения без контекста (breadcrumbs) | TASK_036 | `core/permissions.py:105` |

### Тема 7: 🧪 Testing - Тестирование (P6)
| Проблема | Источник | Файлы |
|----------|----------|-------|
| Тесты заблокированы импортами | TASK_033, TASK_036 | `tests/conftest.py`, `interfaces/service_interfaces.py` |
| Неверные пути моков | TASK_033 | `tests/conftest.py:70` |
| Отсутствие интеграционных тестов | TASK_036 | Нет файлов |
| Нет тестов для YoY и долей | TASK_036 | Нет файлов |
| Нет тестов для RBAC | TASK_036 | Нет файлов |

### Тема 8: 📈 Dash/UI Layer - Интеграция дашбордов (P7)
| Проблема | Источник | Файлы |
|----------|----------|-------|
| Dash использует заглушки (sample_data) | TASK_033, TASK_036 | `dashboards/implementations/dashboard_1.py` |
| Нет реальной интеграции с API | TASK_036 | `dash_app.py`, `dashboards/` |
| Отсутствие обработки ошибок в callbacks | TASK_036 | `dash_app.py:208-233` |
| Нет проверки валидности JWT в Dash | TASK_036 | `dash_app.py` |
| Фильтры не подключены к бэкенду | TASK_036 | `dashboards/components/filters.py` |

### Тема 9: 📝 Logging & Monitoring (P8)
| Проблема | Источник | Файлы |
|----------|----------|-------|
| Нет структурированного логирования (JSON) | TASK_036 | `core/logging_config.py` |
| Access логи не сохраняются в БД | TASK_036 | Отсутствует |
| Нет метрик (Prometheus) | TASK_036 | Отсутствует |

---

## Детальный план доработки системы

### Этап 1: P0 - Critical Fixes (Неделя 1, дни 1-2)

#### Task 1: Исправление импортов и создание Graph моделей
**Цель**: Восстановить работоспособность импортов и запуск тестов  
**Файлы**: 
- `src/mko_bi/interfaces/service_interfaces.py` (исправить импорт)
- `src/mko_bi/models/graph.py` (создать новый файл)
- `src/mko_bi/db/models/graphs.py` (проверить GraphRead)

**Изменения**:
1. Создать Pydantic модели `GraphRead`, `GraphCreate`, `GraphUpdate` в `src/mko_bi/models/graph.py`
2. Исправить импорт в `interfaces/service_interfaces.py:12`
3. Проверить соответствие полей в SQLAlchemy и Pydantic моделях

---

#### Task 2: Исправление моков в тестах
**Цель**: Запустить существующие тесты  
**Файлы**: 
- `tests/conftest.py` (исправить пути моков)

**Изменения**:
1. Исправить `patch("mko_bi.db.session.get_engine", ...)` на правильный путь
2. Проверить все моки в тестах на соответствие реальным именам функций
3. Запустить `uv run pytest` и исправить падающие тесты

---

#### Task 3: Настройка MyPy
**Цель**: Корректная работа статического анализа типов  
**Файлы**: 
- `pyproject.toml` (настройка mypy)

**Изменения**:
1. Исправить конфигурацию mypy для src-layout
2. Настроить `mypy_path` и `namespace_packages`
3. Убедиться, что `uv run mypy src/` проходит без ошибок конфигурации

---

### Этап 2: P1 - Architecture Fixes (Неделя 1, дни 3-5)

#### Task 4: Рефакторинг auth_service (унификация)
**Цель**: Устранить дублирование подходов (класс vs функции)  
**Файлы**: 
- `src/mko_bi/services/auth_service.py`
- `src/mko_bi/api/routes/auth.py`
- `src/mko_bi/api/deps.py`

**Изменения**:
1. Выбрать один подход (рекомендуется класс `AuthService`)
2. Переписать standalone-функции `register_user()`, `login_user()` как методы класса
3. Обновить вызовы в `api/routes/auth.py`
4. Убрать дублирование rate limiting

---

#### Task 5: Разрыв tight coupling в deps.py
**Цель**: Использовать только интерфейсы в type hints  
**Файлы**: 
- `src/mko_bi/api/deps.py`

**Изменения**:
1. Убрать импорты конкретных реализаций (`UserRepository`, `AuthService`)
2. Оставить только интерфейсы (`IUserRepository`, `IAuthService`)
3. Инстанцировать реализации внутри фабричных методов

---

#### Task 6: Создание GraphService
**Цель**: Реализовать сервис для работы с графиками  
**Файлы**: 
- `src/mko_bi/services/graph_service.py` (создать)
- `src/mko_bi/interfaces/service_interfaces.py` (проверить интерфейс)

**Изменения**:
1. Реализовать `GraphService` с методами CRUD для графиков
2. Использовать `IGraphService` интерфейс
3. Интегрировать с `GraphRepository`

---

#### Task 7: Исправление передачи сессий БД
**Цель**: Устранить множественные независимые сессии  
**Файлы**: 
- `src/mko_bi/services/data_service.py`
- `src/mko_bi/core/base_service.py`

**Изменения**:
1. Передавать сессию как параметр через все уровни
2. Использовать контекстный менеджер для транзакций
3. Убрать вызовы `get_session()` внутри методов сервисов

---

### Этап 3: P2 - Code Quality (Неделя 2, дни 1-3)

#### Task 8: Исправление Ruff ошибок
**Цель**: Чистый код без ошибок линтера  
**Файлы**: 
- Все файлы с ошибками Ruff

**Изменения**:
1. Запустить `uv run ruff check . --fix`
2. Исправить E402 (импорты не в начале файла)
3. Исправить B904 (raise ... from err)
4. Исправить UP047 (generic function type parameters)
5. Удалить неиспользуемые импорты (F401)

---

#### Task 9: Улучшение типизации (замена Any)
**Цель**: Конкретные типы вместо Any  
**Файлы**: 
- `src/mko_bi/interfaces/service_interfaces.py`
- `src/mko_bi/services/data_service.py`
- `src/mko_bi/db/models/aggregated_data.py`

**Изменения**:
1. Заменить `dict[str, Any]` на `TypedDict` или конкретные модели
2. Добавить type hints для всех методов
3. Исправить `any` на `Any` в импортах

---

#### Task 10: Удаление мертвого кода
**Цель**: Очистка от неиспользуемого кода  
**Файлы**: 
- `src/mko_bi/interfaces_old/` (удалить папку)
- `src/mko_bi/core/base_service.py` (удалить или реализовать)
- `src/mko_bi/data/processing/base.py` (проверить использование)

**Изменения**:
1. Удалить папку `interfaces_old/`
2. Либо реализовать `BaseService.validate_data()`, либо удалить класс
3. Удалить неиспользуемые методы из интерфейсов (`get_session()`, `create_bulk()`)

---

### Этап 4: P3 - Data Processing (Неделя 2, дни 4-5)

#### Task 11: Исправление расчета YoY
**Цель**: Корректный расчет Year-over-Year с группировкой  
**Файлы**: 
- `src/mko_bi/data/processing/transformations.py` (_calculate_yoy)

**Изменения**:
1. Переписать `_calculate_yoy()` с группировкой по dims/категориям
2. Использовать `pl.groupby()` перед расчетом сдвига
3. Добавить тесты для проверки корректности

---

#### Task 12: Корректная обработка GZ файлов
**Цель**: Поддержка .csv.gz согласно SPEC  
**Файлы**: 
- `src/mko_bi/services/data_service.py` (_process_csv_file)

**Изменения**:
1. Проверять расширение файла (.gz)
2. Использовать `gzip.open()` для чтения сжатых файлов
3. Передавать файловый объект в `pl.read_csv()`

---

#### Task 13: Реализация расчета долей (shares)
**Цель**: Полная реализация согласно SPEC  
**Файлы**: 
- `src/mko_bi/data/processing/transformations.py` (_calculate_share)

**Изменения**:
1. Проверить корректность расчета долей
2. Добавить поддержку группировок для долей
3. Добавить тесты

---

#### Task 14: Безопасная обработка больших CSV
**Цель**: Предотвращение исчерпания памяти  
**Файлы**: 
- `src/mko_bi/services/data_service.py`

**Изменения**:
1. Добавить проверку размера файла ДО чтения
2. Использовать chunked чтение для больших файлов (Polars scan_csv)
3. Добавить лимиты на размер в конфигурацию

---

### Этап 5: P4 - Security (Неделя 3, дни 1-2)

#### Task 15: Валидация путей файлов (защита от directory traversal)
**Цель**: Безопасная загрузка файлов  
**Файлы**: 
- `src/mko_bi/services/data_service.py` (_save_uploaded_file)

**Изменения**:
1. Использовать `secure_filename` из werkzeug
2. Валидировать путь через `Path.resolve()`
3. Проверять, что результирующий путь находится в разрешенной директории

---

#### Task 16: Перенос rate limiting в Redis
**Цель**: Persistent rate limiting для production  
**Файлы**: 
- `src/mko_bi/api/routes/auth.py`
- `src/mko_bi/services/auth_service.py`
- `src/mko_bi/core/security.py` (добавить Redis клиент)

**Изменения**:
1. Создать модуль для работы с Redis
2. Перенести `_login_attempts` в Redis
3. Настроить TTL для записей попыток входа

---

#### Task 17: Настройка CORS для production
**Цель**: Безопасность в production  
**Файлы**: 
- `src/mko_bi/app.py`
- `src/mko_bi/settings/app.yaml` (добавить CORS origins)

**Изменения**:
1. Добавить список разрешенных доменов в конфигурацию
2. Убрать `allow_origins=["*"]`
3. Читать origins из настроек

---

#### Task 18: Улучшение обработки паролей
**Цель**: Поддержка паролей длиннее 72 байт  
**Файлы**: 
- `src/mko_bi/core/security.py`

**Изменения**:
1. Добавить pre-hash (SHA256) перед bcrypt
2. Документировать ограничения bcrypt
3. Обновить методы хеширования и проверки

---

### Этап 6: P5 - Error Handling (Неделя 3, дни 3-4)

#### Task 19: Исправление обработки ошибок (замена bare except)
**Цель**: Корректная обработка исключений  
**Файлы**: 
- `src/mko_bi/services/data_service.py`
- Все файлы с `except:` без указания типа

**Изменения**:
1. Заменить `except:` на конкретные исключения
2. Добавить логирование с контекстом (breadcrumbs)
3. Использовать `raise ... from e` для сохранения цепочки

---

#### Task 20: Управление транзакциями
**Цель**: Явные commit/rollback  
**Файлы**: 
- `src/mko_bi/services/data_service.py`
- `src/mko_bi/core/base_service.py`

**Изменения**:
1. Обернуть операции с БД в `with session.begin():`
2. Добавить rollback при ошибках
3. Обновить статус логов обработки при ошибках

---

#### Task 21: Корректная работа с файлами
**Цель**: Закрытие дескрипторов и удаление временных файлов  
**Файлы**: 
- `src/mko_bi/api/routes/upload.py`
- `src/mko_bi/services/data_service.py`

**Изменения**:
1. Использовать контекстный менеджер для файлов
2. Добавить блок `finally` для очистки
3. Удалять временные файлы при ошибке обработки

---

### Этап 7: P6 - Testing (Неделя 3, день 5 + Неделя 4, дни 1-2)

#### Task 22: Исправление и запуск существующих тестов
**Цель**: Все тесты проходят  
**Файлы**: 
- `tests/` (все тестовые файлы)

**Изменения**:
1. Исправить все ошибки импортов
2. Обновить моки на правильные пути
3. Запустить `uv run pytest` и добиться 100% прохождения

---

#### Task 23: Добавление интеграционных тестов
**Цель**: Покрытие полного цикла  
**Файлы**: 
- `tests/test_integration_upload_process.py` (создать)
- `tests/test_integration_dashboards.py` (создать)

**Изменения**:
1. Тест полного цикла: upload → process → get data
2. Тесты для RBAC (проверка доступов)
3. Тесты для различных ролей (admin/editor/viewer)

---

#### Task 24: Тесты для YoY и долей
**Цель**: Проверка корректности расчетов  
**Файлы**: 
- `tests/test_yoy_calculation.py` (создать)
- `tests/test_share_calculation.py` (создать)

**Изменения**:
1. Тесты для `_calculate_yoy()` с группировками
2. Тесты для `_calculate_share()`
3. Edge cases (пустые данные, деление на ноль)

---

### Этап 8: P7 - Dash/UI Integration (Неделя 4, дни 3-5)

#### Task 25: Интеграция Dash с реальными данными
**Цель**: Замена заглушек на реальные API вызовы  
**Файлы**: 
- `src/mko_bi/dashboards/implementations/dashboard_1.py`
- `src/mko_bi/dashboards/implementations/dashboard_2.py`

**Изменения**:
1. Заменить `sample_data` на вызовы API или сервисов
2. Реализовать `get_data()`, `apply_filters()`, `render()`
3. Подключить фильтры к бэкенду

---

#### Task 26: Обработка ошибок в Dash callbacks
**Цель**: Корректная обработка ошибок на фронтенде  
**Файлы**: 
- `src/mko_bi/dash_app.py`

**Изменения**:
1. Добавить обработку различных статус-кодов ответов
2. Показывать пользователю понятные сообщения
3. Логировать ошибки API вызовов

---

#### Task 27: Проверка JWT токена на стороне Dash
**Цель**: Безопасность фронтенда  
**Файлы**: 
- `src/mko_bi/dash_app.py`

**Изменения**:
1. Проверять срок действия токена
2. Реализовать redirect на login при истечении
3. Обновлять токен (refresh token mechanism)

---

### Этап 9: P8 - Logging & Monitoring (Неделя 5, дни 1-2)

#### Task 28: Структурированное логирование (JSON)
**Цель**: Логи в формате JSON для production  
**Файлы**: 
- `src/mko_bi/core/logging_config.py`

**Изменения**:
1. Настроить JSON форматтер для логов
2. Добавить обязательные поля (timestamp, level, service, etc.)
3. Настроить вывод в stdout для Docker

---

#### Task 29: Сохранение access логов в БД
**Цель**: История доступа  
**Файлы**: 
- `src/mko_bi/core/logging_config.py`
- `src/mko_bi/db/models/access_log.py` (создать)
- `src/mko_bi/services/access_log_service.py` (создать)

**Изменения**:
1. Создать таблицу `access_logs` в БД
2. Реализовать сохранение логов доступа в БД
3. Добавить API для просмотра логов (для admin)

---

## Новая структура компонентов (предлагаемая)

```
src/mko_bi/
├── api/
│   ├── deps.py                    # Dependency injection (только интерфейсы)
│   └── routes/
│       ├── auth.py
│       ├── dashboards.py
│       ├── data.py
│       ├── filters.py
│       ├── processing_configs.py
│       ├── processing_logs.py
│       ├── upload.py               # Использует сервисный слой (не БД напрямую)
│       └── users.py
├── core/
│   ├── base_repository.py
│   ├── base_service.py             # Реализовать или удалить
│   ├── permissions.py              # Добавить инвалидацию кэша
│   ├── security.py                 # Redis для rate limiting, pre-hash паролей
│   └── logging_config.py           # JSON форматирование
├── dashboards/
│   ├── base.py                     # Интегрировать с реальными данными
│   ├── components/
│   │   ├── charts/                 # Готово
│   │   ├── filters.py              # Подключить к бэкенду
│   │   └── layout.py
│   ├── implementations/
│   │   ├── dashboard_1.py          # Заменить заглушки на API вызовы
│   │   └── dashboard_2.py          # Заменить заглушки на API вызовы
│   └── registry.py
├── data/
│   ├── loaders/                    # Готово
│   ├── processing/
│   │   ├── base.py                 # Проверить использование
│   │   ├── registry.py
│   │   └── transformations.py      # Исправить YoY, доли
│   └── storage/
│       └── manager.py
├── db/
│   ├── models/
│   │   ├── access.py
│   │   ├── aggregated_data.py
│   │   ├── dashboard.py
│   │   ├── filters.py
│   │   ├── graphs.py
│   │   ├── layout.py
│   │   ├── processing_configs.py
│   │   ├── processing_logs.py
│   │   └── user.py
│   ├── repositories/
│   │   ├── access_repo.py
│   │   ├── aggregated_data_repo.py
│   │   ├── dashboard_repo.py
│   │   ├── filter_repo.py
│   │   ├── graph_repo.py           # Проверить наличие
│   │   ├── processing_config_repo.py
│   │   ├── processing_log_repo.py
│   │   └── user_repo.py
│   ├── base.py
│   └── session.py
├── interfaces/
│   ├── repository_interfaces.py     # Очистить от неиспользуемых методов
│   └── service_interfaces.py       # Заменить Any на конкретные типы
├── models/                          # Pydantic модели
│   ├── access.py
│   ├── auth.py
│   ├── dashboard.py
│   ├── data.py
│   ├── filters.py
│   ├── graph.py                     # СОЗДАТЬ (GraphRead, GraphCreate, GraphUpdate)
│   ├── processing_configs.py
│   ├── processing_logs.py
│   ├── user.py
│   └── user_roles.py
├── services/
│   ├── auth_service.py              # Унифицировать (класс или функции)
│   ├── dashboard_service.py
│   ├── data_service.py              # Исправить: передавать сессию, убрать SQL
│   ├── filter_service.py
│   ├── graph_service.py             # СОЗДАТЬ
│   ├── processing_config_service.py
│   ├── processing_log_service.py
│   ├── user_service.py
│   └── access_log_service.py        # СОЗДАТЬ (для логов доступа)
├── utils/
│   ├── decorators.py                # Исправить типизацию
│   ├── exceptions.py
│   ├── file_utils.py                # Добавить secure_filename
│   ├── time_utils.py
│   └── validators.py
├── app.py                           # Настроить CORS
├── config.py
├── dash_app.py                      # Интегрировать с реальными данными
├── logging_config.py
└── main.py
```

---

## Метрики успеха

| Категория | До | После (цель) |
|-----------|----|------------|
| Соответствие SPEC.md | 70% | 95% |
| Архитектура | 60% | 90% |
| Качество кода | 65% | 90% |
| Типизация | 50% | 85% |
| Тестируемость | 30% | 80% |
| Безопасность | 70% | 90% |
| **Общая оценка** | **55%** | **90%** |

---

## Порядок выполнения задач LLM

Задачи должны выполняться в порядке возрастания номера (Task 1 → Task 29).
Каждая задача сохраняется в отдельный файл в папке `TODO/DEV/`.

Формат именования: `TASK_XXX_<short_name>.md`

---

**Конец плана**
