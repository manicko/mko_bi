TASK: Реализовать YoY (Year-over-Year) расчеты в обработке данных

FILE: src/mko_bi/data/processing/transformations.py, src/mko_bi/dashboards/components/charts/line.py

GOAL: Добавить расчет год-к-год сравнения для временных рядов согласно SPEC.md

IMPLEMENT:

func: calculate_yoy(current_df, previous_df, metric_columns)
func: add_yoy_to_graph(graph_config, data)

LOGIC:

1. В transformations.py:
   - Функция calculate_yoy:
     * Принимает текущий и предыдущий период данных
     - Вычисляет разницу в абсолютных значениях
     - Вычисляет процентное изменение
     - Возвращает DataFrame с колонками yoy_diff, yoy_pct
   - Обработка edge cases:
     * Деление на ноль
     * Отсутствие данных за предыдущий период
     * Неполные данные
2. В line.py:
   - Добавить поддержку отображения YoY линий
   - Настройка отображения (сплошная/пунктирная)
   - Цветовая схема для YoY
3. Интеграция в pipeline:
   - Вызов YoY расчета после базовых агрегаций
   - Сохранение YoY метрик в aggregated_data
   - Передача в frontend для отображения

CONSTRAINTS:

- Использовать Polars для вычислений
- Поддержка нескольких метрик одновременно
- Корректная обработка missing данных
- Производительность на больших датасетах
- Сохранение результатов в БД

DONE:

- YoY расчеты работают корректно
- Данные сохраняются в aggregated_data
- Графики отображают YoY линии
- Тесты покрывают edge cases
- Производительность приемлемая
