"""Трансформации и агрегации данных для пайплайна обработки.

Этот модуль предоставляет функции для применения различных
трансформаций к данным, включая фильтрацию, группировку,
сортировку, расчет YoY и долей.
"""

import logging
from typing import Any

import polars as pl

logger = logging.getLogger(__name__)


def apply_transformations(
    df: pl.DataFrame,
    filters: list[dict[str, Any]] | None = None,
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
            Каждое условие - словарь с ключами:
            - column: имя колонки
            - operator: оператор (==, !=, >, <, >=, <=)
            - value: значение для сравнения
        groupby: Список колонок для группировки.
        sort_by: Список колонок для сортировки.
        descending: Сортировать по убыванию.
        limit: Максимальное количество строк.

    Returns:
        pl.DataFrame: Трансформированный DataFrame.

    Examples:
        >>> df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        >>> result = apply_transformations(
        ...     df,
        ...     filters=[{"column": "a", "operator": ">", "value": 1}],
        ...     sort_by=["b"],
        ... )
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
    filters: list[dict[str, Any]],
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
        column = condition["column"]
        operator = condition["operator"]
        value = condition["value"]

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
    aggregations: list[dict[str, Any]] | None = None,
    yoy_config: dict[str, Any] | None = None,
    share_config: dict[str, Any] | None = None,
    custom_metrics: list[dict[str, Any]] | None = None,
) -> pl.DataFrame:
    """Выполняет агрегации данных с поддержкой YoY и долей.

    Args:
        df: Исходный DataFrame.
        groupby: Список колонок для группировки.
        aggregations: Список агрегаций.
            Каждая агрегация - словарь с ключами:
            - column: имя колонки
            - function: функция агрегации (sum, mean, count, min, max)
            - alias: опциональное имя результирующей колонки
        yoy_config: Конфигурация для YoY расчета.
            - year_column: колонка с годом
            - value_column: колонка со значением
            - alias: имя результирующей колонки (по умолчанию: 'yoy')
        share_config: Конфигурация для расчета долей.
            - value_column: колонка со значением
            - alias: имя результирующей колонки (по умолчанию: 'share')
        custom_metrics: Список кастомных метрик.
            Каждая метрика - словарь с ключами:
            - name: имя метрики
            - formula: формула расчета (например, "revenue / cost * 100")

    Returns:
        pl.DataFrame: DataFrame с агрегированными данными.

    Examples:
        >>> df = pl.DataFrame({
        ...     "year": [2022, 2022, 2023, 2023],
        ...     "category": ["A", "B", "A", "B"],
        ...     "revenue": [100, 200, 150, 250],
        ... })
        >>> result = calculate_aggregations(
        ...     df,
        ...     groupby=["year", "category"],
        ...     aggregations=[{"column": "revenue", "function": "sum"}],
        ...     yoy_config={"year_column": "year", "value_column": "revenue_sum"},
        ... )
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
        result = _calculate_yoy(result, **yoy_config)

    # Расчет долей
    if share_config:
        logger.debug("Расчет долей: %s", share_config)
        result = _calculate_share(result, **share_config)

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
    aggregations: list[dict[str, Any]],
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
        column = agg["column"]
        function = agg["function"]
        alias = agg.get("alias", f"{column}_{function}")

        if function == "sum":
            expr = pl.col(column).sum().alias(alias)
        elif function == "mean":
            expr = pl.col(column).mean().alias(alias)
        elif function == "count":
            expr = pl.col(column).count().alias(alias)
        elif function == "min":
            expr = pl.col(column).min().alias(alias)
        elif function == "max":
            expr = pl.col(column).max().alias(alias)
        elif function == "median":
            expr = pl.col(column).median().alias(alias)
        elif function == "std":
            expr = pl.col(column).std().alias(alias)
        elif function == "var":
            expr = pl.col(column).var().alias(alias)
        elif function == "first":
            expr = pl.col(column).first().alias(alias)
        elif function == "last":
            expr = pl.col(column).last().alias(alias)
        else:
            logger.warning("Неизвестная функция агрегации: %s", function)
            continue

        agg_exprs.append(expr)

    result = df.group_by(groupby).agg(agg_exprs)
    logger.debug(
        "Группировка выполнена: %d групп, %d агрегаций",
        result.shape[0],
        len(agg_exprs),
    )
    return result


def _calculate_yoy(df: pl.DataFrame, year_column: str, value_column: str, alias: str = "yoy") -> pl.DataFrame:
    """Вычисляет годовой рост (Year-over-Year).

    Args:
        df: Исходный DataFrame.
        year_column: Имя колонки с годом.
        value_column: Имя колонки со значением для сравнения.
        alias: Имя результирующей колонки.

    Returns:
        pl.DataFrame: DataFrame с колонкой YoY.
    """
    # Сортируем по году для корректного расчета
    result = df.sort(year_column)

    # Вычисляем предыдущее значение
    prev_value = result[value_column].shift(1)

    # Вычисляем YoY как процентное изменение
    result = result.with_columns(
        (
            (pl.col(value_column) - prev_value) / prev_value * 100
        ).alias(alias)
    )

    # Заменяем бесконечности и NaN на None
    result = result.with_columns(
        pl.col(alias).replace([float("inf"), float("-inf")], None)
    )

    logger.debug("YoY расчет завершен для колонки '%s'", value_column)
    return result


def _calculate_share(df: pl.DataFrame, value_column: str, alias: str = "share") -> pl.DataFrame:
    """Вычисляет долю каждого значения от общего.

    Args:
        df: Исходный DataFrame.
        value_column: Имя колонки со значением.
        alias: Имя результирующей колонки.

    Returns:
        pl.DataFrame: DataFrame с колонкой долей.
    """
    total = df[value_column].sum()

    if total == 0:
        logger.warning("Сумма значений равна 0, доли будут равны 0")
        result = df.with_columns(pl.lit(0.0).alias(alias))
    else:
        result = df.with_columns(
            (pl.col(value_column) / total * 100).alias(alias)
        )

    logger.debug("Расчет долей завершен для колонки '%s'", value_column)
    return result


def _apply_custom_metrics(
    df: pl.DataFrame,
    custom_metrics: list[dict[str, Any]],
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
        name = metric["name"]
        formula = metric["formula"]

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