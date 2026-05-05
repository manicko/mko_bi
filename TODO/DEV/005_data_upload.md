---
## BLOCK 5: DATA UPLOAD
---

### TASK: File upload endpoint

FILE: `src/mko_bi/api/routes/upload.py`

GOAL: Endpoint для загрузки CSV/CSV.gz (SPEC.md п.8, п.14.3)

IMPLEMENT:

* `POST /api/v1/upload/{dashboard_id}?mode=overwrite|append`:
  * `File(...)` - multipart file
  * `mode: UploadMode = UploadMode.OVERWRITE`
  * `current_user: User = Depends(get_current_user)`
  * Response: `{"message": str, "processing_log_id": UUID}`
  * Логика:
    1. Проверка прав (editor+)
    2. Валидация файла (extension, MIME-type, size)
    3. Сохранение во временную папку (platformdirs)
    4. Создание processing_log (status=UPLOADED)
    5. Enqueue processing task
    6. Возврат processing_log_id

LOGIC:

1. Использовать FastAPI `UploadFile`
2. Rate limiting (slowapi или custom middleware)
3. Максимальный размер файла из config
4. Проверка `content-type` header + file extension
5. Логирование upload event

DONE:

* [ ] Upload endpoint работает
* [ ] Валидация файла работает
* [ ] Временный файл создается
* [ ] Processing log создается
* [ ] Тесты написаны

---

### TASK: Upload service

FILE: `src/mko_bi/services/data_service.py` (расширение)

GOAL: Бизнес-логика загрузки

IMPLEMENT:

* `async def handle_upload(...) -> ProcessingLogResponse`:
  * Сохранение файла во временную папку
  * Вызов loader для чтения
  * Определение mode (overwrite/append)
  * Очистка временных файлов

LOGIC:

1. Использование `file_utils.get_user_temp_dir()`
2. `shutil.copyfileobj()` для сохранения uploaded file
3. Обработка ошибок с rollback

DONE:

* [ ] Сервис работает
* [ ] Интеграция с API
* [ ] Тесты написаны

---

### TASK: Data loader (Polars)

FILE: `src/mko_bi/data/loaders/loader.py`

GOAL: Загрузка CSV/CSV.gz через Polars (SPEC.md п.2.26, п.7)

IMPLEMENT:

* `async def load_csv(filepath: Path, config: dict | None = None) -> pl.DataFrame`:
  * Поддержка .csv и .csv.gz
  * UTF-8 encoding
  * Параметры из processing_configs (separator, has_header, etc.)
* `def detect_file_type(filename: str) -> str`:
  * Возврат "csv" или "csv_gz"

LOGIC:

1. `polars.read_csv()` для .csv
2. `polars.read_csv(gzip.imopen(filepath))` для .csv.gz
3. Проверка на пустой DataFrame
4. Логирование: количество строк, колонок

DONE:

* [ ] CSV читается
* [ ] CSV.gz читается
* [ ] Ошибки обрабатываются
* [ ] Тесты написаны

---

### TASK: File validator

FILE: `src/mko_bi/data/loaders/validator.py`

GOAL: Валидация загружаемых файлов (SPEC.md п.6)

IMPLEMENT:

* `def validate_file_extension(filename: str) -> bool`
* `def validate_mime_type(mime_type: str) -> bool`
* `def validate_file_size(file_size: int, max_size_mb: int) -> bool`
* `def validate_dataframe(df: pl.DataFrame, config: dict) -> list[str]` (warnings/errors)

LOGIC:

1. Использовать `MimeTypeEnum`, `FileExtensionEnum`
2. Проверка максимального размера из config
3. Валидация структуры DataFrame (обязательные колонки)

DONE:

* [ ] Валидация работает
* [ ] Тесты написаны

---
