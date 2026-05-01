TASK: исправление расчета YoY

FILE: src/mko_bi/data/processing/transformations.py

GOAL: корректный расчет Year-over-Year с группировкой

IMPLEMENT:

def _calculate_yoy(df: pl.DataFrame) -> pl.DataFrame:
    # группировка по dims перед сдвигом
    group_cols = ["dimension"]  # или другие категориальные колонки
    df = df.sort(["year", "month"] + group_cols)
    df = df.with_columns([
        pl.col("metric_value").shift(12).over(group_cols).alias("yoy_value"),
        pl.col("metric_value").shift(12).over(group_cols).alias("prev_year_value")
    ])
    df = df.with_columns([
        ((pl.col("metric_value") - pl.col("prev_year_value")) / pl.col("prev_year_value") * 100).alias("yoy_percent")
    ])
    return df

LOGIC:

группировать по dims/категориям перед расчетом сдвига
сдвиг на 12 месяцев (для месячных данных)
рассчитать процентное изменение

CONSTRAINTS:

учитывать группировки по dimensions
корректная обработка граничных случаев (первая запись)

DONE:

YoY рассчитывается корректно с учетом группировок
добавлены тесты для YoY
