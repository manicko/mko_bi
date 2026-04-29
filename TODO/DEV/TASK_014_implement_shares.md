TASK: реализация расчета долей (shares)

FILE: src/mko_bi/data/processing/transformations.py

GOAL: полная реализация согласно SPEC

IMPLEMENT:

def _calculate_share(df: pl.DataFrame, group_cols: list[str] = None) -> pl.DataFrame:
    if group_cols is None:
        group_cols = ["year", "month"]
    
    # расчет доли от общей суммы по группе
    total = df.group_by(group_cols).agg(pl.col("metric_value").sum().alias("total"))
    df = df.join(total, on=group_cols)
    df = df.with_columns([
        (pl.col("metric_value") / pl.col("total") * 100).alias("share_percent")
    ])
    return df.drop("total")

LOGIC:

группировать по указанным колонкам
посчитать общую сумму по группе
рассчитать долю каждой записи в процентах

CONSTRAINTS:

поддержка группировок
корректная обработка деления на ноль

DONE:

доли рассчитываются корректно
добавлены тесты для shares
