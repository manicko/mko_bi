"""Seed script for test_media_dash dashboard.

Creates a test dashboard with graphs, filters, and processing config.
Idempotent - can be re-run without creating duplicates.
"""

import asyncio
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from mkobi.db.models import Dashboard, Filter, Graph, ProcessingConfig
from mkobi.db.models.filters import dashboard_filters
from mkobi.db.session import get_session
from mkobi.models.enums import FilterType, GraphType


async def seed_test_media_dash() -> dict[str, Any]:
    """Create or update test_media_dash dashboard with all related records.

    Returns:
        dict with created/updated record IDs.
    """
    result: dict[str, Any] = {
        "dashboard_id": None,
        "graph_ids": [],
        "filter_ids": [],
        "action": "none",
    }

    async with get_session() as db:
        # Check if dashboard already exists
        stmt = select(Dashboard).where(Dashboard.name == "test_media_dash")
        existing_dashboard = (await db.execute(stmt)).scalar_one_or_none()

        if existing_dashboard:
            result["dashboard_id"] = str(existing_dashboard.id)
            result["action"] = "updated"
            # Flush deletes first to prevent FK issues with new filter bindings
            for graph in list(existing_dashboard.graphs):
                await db.delete(graph)
            for filter_obj in list(existing_dashboard.filters):
                await db.delete(filter_obj)
            await db.flush()
            dashboard = existing_dashboard
        else:
            dashboard = Dashboard(
                name="test_media_dash",
                description="Test media dashboard for Phase 02",
            )
            db.add(dashboard)

        # Set dashboard config with filters
        dashboard.config = {
            "filters": [
                {
                    "field": "targetaudience",
                    "type": "multiselect",
                    "source": "data",
                    "multi": True,
                },
                {
                    "field": "category",
                    "type": "multiselect",
                    "source": "data",
                    "multi": True,
                },
            ]
        }

        # Create filters (always create new ones for this dashboard)
        filter1 = Filter(
            name="targetaudience",
            type=FilterType.MULTISELECT,
            config={"source": "data"},
        )
        filter2 = Filter(
            name="category",
            type=FilterType.MULTISELECT,
            config={"source": "data"},
        )
        db.add(filter1)
        db.add(filter2)

        # Create graphs
        graph1 = Graph(
            name="Monthly TVR by Brand",
            type=GraphType.BAR,
            dimensions=["year", "month", "month_label", "brand"],
            metrics=["tvr"],
            config={
                "x": "month_label",
                "color": "brand",
                "metrics": ["tvr_sum"],
                "orientation": "v",
                "barmode": "group",
            },
            dashboard=dashboard,
        )
        graph2 = Graph(
            name="Monthly TVR by Advertiser",
            type=GraphType.BAR,
            dimensions=["year", "month", "month_label", "advertiser"],
            metrics=["tvr"],
            config={
                "x": "month_label",
                "color": "advertiser",
                "metrics": ["tvr_sum"],
                "orientation": "v",
                "barmode": "group",
            },
            dashboard=dashboard,
        )
        db.add(graph1)
        db.add(graph2)

        # Bind filters to dashboard via dashboard_filters table
        await db.flush()  # Ensure we have IDs for foreign key references

        # Remove existing filter bindings for idempotency
        stmt = dashboard_filters.delete().where(
            dashboard_filters.c.dashboard_id == dashboard.id
        )
        await db.execute(stmt)

        # Insert new filter bindings
        await db.execute(
            dashboard_filters.insert().values(
                [
                    {"dashboard_id": dashboard.id, "filter_id": filter1.id},
                    {"dashboard_id": dashboard.id, "filter_id": filter2.id},
                ]
            )
        )

        # Create or update processing config
        proc_config = await db.get(ProcessingConfig, dashboard.id)
        if proc_config:
            result["action"] = "updated"
        else:
            proc_config = ProcessingConfig(dashboard_id=dashboard.id)
            db.add(proc_config)

        # Set processing config settings
        proc_config.settings = {
            "separator": ";",
            "encoding": "utf-8-sig",
            "date_format": "%d/%m/%Y",
            "decimal_separator": ",",
            "column_types": {
                "date": "date",
                "TVR": "float",
                "advertiser": "str",
                "brand": "str",
                "targetaudience": "str",
                "category": "str",
            },
            "date_column": "date",
            "computed_fields": [
                {"name": "year", "expr": "pl.col('date').dt.year()"},
                {"name": "month", "expr": "pl.col('date').dt.month()"},
                {"name": "month_label", "expr": "pl.col('date').dt.strftime('%b %Y')"},
            ],
            "renames": {"TVR": "tvr"},
        }

        try:
            await db.commit()
            # Refresh to get IDs after commit
            await db.refresh(dashboard)
            await db.refresh(filter1)
            await db.refresh(filter2)
            await db.refresh(graph1)
            await db.refresh(graph2)

            result["dashboard_id"] = str(dashboard.id)
            result["filter_ids"] = [str(filter1.id), str(filter2.id)]
            result["graph_ids"] = [str(graph1.id), str(graph2.id)]
        except SQLAlchemyError as e:
            await db.rollback()
            raise RuntimeError(f"Failed to seed test_media_dash: {e}") from e

    return result


async def main() -> None:
    """Run the seed script and print summary."""
    print("Seeding test_media_dash dashboard...")

    result = await seed_test_media_dash()

    print(f"Dashboard ID: {result['dashboard_id']}")
    print(f"Action: {result['action']}")
    print(f"Filter IDs: {result['filter_ids']}")
    print(f"Graph IDs: {result['graph_ids']}")
    print("Seeding complete.")


if __name__ == "__main__":
    asyncio.run(main())