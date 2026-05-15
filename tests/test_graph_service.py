"""Unit tests for GraphService business logic."""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from mkobi.models.enums import GraphType
from mkobi.models.graph import GraphCreate, GraphRead, GraphUpdate
from mkobi.services.graph_service import GraphService


@pytest.mark.asyncio
class TestGraphService:
    """Unit tests for GraphService business logic."""

    @pytest.fixture
    def mock_graph_repo(self):
        """Create a mock graph repository."""
        return AsyncMock()

    @pytest.fixture
    def graph_service(self, mock_graph_repo):
        """Create GraphService with mocked repository."""
        return GraphService(mock_graph_repo)

    # --- Helper ---

    def _make_graph_obj(self, graph_id=None, name="Test Graph", dashboard_id=None,
                         type_=GraphType.BAR, config=None, dimensions=None, metrics=None):
        """Create a mock graph DB object."""
        obj = MagicMock()
        obj.id = graph_id or uuid4()
        obj.name = name
        obj.dashboard_id = dashboard_id or uuid4()
        obj.type = type_
        obj.config = config or {"xaxis": {"title": "X"}}
        obj.dimensions = dimensions or ["category"]
        obj.metrics = metrics or ["revenue"]
        return obj

    # --- create tests ---

    async def test_create_graph_success(self, graph_service, mock_graph_repo):
        """Test successful graph creation."""
        dashboard_id = uuid4()
        mock_graph_repo.create.return_value = self._make_graph_obj(
            name="Sales", dashboard_id=dashboard_id, type_=GraphType.BAR
        )

        data = GraphCreate(
            name="Sales",
            type=GraphType.BAR,
            dashboard_id=dashboard_id,
            config={"xaxis": {"title": "Month"}},
            dimensions=["month"],
            metrics=["revenue"],
        )
        result = await graph_service.create(data)

        assert isinstance(result, GraphRead)
        assert result.name == "Sales"
        assert result.type == GraphType.BAR
        mock_graph_repo.create.assert_called_once()

    async def test_create_graph_empty_name_raises(self, graph_service, mock_graph_repo):
        """Test graph creation fails with empty name."""
        data = GraphCreate(
            name="",
            type=GraphType.BAR,
            dashboard_id=uuid4(),
            config={},
            dimensions=["cat"],
            metrics=["rev"],
        )

        with pytest.raises(ValueError, match="Graph name cannot be empty"):
            await graph_service.create(data)

    async def test_create_graph_invalid_type_raises(self, graph_service, mock_graph_repo):
        """Test graph creation fails with invalid type via direct dict bypass."""
        with pytest.raises(ValueError, match="Invalid graph type"):
            await graph_service._validate_graph_data(
                MagicMock(name="Test", type="invalid_type", dashboard_id=uuid4())
            )

    async def test_create_graph_repo_returns_none_raises(self, graph_service, mock_graph_repo):
        """Test graph creation fails when repo returns None."""
        mock_graph_repo.create.return_value = None

        data = GraphCreate(
            name="Test",
            type=GraphType.LINE,
            dashboard_id=uuid4(),
            config={},
            dimensions=["cat"],
            metrics=["rev"],
        )

        with pytest.raises(ValueError, match="Failed to create graph"):
            await graph_service.create(data)

    # --- get tests ---

    async def test_get_graph_found(self, graph_service, mock_graph_repo):
        """Test getting graph by ID when it exists."""
        graph_id = uuid4()
        mock_graph_repo.get.return_value = self._make_graph_obj(graph_id=graph_id)

        result = await graph_service.get(graph_id)

        assert isinstance(result, GraphRead)
        assert result.id == graph_id

    async def test_get_graph_not_found(self, graph_service, mock_graph_repo):
        """Test getting graph by ID when it doesn't exist."""
        mock_graph_repo.get.return_value = None

        result = await graph_service.get(uuid4())

        assert result is None

    # --- update tests ---

    async def test_update_graph_success(self, graph_service, mock_graph_repo):
        """Test successful graph update."""
        graph_id = uuid4()
        mock_graph_repo.update.return_value = self._make_graph_obj(
            graph_id=graph_id, name="Updated Graph"
        )

        data = GraphUpdate(name="Updated Graph")
        result = await graph_service.update(graph_id, data)

        assert isinstance(result, GraphRead)
        assert result.name == "Updated Graph"

    async def test_update_graph_not_found(self, graph_service, mock_graph_repo):
        """Test update returns None when graph not found."""
        mock_graph_repo.update.return_value = None

        data = GraphUpdate(name="Nonexistent")
        result = await graph_service.update(uuid4(), data)

        assert result is None

    async def test_update_graph_partial(self, graph_service, mock_graph_repo):
        """Test partial update only changes provided fields."""
        graph_id = uuid4()
        mock_graph_repo.update.return_value = self._make_graph_obj(
            graph_id=graph_id, name="Updated Name", type_=GraphType.PIE
        )

        data = GraphUpdate(name="Updated Name")
        result = await graph_service.update(graph_id, data)

        assert result.name == "Updated Name"
        mock_graph_repo.update.assert_called_once()

    # --- delete tests ---

    async def test_delete_graph_success(self, graph_service, mock_graph_repo):
        """Test successful graph deletion."""
        mock_graph_repo.delete.return_value = True

        result = await graph_service.delete(uuid4())

        assert result is True

    async def test_delete_graph_not_found(self, graph_service, mock_graph_repo):
        """Test deletion returns False when graph not found."""
        mock_graph_repo.delete.return_value = False

        result = await graph_service.delete(uuid4())

        assert result is False

    # --- list_by_dashboard tests ---

    async def test_list_by_dashboard_with_graphs(self, graph_service, mock_graph_repo):
        """Test listing graphs for a dashboard with results."""
        dashboard_id = uuid4()
        mock_graph_repo.get_by_dashboard_id.return_value = [
            self._make_graph_obj(name="Graph 1", dashboard_id=dashboard_id),
            self._make_graph_obj(name="Graph 2", dashboard_id=dashboard_id),
        ]

        result = await graph_service.list_by_dashboard(dashboard_id)

        assert len(result) == 2
        assert all(isinstance(g, GraphRead) for g in result)

    async def test_list_by_dashboard_empty(self, graph_service, mock_graph_repo):
        """Test listing graphs for dashboard with no graphs."""
        mock_graph_repo.get_by_dashboard_id.return_value = []

        result = await graph_service.list_by_dashboard(uuid4())

        assert result == []

    # --- get_graphs_by_dashboard tests ---

    async def test_get_graphs_by_dashboard(self, graph_service, mock_graph_repo):
        """Test get_graphs_by_dashboard alias method."""
        dashboard_id = uuid4()
        mock_graph_repo.get_by_dashboard_id.return_value = [
            self._make_graph_obj(dashboard_id=dashboard_id)
        ]

        result = await graph_service.get_graphs_by_dashboard(dashboard_id)

        assert len(result) == 1

    # --- get_graph_by_name_and_dashboard tests ---

    async def test_get_graph_by_name_and_dashboard_found(self, graph_service, mock_graph_repo):
        """Test finding graph by name and dashboard."""
        dashboard_id = uuid4()
        mock_graph_repo.get_by_name_and_dashboard.return_value = self._make_graph_obj(
            name="Revenue Chart", dashboard_id=dashboard_id
        )

        result = await graph_service.get_graph_by_name_and_dashboard("Revenue Chart", dashboard_id)

        assert isinstance(result, GraphRead)
        assert result.name == "Revenue Chart"

    async def test_get_graph_by_name_and_dashboard_not_found(self, graph_service, mock_graph_repo):
        """Test finding graph by name returns None when missing."""
        mock_graph_repo.get_by_name_and_dashboard.return_value = None

        result = await graph_service.get_graph_by_name_and_dashboard("Missing", uuid4())

        assert result is None

    # --- Interface compliance ---

    async def test_service_implements_IGraphService(self, graph_service):
        """Test that GraphService implements IGraphService interface."""
        from mkobi.interfaces.service_interfaces import IGraphService

        assert isinstance(graph_service, IGraphService)