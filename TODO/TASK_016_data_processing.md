TASK: Пайплайн обработки данных

FILE: src/mko_bi/data/processing/base.py
FILE: src/mko_bi/data/processing/registry.py
FILE: src/mko_bi/data/processing/transformations.py

GOAL: Реализовать пайплайн трансформации и агрегации данных

IMPLEMENT:

class: DataProcessor
class: TransformationRegistry
func: apply_transformations
func: calculate_aggregations

LOGIC:
- DataProcessor: orchestration всего пайплайна
- TransformationRegistry: реестр трансформаций
- apply_transformations: фильтрация, группировка, сортировка
- calculate_aggregations: groupby, YoY, доли, кастомные метрики
- Полный пересчет данных для дашборда

CONSTRAINTS:
- Использовать Polars для трансформаций
- Поддержка groupby, sum, mean, count
- YoY расчет: сравнение с предыдущим годом
- Доли: процент от общего
- Кастомные метрики через конфигурацию

DONE:
- Пайплайн обрабатывает данные
- Трансформации применяются корректно
- Агрегации рассчитываются
- YoY и доли работают
- Данные готовы для сохранения

Тесты: нужны только глубоко тестирующие бизнес-логику.