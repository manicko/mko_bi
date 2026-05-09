"""Tests for file upload API endpoints."""

import gzip
import tempfile
from pathlib import Path

import pytest
from fastapi import status
from httpx import AsyncClient

from mkobi.db.models.dashboard import Dashboard
from mkobi.db.repositories.access_repo import AccessRepository
from mkobi.db.repositories.dashboard_repo import DashboardRepository
import uuid
from mkobi.models.enums import DashboardPermission


class TestUploadCSV:
    """Tests for CSV file upload."""

    @pytest.fixture
    async def test_dashboard(self, async_db_session) -> Dashboard:
        """Create a test dashboard for upload tests."""
        repo = DashboardRepository()
        dashboard = await repo.create(
            db=async_db_session,
            name=f"test_upload_dashboard_{uuid.uuid4().hex[:8]}",
            description="Dashboard for upload tests",
        )
        # Commit the dashboard so the API can see it
        await async_db_session.commit()
        return dashboard

    @pytest.fixture
    def csv_content(self) -> bytes:
        """Sample CSV content."""
        return b"date,category,revenue\n2023-01-01,A,100.5\n2023-01-02,B,200.0\n"

    @pytest.fixture
    def csv_file(self, csv_content: bytes) -> Path:
        """Create a temporary CSV file."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            path = Path(f.name)
        yield path
        path.unlink(missing_ok=True)

    async def test_upload_csv_success(
        self,
        authenticated_client: AsyncClient,
        async_db_session,
        test_user: dict,
        test_dashboard: Dashboard,
        csv_file: Path,
    ) -> None:
        """Test successful CSV file upload."""
        # Grant edit access to test user
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=test_user["id"],
            dashboard_id=test_dashboard.id,
            permission=DashboardPermission.EDIT,
        )
        # Commit the access grant so the API can see it
        await async_db_session.commit()

        with open(csv_file, "rb") as f:
            response = await authenticated_client.post(
                f"/upload/{test_dashboard.id}",
                files={"file": ("test.csv", f, "text/csv")},
            )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "message" in data
        assert "processing_log_id" in data

    async def test_upload_csv_gz_success(
        self,
        authenticated_client: AsyncClient,
        async_db_session,
        test_user: dict,
        test_dashboard: Dashboard,
        csv_content: bytes,
    ) -> None:
        """Test successful CSV.gz file upload."""
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".csv.gz", delete=False
        ) as f:
            with gzip.GzipFile(fileobj=f, mode="wb") as gz:
                gz.write(csv_content)
            gz_path = Path(f.name)

        try:
            # Grant edit access to test user
            access_repo = AccessRepository()
            await access_repo.grant_access(
                db=async_db_session,
                user_id=test_user["id"],
                dashboard_id=test_dashboard.id,
                permission=DashboardPermission.EDIT,
            )
            # Commit the access grant so the API can see it
            await async_db_session.commit()

            with open(gz_path, "rb") as f:
                response = await authenticated_client.post(
                    f"/upload/{test_dashboard.id}",
                    files={"file": ("test.csv.gz", f, "application/gzip")},
                )
            assert response.status_code == status.HTTP_201_CREATED
        finally:
            gz_path.unlink(missing_ok=True)

    async def test_upload_wrong_extension(
        self,
        authenticated_client: AsyncClient,
        async_db_session,
        test_user: dict,
        test_dashboard: Dashboard,
    ) -> None:
        """Test upload with wrong file extension (should return 415)."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as f:
            f.write(b"some text")
            txt_path = Path(f.name)

        try:
            with open(txt_path, "rb") as f:
                response = await authenticated_client.post(
                    f"/upload/{test_dashboard.id}",
                    files={"file": ("test.txt", f, "text/plain")},
                )
            assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        finally:
            txt_path.unlink(missing_ok=True)

    async def test_upload_wrong_mime(
        self,
        authenticated_client: AsyncClient,
        async_db_session,
        test_user: dict,
        test_dashboard: Dashboard,
        csv_file: Path,
    ) -> None:
        """Test upload with wrong MIME type (should return 415)."""
        with open(csv_file, "rb") as f:
            response = await authenticated_client.post(
                f"/upload/{test_dashboard.id}",
                files={"file": ("test.csv", f, "application/octet-stream")},
            )
        assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE

    async def test_upload_too_large(
        self,
        authenticated_client: AsyncClient,
        async_db_session,
        test_user: dict,
        test_dashboard: Dashboard,
    ) -> None:
        """Test upload with file too large (should return 413)."""
        # Grant edit access to test user for this dashboard
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=test_user["id"],
            dashboard_id=test_dashboard.id,
            permission=DashboardPermission.EDIT,
        )
        await async_db_session.commit()

        # Create a file larger than max_file_size (default 100MB)
        # Using 101MB to exceed the limit
        large_content = b"x" * (101 * 1024 * 1024)  # 101MB

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as f:
            f.write(large_content)
            large_path = Path(f.name)

        try:
            with open(large_path, "rb") as f:
                response = await authenticated_client.post(
                    f"/upload/{test_dashboard.id}",
                    files={"file": ("large.csv", f, "text/csv")},
                )
            assert response.status_code == status.HTTP_413_CONTENT_TOO_LARGE
        finally:
            large_path.unlink(missing_ok=True)

    async def test_upload_no_permission(
        self,
        authenticated_client: AsyncClient,
        test_user: dict,
        test_dashboard: Dashboard,
        csv_file: Path,
    ) -> None:
        """Test upload without permission (should return 403)."""
        # Use authenticated_client but DO NOT grant access
        # This way, the API returns 403 Forbidden
        with open(csv_file, "rb") as f:
            response = await authenticated_client.post(
                f"/upload/{test_dashboard.id}",
                files={"file": ("test.csv", f, "text/csv")},
            )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_upload_mode_overwrite(
        self,
        authenticated_client: AsyncClient,
        async_db_session,
        test_user: dict,
        test_dashboard: Dashboard,
        csv_file: Path,
    ) -> None:
        """Test upload with overwrite mode."""
        # Grant edit access to test user
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=test_user["id"],
            dashboard_id=test_dashboard.id,
            permission=DashboardPermission.EDIT,
        )
        # Commit the access grant so the API can see it
        await async_db_session.commit()

        with open(csv_file, "rb") as f:
            response = await authenticated_client.post(
                f"/upload/{test_dashboard.id}?mode=overwrite",
                files={"file": ("test.csv", f, "text/csv")},
            )
        assert response.status_code == status.HTTP_201_CREATED

    async def test_upload_mode_append(
        self,
        authenticated_client: AsyncClient,
        async_db_session,
        test_user: dict,
        test_dashboard: Dashboard,
        csv_file: Path,
    ) -> None:
        """Test upload with append mode."""
        # Grant edit access to test user
        access_repo = AccessRepository()
        await access_repo.grant_access(
            db=async_db_session,
            user_id=test_user["id"],
            dashboard_id=test_dashboard.id,
            permission=DashboardPermission.EDIT,
        )
        # Commit the access grant so the API can see it
        await async_db_session.commit()

        with open(csv_file, "rb") as f:
            response = await authenticated_client.post(
                f"/upload/{test_dashboard.id}?mode=append",
                files={"file": ("test.csv", f, "text/csv")},
            )
        assert response.status_code == status.HTTP_201_CREATED

    async def test_upload_mode_invalid(
        self,
        authenticated_client: AsyncClient,
        test_dashboard: Dashboard,
        csv_file: Path,
    ) -> None:
        """Test upload with invalid mode (should return 422)."""
        with open(csv_file, "rb") as f:
            response = await authenticated_client.post(
                f"/upload/{test_dashboard.id}?mode=invalid",
                files={"file": ("test.csv", f, "text/csv")},
            )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
