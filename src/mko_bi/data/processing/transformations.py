"""Трансформации и агрегации данных для пайплайна обработки.

Этот модуль предоставляет функции для применения различных
трансформаций к данным, включая фильтрацию, группировку,
сортировку, расчет YoY и долей.
"""

import logging

import polars as pl

from mko_bi.models.transformation_configs import (
    AggregationConfig,
    CustomMetricConfig,
    FilterConfig,
    ShareConfig,
    YoyConfig,
)
from mko_bi.models.user_roles import AggregationFunctionEnum

logger = logging.getLogger(__name__)

# Маппинг функций агрегации на Polars выражения
AGG_FUNC_MAP = {
    AggregationFunctionEnum.SUM: lambda col: pl.col(col).sum(),
    AggregationFunctionEnum.MEAN: lambda col: pl.col(col).mean(),
    AggregationFunctionEnum.COUNT: lambda col: pl.col(col).count(),
    AggregationFunctionEnum.MIN: lambda col: pl.col(col).min(),
    AggregationFunctionEnum.MAX: lambda col: pl.col(col).max(),
    AggregationFunctionEnum.MEDIAN: lambda col: pl.col(col).median(),
    AggregationFunctionEnum.STD: lambda col: pl.col(col).std(),
    AggregationFunctionEnum.VAR: lambda col: pl.col(col).var(),
    AggregationFunctionEnum.FIRST: lambda col: pl.col(col).first(),
    AggregationFunctionEnum.LAST: lambda col: pl.col(col).last(),
}


def apply_transformations(
    df: pl.DataFrame,
    filters: list[FilterConfig] | None = None,
    groupby: list[str] | None = None,
    sort_by: list[str] | None = None,
    descending: bool = False,
    limit: int | None = None,
) -> pl.DataFrame:
    """Применяет серию трансформаций к DataFrame.

    Выполняет фильтрацию, группировку, сортировку и ограничение
    строк в указанном порядке.

    Args:
        df: Исходный DataFrame.
        filters: Список условий фильтрации.
        groupby: Список колонок для группировки.
        sort_by: Список колонок для сортировки.
        descending: Сортировать по убыванию.
        limit: Максимальное количество строк.

    Returns:
        pl.DataFrame: Трансформированный DataFrame.
    """
    logger.info("Начало применения трансформаций")
    result = df

    # Применяем фильтры
    if filters:
        logger.debug("Применение фильтров: %s", filters)
        result = _apply_filters(result, filters)

    # Применяем группировку
    if groupby:
        logger.debug("Применение группировки по: %s", groupby)
        # Если после группировки нужно агрегировать, это делается отдельно
        # Здесь просто группируем для дальнейшей обработки
        result = result.group_by(groupby).agg(pl.all())

    # Применяем сортировку
    if sort_by:
        logger.debug("Применение сортировки по: %s, descending=%s", sort_by, descending)
        result = result.sort(sort_by, descending=descending)

    # Применяем ограничение
    if limit is not None:
        logger.debug("Применение ограничения: %d строк", limit)
        result = result.limit(limit)

    logger.info(
        "Трансформации применены: %d строк, %d колонок",
        result.shape[0],
        result.shape[1],
    )
    return result


def _apply_filters(
    df: pl.DataFrame,
    filters: list[FilterConfig],
) -> pl.DataFrame:
    """Применяет фильтры к DataFrame.

    Args:
        df: Исходный DataFrame.
        filters: Список условий фильтрации.

    Returns:
        pl.DataFrame: Отфильтрованный DataFrame.
    """
    result = df
    for condition in filters:
        column = condition.column
        operator = condition.operator
        value = condition.value

        if operator == "==":
            result = result.filter(pl.col(column) == value)
        elif operator == "!=":
            result = result.filter(pl.col(column) != value)
        elif operator == ">":
            result = result.filter(pl.col(column) > value)
        elif operator == "<":
            result = result.filter(pl.col(column) < value)
        elif operator == ">=":
            result = result.filter(pl.col(column) >= value)
        elif operator == "<=":
            result = result.filter(pl.col(column) <= value)
        else:
            logger.warning("Неизвестный оператор фильтрации: %s", operator)
            continue

        logger.debug("Применен фильтр: %s %s %s", column, operator, value)

    return result


def calculate_aggregations(
    df: pl.DataFrame,
    groupby: list[str] | None = None,
    aggregations: list[AggregationConfig] | None = None,
    yoy_config: YoyConfig | None = None,
    share_config: ShareConfig | None = None,
    custom_metrics: list[CustomMetricConfig] | None = None,
) -> pl.DataFrame:
    """Выполняет агрегации данных с поддержкой YoY и долей.

    Args:
        df: Исходный DataFrame.
        groupby: Список колонок для группировки.
        aggregations: Список агрегаций.
        yoy_config: Конфигурация для YoY расчета.
        share_config: Конфигурация для расчета долей.
        custom_metrics: Список кастомных метрик.

    Returns:
        pl.DataFrame: DataFrame с агрегированными данными.
    """
    logger.info("Начало расчета агрегаций")
    result = df

    # Группировка и базовые агрегации
    if groupby and aggregations:
        logger.debug("Группировка по: %s", groupby)
        logger.debug("Агрегации: %s", aggregations)
        result = _apply_groupby_aggregations(result, groupby, aggregations)
    elif groupby and not aggregations:
        # Если только группировка без агрегаций, просто группируем
        result = result.group_by(groupby).agg(pl.all())

    # YoY расчет
    if yoy_config:
        logger.debug("YoY расчет: %s", yoy_config)
        result = _calculate_yoy(result, **yoy_config.model_dump())

    # Расчет долей
    if share_config:
        logger.debug("Расчет долей: %s", share_config)
        result = _calculate_share(result, **share_config.model_dump())

    # Кастомные метрики
    if custom_metrics:
        logger.debug("Кастомные метрики: %s", custom_metrics)
        result = _apply_custom_metrics(result, custom_metrics)

    logger.info(
        "Агрегации рассчитаны: %d строк, %d колонок",
        result.shape[0],
        result.shape[1],
    )
    return result


def _apply_groupby_aggregations(
    df: pl.DataFrame,
    groupby: list[str],
    aggregations: list[AggregationConfig],
) -> pl.DataFrame:
    """Применяет группировку и агрегации.

    Args:
        df: Исходный DataFrame.
        groupby: Список колонок для группировки.
        aggregations: Список агрегаций.

    Returns:
        pl.DataFrame: Агрегированный DataFrame.
    """
    agg_exprs = []
    for agg in aggregations:
        column = agg.column
        func_enum = agg.function
        alias = agg.alias if agg.alias else f"{column}_{func_enum.value}"

        if func_enum not in AGG_FUNC_MAP:
            logger.warning("Неизвестная функция агрегации: %s", func_enum)
            continue

        expr = AGG_FUNC_MAP[func_enum](column).alias(alias)
        agg_exprs.append(expr)

    result = df.group_by(groupby).agg(agg_exprs)
    logger.debug(
        "Группировка выполнена: %d групп, %d агрегаций",
        result.shape[0],
        len(agg_exprs),
    )
    return result


def _calculate_yoy(
    df: pl.DataFrame,
    year_column: str,
    value_column: str,
    group_cols: list[str] | None = None,
    month_column: str | None = None,
    alias: str = "yoy",
    percent_alias: str | None = None,
) -> pl.DataFrame:
    """Вычисляет годовой рост (Year-over-Year) с учетом группировки по измерениям.

    Args:
        df: Исходный DataFrame.
        year_column: Имя колонки с годом.
        value_column: Имя колонки со значением для сравнения.
        group_cols: Список колонок для группировки (измерения/dims).
        month_column: Имя колонки с месяцем (опционально).
        alias: Имя результирующей колонки (процентное изменение).
        percent_alias: Не используется (оставлено для обратной совместимости).

    Returns:
        pl.DataFrame: DataFrame с колонкой YoY.
    """
    # Определяем колонки для сортировки
    sort_cols = [year_column]
    if month_column:
        sort_cols.append(month_column)
    if group_cols:
        sort_cols.extend(group_cols)

    # Сортируем данные
    result = df.sort(sort_cols)

    if month_column:
        # Для месячных данных: группируем по месяцу + group_cols
        # и делаем shift(1) внутри каждой группы
        logger.debug("YoY расчет с месяцем: %s", month_column)

        shift_group_cols = [month_column]
        if group_cols:
            shift_group_cols.extend(group_cols)

        # Получаем предыдущее значение внутри группы
        result = result.with_columns([
            pl.col(value_column).shift(1).over(shift_group_cols).alias("__prev_value"),
            pl.col(year_column).shift(1).over(shift_group_cols).alias("__prev_year"),
        ])

        # Вычисляем YoY только если год отличается на 1
        year_diff = pl.col(year_column) - pl.col("__prev_year")
        prev_value_expr = pl.when(year_diff == 1).then(pl.col("__prev_value")).otherwise(None)
    else:
        # Стандартный расчет без месяцев
        shift_lag = 1

        if group_cols:
            logger.debug("YoY расчет с группировкой по: %s", group_cols)
            prev_value_expr = pl.col(value_column).shift(shift_lag).over(group_cols)
        else:
            logger.debug("YoY расчет без группировки")
            prev_value_expr = pl.col(value_column).shift(shift_lag)

    # Вычисляем процентное изменение
    result = result.with_columns([
        pl.when(prev_value_expr.is_null() | (prev_value_expr == 0))
        .then(None)
        .otherwise(
            (pl.col(value_column) - prev_value_expr) / prev_value_expr * 100
        )
        .alias(alias)
    ])

    # Заменяем NaN на None и убираем временные колонки
    result = result.with_columns([
        pl.col(alias).fill_nan(None),
    ])

    # Удаляем временные колонки
    temp_cols = ["__prev_value", "__prev_year"]
    for col in temp_cols:
        if col in result.columns:
            result = result.drop(col)

    logger.debug("YoY расчет завершен для колонки '%s'", value_column)
    return result


def _calculate_share(
    df: pl.DataFrame,
    value_column: str,
    alias: str = "share",
    group_cols: list[str] | None = None,
) -> pl.DataFrame:
    """Вычисляет долю каждого значения от общей суммы по группе.

    Args:
        df: Исходный DataFrame.
        value_column: Имя колонки со значением.
        alias: Имя результирующей колонки.
        group_cols: Список колонок для группировки. Если None, считает долю от общей суммы.

    Returns:
        pl.DataFrame: DataFrame с колонкой долей.
    """
    if group_cols:
        logger.debug("Расчет долей с группировкой по: %s", group_cols)
        # Группируем и считаем сумму по группам
        total_df = df.group_by(group_cols).agg(
            pl.col(value_column).sum().alias("total")
        )
        # Джойним обратно к исходному df
        result = df.join(total_df, on=group_cols)
        # Считаем долю, обрабатываем деление на ноль
        result = result.with_columns(
            pl.when(pl.col("total") == 0)
            .then(0.0)
            .otherwise(pl.col(value_column) / pl.col("total") * 100)
            .alias(alias)
        )
        result = result.drop("total")
    else:
        logger.debug("Расчет долей без группировки")
        total = df[value_column].sum()
        if total == 0:
            logger.warning("Сумма значений колонки '%s' равна 0, доли установлены в 0", value_column)
            result = df.with_columns(pl.lit(0.0).alias(alias))
        else:
            result = df.with_columns(
                (pl.col(value_column) / total * 100).alias(alias)
            )

    logger.debug("Расчет долей завершен для колонки '%s'", value_column)
    return result


def _apply_custom_metrics(
    df: pl.DataFrame,
    custom_metrics: list[CustomMetricConfig],
) -> pl.DataFrame:
    """Применяет кастомные метрики на основе формул.

    Args:
        df: Исходный DataFrame.
        custom_metrics: Список кастомных метрик.

    Returns:
        pl.DataFrame: DataFrame с добавленными метриками.
    """
    result = df

    for metric in custom_metrics:
        name = metric.name
        formula = metric.formula

        try:
            # Простая реализация: заменяем имена колонок на pl.col()
            # Это базовая реализация, в production нужно использовать
            # более безопасный парсер выражений
            expr = _parse_formula(formula)
            result = result.with_columns(expr.alias(name))
            logger.debug("Кастомная метрика '%s' применена", name)
        except Exception as e:
            logger.error(
                "Ошибка при применении кастомной метрики '%s': %s",
                name,
                e,
            )
            raise

    return result


def _parse_formula(formula: str) -> pl.Expr:
    """Парсит простую формулу в Polars выражение.

    Поддерживаются базовые операции: +, -, *, /.
    Имена колонок должны быть корректными идентификаторами.

    Args:
        formula: Строка формулы (например, "revenue / cost * 100").

    Returns:
        pl.Expr: Polars выражение.

    Note:
        Это упрощенная реализация. Для production используйте
        более надежный парсер или eval с ограниченным контекстом.
    """
    # Разбиваем формулу на токены
    tokens = formula.split()

    if len(tokens) == 1:
        # Одна колонка
        return pl.col(tokens[0])

    # Строим выражение шаг за шагом
    expr = pl.col(tokens[0])
    i = 1
    while i < len(tokens):
        op = tokens[i]
        next_token = tokens[i + 1]

        if op == "+":
            expr = expr + pl.col(next_token)
        elif op == "-":
            expr = expr - pl.col(next_token)
        elif op == "*":
            expr = expr * pl.col(next_token)
        elif op == "/":
            expr = expr / pl.col(next_token)
        else:
            raise ValueError(f"Неизвестный оператор в формуле: {op}")

        i += 2

    return expr