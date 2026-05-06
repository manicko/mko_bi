---
## CODE QUALITY & REFACTORING
---

### TASK: Централизация валидации файлов

FILE: `src/mkobi/api/routes/upload.py`, `src/mkobi/services/data_service.py`

GOAL: Устранить дублирование логики валидации файлов

FINDINGS (TASK_01):
- Проверка размера файла выполняется дважды (в роутере и в сервисе)
- MIME-type проверяется и там и там
- Дублирование увеличивает риск несогласованных изменений

IMPLEMENT:

* Оставить валидацию в сервисном слое (`data_service.py`)
* Убрать дублирующие проверки из роутера (`upload.py`)
* В роутере оставить только HTTP-специфичные аспекты

DONE:

* [ ] Валидация централизована в сервисном слое
* [ ] Дублирование кода устранено
* [ ] Тесты валидации проходят

---

### TASK: Улучшение очистки временных файлов

FILE: `src/mkobi/services/data_service.py`

GOAL: Расширить шаблоны поиска временных файлов

FINDINGS (TASK_01):
- `cleanup_task_files` ищет только `*.csv.gz` файлы
- Могут оставаться `.csv` файлы

IMPLEMENT:

* Изменить шаблон поиска на `*{task_id}*.csv*` (оба расширения)
* Проверить функцию `trigger_processing` на аналогичные проблемы

DONE:

* [ ] Поиск файлов охватывает оба расширения (.csv и .csv.gz)
* [ ] Временные файлы корректно удаляются

---

### TASK: Рефакторинг длинных функций в data_service.py

FILE: `src/mkobi/services/data_service.py`

GOAL: Разбить длинные функции на более мелкие для улучшения тестируемости

FINDINGS (TASK_01):
- `_validate_file` (строки 83-129) - длинная, выполняет несколько проверок
- `_process_csv_file` (строки 651-709) - очень длинная
- `upload_file` / `_upload_file_logic` (120+ строк)

DECISION: Рефакторинг без overengineering. Разбить только если это улучшит читаемость.

IMPLEMENT (только если функция > 50 строк и имеет несколько обязанностей):

* `_validate_file` → разбить на `_validate_mime_type`, `_validate_extension`, `_validate_size`
* `_upload_file_logic` → вынести `check_dashboard_access`, `handle_upload_mode`, `create_processing_log`
* Добавить docstrings для новых функций

DONE:

* [ ] Длинные функции разбиты (при необходимости)
* [ ] Код стал более читаемым
* [ ] Тесты проходят

---

### TASK: Объединение дублирующих эндпоинтов auth.py

FILE: `src/mkobi/api/routes/auth.py`

GOAL: Устранить дублирование между /login и /login/form

FINDINGS (TASK_01):
- `/login/form` дублирует логику основного `/login` эндпоинта

IMPLEMENT:

* Сделать `/login/form` оберткой над `/login`
* Или объединить логику в сервисном слое
* Оставить в роутерах только обработку HTTP-specific аспектов

DONE:

* [ ] Дублирование кода устранено
* [ ] Логика аутентификации в одном месте (сервис)

---
