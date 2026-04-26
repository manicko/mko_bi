TASK: Тесты пайплайна данных

FILE: tests/data/test_pipeline.py
FILE: tests/data/test_processing.py

GOAL: Написать тесты для загрузки и обработки данных

IMPLEMENT:

test: test_csv_loading
test: test_data_validation
test: test_transformations
test: test_aggregations
test: test_storage

LOGIC:
- Тесты загрузки .csv.gz файлов
- Тесты валидации структуры данных
- Тесты трансформаций (фильтры, группировки)
- Тесты агрегаций (groupby, YoY, доли)
- Тесты сохранения в БД

CONSTRAINTS:
- Использовать pytest
- Мокирование файловой системы
- Изоляция тестов
- Фикстуры для тестовых данных
- Покрытие: 90%+ пайплайна

DONE:
- Пайплайн протестирован
- Загрузка работает корректно
- Трансформации верны
- Агрегации точны
- Сохранение работает

Тесты: нужны только глубоко тестирующие бизнес-логику.