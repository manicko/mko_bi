TASK: Создать API эндпоинты для логов обработки (processing_logs)

FILE: src/mko_bi/api/routes/processing_logs.py, src/mko_bi/services/processing_log_service.py

GOAL: Реализовать API для аудита и мониторинга процесса обработки данных

IMPLEMENT:

func: create_log()
func: update_log_status()
func: get_logs()
func: get_log()

LOGIC:

1. В processing_log_service.py:
   - Создание записи лога при старте обработки
   - Обновление статуса (started → success/failed)
   - Запись сообщения об ошибке
   - Фильтрация логов по dashboard_id, статусу, дате
2. В api/routes/processing_logs.py:
   - POST /processing-logs/ - создать запись
   - PUT /processing-logs/{id}/status - обновить статус
   - GET /processing-logs/ - список логов (с фильтрацией)
   - GET /processing-logs/{id} - получить лог
3. Интеграция с data_service:
   - Вызов create_log() при старте обработки
   - Вызов update_log_status() по завершении
   - Логирование ошибок
4. Модели Pydantic:
   - ProcessingLogCreate - создание
   - ProcessingLogUpdate - обновление статуса
   - ProcessingLogRead - чтение

CONSTRAINTS:

- Автоматическое создание при запуске обработки
- Обновление finished_at при завершении
- Фильтрация по dashboard_id и статусу
- Сохранение ошибок для дебаггинга
- Только admin/editor могут читать логи
- Пагинация для больших списков

DONE:

- API для логов обработки работает
- Автоматическое создание при старте
- Обновление статусов
- Фильтрация и поиск
- Аудит всех операций обработки

