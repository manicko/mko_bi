TASK: Использование CSVLoader вместо дублирования (цепочка)

FILE: src/mko_bi/services/data_service.py
FILE: src/mko_bi/data/loaders/loader.py

GOAL: Устранить дублирование кода загрузки CSV через использование существующего CSVLoader

IMPLEMENT:

func: рефакторинг data_service.py для использования CSVLoader

LOGIC:

1. В data_service.py импортировать CSVLoader:
```
from mko_bi.data.loaders.loader import CSVLoader
```

2. Заменить дублирующие функции:
   - `_read_csv_safe()` -> `CSVLoader.load_csv()`
   - `_validate_file_size()` -> встроено в CSVLoader

3. Обновить `_upload_file_logic`:
```
# Вместо:
# csv_df = _read_csv_safe(file_path)
# Использовать:
loader = CSVLoader()
csv_df = loader.load_csv(file_path, lazy_threshold_mb=config.lazy_threshold_mb)
```

4. Удалить функции `_read_csv_safe`, `_validate_file_size` из data_service.py после рефакторинга

5. Проверить что CSVLoader поддерживает все нужные опции:
   - .csv и .csv.gz
   - Lazy loading для больших файлов
   - Валидация размера

CONSTRAINTS:

- Выполняется ПОСЛЕ TASK-008 (после рефакторинга pipeline)
- CSVLoader уже реализован в data/loaders/loader.py
- Не создавать новый код, использовать существующий
- Сохранить поддержку.gz файлов

DONE:

- `_read_csv_safe()` и `_validate_file_size()` удалены из data_service.py
- CSVLoader используется для загрузки CSV
- Все опции (lazy_threshold, .gz support) сохранены
- `uv run ruff check .` проходит
- `uv run pytest tests/test_data_loader.py` проходит

TEST:

uv run pytest tests/test_data_loader.py -v
uv run pytest tests/services/test_data_service.py -v
