---
## BLOCK 11: PROCESSING LOGS
---

### TASK: Processing logs repository

FILE: `src/mko_bi/db/repositories/processing_log_repo.py`

GOAL: Репозиторий для логов обработки (SPEC.md п.16.1, таблица processing_logs)

IMPLEMENT:

* `class ProcessingLogRepository(BaseRepository[ProcessingLog])`:
  * `async def create_log(self, dashboard_id: UUID | None, status: ProcessingStatus, message: str | None = None) -> ProcessingLog`
  * `async def update_status(self, log_id: UUID, status: ProcessingStatus, message: str | None = None) -> None`
  * `async def get_by_dashboard(self, dashboard_id: UUID, db: AsyncSession) -> list[ProcessingLogResponse]`
  * `async def get_filtered(self, filters: ProcessingLogFilter, db: AsyncSession) -> list[ProcessingLogResponse]`
  * `async def get_latest_by_dashboard(self, dashboard_id: UUID, db: AsyncSession) -> ProcessingLogResponse | None`

LOGIC:

1. started_at заполняется при создании
2. finished_at заполняется при SUCCESS/FAILED
3. message хранит описание ошибки или успеха

DONE:

* [ ] Repository методы работают
* [ ] Тесты написаны

---

### TASK: Processing logs API

FILE: `src/mko_bi/api/routes/processing_logs.py`

GOAL: Endpoint для просмотра логов (SPEC.md п.14.4)

IMPLEMENT:

* `GET /api/v1/admin/logs` (admin):
  * Query params: `dashboard_id`, `status`, `date_from`, `date_to`, `skip`, `limit`
  * Response: `list[ProcessingLogResponse]`
* `GET /api/v1/admin/logs/{log_id}` (admin) - детали лога

LOGIC:

1. Фильтрация по dashboard_id, status, date range
2. Пагинация (skip, limit)
3. Сортировка по started_at DESC

DONE:

* [ ] Logs endpoint работает
* [ ] Фильтры применяются
* [ ] Тесты написаны

---

### TASK: Processing logs service

FILE: `src/mko_bi/services/processing_log_service.py`

GOAL: Бизнес-логика логов

IMPLEMENT:

* `class ProcessingLogService`:
  * `async def create_started_log(dashboard_id: UUID | None, db: AsyncSession) -> ProcessingLogResponse`
  * `async def update_to_uploaded(log_id: UUID, db: AsyncSession)`
  * `async def update_to_processing(log_id: UUID, db: AsyncSession)`
  * `async def update_to_success(log_id: UUID, message: str | None, db: AsyncSession)`
  * `async def update_to_failed(log_id: UUID, error: str, db: AsyncSession)`
  * `async def get_filtered(filters: ProcessingLogFilter, db: AsyncSession) -> list[ProcessingLogResponse]`

LOGIC:

1. Вызывается из DataPipeline на каждом этапе
2. Логирование upload, processing, errors (SPEC.md п.20)
3. Уровни: INFO, WARNING, ERROR

DONE:

* [ ] Service методы работают
* [ ] Интеграция с pipeline
* [ ] Тесты написаны

---
