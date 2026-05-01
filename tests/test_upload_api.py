"""Тесты для API загрузки и обработки данных.

Тестирует эндпоинты загрузки файлов, запуска обработки и проверки статуса
через httpx.AsyncClient с реальным FastAPI стеком.
"""

import gzip
import pytest
from uuid import uuid4
from httpx import AsyncClient


class TestUploadFileEndpoint:
    """Тесты эндпоинта загрузки файла."""

    @pytest.mark.asyncio
    async def test_upload_file_success(self, authenticated_client: AsyncClient, test_user: dict):
        """Успешная загрузка файла."""
        dashboard_id = uuid4()

        # Создаем дашборд через API для получения реального ID
        dashboard_resp = await authenticated_client.post(
            "/dashboards/",
            json={"name": "Test Dashboard", "config": {"graph_types": ["bar"]}},
        )
        assert dashboard_resp.status_code == 201
        dashboard_id = dashboard_resp.json()["id"]

        # Загружаем файл (требуется .csv.gz)
        csv_content = b"col1,col2\n1,2\n3,4"
        gzipped_content = gzip.compress(csv_content)
        files = {"file": ("test_data.csv.gz", gzipped_content, "application/gzip")}
        response = await authenticated_client.post(
            f"/upload/{dashboard_id}",
            files=files,
        )

        assert response.status_code == 201
        data = response.json()
        assert "task_id" in data
        assert data["filename"] == "test_data.csv.gz"
        assert data["dashboard_id"] == dashboard_id

    @pytest.mark.asyncio
    async def test_upload_file_invalid_format(self, authenticated_client: AsyncClient, test_user: dict):
        """Ошибка при загрузке файла с недопустимым форматом."""
        dashboard_id = uuid4()

        # Создаем дашборд
        dashboard_resp = await authenticated_client.post(
            "/dashboards/",
            json={"name": "Test Dashboard 2", "config": {"graph_types": ["bar"]}},
        )
        assert dashboard_resp.status_code == 201
        dashboard_id = dashboard_resp.json()["id"]

        # Пытаемся загрузить файл с неправильным расширением
        files = {"file": ("test_data.txt", b"invalid content", "text/plain")}
        response = await authenticated_client.post(
            f"/upload/{dashboard_id}",
            files=files,
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_upload_file_no_auth(self):
        """Ошибка при загрузке файла без аутентификации."""
        dashboard_id = str(uuid4())
        files = {"file": ("test_data.csv", b"col1,col2\n1,2", "text/csv")}

        # Используем клиент без токена
        import httpx
        from httpx import ASGITransport
        from mko_bi.main import app

        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                f"/upload/{dashboard_id}",
                files=files,
            )

        assert response.status_code == 401


class TestGetStatusEndpoint:
    """Тесты эндпоинта получения статуса."""

    @pytest.mark.asyncio
    async def test_get_status_not_found(self, authenticated_client: AsyncClient):
        """Ошибка при получении статуса несуществующей задачи."""
        task_id = str(uuid4())
        response = await authenticated_client.get(f"/upload/status/{task_id}")

        assert response.status_code == 404


class TestGetResultEndpoint:
    """Тесты эндпоинта получения результата."""

    @pytest.mark.asyncio
    async def test_get_result_not_found(self, authenticated_client: AsyncClient):
        """Ошибка при получении результата несуществующей задачи."""
        task_id = str(uuid4())
        response = await authenticated_client.get(f"/upload/result/{task_id}")

        assert response.status_code == 404
