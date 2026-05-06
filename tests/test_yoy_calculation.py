"""Тесты для расчета Year-over-Year (YoY).

Проверяет корректность расчета годового роста с учетом
группировки по измерениям и граничных случаев.
"""

import polars as pl

from mkobi.data.processing.transformations import _calculate_yoy
from mkobi.models.transformation_configs import YoyConfig


class TestCalculateYoyBasic:
    """Базовые тесты расчета YoY без группировки."""

    def test_yoy_simple_two_years(self):
        """Простой тест: два года, одна запись на год."""
        df = pl.DataFrame({
            "year": [2022, 2023],
            "value": [100, 150],
        })
        result = _calculate_yoy(df, year_column="year", value_column="value", alias="yoy")
        assert result["yoy"][0] is None  # Первый год
        assert result["yoy"][1] == 50.0  # (150-100)/100 * 100 = 50%

    def test_yoy_multiple_years(self):
        """Тест с несколькими годами."""
        df = pl.DataFrame({
            "year": [2020, 2021, 2022, 2023],
            "value": [100, 120, 150, 180],
        })
        result = _calculate_yoy(df, year_column="year", value_column="value", alias="yoy")
        assert result["yoy"][0] is None
        assert result["yoy"][1] == 20.0  # (120-100)/100 * 100
        assert result["yoy"][2] == 25.0  # (150-120)/120 * 100
        assert result["yoy"][3] == 20.0  # (180-150)/150 * 100

    def test_yoy_negative_growth(self):
        """Тест с отрицательным ростом."""
        df = pl.DataFrame({
            "year": [2022, 2023],
            "value": [200, 150],
        })
        result = _calculate_yoy(df, year_column="year", value_column="value", alias="yoy")
        assert result["yoy"][1] == -25.0  # (150-200)/200 * 100 = -25%

    def test_yoy_zero_growth(self):
        """Тест с нулевым ростом."""
        df = pl.DataFrame({
            "year": [2022, 2023],
            "value": [100, 100],
        })
        result = _calculate_yoy(df, year_column="year", value_column="value", alias="yoy")
        assert result["yoy"][1] == 0.0


class TestCalculateYoyWithGrouping:
    """Тесты расчета YoY с группировкой по измерениям."""

    def test_yoy_with_grouping(self):
        """Тест: YoY с группировкой по измерению.

        Проверяет, что 2024-A сравнивается с 2023-A (не с 2023-B).
        """
        df = pl.DataFrame({
            "year": [2023, 2023, 2024, 2024],
            "dimension": ["A", "B", "A", "B"],
            "metric_value": [100, 200, 110, 240],
        })
        result = _calculate_yoy(
            df,
            year_column="year",
            value_column="metric_value",
            group_cols=["dimension"],
            alias="yoy",
        )
        # 2024-A сравнивается с 2023-A: (110-100)/100 * 100 = 10%
        a_2024 = result.filter((pl.col("year") == 2024) & (pl.col("dimension") == "A"))
        assert a_2024["yoy"][0] == 10.0

        # 2024-B сравнивается с 2023-B: (240-200)/200 * 100 = 20%
        b_2024 = result.filter((pl.col("year") == 2024) & (pl.col("year") == 2024))
        b_2024 = result.filter((pl.col("year") == 2024) & (pl.col("dimension") == "B"))
        assert b_2024["yoy"][0] == 20.0

    def test_yoy_with_multiple_grouping_columns(self):
        """Тест с несколькими колонками для группировки."""
        df = pl.DataFrame({
            "year": [2023, 2023, 2023, 2024, 2024, 2024],
            "category": ["X", "X", "Y", "X", "Y", "Y"],
            "region": ["R1", "R2", "R1", "R1", "R1", "R2"],
            "value": [100, 200, 150, 110, 180, 170],
        })
        result = _calculate_yoy(
            df,
            year_column="year",
            value_column="value",
            group_cols=["category", "region"],
            alias="yoy",
        )
        # X-R1: (110-100)/100 * 100 = 10%
        x_r1_2024 = result.filter(
            (pl.col("year") == 2024) & (pl.col("category") == "X") & (pl.col("region") == "R1")
        )
        assert x_r1_2024["yoy"][0] == 10.0

        # Y-R1: (180-150)/150 * 100 = 20%
        y_r1_2024 = result.filter(
            (pl.col("year") == 2024) & (pl.col("category") == "Y") & (pl.col("region") == "R1")
        )
        assert y_r1_2024["yoy"][0] == 20.0

    def test_yoy_grouping_preserves_first_year_null(self):
        """Тест: для первого года в группе YoY должен быть None."""
        df = pl.DataFrame({
            "year": [2023, 2023, 2024, 2024],
            "dimension": ["A", "B", "A", "B"],
            "value": [100, 200, 110, 240],
        })
        result = _calculate_yoy(
            df,
            year_column="year",
            value_column="value",
            group_cols=["dimension"],
            alias="yoy",
        )
        # 2023-A и 2023-B должны быть None
        a_2023 = result.filter((pl.col("year") == 2023) & (pl.col("dimension") == "A"))
        assert a_2023["yoy"][0] is None


class TestCalculateYoyWithMonth:
    """Тесты расчета YoY с учетом месяцев."""

    def test_yoy_with_month_column(self):
        """Тест YoY с месяцами (сдвиг на 12 месяцев)."""
        df = pl.DataFrame({
            "year": [2022, 2022, 2023, 2023],
            "month": [1, 2, 1, 2],
            "value": [100, 200, 110, 220],
        })
        result = _calculate_yoy(
            df,
            year_column="year",
            value_column="value",
            month_column="month",
            alias="yoy",
        )
        # Январь 2023 vs Январь 2022: (110-100)/100 * 100 = 10%
        jan_2023 = result.filter((pl.col("year") == 2023) & (pl.col("month") == 1))
        assert jan_2023["yoy"][0] == 10.0


class TestCalculateYoyEdgeCases:
    """Тесты граничных случаев для YoY."""

    def test_yoy_empty_dataframe(self):
        """Тест с пустым DataFrame."""
        df = pl.DataFrame({"year": [], "value": []}, schema={"year": pl.Int64, "value": pl.Float64})
        result = _calculate_yoy(df, year_column="year", value_column="value", alias="yoy")
        assert result.shape[0] == 0
        assert "yoy" in result.columns

    def test_yoy_single_row(self):
        """Тест с одной строкой (нечего сравнивать)."""
        df = pl.DataFrame({"year": [2023], "value": [100]})
        result = _calculate_yoy(df, year_column="year", value_column="value", alias="yoy")
        assert result["yoy"][0] is None

    def test_yoy_division_by_zero(self):
        """Тест деления на ноль (предыдущее значение = 0)."""
        df = pl.DataFrame({
            "year": [2022, 2023],
            "value": [0, 100],
        })
        result = _calculate_yoy(df, year_column="year", value_column="value", alias="yoy")
        assert result["yoy"][0] is None  # Первый год
        assert result["yoy"][1] is None  # Деление на ноль

    def test_yoy_previous_value_null(self):
        """Тест, когда предыдущее значение отсутствует (NaN)."""
        df = pl.DataFrame({
            "year": [2023, 2024],
            "value": [100, 150],
        })
        result = _calculate_yoy(df, year_column="year", value_column="value", alias="yoy")
        # Проверяем, что нет NaN в результате
        assert not result["yoy"].is_nan().any()

    def test_yoy_unsorted_data(self):
        """Тест с неотсортированными данными."""
        df = pl.DataFrame({
            "year": [2024, 2022, 2023],
            "value": [150, 100, 120],
        })
        result = _calculate_yoy(df, year_column="year", value_column="value", alias="yoy")
        # Данные должны быть отсортированы внутри функции
        sorted_result = result.sort("year")
        assert sorted_result["yoy"][0] is None  # 2022
        assert sorted_result["yoy"][1] == 20.0  # 2023: (120-100)/100 * 100


class TestYoyConfig:
    """Тесты конфигурации YoY."""

    def test_yoy_config_creation(self):
        """Тест создания YoyConfig."""
        config = YoyConfig(
            year_column="year",
            value_column="revenue",
            group_cols=["category"],
            alias="yoy_percent",
        )
        assert config.year_column == "year"
        assert config.value_column == "revenue"
        assert config.group_cols == ["category"]
        assert config.alias == "yoy_percent"

    def test_yoy_config_defaults(self):
        """Тест значений по умолчанию в YoyConfig."""
        config = YoyConfig(year_column="year", value_column="value")
        assert config.group_cols is None
        assert config.month_column is None
        assert config.alias == "yoy"
        assert config.percent_alias == "yoy_percent"
