TASK: Интеграция transformations.py в pipeline обработки (цепочка)

FILE: src/mko_bi/services/data_service.py
FILE: src/mko_bi/data/processing/transformations.py

GOAL: Использование полноценных функций трансформации (calculate_aggregations, apply_transformations) вместо упрощенных версий

IMPLEMENT:

func: рефакторинг _trigger_processing_logic для использования transformations.py

LOGIC:

1. В data_service.py импортировать функции из transformations.py:
```
from mko_bi.data.processing.transformations import (
    apply_transformations,
    calculate_aggregations,
)
```

2. Найти место в `_trigger_processing_logic` где применяются агрегации:
   - Сейчас используются упрощенные `_apply_aggregations`, `_apply_filters`
   - Заменить на вызов `calculate_aggregations()`

3. Обновить логику обработки:
```
# Вместо упрощенных функций:
if processing_config:
    result_df = calculate_aggregations(
        df=df,
        groupby=processing_config.groupby,
        aggregations=processing_config.aggregations,
        yoy_config=processing_config.yoy,
        share_config=processing_config.share,
        custom_metrics=processing_config.custom_metrics,
    )
```

4. Убедиться что все параметры корректно передаются (FilterConfig, AggregationConfig и т.д.)

5. Удалить неиспользуемый упрощенный код после рефакторинга

CONSTRAINTS:

- Выполняется ПОСЛЕ TASK-001 (перевод на async) если затрагивает async код
- Сохранить обратную совместимость с существующими processing_configs
- Использовать существующие функции в transformations.py (они уже реализованы)
- Функции YoY, share, custom_metrics должны работать

DONE:

- `calculate_aggregations()` интегрирована в pipeline
- YoY расчеты работают (проверено на тестовых данных)
- Share calculations работают
- Custom metrics работают
- Упрощенные функции-дубликаты удалены
- `uv run pytest tests/test_data_processing.py` проходит

TEST:

uv run pytest tests/test_data_processing.py -v
uv run pytest tests/services/test_data_service.py -v
