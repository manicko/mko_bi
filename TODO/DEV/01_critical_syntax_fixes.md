---
## CRITICAL SYNTAX FIXES
---

### TASK: Исправление синтаксических ошибок в auth.py

FILE: `src/mkobi/api/routes/auth.py`

GOAL: Устранить синтаксические ошибки, препятствующие запуску кода

FINDINGS (TASK_03):
- Строка 67: отсутствует запятая между аргументами `login_data.email, login_data.password`
- Строки 112-113: `auth_service.login_user()` вызывается без `await` (функция async)

IMPLEMENT:

* Исправить строку 67: добавить запятую
* Исправить строки 112-113: добавить `await` перед `auth_service.login_user()`
* Проверить все вызовы async функций в файле

DONE:

* [ ] Синтаксическая ошибка в строке 67 исправлена
* [ ] Добавлен `await` в строках 112-113
* [ ] Проверка остальных async вызовов в auth.py
* [ ] Код запускается без SyntaxError

---

### TASK: Исправление синтаксических ошибок в data_service.py

FILE: `src/mkobi/services/data_service.py`

GOAL: Устранить синтаксические ошибки и опечатки в именах enum

FINDINGS (TASK_03 + code review):
- Строка 448: `ProcessingStatus.PROCESS_ING` - опечатка (лишнее O), должно быть `ProcessingStatus.PROCESSING`
- Строка 464: `ProcessingStatus.PROCESS_ING` - та же опечатка
- Строка 467: отсутствует запятая `db, task_id, **log_update.model_dump()`
- Строка 356: отсутствует запятая `dashboard_id, processing_log, db`
- Строка 369: отсутствует запятая `dashboard_id, processing_log, db`
- Множественные вызовы `ProcessingLogRepository.update(db, task_id, **log_update.model_dump())` - отсутствует запятая после db

IMPLEMENT:

* Найти все обращения к `ProcessingStatus.PROCESS_ING` и исправить на `ProcessingStatus.PROCESSING`
* Добавить запятые во все вызовы функций с пропущенными запятыми
* Проверить файл на наличие других синтаксических ошибок

DONE:

* [ ] Опечатки `PROCESS_ING` исправлены на `PROCESSING`
* [ ] Запятые добавлены во все вызовы функций
* [ ] Файл проходит синтаксический анализ (python -m py_compile)

---

### TASK: Исправление вызова get_current_user в permissions.py

FILE: `src/mkobi/core/permissions.py`

GOAL: Добавить await для async функции get_current_user

FINDINGS (TASK_03):
- Строка 435: `user = get_current_user(credentials.credentials, db)` вызывается без `await`
- Функция `get_current_user` является async

IMPLEMENT:

* Добавить `await` перед `get_current_user()` в строке 435
* Проверить тип возвращаемого значения (должен быть `UserDB`)

DONE:

* [ ] Добавлен `await` в строке 435
* [ ] Проверка типизации вызова

---

### TASK: Исправление открытия файла в upload.py

FILE: `src/mkobi/api/routes/upload.py`

GOAL: Использовать контекстный менеджер для открытия файла

FINDINGS (TASK_03):
- Строка 140: `open(file_path, "wb")` не закрывается явно

IMPLEMENT:

* Заменить `open(file_path, "wb")` на `with open(...) as f:`
* Или использовать `async with aiofiles.open(...)` для асинхронности

DONE:

* [ ] Использован контекстный менеджер для открытия файла
* [ ] Утечек файловых дескрипторов нет

---
