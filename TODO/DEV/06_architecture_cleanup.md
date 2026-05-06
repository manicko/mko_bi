---
## ARCHITECTURE CLEANUP (LOW PRIORITY)
---

### TASK: Dash Legacy Components Cleanup

FILE: `src/mkobi/dashboards/`, `src/mkobi/dash_app.py`

GOAL: Очистить или заархивировать Dash компоненты (переход на React + Plotly.js)

FINDINGS (TASK_02):
- `dashboards/` директория содержит Dash-специфичный код
- `dash_app.py` монтирует Dash app at `/dashboards`
- SPEC.md указывает на миграцию к React + Plotly.js

DECISION: Если фронтенд полностью мигрировал на React:
- Удалить `dashboards/` директорию
- Удалить `dash_app.py`
- Убрать зависимости Dash из `pyproject.toml`

Если миграция не завершена:
- Оставить как есть до завершения миграции

IMPLEMENT (только после проверки, что React фронтенд работает полностью):

* Проверить, используется ли Dash в продакшене
* Если нет - удалить `dashboards/` и `dash_app.py`
* Обновить `app.py` (убрать монтирование Dash)

DONE:

* [ ] Проверена необходимость Dash компонентов
* [ ] Dash компоненты удалены ИЛИ оставлены с документацией

---

### TASK: Проверка async/sync смешивания

FILE: `src/mkobi/services/*.py`

GOAL: Устранить смешивание async/sync кода

FINDINGS (TASK_02 + TASK_03):
- Некоторые сервисы используют async, другие sync
- Забытые `await` в некоторых местах (уже частично исправлено в BLOCK 01)

IMPLEMENT:

* Проверить все сервисы на корректность async/await
* Убедиться, что интерфейсы (interfaces/) соответствуют реализации
* Исправить несоответствия типов в интерфейсах

DONE:

* [ ] Все async функции вызываются с `await`
* [ ] Интерфейсы соответствуют реализации
* [ ] mypy не выдает ошибок override incompatibility

---

### TASK: Настройка Rate Limiting для login

FILE: `src/mkobi/api/routes/auth.py`, `src/mkobi/core/security.py`

GOAL: Добавить rate limiting для эндпоинта /login

FINDINGS (TASK_03):
- В `security.py` есть `RateLimiter`, но он используется только для upload
- Для защиты от брутфорса нужен rate limit на login

IMPLEMENT:

* Добавить RateLimiter для `/login` и `/login/form`
* Настроить лимит (например, 5 попыток в минуту)
* Использовать Redis для отслеживания

DONE:

* [ ] Rate limiting настроен для login эндпоинтов
* [ ] Защита от брутфорса работает

---
