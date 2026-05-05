---
## BLOCK 4: CORE INFRASTRUCTURE
---

### TASK: Logging configuration

FILE: `src/mko_bi/core/logging_config.py`

GOAL: Настройка логирования согласно SPEC.md п.20, п.2.31

IMPLEMENT:

* `setup_logging(log_level: str = "INFO", log_file: str | None = None) -> None`
  * Настройка root logger
  * Форматтер с временем, уровнем, модулем
  * Handler для консоли (stdout)
  * Handler для файла (опционально, JSON формат)
* `get_logger(name: str) -> logging.Logger`
  * Фабрика логгеров для модулей

LOGIC:

1. Использовать `logging` стандартную библиотеку
2. JSON формат для продакшена (`python-json-logger` или custom)
3. Уровни: INFO, WARNING, ERROR (SPEC.md п.20)
4. Логирование upload, processing, errors, access events

DONE:

* [ ] Логирование настроено
* [ ] Логи пишутся в файл (если указан)
* [ ] JSON формат работает

---

### TASK: Base repository (async)

FILE: `src/mko_bi/core/base_repository.py`

GOAL: Базовый класс для async репозиториев (SPEC.md требует async SQLAlchemy)

IMPLEMENT:

* `class BaseRepository[T]` (Generic):
  * `def __init__(self, model: type[T], db: AsyncSession)`
  * `async def get_by_id(self, id: UUID) -> T | None`
  * `async def get_all(self, skip: int = 0, limit: int = 100) -> list[T]`
  * `async def create(self, obj_in: dict | BaseModel) -> T`
  * `async def update(self, id: UUID, obj_in: dict | BaseModel) -> T | None`
  * `async def delete(self, id: UUID) -> bool`
  * `async def exists(self, **kwargs) -> bool`

LOGIC:

1. Использовать `sqlalchemy.ext.asyncio` сессии
2. `select()`, `insert()`, `update()`, `delete()` операции
3. Поддержка `commit()` и `refresh()`
4. Обработка `NoResultFound` exception

DONE:

* [ ] BaseRepository работает
* [ ] Все CRUD операции работают
* [ ] Тесты на базовые операции

---

### TASK: Task queue for data processing

FILE: `src/mko_bi/core/task_queue.py`

GOAL: Очередь задач для асинхронной обработки данных (SPEC.md подразумевает processing pipeline)

IMPLEMENT:

* `class TaskQueue`:
  * `async def enqueue(self, task_func: Callable, *args, **kwargs) -> str` (task_id)
  * `async def process_next(self) -> None`
  * `async def get_status(self, task_id: str) -> ProcessingStatus`

LOGIC:

1. Для MVP: простая in-memory очередь (asyncio.Queue)
2. Для production: можно заменить на Redis/RabbitMQ
3. Сохранение статуса в processing_logs
4. Обработка ошибок с retry (опционально)

DONE:

* [ ] Очередь работает
* [ ] Задачи выполняются асинхронно
* [ ] Статусы отслеживаются

---

### TASK: File utilities (platformdirs)

FILE: `src/mko_bi/utils/file_utils.py`

GOAL: Работа с временными файлами через platformdirs (SPEC.md п.33, п.7)

IMPLEMENT:

* `get_user_temp_dir(user_id: UUID | str) -> Path`
  * Использовать `platformdirs.user_cache_dir()` + prefix
* `cleanup_temp_dir(temp_dir: Path) -> None`
  * Удаление временной папки после обработки
* `validate_file_extension(filename: str) -> bool`
  * Проверка .csv, .csv.gz
* `validate_mime_type(mime_type: str) -> bool`
  * Проверка text/csv, application/gzip

LOGIC:

1. `platformdirs.user_cache_dir("mko_bi", appauthor=False)` 
2. Создание уникальной подпапки для каждого upload
3. Удаление через `shutil.rmtree()` после processing
4. Проверка расширений через `pathlib.Path.suffix`

DONE:

* [ ] Temp dir создается
* [ ] Temp dir удаляется
* [ ] Валидация файлов работает

---

### TASK: Exception handlers

FILE: `src/mko_bi/utils/exceptions.py`

GOAL: Кастомные исключения и обработчики

IMPLEMENT:

* `class AppException(Exception)` - базовый
* `class NotFoundException(AppException)`
* `class PermissionDeniedException(AppException)`
* `class ValidationException(AppException)`
* `class FileUploadException(AppException)`
* `add_exception_handlers(app: FastAPI) -> None`
  * Регистрация обработчиков в FastAPI

LOGIC:

1. Наследование от Exception
2. Атрибуты: status_code, detail, error_code
3. FastAPI exception_handler decorator

DONE:

* [ ] Исключения определены
* [ ] Обработчики зарегистрированы
* [ ] Возвращают правильные HTTP статусы

---
