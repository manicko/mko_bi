# План доработки BI Dashboard системы
## Анализ аудита и соответствия ТЗ (SPEC.md)

**Дата:** 2026-04-28  
**Версия проекта:** 1.0.8  
**Приоритет:** Критические → Высокие → Средние → Низкие

---

## 1. КРИТИЧЕСКИЕ ПРОБЛЕМЫ (Блокирующие запуск/работу)

### 1.1 Утечка дискового пространства - незакрытые файлы
**Текущее состояние:** Загруженные CSV файлы никогда не удаляются, накапливаются в `data/tmp_uploads/`  
**Файлы для изменения:**
- `src/mko_bi/api/routes/upload.py` - добавить вызов очистки после обработки
- `src/mko_bi/services/data_service.py` - вызов `cleanup_task_files()` в `_process_csv_file()` и `trigger_processing()`
- `src/mko_bi/utils/file_utils.py` - убедиться, что `cleanup_task_files()` работает корректно

**Новая структура:**
```
src/mko_bi/utils/
  └── file_utils.py          # Улучшить: гарантированное удаление в finally
```

**Задача:** Реализовать автоматическую очистку временных файлов после успешной обработки и добавить фоновую задачу для удаления старых файлов.

---

### 1.2 Отсутствие пользовательского интерфейса (Dash/Plotly)
**Текущее состояние:** Компоненты графиков существуют, но Dash-сервер не запущен, нет UI-страниц  
**Файлы для создания/изменения:**
- `src/mko_bi/dash_app.py` - NEW: Основное Dash приложение
- `src/mko_bi/dashboards/ui/` - NEW: Папка с UI-компонентами
  - `login_page.py` - страница авторизации
  - `dashboard_list.py` - список дашбордов
  - `dashboard_page.py` - страница дашборда с графиками и фильтрами
- `src/mko_bi/dashboards/ui/components/` - NEW: UI компоненты
  - `filter_panel.py` - панель фильтров
  - `graph_renderer.py` - рендеринг Plotly графиков
- `src/mko_bi/app.py` - интеграция Dash в FastAPI

**Новая структура:**
```
src/mko_bi/
  ├── dash_app.py                 # Dash приложение, монтируется в FastAPI
  └── dashboards/
      └── ui/
          ├── login_page.py       # Login page (Plotly/Dash)
          ├── dashboard_list.py   # Список доступных дашбордов
          ├── dashboard_page.py   # Страница дашборда
          └── components/
              ├── filter_panel.py # UI фильтров
              └── graph_renderer.py # Рендеринг графиков
```

**Задача:** Создать полнофункциональный веб-интерфейс с использованием Dash и Plotly для визуализации данных.

---

### 1.3 Отсутствие обязательных таблиц БД
**Текущее состояние:** Таблицы `filters`, `processing_configs`, `processing_logs` не созданы  
**Файлы для создания:**
- `src/mko_bi/db/models/filters.py` - модель таблицы filters
- `src/mko_bi/db/models/processing_configs.py` - модель таблицы processing_configs
- `src/mko_bi/db/models/processing_logs.py` - модель таблицы processing_logs
- `src/mko_bi/db/repositories/filters_repo.py` - репозиторий для filters
- `src/mko_bi/db/repositories/processing_configs_repo.py` - репозиторий для processing_configs
- `src/mko_bi/db/repositories/processing_logs_repo.py` - репозиторий для processing_logs
- `create_db.sql` - добавить CREATE TABLE скрипты

**Новая структура:**
```
src/mko_bi/db/
  ├── models/
  │   ├── filters.py              # Таблица глобальных фильтров
  │   ├── processing_configs.py   # Настройки обработки per dashboard
  │   └── processing_logs.py      # Логи обработки данных
  └── repositories/
      ├── filters_repo.py         # Репозиторий filters
      ├── processing_configs_repo.py # Репозиторий processing_configs
      └── processing_logs_repo.py # Репозиторий processing_logs
```

**Таблица filters:**
```sql
CREATE TABLE filters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,  -- 'select' | 'multiselect' | 'range' | 'date'
    config JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Таблица processing_configs:**
```sql
CREATE TABLE processing_configs (
    dashboard_id UUID PRIMARY KEY REFERENCES dashboards(id) ON DELETE CASCADE,
    settings JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Таблица processing_logs:**
```sql
CREATE TABLE processing_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dashboard_id UUID REFERENCES dashboards(id),
    status TEXT NOT NULL CHECK (status IN ('started', 'success', 'failed')),
    message TEXT,
    started_at TIMESTAMP,
    finished_at TIMESTAMP
);
```

**Задача:** Создать недостающие таблицы БД согласно SPEC.md, включая модели, репозитории и миграции.

---

### 1.4 Отсутствие GIN индекса на aggregated_data.dims
**Текущее состояние:** GIN индекс не создан, фильтрация по JSONB будет крайне медленной  
**Файлы для изменения:**
- `create_db.sql` - добавить CREATE INDEX
- `src/mko_bi/db/base.py` - при необходимости добавить индексы через SQLAlchemy

**SQL:**
```sql
CREATE INDEX idx_agg_dims_gin ON aggregated_data USING GIN (dims);
```

**Задача:** Добавить GIN индекс для оптимизации фильтрации по полю dims (JSONB).

---

### 1.5 Хардкод секретов
**Текущее состояние:** JWT_SECRET_KEY имеет дефолтное значение "your-secret-key-change-in-production"  
**Файлы для изменения:**
- `src/mko_bi/config.py` - сделать секреты обязательными env-переменными
- `src/mko_bi/db/session.py` - убрать хардкод пароля БД

**Задача:** Убрать все дефолтные секреты, сделать обязательными переменные окружения.

---

## 2. ВЫСОКОПРИОРИТЕТНЫЕ ЗАДАЧИ (Качество и безопасность)

### 2.1 Реализация YoY (Year-over-Year) расчетов
**Текущее состояние:** YoY не реализовано, требуется по SPEC.md  
**Файлы для изменения:**
- `src/mko_bi/data/processing/transformations.py` - добавить функции YoY
- `src/mko_bi/dashboards/components/charts/line.py` - поддержка YoY в графиках

**Новая структура:**
```
src/mko_bi/data/processing/
  └── transformations.py        # YoY, доли, кастомные метрики
```

**Задача:** Реализовать расчет год-к-год сравнения для временных рядов.

---

### 2.2 Реализация расчета долей/процентов
**Текущее состояние:** Не реализовано, требуется по SPEC.md  
**Файлы для изменения:**
- `src/mko_bi/data/processing/transformations.py` - добавить функции расчета долей

**Задача:** Реализовать вычисление процентных долей от общего итога.

---

### 2.3 API для управления фильтрами
**Текущее состояние:** Нет CRUD API для таблицы filters  
**Файлы для создания:**
- `src/mko_bi/api/routes/filters.py` - эндпоинты для filters
- `src/mko_bi/services/filter_service.py` - бизнес-логика

**Новая структура:**
```
src/mko_bi/
  ├── api/routes/filters.py      # CRUD эндпоинты
  └── services/filter_service.py  # Бизнес-логика
```

**Эндпоинты:**
- `GET /filters/` - список фильтров
- `POST /filters/` - создать фильтр
- `GET /filters/{id}` - получить фильтр
- `PUT /filters/{id}` - обновить фильтр
- `DELETE /filters/{id}` - удалить фильтр

**Задача:** Реализовать полный CRUD для глобальных фильтров.

---

### 2.4 API для управления настройками обработки
**Текущее состояние:** Нет CRUD API для таблицы processing_configs  
**Файлы для создания:**
- `src/mko_bi/api/routes/processing_configs.py` - эндпоинты
- `src/mko_bi/services/processing_config_service.py` - бизнес-логика

**Новая структура:**
```
src/mko_bi/
  ├── api/routes/processing_configs.py    # CRUD эндпоинты
  └── services/processing_config_service.py # Бизнес-логика
```

**Эндпоинты:**
- `GET /processing-configs/{dashboard_id}` - получить настройки
- `PUT /processing-configs/{dashboard_id}` - обновить настройки

**Задача:** Реализовать API для настройки параметров обработки данных per dashboard.

---

### 2.5 API для логов обработки
**Текущее состояние:** Нет API для чтения processing_logs  
**Файлы для создания:**
- `src/mko_bi/api/routes/processing_logs.py` - эндпоинты
- `src/mko_bi/services/processing_log_service.py` - бизнес-логика

**Новая структура:**
```
src/mko_bi/
  ├── api/routes/processing_logs.py  # CRUD эндпоинты
  └── services/processing_log_service.py # Бизнес-логика
```

**Эндпоинты:**
- `GET /processing-logs/` - список логов (с фильтрацией)
- `GET /processing-logs/{id}` - получить лог
- `POST /processing-logs/` - создать запись лога

**Задача:** Реализовать API для аудита и мониторинга процесса обработки данных.

---

### 2.6 Сохранение агрегатов в БД
**Текущее состояние:** Агрегаты возвращаются клиенту, но не сохраняются в таблице aggregated_data  
**Файлы для изменения:**
- `src/mko_bi/services/data_service.py` - `_process_csv_file()` - добавить сохранение
- `src/mko_bi/db/repositories/aggregated_data_repo.py` - NEW: репозиторий

**Новая структура:**
```
src/mko_bi/db/repositories/
  └── aggregated_data_repo.py     # Репозиторий для aggregated_data
```

**Задача:** Реализовать сохранение агрегированных данных в БД после обработки CSV.

---

### 2.7 Транзакции для связанных операций
**Текущее состояние:** Нет явных транзакций, риск частичного выполнения  
**Файлы для изменения:**
- `src/mko_bi/services/dashboard_service.py` - обернуть в транзакцию
- `src/mko_bi/services/data_service.py` - обернуть обработку в транзакцию
- `src/mko_bi/services/auth_service.py` - регистрация пользователя

**Задача:** Добавить явные транзакции для операций, требующих атомарности.

---

## 3. АРХИТЕКТУРНЫЕ ИЗМЕНЕНИЯ

### 3.1 Выделение бизнес-логики из API роутов
**Текущее состояние:** Бизнес-логика смешана с эндпоинтами  
**Файлы для изменения:**
- `src/mko_bi/api/routes/dashboards.py` - перенести логику в сервис
- `src/mko_bi/api/routes/users.py` - перенести логику в сервис
- `src/mko_bi/api/routes/auth.py` - вынести rate limiting в middleware

**Новая структура:**
```
src/mko_bi/api/routes/
  ├── dashboards.py    # Только координация, без бизнес-логики
  ├── users.py         # Только координация
  └── auth.py          # Только аутентификация
```

**Задача:** Привести в соответствие с Clean Architecture - роуты только координируют, вся логика в сервисах.

---

### 3.2 Устранение циклических зависимостей
**Текущее состояние:** Потенциальные циклические импорты между слоями  
**Файлы для изменения:**
- `src/mko_bi/core/permissions.py` - использовать интерфейсы
- `src/mko_bi/api/deps.py` - рефакторинг зависимостей
- `src/mko_bi/services/` - внедрение зависимостей через конструкторы

**Новая структура:**
```
src/mko_bi/interfaces/          # NEW
  ├── repository_interfaces.py  # ABC для репозиториев
  └── service_interfaces.py     # ABC для сервисов
```

**Задача:** Внедрить Dependency Injection и устранить циклические зависимости.

---

### 3.3 Интерфейсы и абстракции
**Текущее состояние:** Нет абстрактных классов для слоев  
**Файлы для создания:**
- `src/mko_bi/interfaces/repository_interfaces.py` - ABC репозиториев
- `src/mko_bi/interfaces/service_interfaces.py` - ABC сервисов

**Задача:** Создать интерфейсы для возможности замены реализаций (например, PostgreSQL → MongoDB).

---

### 3.4 Управление глобальным состоянием
**Текущее состояние:** Глобальные переменные в config, data_service, session  
**Файлы для изменения:**
- `src/mko_bi/config.py` - использовать pydantic-settings
- `src/mko_bi/services/data_service.py` - убрать `_task_statuses` в БД
- `src/mko_bi/db/session.py` - контекстный менеджер для сессий

**Новая структура:**
```
src/mko_bi/
  ├── config.py                  # Использовать pydantic-settings
  └── db/
      └── session.py             # Контекстный менеджер сессий
```

**Задача:** Убрать глобальное состояние, использовать контекстный менеджмент.

---

## 4. УЛУЧШЕНИЕ КАЧЕСТВА КОДА

### 4.1 Исправление ошибок статического анализа
**Текущее состояние:** 125 ошибок ruff, 31 ошибка mypy  
**Файлы для исправления:**
- ВСЕ файлы проекта - привести к соответствию стандартам

**Основные проблемы:**
- B008: Depends() в аргументах по умолчанию (28 мест)
- B904: raise без from (4 места)
- B905: zip() без strict= (8 мест)
- F401: Неиспользуемые импорты (40+ мест)
- Отсутствующие аннотации типов

**Задача:** Привести код к нулевым ошибкам ruff и mypy.

---

### 4.2 Обработка ошибок и исключений
**Текущее состояние:** Нет from e, пустые except, неправильные статус-коды  
**Файлы для изменения:**
- `src/mko_bi/utils/exceptions.py` - кастомные исключения
- `src/mko_bi/api/routes/` - все файлы маршрутов
- `src/mko_bi/services/` - все сервисы

**Новая структура:**
```
src/mko_bi/utils/
  └── exceptions.py            # Кастомные исключения
```

**Задача:** Внедрить единый подход к обработке ошибок с корректными HTTP статус-кодами.

---

### 4.3 Транзакции и управление сессиями
**Текущее состояние:** Утечки сессий БД, нет явных транзакций  
**Файлы для изменения:**
- `src/mko_bi/db/session.py` - контекстный менеджер
- `src/mko_bi/core/permissions.py` - гарантированное закрытие
- `src/mko_bi/services/` - все использования SessionLocal

**Задача:** Обеспечить 100% гарантию закрытия сессий БД.

---

### 4.4 Безопасность
**Текущее состояние:** Нет rate limiting, SQL-инъекции в Polars, инъекции в CSV  
**Файлы для изменения:**
- `src/mko_bi/core/security.py` - валидация полей
- `src/mko_bi/api/routes/upload.py` - валидация CSV
- `src/mko_bi/data/processing/` - белые списки полей
- `src/mko_bi/app.py` - middleware rate limiting

**Новая структура:**
```
src/mko_bi/core/
  └── security.py              # Валидация, безопасность
```

**Задача:** Усилить безопасность: rate limiting, валидация входных данных.

---

### 4.5 Работа с файлами
**Текущее состояние:** Path traversal, незакрытые дескрипторы, orphaned files  
**Файлы для изменения:**
- `src/mko_bi/utils/file_utils.py` - улучшить очистку
- `src/mko_bi/api/routes/upload.py` - валидация filename
- `src/mko_bi/services/data_service.py` - гарантированное удаление

**Задача:** Обеспечить безопасную и надежную работу с файлами.

---

### 4.6 Type hints и mypy
**Текущее состояние:** Использование Any, missing Optional, циклические импорты  
**Файлы для изменения:**
- ВСЕ файлы проекта - добавить корректные аннотации

**Задача:** Привести типизацию к стандарту, устранить все ошибки mypy.

---

### 4.7 Документация
**Текущее состояние:** Отсутствуют docstring, неясные названия  
**Файлы для изменения:**
- ВСЕ публичные функции и классы

**Задача:** Добавить Google-style docstrings ко всей публичной API.

---

## 5. УДАЛЕНИЕ ДУБЛИРОВАНИЯ И СТАНДАРТИЗАЦИЯ

### 5.1 Базовые классы
**Файлы для создания:**
- `src/mko_bi/core/base_repository.py` - базовый репозиторий
- `src/mko_bi/core/base_service.py` - базовый сервис
- `src/mko_bi/api/deps.py` - общие зависимости

**Задача:** Вынести общие паттерны в базовые классы.

---

### 5.2 Утилиты и валидация
**Файлы для создания:**
- `src/mko_bi/utils/validators.py` - валидаторы email, роли и т.д.
- `src/mko_bi/utils/decorators.py` - декораторы (обработка ошибок, rate limit)

**Задача:** Централизовать повторяющийся код.

---

## 6. ТЕСТИРОВАНИЕ

### 6.1 Исправление существующих тестов
**Файлы для исправления:**
- `tests/services/test_data_service.py:672-673` - синтаксическая ошибка
- Все тесты - привести к рабочему состоянию

**Задача:** Исправить синтаксические ошибки в тестах.

---

### 6.2 Новые тесты
**Файлы для создания:**
- `tests/test_dash_app.py` - тесты Dash приложения
- `tests/test_filters_api.py` - тесты API фильтров
- `tests/test_processing_configs_api.py` - тесты API настроек
- `tests/test_processing_logs_api.py` - тесты API логов
- `tests/test_integration.py` - интеграционные тесты

**Задача:** Дополнить тестовое покрытие.

---

## 7. КОНФИГУРАЦИЯ И РАЗВЕРТЫВАНИЕ

### 7.1 Миграции БД
**Файлы для создания:**
- `alembic/` - каталог миграций
- `.env.example` - шаблон переменных окружения

**Задача:** Настроить Alembic для управления миграциями.

---

### 7.2 Docker
**Файлы для изменения:**
- `src/mko_bi/Dockerfile` - исправить опечатку
- `docker-compose.yml` - добавить сервисы БД, Redis

**Задача:** Настроить контейнеризацию.

---

## ИТОГОВАЯ ОЦЕНКА

**Время на реализацию:**
- Критические проблемы: 1 неделя
- Высокоприоритетные: 2 недели  
- Архитектурные изменения: 1 неделя
- Качество кода: 1 неделя
- Тестирование: 1 неделя

**Итого:** ~6 недель до production-ready состояния

**Риски:**
1. Интеграция Dash с FastAPI может потребовать дополнительного времени
2. YoY расчеты требуют четкого понимания бизнес-логики
3. Рефакторинг архитектуры может повлиять на существующий код

**Рекомендация:** Выполнять задачи итеративно, начиная с критических проблем.
