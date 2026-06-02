"""Tests for cumulative file size check during streaming when file.size is None."""
import tempfile
from pathlib import Path

import pytest
from fastapi import status
from httpx import AsyncClient
from unittest.mock import patch

from mkobi.config import get_config
from mkobi.core.security import hash_password, create_access_token
from mkobi.db.models.dashboard import Dashboard
from mkobi.db.repositories.access_repo import AccessRepository
from mkobi.db.repositories.dashboard_repo import DashboardRepository
from mkobi.db.repositories.user_repo import UserRepository
from mkobi.models.enums import DashboardPermission
import uuid


class TestStreamingSizeLimit:
    """Test cumulative size check during file streaming when Content-Length is absent.

    When file.size is None (no Content-Length header), the streaming loop must
    enforce the max_file_size limit through cumulative byte counting to prevent
    disk exhaustion attacks.
    """

    @pytest.fixture
    async def test_dashboard(self, async_db_session) -> Dashboard:
        """Create a test dashboard for upload tests."""
        repo = DashboardRepository()
        dashboard = await repo.create(
            db=async_db_session,
            name=f"test_streaming_dashboard_{uuid.uuid4().hex[:8]}",
            description="Dashboard for streaming size limit tests",
        )
        await async_db_session.commit()
        return dashboard

    @pytest.fixture
    async def test_user_for_streaming(self, async_db_session) -> dict:
        """Create a test user for streaming tests."""
        user_repo = UserRepository()
        unique_id = uuid.uuid4().hex[:8]
        user = await user_repo.create(
            db=async_db_session,
            email=f"streaming_{unique_id}@example.com",
            password_hash=hash_password("TestPass123!"),
            role="admin",
        )
        await async_db_session.commit()
        token = create_access_token({"user_id": str(user.id), "email": user.email})
        return {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "token": token,
        }

    @pytest.fixture
    def auth_headers_for_streaming(self, test_user_for_streaming) -> dict[str, str]:
        """Return authorization headers with JWT token for streaming tests."""
        return {"Authorization": f"Bearer {test_user_for_streaming['token']}"}

    async def test_file_within_limit_no_content_length(
        self,
        async_client: AsyncClient,
        auth_headers_for_streaming: dict[str, str],
        async_db_session,
        test_user_for_streaming: dict,
        test_dashboard: Dashboard,
    ) -> None:
        """File under max size without Content-Length should succeed.

        When file.size is None but file content is within limits,
        the upload should succeed with 201 CREATED.
        """
        # Grant edit access to test user
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=test_user_for_streaming["id"],
            dashboard_id=test_dashboard.id,
            permission=DashboardPermission.EDIT,
        )
        await async_db_session.commit()

        config = get_config()
        # Create CSV content well under the limit
        csv_content = b"category,region,sales\nA,North,100\nB,South,200\n"
        assert len(csv_content) < config.max_file_size

        # Mock config to use the actual max file size (file should pass validation)
        temp_dir = Path(tempfile.gettempdir()) / "mkobi_streaming_test"
        mock_config = type(
            "MockConfig",
            (),
            {
                "max_file_size": config.max_file_size,
                "upload": type(
                    "MockUpload", (), {"max_file_size_mb": config.upload.max_file_size_mb}
                )(),
                "upload_temp_dir": str(temp_dir),
                "rate_limiter_fail_closed": False,
            },
        )()

        # Use tempfile to get file.size=None behavior
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_path = Path(f.name)

        try:
            with patch("mkobi.api.routes.upload.get_config", return_value=mock_config):
                with open(csv_path, "rb") as f:
                    response = await async_client.post(
                        f"/upload/{test_dashboard.id}",
                        headers=auth_headers_for_streaming,
                        files={"file": ("small.csv", f, "text/csv")},
                    )
            # Should succeed since content is within limits
            assert response.status_code == status.HTTP_201_CREATED
        finally:
            csv_path.unlink(missing_ok=True)

    async def test_file_exceeds_limit_returns_413(
        self,
        async_client: AsyncClient,
        auth_headers_for_streaming: dict[str, str],
        async_db_session,
        test_user_for_streaming: dict,
        test_dashboard: Dashboard,
    ) -> None:
        """File exceeding max_file_size should return 413.

        When streaming cumulative bytes exceed max_file_size,
        the upload should be rejected with 413 CONTENT_TOO_LARGE.
        """
        # Grant edit access to test user
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=test_user_for_streaming["id"],
            dashboard_id=test_dashboard.id,
            permission=DashboardPermission.EDIT,
        )
        await async_db_session.commit()

        # Set max_file_size to 1 byte to trigger limit during streaming
        temp_dir = Path(tempfile.gettempdir()) / "mkobi_streaming_test"
        mock_config = type(
            "MockConfig",
            (),
            {
                "max_file_size": 1,  # Very small limit to trigger during streaming
                "upload": type("MockUpload", (), {"max_file_size_mb": 100})(),
                "upload_temp_dir": str(temp_dir),
                "rate_limiter_fail_closed": False,
            },
        )()

        # Create CSV content that exceeds 1 byte
        csv_content = b"category,region,sales\nA,North,100\nB,South,200\nC,East,300\n"

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_path = Path(f.name)

        try:
            with patch("mkobi.api.routes.upload.get_config", return_value=mock_config):
                with open(csv_path, "rb") as f:
                    response = await async_client.post(
                        f"/upload/{test_dashboard.id}",
                        headers=auth_headers_for_streaming,
                        files={"file": ("oversized.csv", f, "text/csv")},
                    )
            assert response.status_code == status.HTTP_413_CONTENT_TOO_LARGE
        finally:
            csv_path.unlink(missing_ok=True)

    async def test_temp_file_cleaned_after_rejection(
        self,
        async_client: AsyncClient,
        auth_headers_for_streaming: dict[str, str],
        async_db_session,
        test_user_for_streaming: dict,
        test_dashboard: Dashboard,
    ) -> None:
        """Temp file should be deleted after size limit rejection.

        When upload is rejected due to size limit, the temporary file
        created during streaming must be cleaned up to prevent disk exhaustion.
        """
        # Grant edit access to test user
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=test_user_for_streaming["id"],
            dashboard_id=test_dashboard.id,
            permission=DashboardPermission.EDIT,
        )
        await async_db_session.commit()

        # Use small limit and isolated temp dir for this test
        temp_dir = Path(tempfile.gettempdir()) / "mkobi_streaming_cleanup_test"
        temp_dir.mkdir(parents=True, exist_ok=True)

        mock_config = type(
            "MockConfig",
            (),
            {
                "max_file_size": 1,  # Very small limit
                "upload": type("MockUpload", (), {"max_file_size_mb": 100})(),
                "upload_temp_dir": str(temp_dir),
                "rate_limiter_fail_closed": False,
            },
        )()

        csv_content = b"category,sales\nA,100\nB,200\n"

        # Get initial state of temp dir
        initial_files = set(temp_dir.glob("*.csv*"))

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_path = Path(f.name)

        try:
            with patch("mkobi.api.routes.upload.get_config", return_value=mock_config):
                with open(csv_path, "rb") as f:
                    response = await async_client.post(
                        f"/upload/{test_dashboard.id}",
                        headers=auth_headers_for_streaming,
                        files={"file": ("rejected.csv", f, "text/csv")},
                    )

            # Verify rejection
            assert response.status_code == status.HTTP_413_CONTENT_TOO_LARGE

            # Verify temp files were cleaned up - no new files should remain
            final_files = set(temp_dir.glob("*.csv*"))
            new_files = final_files - initial_files
            assert len(new_files) == 0, f"Lingering temp files after rejection: {new_files}"
        finally:
            csv_path.unlink(missing_ok=True)

    async def test_file_size_none_triggers_cumulative_check(
        self,
        async_client: AsyncClient,
        auth_headers_for_streaming: dict[str, str],
        async_db_session,
        test_user_for_streaming: dict,
        test_dashboard: Dashboard,
    ) -> None:
        """file.size=None triggers the cumulative check path.

        When UploadFile.size is None (no Content-Length header),
        the streaming loop's cumulative size check must enforce the limit.
        This test uses tempfile which may not send Content-Length.
        """
        # Grant edit access to test user
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=test_user_for_streaming["id"],
            dashboard_id=test_dashboard.id,
            permission=DashboardPermission.EDIT,
        )
        await async_db_session.commit()

        temp_dir = Path(tempfile.gettempdir()) / "mkobi_size_none_test"
        temp_dir.mkdir(parents=True, exist_ok=True)

        mock_config = type(
            "MockConfig",
            (),
            {
                "max_file_size": 1,  # Very small limit to trigger during streaming
                "upload": type("MockUpload", (), {"max_file_size_mb": 100})(),
                "upload_temp_dir": str(temp_dir),
                "rate_limiter_fail_closed": False,
            },
        )()

        csv_content = b"category,sales\nA,100\nB,200\nC,300\n"

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_path = Path(f.name)

        try:
            with patch("mkobi.api.routes.upload.get_config", return_value=mock_config):
                with open(csv_path, "rb") as f:
                    response = await async_client.post(
                        f"/upload/{test_dashboard.id}",
                        headers=auth_headers_for_streaming,
                        files={"file": ("no_size.csv", f, "text/csv")},
                    )

            # Should be rejected because cumulative bytes exceed limit
            assert response.status_code == status.HTTP_413_CONTENT_TOO_LARGE

            # Verify temp files cleaned up
            temp_files = list(temp_dir.glob("*.csv*"))
            assert len(temp_files) == 0, f"Temp files not cleaned up: {temp_files}"
        finally:
            csv_path.unlink(missing_ok=True)

    async def test_file_size_provided_by_client_works(
        self,
        async_client: AsyncClient,
        auth_headers_for_streaming: dict[str, str],
        async_db_session,
        test_user_for_streaming: dict,
        test_dashboard: Dashboard,
    ) -> None:
        """file.size provided by client still works correctly.

        When Content-Length header IS provided (file.size is set),
        the pre-stream size check should reject oversized files before streaming starts.
        This is the fast-path check that avoids unnecessary I/O.
        """
        # Grant edit access to test user
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=test_user_for_streaming["id"],
            dashboard_id=test_dashboard.id,
            permission=DashboardPermission.EDIT,
        )
        await async_db_session.commit()

        temp_dir = Path(tempfile.gettempdir()) / "mkobi_size_provided_test"
        temp_dir.mkdir(parents=True, exist_ok=True)

        mock_config = type(
            "MockConfig",
            (),
            {
                "max_file_size": 1,  # Very small limit
                "upload": type("MockUpload", (), {"max_file_size_mb": 100})(),
                "upload_temp_dir": str(temp_dir),
                "rate_limiter_fail_closed": False,
            },
        )()

        csv_content = b"category,sales\nA,100\nB,200\nC,300\n"

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            csv_path = Path(f.name)

        try:
            # httpx sends Content-Length by default for files opened from disk,
            # so file.size should be set and pre-check should trigger
            with patch("mkobi.api.routes.upload.get_config", return_value=mock_config):
                with open(csv_path, "rb") as f:
                    response = await async_client.post(
                        f"/upload/{test_dashboard.id}",
                        headers=auth_headers_for_streaming,
                        files={"file": ("with_size.csv", f, "text/csv")},
                    )

            # Should be rejected - either by pre-check or streaming check
            assert response.status_code == status.HTTP_413_CONTENT_TOO_LARGE
        finally:
            csv_path.unlink(missing_ok=True)