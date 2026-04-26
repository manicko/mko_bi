TASK: API загрузки и обработки данных

FILE: src/mko_bi/api/routes/upload.py

GOAL: Создать эндпоинты для загрузки CSV и триггера обработки

IMPLEMENT:

router: APIRouter с prefix="/upload"

@endpoint: POST /upload
@endpoint: POST /upload/{dashboard_id}/process
@endpoint: GET /upload/status/{task_id}

LOGIC:
- POST /upload: загрузка .csv.gz файла во временную директорию
- POST /upload/{id}/process: запуск пайплайна обработки данных
- GET /upload/status/{id}: проверка статуса обработки
- Валидация формата файла и размера
- Удаление файла после обработки

CONSTRAINTS:
- Разрешены только .csv.gz файлы
- Максимальный размер: 100MB
- Обработка через DataService
- Асинхронная обработка (BackgroundTasks)
- Очистка временных файлов
- HTTP статусы: 200, 202, 413, 415

DONE:
- Эндпоинт загрузки работает
- Триггер обработки запускает пайплайн
- Статус задачи доступен
- Валидация файлов работает
- Файлы удаляются после обработки

Тесты: нужны только глубоко тестирующие бизнес-логику.