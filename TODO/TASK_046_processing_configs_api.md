TASK: Создать API эндпоинты для управления настройками обработки (processing_configs)

FILE: src/mko_bi/api/routes/processing_configs.py, src/mko_bi/services/processing_config_service.py

GOAL: Реализовать API для настройки параметров обработки данных per dashboard

IMPLEMENT:

func: create_or_update_config()
func: get_config()
func: update_config()

LOGIC:

1. В processing_config_service.py:
   - Бизнес-логика для processing_configs
   - Создание/обновление настроек
   - Валидация settings JSONB
   - Проверка прав доступа (admin/editor)
2. В api/routes/processing_configs.py:
   - GET /processing-configs/{dashboard_id} - получить настройки
   - PUT /processing-configs/{dashboard_id} - обновить настройки
3. Модели Pydantic:
   - ProcessingConfigCreate - создание
   - ProcessingConfigUpdate - обновление
   - ProcessingConfigRead - чтение
4. Валидация:
   - Проверка структуры settings
   - Обязательные поля (loader, date_column, timezone)
   - Формат значений

CONSTRAINTS:

- Связь 1:1 с dashboard (dashboard_id PK/FK)
- Только admin/editor могут изменять
- Viewer может только читать
- Валидация JSONB структуры
- Обновление updated_at при изменении
- Корректные ошибки валидации

DONE:

- API для настройки обработки работает
- Валидация settings
- Проверка прав доступа
- Связь с дашбордом
- Тесты на CRUD операции
- Логирование изменений
