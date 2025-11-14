"""Unit tests for the file utilities module."""

import os
import platform
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from filesearch.core.exceptions import FileSearchError
from filesearch.core.file_utils import (
    get_file_info,
    get_file_modified_time,
    get_file_size,
    is_directory,
    open_containing_folder,
    safe_open,
)


class TestGetFileInfo:
    """Test cases for get_file_info function."""

    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)

        yield temp_path

        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_get_file_info_for_file(self, temp_file):
        """Test getting file info for a regular file."""
        info = get_file_info(temp_file)

        assert info["path"] == str(temp_file.resolve())
        assert info["name"] == temp_file.name
        assert info["size"] == len("test content")
        assert isinstance(info["modified"], float)
        assert info["type"] == ".txt"
        assert info["is_directory"] is False

    def test_get_file_info_for_directory(self, tmpdir):
        """Test getting file info for a directory."""
        info = get_file_info(Path(tmpdir))

        assert info["path"] == str(Path(tmpdir).resolve())
        assert info["name"] == Path(tmpdir).name
        assert info["size"] >= 0  # Directory size varies by OS
        assert isinstance(info["modified"], float)
        assert info["type"] == "directory"
        assert info["is_directory"] is True

    def test_get_file_info_nonexistent_path(self):
        """Test getting file info for non-existent path."""
        with pytest.raises(FileSearchError, match="File does not exist"):
            get_file_info("/nonexistent/path/file.txt")

    def test_get_file_info_with_string_path(self, temp_file):
        """Test getting file info with string path."""
        info = get_file_info(str(temp_file))

        assert info["path"] == str(temp_file.resolve())
        assert info["name"] == temp_file.name

    def test_get_file_info_unicode_filename(self):
        """Test getting file info for file with Unicode name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            unicode_file = Path(tmpdir) / "测试文件.txt"
            unicode_file.write_text("Unicode content")

            info = get_file_info(unicode_file)

            assert info["name"] == "测试文件.txt"
            assert info["type"] == ".txt"
            assert info["is_directory"] is False


class TestSafeOpen:
    """Test cases for safe_open function."""

    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)

        yield temp_path

        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    def test_safe_open_file_not_found(self):
        """Test opening non-existent file."""
        with pytest.raises(FileSearchError, match="File does not exist"):
            safe_open("/nonexistent/file.txt")

    def test_safe_open_directory(self, tmpdir):
        """Test opening a directory instead of file."""
        with pytest.raises(FileSearchError, match="Path is not a file"):
            safe_open(Path(tmpdir))

    @patch("platform.system")
    @patch("subprocess.run")
    def test_safe_open_linux(self, mock_run, mock_system, temp_file):
        """Test opening file on Linux."""
        mock_system.return_value = "Linux"
        mock_run.return_value = Mock()

        result = safe_open(temp_file)

        assert result is True
        mock_run.assert_called_once_with(["xdg-open", str(temp_file)], check=True)

    @patch("platform.system")
    @patch("subprocess.run")
    def test_safe_open_macos(self, mock_run, mock_system, temp_file):
        """Test opening file on macOS."""
        mock_system.return_value = "Darwin"
        mock_run.return_value = Mock()

        result = safe_open(temp_file)

        assert result is True
        mock_run.assert_called_once_with(["open", str(temp_file)], check=True)

    @patch("platform.system")
    def test_safe_open_windows(self, mock_system, temp_file):
        """Test opening file on Windows."""
        mock_system.return_value = "Windows"

        # Mock os.startfile for Windows
        with patch("os.startfile", create=True) as mock_startfile:
            result = safe_open(temp_file)

            assert result is True
            mock_startfile.assert_called_once_with(str(temp_file))

    @patch("subprocess.run")
    def test_safe_open_subprocess_error(self, mock_run, temp_file):
        """Test handling subprocess error."""
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, "xdg-open")

        with pytest.raises(FileSearchError, match="Failed to open file"):
            # Force Linux path for consistent testing
            with patch("platform.system", return_value="Linux"):
                safe_open(temp_file)


class TestOpenContainingFolder:
    """Test cases for open_containing_folder function."""

    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)

        yield temp_path

        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    def test_open_containing_folder_file_not_found(self):
        """Test opening folder for non-existent path."""
        with pytest.raises(FileSearchError, match="Path does not exist"):
            open_containing_folder("/nonexistent/path/file.txt")

    @patch("platform.system")
    @patch("subprocess.run")
    def test_open_containing_folder_linux_file(self, mock_run, mock_system, temp_file):
        """Test opening containing folder for file on Linux."""
        mock_system.return_value = "Linux"
        mock_run.return_value = Mock()

        result = open_containing_folder(temp_file)

        assert result is True
        mock_run.assert_called_once_with(
            ["xdg-open", str(temp_file.parent)], check=True
        )

    @patch("platform.system")
    @patch("subprocess.run")
    def test_open_containing_folder_linux_directory(
        self, mock_run, mock_system, tmpdir
    ):
        """Test opening directory on Linux."""
        mock_system.return_value = "Linux"
        mock_run.return_value = Mock()

        result = open_containing_folder(Path(tmpdir))

        assert result is True
        mock_run.assert_called_once_with(["xdg-open", str(Path(tmpdir))], check=True)

    @patch("platform.system")
    @patch("subprocess.run")
    def test_open_containing_folder_macos_file(self, mock_run, mock_system, temp_file):
        """Test opening containing folder for file on macOS."""
        mock_system.return_value = "Darwin"
        mock_run.return_value = Mock()

        result = open_containing_folder(temp_file)

        assert result is True
        mock_run.assert_called_once_with(["open", "-R", str(temp_file)], check=True)

    @patch("platform.system")
    def test_open_containing_folder_windows_file(self, mock_system, temp_file):
        """Test opening containing folder for file on Windows."""
        mock_system.return_value = "Windows"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock()

            result = open_containing_folder(temp_file)

            assert result is True
            mock_run.assert_called_once_with(
                ["explorer", "/select," + str(temp_file)], check=True
            )

    @patch("platform.system")
    def test_open_containing_folder_windows_directory(self, mock_system, tmpdir):
        """Test opening directory on Windows."""
        mock_system.return_value = "Windows"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock()

            result = open_containing_folder(Path(tmpdir))

            assert result is True
            mock_run.assert_called_once_with(
                ["explorer", str(Path(tmpdir))], check=True
            )


class TestConvenienceFunctions:
    """Test cases for convenience functions."""

    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test content for convenience functions")
            temp_path = Path(f.name)

        yield temp_path

        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    def test_get_file_size(self, temp_file):
        """Test getting file size."""
        size = get_file_size(temp_file)
        expected_size = len("test content for convenience functions")
        assert size == expected_size

    def test_get_file_modified_time(self, temp_file):
        """Test getting file modification time."""
        modified_time = get_file_modified_time(temp_file)
        assert isinstance(modified_time, float)
        assert modified_time > 0

    def test_is_directory_with_file(self, temp_file):
        """Test checking if path is directory (file case)."""
        assert is_directory(temp_file) is False

    def test_is_directory_with_directory(self, tmpdir):
        """Test checking if path is directory (directory case)."""
        assert is_directory(Path(tmpdir)) is True

    def test_convenience_functions_error_handling(self):
        """Test that convenience functions handle errors properly."""
        with pytest.raises(FileSearchError):
            get_file_size("/nonexistent/file.txt")

        with pytest.raises(FileSearchError):
            get_file_modified_time("/nonexistent/file.txt")

        with pytest.raises(FileSearchError):
            is_directory("/nonexistent/path")
