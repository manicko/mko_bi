from typing import Dict, Any
import polars as pl


class DataPipeline:
    """Base data pipeline for processing.

    Orchestrates the data processing workflow:
    1. Transform
    2. Aggregate
    3. Return result
    """

    def run(self, df: pl.DataFrame, config: Dict[str, Any]) -> pl.DataFrame:
        """Run the full data processing pipeline.

        Args:
            df: Input DataFrame
            config: Processing configuration

        Returns:
            Processed DataFrame
        """
        # Transform
        transformed_df = self.transform(df, config)

        # Aggregate
        aggregated_df = self.aggregate(transformed_df, config)

        return aggregated_df

    def transform(self, df: pl.DataFrame, config: Dict[str, Any]) -> pl.DataFrame:
        """Apply transformations to DataFrame.

        Args:
            df: Input DataFrame
            config: Transformation configuration

        Returns:
            Transformed DataFrame
        """
        # Apply filters
        if "filters" in config:
            for filter_config in config["filters"]:
                column = filter_config["column"]
                value = filter_config["value"]
                df = df.filter(pl.col(column) == value)

        # Apply computed fields
        if "computed_fields" in config:
            for field_config in config["computed_fields"]:
                field_name = field_config["name"]
                expression = field_config["expression"]
                df = df.with_columns([expression.alias(field_name)])

        return df

    def aggregate(self, df: pl.DataFrame, config: Dict[str, Any]) -> pl.DataFrame:
        """Apply aggregations to DataFrame.

        Args:
            df: Transformed DataFrame
            config: Aggregation configuration

        Returns:
            Aggregated DataFrame
        """
        if "aggregations" not in config:
            return df

        # Group by columns
        group_by_cols = config.get("group_by", [])

        # Build aggregation expressions
        agg_exprs = []
        for agg_config in config["aggregations"]:
            column = agg_config["column"]
            operation = agg_config["operation"]
            alias = agg_config.get("alias", f"{operation}_{column}")

            if operation == "sum":
                expr = pl.col(column).sum().alias(alias)
            elif operation == "mean":
                expr = pl.col(column).mean().alias(alias)
            elif operation == "count":
                expr = pl.count().alias(alias)
            elif operation == "min":
                expr = pl.col(column).min().alias(alias)
            elif operation == "max":
                expr = pl.col(column).max().alias(alias)
            else:
                raise ValueError(f"Unknown aggregation operation: {operation}")

            agg_exprs.append(expr)

        if group_by_cols:
            return df.group_by(group_by_cols).agg(agg_exprs)
        else:
            return df.select(agg_exprs)
