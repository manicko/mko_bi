"""Tests for file cleanup utilities."""
import os
import shutil
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from mkobi.services.file_cleanup import cleanup_stale_temp_files, cleanup_task_files


@pytest.fixture(autouse=True)
def setup_temp_dir_fixture(monkeypatch):
    """Set up a temporary directory for upload tests."""
    temp_dir = tempfile.mkdtemp()
    
    class MockConfig:
        upload_temp_dir = temp_dir
        stale_file_threshold_hours = 24
    
    def get_config_mock():
        return MockConfig()
    
    monkeypatch.setattr("mkobi.services.file_cleanup.get_config", get_config_mock)
    monkeypatch.setattr("mkobi.config.get_config", get_config_mock)
    
    yield temp_dir
    
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestFileCleanup:
    """Tests for file cleanup utilities."""

    def test_cleanup_task_files_deletes_matching_files(self, setup_temp_dir_fixture):
        """Test cleanup_task_files deletes files matching task ID."""
        temp_dir = setup_temp_dir_fixture
        task_id = uuid4()
        # Create test files
        for suffix in ["", ".gz"]:
            file_path = Path(temp_dir) / f"test_{task_id}{suffix}.csv"
            file_path.write_text("test,data\n1,2\n")

        # Create a file that should NOT be deleted
        other_id = uuid4()
        other_file = Path(temp_dir) / f"other_{other_id}.csv"
        other_file.write_text("other\n")

        cleanup_task_files(task_id)

        # Files with task_id should be deleted
        remaining_files = list(Path(temp_dir).glob(f"*{task_id}*.csv*"))
        assert len(remaining_files) == 0
        # Other files should remain
        assert other_file.exists()

    def test_cleanup_task_files_no_matching_files(self, setup_temp_dir_fixture):
        """Test cleanup_task_files with no matching files."""
        temp_dir = setup_temp_dir_fixture
        task_id = uuid4()
        # Create a file that doesn't match
        other_file = Path(temp_dir) / "other_file.csv"
        other_file.write_text("other\n")

        cleanup_task_files(task_id)

        # No crash, other file should still exist
        assert other_file.exists()

    def test_cleanup_stale_temp_files_deletes_old_files(self, setup_temp_dir_fixture):
        """Test cleanup_stale_temp_files deletes files older than threshold."""
        temp_dir = setup_temp_dir_fixture
        # Create a file
        old_file = Path(temp_dir) / "old_file.csv"
        old_file.write_text("old,data\n1,2\n")

        # Set mtime to 25 hours ago (older than default 24h threshold)
        old_time = time.time() - (25 * 3600)
        old_file.touch()
        os.utime(old_file, (old_time, old_time))

        # Create a recent file
        recent_file = Path(temp_dir) / "recent_file.csv"
        recent_file.write_text("recent\n")

        deleted_count = cleanup_stale_temp_files()

        assert deleted_count == 1
        assert not old_file.exists()
        assert recent_file.exists()

    def test_cleanup_stale_temp_files_custom_threshold(self, setup_temp_dir_fixture):
        """Test cleanup_stale_temp_files with custom threshold."""
        temp_dir = setup_temp_dir_fixture
        # Create a file 3 hours old
        file_path = Path(temp_dir) / "medium_file.csv"
        file_path.write_text("medium\n")
        old_time = time.time() - (3 * 3600)
        file_path.touch()
        os.utime(file_path, (old_time, old_time))

        # With 2 hour threshold, should be deleted
        deleted_count = cleanup_stale_temp_files(max_age_hours=2)
        assert deleted_count == 1

    def test_cleanup_stale_temp_files_keeps_recent_files(self, setup_temp_dir_fixture):
        """Test cleanup keeps recent files with 5 hour threshold."""
        temp_dir = setup_temp_dir_fixture
        # Create a fresh file that's 3 hours old
        file_path = Path(temp_dir) / "recent_file.csv"
        file_path.write_text("recent\n")
        old_time = time.time() - (3 * 3600)
        file_path.touch()
        os.utime(file_path, (old_time, old_time))

        # With 5 hour threshold, should NOT be deleted
        deleted_count = cleanup_stale_temp_files(max_age_hours=5)
        assert deleted_count == 0
        assert file_path.exists()

    def test_cleanup_stale_temp_files_nonexistent_directory(self, monkeypatch):
        """Test cleanup when upload directory doesn't exist."""
        monkeypatch.setattr(
            "mkobi.services.file_cleanup.get_config",
            lambda: MagicMock(upload_temp_dir="/nonexistent/path", stale_file_threshold_hours=24)
        )

        deleted_count = cleanup_stale_temp_files()
        assert deleted_count == 0

    def test_cleanup_stale_temp_files_invalid_threshold(self, monkeypatch):
        """Test cleanup with invalid threshold returns 0."""
        temp_dir = tempfile.mkdtemp()
        monkeypatch.setattr(
            "mkobi.services.file_cleanup.get_config",
            lambda: MagicMock(upload_temp_dir=temp_dir, stale_file_threshold_hours=24)
        )

        deleted_count = cleanup_stale_temp_files(max_age_hours=0)
        assert deleted_count == 0

        deleted_count = cleanup_stale_temp_files(max_age_hours=-1)
        assert deleted_count == 0
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)