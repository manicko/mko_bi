TASK: тесты для YoY и долей

FILE: tests/test_yoy_calculation.py, tests/test_share_calculation.py

GOAL: проверка корректности расчетов

IMPLEMENT:

# test_yoy_calculation.py
def test_yoy_with_grouping():
    df = pl.DataFrame({
        "year": [2023, 2023, 2024, 2024],
        "dimension": ["A", "B", "A", "B"],
        "metric_value": [100, 200, 110, 240]
    })
    result = _calculate_yoy(df)
    # 2024-A сравнивается с 2023-A (не с 2023-B)
    assert result.filter(year=2024, dimension="A")["yoy_percent"] == 10.0

# test_share_calculation.py
def test_share_calculation():
    ...

LOGIC:

написать тесты для _calculate_yoy() с группировками
написать тесты для _calculate_share()
протестировать edge cases (пустые данные, деление на ноль)

CONSTRAINTS:

покрытие всех граничных случаев
корректность расчетов

DONE:

тесты для YoY созданы
тесты для долей созданы
edge cases покрыты
