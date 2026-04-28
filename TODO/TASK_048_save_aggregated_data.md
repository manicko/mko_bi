TASK: Реализовать сохранение агрегированных данных в БД

FILE: src/mko_bi/services/data_service.py, src/mko_bi/db/repositories/aggregated_data_repo.py

GOAL: Сохранять результаты агрегации в таблицу aggregated_data после обработки CSV

IMPLEMENT:

func: save_aggregated_data()
func: _process_csv_file() - интеграция сохранения

LOGIC:

1. В aggregated_data_repo.py:
   - Репозиторий для работы с aggregated_data
   - Метод bulk_insert для пакетной вставки
   - Метод delete_by_dashboard для очистки старых данных
   - Метод get_by_graph для чтения
2. В data_service.py:
   - После агрегации в _process_csv_file():
     * Подготовить данные для вставки
     * Вызвать bulk_insert через репозиторий
     * В транзакции с обработкой
   - Удалить старые данные перед вставкой новых
   - Обработка ошибок сохранения
3. Формат данных:
   - dashboard_id: UUID
   - graph_id: UUID
   - dims: JSONB (значения измерений)
   - metrics: JSONB (значения метрик)

CONSTRAINTS:

- Использовать bulk_insert для производительности
- Удалять старые данные для данного dashboard_id
- Обрабатывать ошибки уникальности
- Сохранять все метрики и измерения
- Работать в транзакции с обработкой
- Логировать количество сохраненных строк

DONE:

- Агрегаты сохраняются в aggregated_data
- Данные доступны для дашбордов
- Нет дублирования при повторной обработке
- Производительность приемлемая
- Тесты на сохранение данных
