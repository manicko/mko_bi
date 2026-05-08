"""Tests for StorageManager."""

from __future__ import annotations

import pytest
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from mkobi.data.storage.manager import StorageManager


@pytest.fixture
def manager(async_db_session: AsyncSession) -> StorageManager:
    """Create StorageManager instance."""
    return StorageManager(db=async_db_session)


@pytest.mark.asyncio
async def test_clear_graph_data(manager: StorageManager, async_db_session: AsyncSession):
    """Test clear_graph_data method."""
    graph_id = uuid4()

    # Test deleting from empty table
    deleted = await manager.clear_graph_data(graph_id=graph_id)
    assert deleted == 0

    # TODO: Add test with actual data when AggregatedData model is available


@pytest.mark.asyncio
async def test_clear_dashboard_data(manager: StorageManager, async_db_session: AsyncSession):
    """Test clear_dashboard_data method."""
    dashboard_id = uuid4()

    # Test deleting from empty table
    deleted = await manager.clear_dashboard_data(dashboard_id=dashboard_id)
    assert deleted == 0

    # TODO: Add test with actual data when AggregatedData model is available


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
