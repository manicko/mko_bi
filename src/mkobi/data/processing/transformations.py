"""Трансформации и агрегации данных для пайплайна обработки.

Этот модуль предоставляет функции для применения различных
трансформаций к данным, включая фильтрацию, группировку,
сортировку, расчет YoY и долей.
"""

import logging
import re
from typing import Any

import polars as pl

from mkobi.models.user_roles import AggregationFunctionEnum

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
    config: dict[str, Any] | None = None,
    filters: list[dict[str, Any]] | None = None,
    groupby: list[str] | None = None,
    sort_by: str | None = None,
    descending: bool = False,
    limit: int | None = None,
) -> pl.DataFrame:
    """Применяет трансформации к DataFrame согласно конфигу.
    
    Выполняет фильтрацию, группировку, сортировку,
    добавление вычисляемых полей, переименование колонок
    и приведение типов.

    Args:
        df: Исходный DataFrame.
        config: Словарь конфигурации (filters, computed_fields, rename, dtype).
        filters: Список условий фильтрации.
        groupby: Список колонок для группировки (базовой, без агрегаций).
        sort_by: Имя колонки для сортировки.
        descending: Сортировка по убыванию.
        limit: Ограничение количества строк.

    Returns:
        pl.DataFrame: Трансформированный DataFrame.
    """
    config = config or {}
    result = df

    # 1. Фильтрация строк (where conditions)
    filter_list = filters if filters is not None else config.get("filters")
    if filter_list:
        logger.debug("Применение фильтров: %s", filter_list)
        result = _apply_filters(result, filter_list)

    # 2. Группировка (базовая, без агрегаций)
    if groupby:
        logger.debug("Группировка по: %s", groupby)
        result = result.group_by(groupby).agg(pl.all().first())

    # 3. Сортировка
    if sort_by:
        logger.debug("Сортировка по: %s (desc=%s)", sort_by, descending)
        result = result.sort(sort_by, descending=descending)

    # 4. Лимит строк
    if limit:
        logger.debug("Ограничение строк: %s", limit)
        result = result.head(limit)

    # 5. Вычисляемые поля (computed columns)
    computed_fields = config.get("computed_fields")
    if computed_fields:
        logger.debug("Добавление вычисляемых полей: %s", computed_fields)
        result = _add_computed_fields(result, computed_fields)

    # 6. Переименование колонок
    rename_map = config.get("rename")
    if rename_map:
        logger.debug("Переименование колонок: %s", rename_map)
        result = result.rename(rename_map)

    # 7. Типизация колонок
    dtype_map = config.get("dtype")
    if dtype_map:
        logger.debug("Приведение типов: %s", dtype_map)
        result = _apply_dtypes(result, dtype_map)

    logger.info("Трансформации применены: %d строк", result.shape[0])
    return result


def _apply_filters(
    df: pl.DataFrame,
    filters: list[Any],
) -> pl.DataFrame:
    """Применяет фильтры к DataFrame.

    Args:
        df: Исходный DataFrame.
        filters: Список условий фильтрации (FilterConfig объекты или dict с keys: column, operator, value).

    Returns:
        pl.DataFrame: Отфильтрованный DataFrame.
    """
    result = df
    for condition in filters:
        # Handle both Pydantic models and dictionaries
        if isinstance(condition, dict):
            column = condition.get("column")
            operator = condition.get("operator")
            value = condition.get("value")
        else:
            column = getattr(condition, 'column', None)
            operator = getattr(condition, 'operator', None)
            value = getattr(condition, 'value', None)

        if not column or not operator:
            continue

        # Handle operator from FilterOperatorEnum or string
        op_value = operator.value if hasattr(operator, 'value') else operator

        if op_value == "eq" or op_value == "==":
            result = result.filter(pl.col(column) == value)
        elif op_value == "ne" or op_value == "!=":
            result = result.filter(pl.col(column) != value)
        elif op_value == "gt" or op_value == ">":
            result = result.filter(pl.col(column) > value)
        elif op_value == "lt" or op_value == "<":
            result = result.filter(pl.col(column) < value)
        elif op_value == "gte" or op_value == ">=":
            result = result.filter(pl.col(column) >= value)
        elif op_value == "lte" or op_value == "<=":
            result = result.filter(pl.col(column) <= value)
        elif op_value == "in" and isinstance(value, list):
            result = result.filter(pl.col(column).is_in(value))
        else:
            logger.warning("Неизвестный оператор фильтрации: %s", op_value)
            continue

        logger.debug("Применен фильтр: %s %s %s", column, op_value, value)

    return result


def _add_computed_fields(
    df: pl.DataFrame,
    fields: list[dict[str, Any]],
) -> pl.DataFrame:
    """Добавляет вычисляемые поля.

    Args:
        df: Исходный DataFrame.
        fields: Список словарей с ключами 'name' и 'expr'.

    Returns:
        pl.DataFrame: DataFrame с добавленными полями.
    """
    result = df
    for field in fields:
        name = field.get("name")
        expr_str = field.get("expr")
        if not name or not expr_str:
            continue
        try:
            expr = _parse_formula(expr_str)
            result = result.with_columns(expr.alias(name))
            logger.debug("Вычисляемое поле '%s' добавлено", name)
        except Exception as e:
            logger.error("Ошибка в вычисляемом поле '%s': %s", name, e)
            raise
    return result


def _apply_dtypes(
    df: pl.DataFrame,
    dtype_map: dict[str, str],
) -> pl.DataFrame:
    """Применяет типизацию колонок.

    Args:
        df: Исходный DataFrame.
        dtype_map: Словарь {col_name: polars_type_string}.

    Returns:
        pl.DataFrame: DataFrame с приведенными типами.
    """
    import polars as pl

    cast_exprs = []
    for col, dtype_str in dtype_map.items():
        try:
            dtype = getattr(pl, dtype_str.upper(), None)
            if dtype:
                cast_exprs.append(pl.col(col).cast(dtype))
            else:
                logger.warning("Неизвестный тип данных: %s", dtype_str)
        except Exception as e:
            logger.error("Ошибка приведения типа %s: %s", col, e)

    if cast_exprs:
        return df.with_columns(cast_exprs)
    return df


def calculate_aggregations(
    df: pl.DataFrame,
    groupby: list[str] | None = None,
    aggregations: list[dict[str, Any]] | None = None,
    yoy_config: dict[str, Any] | None = None,
    share_config: dict[str, Any] | None = None,
    custom_metrics: list[dict[str, Any]] | None = None,
) -> pl.DataFrame:
    """Выполняет агрегации данных с поддержкой YoY и долей.

    Args:
        df: Исходный DataFrame.
        groupby: Список колонок для группировки.
        aggregations: Список агрегаций (AggregationConfig объекты).
        yoy_config: Конфигурация для YoY расчета.
        share_config: Конфигурация для расчета долей.
        custom_metrics: Список кастомных метрик.

    Returns:
        pl.DataFrame: Агрегированный DataFrame.
    """
    logger.info("Начало расчета агрегаций")
    result = df

    # Группировка и базовые агрегации
    if groupby and aggregations:
        logger.debug("Группировка по: %s", groupby)
        result = _apply_groupby_aggregations(result, groupby, aggregations)

    # YoY расчет
    if yoy_config:
        logger.debug("YoY расчет: %s", yoy_config)
        result = _calculate_yoy(result, **yoy_config)

    # Расчет долей
    if share_config:
        logger.debug("Расчет долей: %s", share_config)
        result = _calculate_share(result, **share_config)

    # Кастомные метрики
    if custom_metrics:
        logger.debug("Кастомные метрики: %s", custom_metrics)
        result = _add_computed_fields(result, custom_metrics)

    logger.info("Агрегации рассчитаны: %d строк", result.shape[0])
    return result


def aggregate_data(
    df: pl.DataFrame,
    graph_configs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Агрегирует данные согласно конфигурации графиков.

    Args:
        df: Исходный DataFrame.
        graph_configs: Список конфигураций графиков.

    Returns:
        list[dict]: Список словарей для JSONB сохранения.
    """
    results = []
    for config in graph_configs:
        groupby = config.get("dimensions", [])
        aggs = config.get("metrics", [])

        if not groupby or not aggs:
            continue

        aggregated = calculate_aggregations(
            df=df,
            groupby=groupby,
            aggregations=aggs,
        )
        results.extend(aggregated.to_dicts())
    return results


def _apply_groupby_aggregations(
    df: pl.DataFrame,
    groupby: list[str],
    aggregations: list[Any],
) -> pl.DataFrame:
    """Применяет группировку и агрегации.

    Args:
        df: Исходный DataFrame.
        groupby: Список колонок для группировки.
        aggregations: Список агрегаций (AggregationConfig объекты или dict).

    Returns:
        pl.DataFrame: Агрегированный DataFrame.
    """
    agg_exprs = []
    for agg in aggregations:
        # Handle both Pydantic models and dictionaries
        if isinstance(agg, dict):
            column = agg.get("column")
            func_str = agg.get("function")
            alias = agg.get("alias", f"{column}_{func_str}")
        else:
            column = getattr(agg, 'column', None)
            func_str = getattr(agg, 'function', None)
            alias = getattr(agg, 'alias', None) or f"{column}_{func_str}"

        try:
            func_enum = AggregationFunctionEnum(func_str) if isinstance(func_str, str) else func_str
        except ValueError:
            logger.warning("Неизвестная функция агрегации: %s", func_str)
            continue

        if func_enum not in AGG_FUNC_MAP:
            logger.warning("Функция не поддерживается: %s", func_enum)
            continue

        expr = AGG_FUNC_MAP[func_enum](column).alias(alias)
        agg_exprs.append(expr)

    return df.group_by(groupby).agg(agg_exprs)


def _calculate_yoy(
    df: pl.DataFrame,
    year_column: str,
    value_column: str,
    group_cols: list[str] | None = None,
    month_column: str | None = None,
    alias: str = "yoy",
    percent_alias: str | None = None,
) -> pl.DataFrame:
    """Вычисляет годовой рост (Year-over-Year).

    Args:
        df: Исходный DataFrame.
        year_column: Имя колонки с годом.
        value_column: Имя колонки со значением.
        group_cols: Список колонок для группировки (измерения).
        month_column: Имя колонки с месяцем.
        alias: Имя результирующей колонки.

    Returns:
        pl.DataFrame: DataFrame с колонкой YoY.
    """
    sort_cols = [year_column]
    if month_column:
        sort_cols.append(month_column)
    if group_cols:
        sort_cols.extend(group_cols)

    result = df.sort(sort_cols)

    if month_column:
        shift_group_cols = [month_column]
        if group_cols:
            shift_group_cols.extend(group_cols)

        result = result.with_columns([
            pl.col(value_column).shift(1).over(shift_group_cols).alias("__prev_value"),
            pl.col(year_column).shift(1).over(shift_group_cols).alias("__prev_year"),
        ])

        year_diff = pl.col(year_column) - pl.col("__prev_year")
        prev_value_expr = pl.when(year_diff == 1).then(pl.col("__prev_value")).otherwise(None)
    else:
        shift_lag = 1
        if group_cols:
            prev_value_expr = pl.col(value_column).shift(shift_lag).over(group_cols)
        else:
            prev_value_expr = pl.col(value_column).shift(shift_lag)

    result = result.with_columns([
        pl.when(prev_value_expr.is_null() | (prev_value_expr == 0))
        .then(None)
        .otherwise((pl.col(value_column) - prev_value_expr) / prev_value_expr * 100)
        .alias(alias)
    ])

    result = result.with_columns([pl.col(alias).fill_nan(None)])
    temp_cols = ["__prev_value", "__prev_year"]
    for col in temp_cols:
        if col in result.columns:
            result = result.drop(col)

    return result


def _calculate_share(
    df: pl.DataFrame,
    value_column: str,
    alias: str = "share",
    group_cols: list[str] | None = None,
) -> pl.DataFrame:
    """Вычисляет долю каждого значения от общей суммы.

    Args:
        df: Исходный DataFrame.
        value_column: Имя колонки со значением.
        alias: Имя результирующей колонки.
        group_cols: Список колонок для группировки.

    Returns:
        pl.DataFrame: DataFrame с колонкой долей.
    """
    if group_cols:
        total_df = df.group_by(group_cols).agg(pl.col(value_column).sum().alias("total"))
        result = df.join(total_df, on=group_cols)
        result = result.with_columns(
            pl.when(pl.col("total") == 0)
            .then(0.0)
            .otherwise(pl.col(value_column) / pl.col("total") * 100)
            .alias(alias)
        )
        result = result.drop("total")
    else:
        total = df[value_column].sum()
        if total == 0:
            result = df.with_columns(pl.lit(0.0).alias(alias))
        else:
            result = df.with_columns((pl.col(value_column) / total * 100).alias(alias))

    return result


def _parse_formula(formula: str) -> pl.Expr:
    """Парсит простую формулу в Polars выражение.

    Args:
        formula: Строка формулы (например, "revenue / cost * 100").

    Returns:
        pl.Expr: Polars выражение.
    """
    tokens = re.split(r'([+\-*/])', formula)
    tokens = [t.strip() for t in tokens if t.strip()]

    if len(tokens) == 1:
        return pl.col(tokens[0])

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
