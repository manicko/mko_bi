"""Тесты для репозиториев (UserRepository, DashboardRepository, AccessRepository)."""

from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4

from mko_bi.db.repositories import user_repo, dashboard_repo
from mko_bi.db.models import user as user_model
from mko_bi.db.models import dashboard as dashboard_model


class TestUserRepository:
    """Тесты для UserRepository."""

    async def test_get_user_success(self):
        mock_db = AsyncMock()
        mock_user = MagicMock(spec=user_model.User)
        mock_user.id = uuid4()
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        result = await user_repo.UserRepository.get(mock_user.id, mock_db)

        assert result == mock_user

    async def test_get_user_not_found(self):
        mock_db = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        user_id = uuid4()
        result = await user_repo.UserRepository.get(user_id, mock_db)

        assert result is None

    async def test_create_user_success(self):
        mock_db = AsyncMock()
        mock_user = MagicMock(spec=user_model.User)
        
        mock_db.add = AsyncMock()
        mock_db.flush = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch('mko_bi.db.repositories.user_repo.user_model.User', return_value=mock_user):
            result = await user_repo.UserRepository.create(
                mock_db,
                email="test@example.com",
                password_hash="hash",
                role="viewer"
            )

        assert result == mock_user

    async def test_delete_user_success(self):
        mock_db = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()
        mock_db.execute.return_value = mock_result
        mock_db.delete = AsyncMock()
        mock_db.flush = AsyncMock()

        user_id = uuid4()
        result = await user_repo.UserRepository.delete(user_id, mock_db)

        assert result is True


class TestDashboardRepository:
    """Тесты для DashboardRepository."""

    async def test_get_dashboard_success(self):
        mock_db = AsyncMock()
        mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_dashboard
        mock_db.execute.return_value = mock_result

        result = await dashboard_repo.DashboardRepository.get(mock_dashboard.id, mock_db)

        assert result == mock_dashboard

    async def test_create_dashboard_success(self):
        mock_db = AsyncMock()
        mock_dashboard = MagicMock(spec=dashboard_model.Dashboard)
        
        mock_db.add = AsyncMock()
        mock_db.flush = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch('mko_bi.db.repositories.dashboard_repo.dashboard_model.Dashboard', 
                   return_value=mock_dashboard):
            result = await dashboard_repo.DashboardRepository.create(
                mock_db, name="Test Dashboard", config={}
            )

        assert result == mock_dashboard
