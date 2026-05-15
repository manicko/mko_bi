"""Tests for StorageManager."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from mkobi.db.models.aggregated_data import AggregatedData
from mkobi.db.repositories.dashboard_repo import DashboardRepository
from mkobi.db.repositories.graph_repo import GraphRepository
from mkobi.models.enums import GraphType

from mkobi.data.storage.manager import StorageManager


@pytest.fixture
def manager(async_db_session: AsyncSession) -> StorageManager:
    """Create StorageManager instance."""
    return StorageManager(db=async_db_session)


@pytest.mark.asyncio
async def test_clear_graph_data(manager: StorageManager):
    """Test clear_graph_data method."""
    graph_id = uuid4()

    # Test deleting from empty table
    deleted = await manager.clear_graph_data(graph_id=graph_id)
    assert deleted == 0


@pytest.mark.asyncio
async def test_clear_graph_data_with_data(
    manager: StorageManager, async_db_session: AsyncSession
):
    """Test clear_graph_data method when actual data exists."""
    # Create a dashboard and graph to own the aggregated data
    dashboard_repo = DashboardRepository()
    dashboard = await dashboard_repo.create(
        db=async_db_session,
        name="test_dashboard",
        description="Test dashboard",
    )
    await async_db_session.commit()

    graph_repo = GraphRepository()
    graph = await graph_repo.create(
        db=async_db_session,
        dashboard_id=dashboard.id,
        name="test_graph",
        type=GraphType.TABLE,
        config={},
        dimensions=[],
        metrics=[],
    )
    await async_db_session.commit()

    # Insert aggregated data for the graph
    test_data = AggregatedData(
        dashboard_id=dashboard.id,
        graph_id=graph.id,
        dims={"category": "A"},
        metrics={"sales": 100},
    )
    async_db_session.add(test_data)
    await async_db_session.commit()

    # Verify data exists before deletion
    result = await async_db_session.execute(
        select(AggregatedData).where(
            AggregatedData.graph_id == graph.id
        )
    )
    assert len(result.scalars().all()) == 1

    # Clear graph data
    deleted = await manager.clear_graph_data(graph_id=graph.id)
    assert deleted == 1

    # Verify data is cleared
    result = await async_db_session.execute(
        select(AggregatedData).where(
            AggregatedData.graph_id == graph.id
        )
    )
    assert len(result.scalars().all()) == 0


@pytest.mark.asyncio
async def test_clear_dashboard_data(manager: StorageManager):
    """Test clear_dashboard_data method."""
    dashboard_id = uuid4()

    # Test deleting from empty table
    deleted = await manager.clear_dashboard_data(dashboard_id=dashboard_id)
    assert deleted == 0


@pytest.mark.asyncio
async def test_clear_dashboard_data_with_data(
    manager: StorageManager, async_db_session: AsyncSession
):
    """Test clear_dashboard_data method when actual data exists."""
    # Create a dashboard and graph to own the aggregated data
    dashboard_repo = DashboardRepository()
    dashboard = await dashboard_repo.create(
        db=async_db_session,
        name="test_dashboard_clear",
        description="Test dashboard for clear",
    )
    await async_db_session.commit()

    graph_repo = GraphRepository()
    graph = await graph_repo.create(
        db=async_db_session,
        dashboard_id=dashboard.id,
        name="test_graph_clear",
        type=GraphType.TABLE,
        config={},
        dimensions=[],
        metrics=[],
    )
    await async_db_session.commit()

    # Insert aggregated data for the dashboard
    test_data = AggregatedData(
        dashboard_id=dashboard.id,
        graph_id=graph.id,
        dims={"category": "B"},
        metrics={"revenue": 200},
    )
    async_db_session.add(test_data)
    await async_db_session.commit()

    # Verify data exists before deletion
    result = await async_db_session.execute(
        select(AggregatedData).where(
            AggregatedData.dashboard_id == dashboard.id
        )
    )
    assert len(result.scalars().all()) == 1

    # Clear dashboard data
    deleted = await manager.clear_dashboard_data(dashboard_id=dashboard.id)
    assert deleted == 1

    # Verify data is cleared
    result = await async_db_session.execute(
        select(AggregatedData).where(
            AggregatedData.dashboard_id == dashboard.id
        )
    )
    assert len(result.scalars().all()) == 0


@pytest.mark.asyncio
async def test_clear_graph_data_compat(async_db_session: AsyncSession):
    """Test clear_graph_data compatibility method."""
    graph_id = uuid4()

    deleted = await StorageManager.clear_graph_data_compat(
        graph_id=graph_id,
        db=async_db_session,
    )
    assert deleted == 0


@pytest.mark.asyncio
async def test_clear_dashboard_data_compat(async_db_session: AsyncSession):
    """Test clear_dashboard_data compatibility method."""
    dashboard_id = uuid4()

    deleted = await StorageManager.clear_dashboard_data_compat(
        dashboard_id=dashboard_id,
        db=async_db_session,
    )
    assert deleted == 0
