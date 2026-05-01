"""Тесты для расчета долей (share calculation).

Проверяет корректность расчета долей от общей суммы
с учетом группировки и граничных случаев.
"""

import polars as pl

from mko_bi.data.processing.transformations import _calculate_share
from mko_bi.models.transformation_configs import ShareConfig


class TestCalculateShareBasic:
    """Базовые тесты расчета долей без группировки."""

    def test_share_simple(self):
        """Простой тест: три значения, сумма долей = 100%."""
        df = pl.DataFrame({"value": [100, 200, 300]})
        result = _calculate_share(df, value_column="value", alias="share")
        shares = result["share"].to_list()
        assert abs(sum(shares) - 100.0) < 0.01
        # 100/600 * 100 = 16.67%
        assert abs(shares[0] - 16.666666666666664) < 0.01

    def test_share_two_values(self):
        """Тест с двумя значениями."""
        df = pl.DataFrame({"value": [30, 70]})
        result = _calculate_share(df, value_column="value", alias="share")
        shares = result["share"].to_list()
        assert abs(sum(shares) - 100.0) < 0.01
        assert abs(shares[0] - 30.0) < 0.01
        assert abs(shares[1] - 70.0) < 0.01

    def test_share_single_value(self):
        """Тест с одним значением (доля = 100%)."""
        df = pl.DataFrame({"value": [50]})
        result = _calculate_share(df, value_column="value", alias="share")
        assert result["share"][0] == 100.0


class TestCalculateShareWithGrouping:
    """Тесты расчета долей с группировкой."""

    def test_share_with_grouping(self):
        """Тест расчета долей с группировкой по году."""
        df = pl.DataFrame({
            "year": [2023, 2023, 2024, 2024],
            "category": ["A", "B", "A", "B"],
            "value": [100, 200, 150, 250],
        })
        result = _calculate_share(
            df,
            value_column="value",
            group_cols=["year"],
            alias="share",
        )
        # 2023: A=100/300*100=33.33%, B=200/300*100=66.67%
        year_2023 = result.filter(pl.col("year") == 2023)
        shares_2023 = year_2023["share"].to_list()
        assert abs(sum(shares_2023) - 100.0) < 0.01
        assert abs(shares_2023[0] - 33.33333333333333) < 0.01

        # 2024: A=150/400*100=37.5%, B=250/400*100=62.5%
        year_2024 = result.filter(pl.col("year") == 2024)
        shares_2024 = year_2024["share"].to_list()
        assert abs(sum(shares_2024) - 100.0) < 0.01
        assert abs(shares_2024[0] - 37.5) < 0.01

    def test_share_with_multiple_grouping_columns(self):
        """Тест с несколькими колонками для группировки."""
        df = pl.DataFrame({
            "year": [2023, 2023, 2023, 2024, 2024, 2024],
            "region": ["R1", "R1", "R2", "R1", "R2", "R2"],
            "category": ["A", "B", "A", "A", "A", "B"],
            "value": [100, 200, 150, 120, 180, 300],
        })
        result = _calculate_share(
            df,
            value_column="value",
            group_cols=["year", "region"],
            alias="share",
        )
        # Проверяем, что сумма долей внутри каждой группы = 100%
        for year in result["year"].unique().to_list():
            for region in result["region"].unique().to_list():
                group = result.filter(
                    (pl.col("year") == year) & (pl.col("region") == region)
                )
                if group.shape[0] > 0:
                    share_sum = group["share"].sum()
                    assert abs(share_sum - 100.0) < 0.01

    def test_share_grouping_preserves_rows(self):
        """Тест: количество строк не меняется при расчете долей."""
        df = pl.DataFrame({
            "year": [2023, 2023, 2024, 2024],
            "category": ["A", "B", "A", "B"],
            "value": [100, 200, 150, 250],
        })
        original_rows = df.shape[0]
        result = _calculate_share(
            df,
            value_column="value",
            group_cols=["year"],
            alias="share",
        )
        assert result.shape[0] == original_rows


class TestCalculateShareEdgeCases:
    """Тесты граничных случаев для расчета долей."""

    def test_share_empty_dataframe(self):
        """Тест с пустым DataFrame."""
        df = pl.DataFrame({"value": []}, schema={"value": pl.Float64})
        result = _calculate_share(df, value_column="value", alias="share")
        assert result.shape[0] == 0
        assert "share" in result.columns

    def test_share_division_by_zero_total(self):
        """Тест деления на ноль (сумма группы = 0)."""
        df = pl.DataFrame({
            "year": [2023, 2023],
            "value": [0, 0],
        })
        result = _calculate_share(
            df,
            value_column="value",
            group_cols=["year"],
            alias="share",
        )
        # Все доли должны быть 0.0
        assert all(v == 0.0 for v in result["share"].to_list())

    def test_share_all_zeros_no_grouping(self):
        """Тест когда все значения равны нулю без группировки."""
        df = pl.DataFrame({"value": [0, 0, 0]})
        result = _calculate_share(df, value_column="value", alias="share")
        # Сумма = 0, все доли устанавливаются в 0.0
        assert all(v == 0.0 for v in result["share"].to_list())

    def test_share_negative_values(self):
        """Тест с отрицательными значениями."""
        df = pl.DataFrame({"value": [100, -50, 50]})
        result = _calculate_share(df, value_column="value", alias="share")
        # Сумма = 100, доли считаются от суммы
        shares = result["share"].to_list()
        assert abs(sum(shares) - 100.0) < 0.01

    def test_share_null_values(self):
        """Тест с null значениями."""
        df = pl.DataFrame({
            "value": [100, None, 200],
            "dummy": [1, 2, 3],
        })
        # Polars обрабатывает null при суммировании (игнорирует их)
        result = _calculate_share(df, value_column="value", alias="share")
        # 100 + 200 = 300
        # 100/300*100 = 33.33%, null обрабатывается polars
        assert "share" in result.columns


class TestShareConfig:
    """Тесты конфигурации расчета долей."""

    def test_share_config_creation(self):
        """Тест создания ShareConfig."""
        config = ShareConfig(
            value_column="revenue",
            group_cols=["year", "category"],
            alias="revenue_share",
        )
        assert config.value_column == "revenue"
        assert config.group_cols == ["year", "category"]
        assert config.alias == "revenue_share"

    def test_share_config_defaults(self):
        """Тест значений по умолчанию в ShareConfig."""
        config = ShareConfig(value_column="value")
        assert config.group_cols is None
        assert config.alias == "share"
