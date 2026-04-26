"""Тесты для пайплайна обработки данных.

Тестирует классы DataProcessor, TransformationRegistry и функции
apply_transformations, calculate_aggregations.
"""

import pytest
import polars as pl

from mko_bi.data.processing.base import DataProcessor
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


class TestDataProcessor:
    """Тесты для базового класса DataProcessor."""

    class ConcreteProcessor(DataProcessor):
        """Конкретная реализация для тестов."""

        def process(self, data: pl.DataFrame) -> pl.DataFrame:
            """Простая обработка - возвращает данные как есть."""
            self._validate_input(data)
            self._log_processing_stats(data, "test")
            return data

    def test_init_with_default_config(self):
        """Тест инициализации с конфигурацией по умолчанию."""
        processor = self.ConcreteProcessor()
        assert processor.config == {}

    def test_init_with_custom_config(self):
        """Тест инициализации с кастомной конфигурацией."""
        config = {"key": "value"}
        processor = self.ConcreteProcessor(config)
        assert processor.config == config

    def test_process_valid_data(self):
        """Тест обработки валидных данных."""
        processor = self.ConcreteProcessor()
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        result = processor.process(df)
        assert isinstance(result, pl.DataFrame)
        assert result.shape == df.shape

    def test_process_empty_data_raises_error(self):
        """Тест обработки пустых данных вызывает ошибку."""
        processor = self.ConcreteProcessor()
        df = pl.DataFrame()
        with pytest.raises(ValueError, match="Входные данные пустые"):
            processor.process(df)

    def test_validate_input_valid(self):
        """Тест валидации валидных входных данных."""
        processor = self.ConcreteProcessor()
        df = pl.DataFrame({"a": [1, 2, 3]})
        # Не должно выбрасывать исключение
        processor._validate_input(df)

    def test_validate_input_empty_rows(self):
        """Тест валидации данных без строк."""
        processor = self.ConcreteProcessor()
        df = pl.DataFrame({"a": []})
        with pytest.raises(ValueError, match="Входные данные пустые"):
            processor._validate_input(df)

    def test_validate_input_empty_columns(self):
        """Тест валидации данных без колонок."""
        processor = self.ConcreteProcessor()
        df = pl.DataFrame()
        with pytest.raises(ValueError, match="Входные данные пустые"):
            processor._validate_input(df)


class TestTransformationRegistry:
    """Тесты для реестра трансформаций."""

    def test_init(self):
        """Тест инициализации реестра."""
        registry = TransformationRegistry()
        assert registry.list_transformations() == []

    def test_register_transformation(self):
        """Тест регистрации трансформации."""
        registry = TransformationRegistry()
        func = lambda df: df
        registry.register("test", func)
        assert "test" in registry.list_transformations()

    def test_register_duplicate_transformation_raises_error(self):
        """Тест регистрации дублирующейся трансформации вызывает ошибку."""
        registry = TransformationRegistry()
        func = lambda df: df
        registry.register("test", func)
        with pytest.raises(ValueError, match="уже зарегистрирована"):
            registry.register("test", func)

    def test_get_existing_transformation(self):
        """Тест получения существующей трансформации."""
        registry = TransformationRegistry()
        func = lambda df: df
        registry.register("test", func)
        retrieved = registry.get("test")
        assert retrieved == func

    def test_get_nonexistent_transformation(self):
        """Тест получения несуществующей трансформации."""
        registry = TransformationRegistry()
        assert registry.get("nonexistent") is None

    def test_has_transformation(self):
        """Тест проверки наличия трансформации."""
        registry = TransformationRegistry()
        func = lambda df: df
        registry.register("test", func)
        assert registry.has_transformation("test") is True
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

    def test_list_transformations(self):
        """Тест получения списка трансформаций."""
        registry = TransformationRegistry()
        registry.register("trans1", lambda df: df)
        registry.register("trans2", lambda df: df)
        transformations = registry.list_transformations()
        assert "trans1" in transformations
        assert "trans2" in transformations
        assert len(transformations) == 2


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
        filters = [{"column": "year", "operator": "==", "value": 2023}]
        result = apply_transformations(sample_df, filters=filters)
        assert result.shape[0] == 3
        assert result["year"].unique().to_list() == [2023]

    def test_apply_multiple_filters(self, sample_df):
        """Тест применения нескольких фильтров."""
        filters = [
            {"column": "year", "operator": "==", "value": 2023},
            {"column": "revenue", "operator": ">", "value": 200},
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
        filters = [{"column": "year", "operator": ">=", "value": 2022}]
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
            {"column": "revenue", "function": "sum", "alias": "total_revenue"},
            {"column": "cost", "function": "sum", "alias": "total_cost"},
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
        aggregations = [{"column": "revenue", "function": "sum"}]
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
        aggregations = [{"column": "revenue", "function": "mean"}]
        result = calculate_aggregations(
            sample_df,
            groupby=["category"],
            aggregations=aggregations,
        )
        assert "revenue_mean" in result.columns

    def test_count_aggregation(self, sample_df):
        """Тест подсчета."""
        aggregations = [{"column": "revenue", "function": "count"}]
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
            {"column": "revenue", "function": "min"},
            {"column": "revenue", "function": "max"},
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
        aggregations = [{"column": "revenue", "function": "sum", "alias": "revenue_sum"}]
        result = calculate_aggregations(
            sample_df,
            groupby=["year"],
            aggregations=aggregations,
            yoy_config={"year_column": "year", "value_column": "revenue_sum", "alias": "yoy"},
        )
        assert "yoy" in result.columns
        # Первый год должен быть NaN
        assert result["yoy"][0] is None

    def test_share_calculation(self, sample_df):
        """Тест расчета долей."""
        aggregations = [{"column": "revenue", "function": "sum", "alias": "revenue_sum"}]
        result = calculate_aggregations(
            sample_df,
            groupby=["category"],
            aggregations=aggregations,
            share_config={"value_column": "revenue_sum", "alias": "share"},
        )
        assert "share" in result.columns
        # Сумма долей должна быть 100%
        total_share = result["share"].sum()
        assert abs(total_share - 100.0) < 0.01

    def test_custom_metrics(self, sample_df):
        """Тест кастомных метрик."""
        aggregations = [
            {"column": "revenue", "function": "sum", "alias": "revenue_sum"},
            {"column": "cost", "function": "sum", "alias": "cost_sum"},
        ]
        custom_metrics = [
            {"name": "profit", "formula": "revenue_sum - cost_sum"},
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
        filters = [{"column": "revenue", "operator": ">", "value": 0}]
        aggregations = [
            {"column": "revenue", "function": "sum", "alias": "revenue_sum"},
            {"column": "cost", "function": "sum", "alias": "cost_sum"},
        ]
        result = apply_transformations(
            sample_df,
            filters=filters,
            sort_by=["year", "category"],
        )
        result = calculate_aggregations(
            result,
            groupby=["year"],
            aggregations=aggregations,
            yoy_config={"year_column": "year", "value_column": "revenue_sum"},
            share_config={"value_column": "revenue_sum"},
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
        filters = [{"column": "a", "operator": ">", "value": 1}]
        result = _apply_filters(df, filters)
        assert result.shape[0] == 2
        assert result["a"].to_list() == [2, 3]

    def test_apply_groupby_aggregations(self):
        """Тест внутренней функции группировки."""
        df = pl.DataFrame({
            "cat": ["A", "A", "B", "B"],
            "val": [10, 20, 30, 40],
        })
        aggregations = [{"column": "val", "function": "sum"}]
        result = _apply_groupby_aggregations(df, ["cat"], aggregations)
        assert result.shape[0] == 2
        assert "val_sum" in result.columns

    def test_calculate_yoy(self):
        """Тест внутренней функции YoY."""
        df = pl.DataFrame({
            "year": [2022, 2023],
            "value": [100, 150],
        })
        result = _calculate_yoy(df, "year", "value", "yoy")
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
        metrics = [{"name": "sum", "formula": "a + b"}]
        result = _apply_custom_metrics(df, metrics)
        assert "sum" in result.columns
        assert result["sum"].to_list() == [15, 30]

