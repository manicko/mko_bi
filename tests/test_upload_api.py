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
from mkobi.models.enums import DashboardPermission


class TestUploadCSV:
    """Tests for CSV file upload."""

    @pytest.fixture
    async def test_dashboard(self, async_db_session) -> Dashboard:
        """Create a test dashboard for upload tests."""
        repo = DashboardRepository()
        dashboard = await repo.create(
            db=async_db_session,
            name="test_upload_dashboard",
            description="Dashboard for upload tests",
        )
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
        """Test upload of file exceeding max size (should return 413)."""
        from mkobi.config import get_config

        config = get_config()
        max_size = config.max_file_size

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as f:
            f.write(b"x" * (max_size + 1))
            large_file = Path(f.name)

        try:
            with open(large_file, "rb") as f:
                response = await authenticated_client.post(
                    f"/upload/{test_dashboard.id}",
                    files={"file": ("large.csv", f, "text/csv")},
                )
            assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        finally:
            large_file.unlink(missing_ok=True)

    async def test_upload_no_permission(
        self,
        async_client: AsyncClient,
        test_dashboard: Dashboard,
        csv_file: Path,
    ) -> None:
        """Test upload without authentication (should return 401)."""
        with open(csv_file, "rb") as f:
            response = await async_client.post(
                f"/upload/{test_dashboard.id}",
                files={"file": ("test.csv", f, "text/csv")},
            )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
