"""Тесты для пайплайна обработки данных.

Тестирует классы TransformationRegistry и функции
apply_transformations, calculate_aggregations.
"""

import pytest
import polars as pl

from mko_bi.data.processing.registry import TransformationRegistry
from mko_bi.data.processing.transformations import (
    apply_transformations,
    calculate_aggregations,
    _apply_filters,
    _apply_groupby_aggregations,
    _calculate_yoy,
    _calculate_share,
    _apply_custom_metrics,
)
from mko_bi.models.transformation_configs import (
    AggregationConfig,
    CustomMetricConfig,
    FilterConfig,
    ShareConfig,
    YoyConfig,
)
from mko_bi.models.user_roles import AggregationFunctionEnum


class TestTransformationRegistry:
    """Тесты для реестра трансформаций."""

    def test_register_and_get_transformation(self):
        """Тест регистрации и получения трансформации."""
        registry = TransformationRegistry()
        func = lambda df: df
        registry.register("test", func)
        assert "test" in registry.list_transformations()
        assert registry.get("test") == func
        assert registry.has_transformation("test") is True

    def test_register_duplicate_transformation_raises_error(self):
        """Тест регистрации дублирующейся трансформации вызывает ошибку."""
        registry = TransformationRegistry()
        func = lambda df: df
        registry.register("test", func)
        with pytest.raises(ValueError, match="уже зарегистрирована"):
            registry.register("test", func)

    def test_get_nonexistent_transformation(self):
        """Тест получения несуществующей трансформации."""
        registry = TransformationRegistry()
        assert registry.get("nonexistent") is None
        assert registry.has_transformation("nonexistent") is False

    def test_apply_transformation(self):
        """Тест применения трансформации."""
        registry = TransformationRegistry()

        def add_column(df: pl.DataFrame) -> pl.DataFrame:
            return df.with_columns(pl.lit(1).alias("new_col"))

        registry.register("add_col", add_column)
        df = pl.DataFrame({"a": [1, 2, 3]})
        result = registry.apply(df, "add_col")
        assert "new_col" in result.columns
        assert result["new_col"].to_list() == [1, 1, 1]

    def test_apply_nonexistent_transformation_raises_error(self):
        """Тест применения несуществующей трансформации вызывает ошибку."""
        registry = TransformationRegistry()
        df = pl.DataFrame({"a": [1, 2, 3]})
        with pytest.raises(ValueError, match="не найдена"):
            registry.apply(df, "nonexistent")


class TestApplyTransformations:
    """Тесты для функции apply_transformations."""

    @pytest.fixture
    def sample_df(self):
        """Создает тестовый DataFrame."""
        return pl.DataFrame({
            "year": [2022, 2022, 2023, 2023, 2023],
            "category": ["A", "B", "A", "B", "C"],
            "revenue": [100, 200, 150, 250, 300],
            "cost": [50, 80, 60, 100, 120],
        })

    def test_apply_filters(self, sample_df):
        """Тест применения фильтров."""
        filters = [FilterConfig(column="year", operator="==", value=2023)]
        result = apply_transformations(sample_df, filters=filters)
        assert result.shape[0] == 3
        assert result["year"].unique().to_list() == [2023]

    def test_apply_multiple_filters(self, sample_df):
        """Тест применения нескольких фильтров."""
        filters = [
            FilterConfig(column="year", operator="==", value=2023),
            FilterConfig(column="revenue", operator=">", value=200),
        ]
        result = apply_transformations(sample_df, filters=filters)
        assert result.shape[0] == 2

    def test_apply_groupby(self, sample_df):
        """Тест применения группировки."""
        result = apply_transformations(sample_df, groupby=["year", "category"])
        # Группировка без агрегации просто группирует
        assert result.shape[0] == 5  # Все строки остаются

    def test_apply_sort(self, sample_df):
        """Тест применения сортировки."""
        result = apply_transformations(sample_df, sort_by=["revenue"], descending=True)
        revenues = result["revenue"].to_list()
        assert revenues == sorted(revenues, reverse=True)

    def test_apply_limit(self, sample_df):
        """Тест применения ограничения строк."""
        result = apply_transformations(sample_df, limit=2)
        assert result.shape[0] == 2

    def test_apply_all_transformations(self, sample_df):
        """Тест применения всех трансформаций."""
        filters = [FilterConfig(column="year", operator=">=", value=2022)]
        result = apply_transformations(
            sample_df,
            filters=filters,
            sort_by=["revenue"],
            descending=True,
            limit=3,
        )
        assert result.shape[0] == 3
        revenues = result["revenue"].to_list()
        assert revenues == sorted(revenues, reverse=True)

    def test_apply_no_transformations(self, sample_df):
        """Тест без применения трансформаций."""
        result = apply_transformations(sample_df)
        assert result.shape == sample_df.shape


class TestCalculateAggregations:
    """Тесты для функции calculate_aggregations."""

    @pytest.fixture
    def sample_df(self):
        """Создает тестовый DataFrame."""
        return pl.DataFrame({
            "year": [2022, 2022, 2023, 2023],
            "category": ["A", "B", "A", "B"],
            "revenue": [100, 200, 150, 250],
            "cost": [50, 80, 60, 100],
        })

    def test_groupby_aggregations(self, sample_df):
        """Тест группировки с агрегациями."""
        aggregations = [
            AggregationConfig(column="revenue", function=AggregationFunctionEnum.SUM, alias="total_revenue"),
            AggregationConfig(column="cost", function=AggregationFunctionEnum.SUM, alias="total_cost"),
        ]
        result = calculate_aggregations(
            sample_df,
            groupby=["year"],
            aggregations=aggregations,
        )
        assert "total_revenue" in result.columns
        assert "total_cost" in result.columns
        assert result.shape[0] == 2  # Два года

    def test_sum_aggregation(self, sample_df):
        """Тест суммы."""
        aggregations = [AggregationConfig(column="revenue", function=AggregationFunctionEnum.SUM)]
        result = calculate_aggregations(
            sample_df,
            groupby=["category"],
            aggregations=aggregations,
        )
        # Категория A: 100 + 150 = 250
        # Категория B: 200 + 250 = 450
        revenues = result["revenue_sum"].sort().to_list()
        assert revenues == [250, 450]

    def test_mean_aggregation(self, sample_df):
        """Тест среднего."""
        aggregations = [AggregationConfig(column="revenue", function=AggregationFunctionEnum.MEAN)]
        result = calculate_aggregations(
            sample_df,
            groupby=["category"],
            aggregations=aggregations,
        )
        assert "revenue_mean" in result.columns

    def test_count_aggregation(self, sample_df):
        """Тест подсчета."""
        aggregations = [AggregationConfig(column="revenue", function=AggregationFunctionEnum.COUNT)]
        result = calculate_aggregations(
            sample_df,
            groupby=["category"],
            aggregations=aggregations,
        )
        assert "revenue_count" in result.columns
        counts = result["revenue_count"].sort().to_list()
        assert counts == [2, 2]  # По 2 записи в каждой категории

    def test_min_max_aggregation(self, sample_df):
        """Тест минимума и максимума."""
        aggregations = [
            AggregationConfig(column="revenue", function=AggregationFunctionEnum.MIN),
            AggregationConfig(column="revenue", function=AggregationFunctionEnum.MAX),
        ]
        result = calculate_aggregations(
            sample_df,
            groupby=["category"],
            aggregations=aggregations,
        )
        assert "revenue_min" in result.columns
        assert "revenue_max" in result.columns

    def test_yoy_calculation(self, sample_df):
        """Тест YoY расчета."""
        # Группируем по году и суммируем доход
        aggregations = [AggregationConfig(column="revenue", function=AggregationFunctionEnum.SUM, alias="revenue_sum")]
        yoy_config = YoyConfig(year_column="year", value_column="revenue_sum", alias="yoy")
        result = calculate_aggregations(
            sample_df,
            groupby=["year"],
            aggregations=aggregations,
            yoy_config=yoy_config,
        )
        assert "yoy" in result.columns
        # Первый год должен быть None
        assert result["yoy"][0] is None

    def test_share_calculation(self, sample_df):
        """Тест расчета долей."""
        aggregations = [AggregationConfig(column="revenue", function=AggregationFunctionEnum.SUM, alias="revenue_sum")]
        share_config = ShareConfig(value_column="revenue_sum", alias="share")
        result = calculate_aggregations(
            sample_df,
            groupby=["category"],
            aggregations=aggregations,
            share_config=share_config,
        )
        assert "share" in result.columns
        # Сумма долей должна быть 100%
        total_share = result["share"].sum()
        assert abs(total_share - 100.0) < 0.01

    def test_share_calculation_grouped(self, sample_df):
        """Тест расчета долей с группировкой по году."""
        aggregations = [
            AggregationConfig(column="revenue", function=AggregationFunctionEnum.SUM, alias="revenue_sum")
        ]
        share_config = ShareConfig(
            value_column="revenue_sum",
            group_cols=["year"],
            alias="share",
        )
        result = calculate_aggregations(
            sample_df,
            groupby=["year", "category"],
            aggregations=aggregations,
            share_config=share_config,
        )
        assert "share" in result.columns
        # Сумма долей внутри каждого года должна быть 100%
        for year in result["year"].unique().to_list():
            year_share_sum = result.filter(pl.col("year") == year)["share"].sum()
            assert abs(year_share_sum - 100.0) < 0.01

    def test_custom_metrics(self, sample_df):
        """Тест кастомных метрик."""
        aggregations = [
            AggregationConfig(column="revenue", function=AggregationFunctionEnum.SUM, alias="revenue_sum"),
            AggregationConfig(column="cost", function=AggregationFunctionEnum.SUM, alias="cost_sum"),
        ]
        custom_metrics = [
            CustomMetricConfig(name="profit", formula="revenue_sum - cost_sum"),
        ]
        result = calculate_aggregations(
            sample_df,
            groupby=["category"],
            aggregations=aggregations,
            custom_metrics=custom_metrics,
        )
        assert "profit" in result.columns
        # Для категории A: (100 + 150) - (50 + 60) = 250 - 110 = 140
        # Для категории B: (200 + 250) - (80 + 100) = 450 - 180 = 270
        profits = result["profit"].sort().to_list()
        assert profits == [140, 270]

    def test_full_pipeline(self, sample_df):
        """Тест полного пайплайна."""
        # Фильтруем, группируем, агрегируем, считаем YoY и доли
        filters = [FilterConfig(column="revenue", operator=">", value=0)]
        aggregations = [
            AggregationConfig(column="revenue", function=AggregationFunctionEnum.SUM, alias="revenue_sum"),
            AggregationConfig(column="cost", function=AggregationFunctionEnum.SUM, alias="cost_sum"),
        ]
        result = apply_transformations(
            sample_df,
            filters=filters,
            sort_by=["year", "category"],
        )
        yoy_config = YoyConfig(year_column="year", value_column="revenue_sum")
        share_config = ShareConfig(value_column="revenue_sum")
        result = calculate_aggregations(
            result,
            groupby=["year"],
            aggregations=aggregations,
            yoy_config=yoy_config,
            share_config=share_config,
        )
        assert result.shape[0] == 2
        assert "revenue_sum" in result.columns
        assert "cost_sum" in result.columns
        assert "yoy" in result.columns
        assert "share" in result.columns


class TestInternalFunctions:
    """Тесты для внутренних функций."""

    def test_apply_filters(self):
        """Тест внутренней функции фильтрации."""
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        filters = [FilterConfig(column="a", operator=">", value=1)]
        result = _apply_filters(df, filters)
        assert result.shape[0] == 2
        assert result["a"].to_list() == [2, 3]

    def test_apply_groupby_aggregations(self):
        """Тест внутренней функции группировки."""
        df = pl.DataFrame({
            "cat": ["A", "A", "B", "B"],
            "val": [10, 20, 30, 40],
        })
        aggregations = [AggregationConfig(column="val", function=AggregationFunctionEnum.SUM)]
        result = _apply_groupby_aggregations(df, ["cat"], aggregations)
        assert result.shape[0] == 2
        assert "val_sum" in result.columns

    def test_calculate_yoy(self):
        """Тест внутренней функции YoY."""
        df = pl.DataFrame({
            "year": [2022, 2023],
            "value": [100, 150],
        })
        result = _calculate_yoy(df, year_column="year", value_column="value", alias="yoy")
        assert "yoy" in result.columns
        assert result["yoy"][0] is None
        assert result["yoy"][1] == 50.0  # (150-100)/100 * 100 = 50%

    def test_calculate_share(self):
        """Тест внутренней функции доли."""
        df = pl.DataFrame({"value": [100, 200, 300]})
        result = _calculate_share(df, "value", "share")
        assert "share" in result.columns
        shares = result["share"].to_list()
        assert abs(sum(shares) - 100.0) < 0.01

    def test_apply_custom_metrics(self):
        """Тест внутренней функции кастомных метрик."""
        df = pl.DataFrame({"a": [10, 20], "b": [5, 10]})
        metrics = [CustomMetricConfig(name="sum", formula="a + b")]
        result = _apply_custom_metrics(df, metrics)
        assert "sum" in result.columns
        assert result["sum"].to_list() == [15, 30]

