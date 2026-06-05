"""Seeder for test_media_dash dashboard.

Creates a test dashboard with graphs, filters, and processing config.
Idempotent - can be re-run without creating duplicates or breaking other dashboards.
"""

import logging
from typing import Any

from sqlalchemy import select, delete

from mkobi.db.models import Dashboard, Graph, ProcessingConfig
from mkobi.db.models.filters import dashboard_filters, Filter
from mkobi.db.session import get_async_sessionlocal
from mkobi.models.enums import FilterType, GraphType

logger = logging.getLogger(__name__)

DASHBOARD_NAME = "test_media_dash"


async def ensure_test_media_dash() -> dict[str, Any]:
    """Create or update test_media_dash dashboard with all related records.

    This function is idempotent and safe to run multiple times.
    When re-seeding, only deletes the dashboard's graphs and filter bindings,
    NOT the Filter records themselves (filters are shared across dashboards).

    Returns:
        dict with created/updated record IDs.
    """
    result: dict[str, Any] = {
        "dashboard_id": None,
        "graph_ids": [],
        "filter_ids": [],
        "action": "none",
    }

    SessionLocal = await get_async_sessionlocal()

    async with SessionLocal() as db:
        # Check if dashboard already exists
        stmt = select(Dashboard).where(Dashboard.name == DASHBOARD_NAME)
        existing_dashboard = (await db.execute(stmt)).scalar_one_or_none()

        if existing_dashboard:
            result["dashboard_id"] = str(existing_dashboard.id)
            result["action"] = "updated"
            dashboard = existing_dashboard

            # Delete only the dashboard's graphs (not filters - they may be shared)
            for graph in list(existing_dashboard.graphs):
                await db.delete(graph)

            # Remove only the filter bindings for this dashboard
            # Filters themselves are NOT deleted as they may be used by other dashboards
            await db.execute(
                delete(dashboard_filters).where(
                    dashboard_filters.c.dashboard_id == dashboard.id
                )
            )
            await db.flush()
        else:
            dashboard = Dashboard(
                name=DASHBOARD_NAME,
                description="Test media dashboard for Phase 02",
            )
            db.add(dashboard)
            result["action"] = "created"

        # Set dashboard config with filter definitions
        dashboard.config = {
            "graph_types": ["bar"],
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
            ],
        }

        # Find or create filters (do not delete existing filters)
        filter1_stmt = select(Filter).where(Filter.name == "targetaudience")
        filter1 = (await db.execute(filter1_stmt)).scalar_one_or_none()
        if filter1 is None:
            filter1 = Filter(
                name="targetaudience",
                type=FilterType.MULTISELECT,
                config={"source": "data"},
            )
            db.add(filter1)

        filter2_stmt = select(Filter).where(Filter.name == "category")
        filter2 = (await db.execute(filter2_stmt)).scalar_one_or_none()
        if filter2 is None:
            filter2 = Filter(
                name="category",
                type=FilterType.MULTISELECT,
                config={"source": "data"},
            )
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

        # Flush to get IDs
        await db.flush()

        # Bind filters to dashboard via dashboard_filters table
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
            pass  # Will be updated below
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

        # Commit the transaction
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
        logger.info(
            "Test dashboard %s: id=%s, filters=%s, graphs=%s",
            result["action"],
            result["dashboard_id"],
            result["filter_ids"],
            result["graph_ids"],
        )

    return result