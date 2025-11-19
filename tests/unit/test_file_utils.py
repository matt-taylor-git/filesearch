"""Unit tests for the file utilities module."""

import os
import platform
import subprocess
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
    normalize_path,
    open_containing_folder,
    reveal_file_in_folder,
    safe_open,
    validate_directory,
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
        assert int(info["size"]) >= 0  # Directory size varies by OS
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
    @patch("subprocess.Popen")
    @patch("PyQt6.QtGui.QDesktopServices.openUrl", return_value=False)
    def test_safe_open_linux(self, mock_open_url, mock_popen, mock_system, temp_file):
        """Test opening file on Linux."""
        mock_system.return_value = "Linux"
        mock_popen.return_value = Mock()

        result = safe_open(temp_file)

        assert result is True
        mock_popen.assert_called_once_with(
            ["xdg-open", str(temp_file)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    @patch("platform.system")
    @patch("subprocess.Popen")
    @patch("PyQt6.QtGui.QDesktopServices.openUrl", return_value=False)
    def test_safe_open_macos(self, mock_open_url, mock_popen, mock_system, temp_file):
        """Test opening file on macOS."""
        mock_system.return_value = "Darwin"
        mock_popen.return_value = Mock()

        result = safe_open(temp_file)

        assert result is True
        mock_popen.assert_called_once_with(
            ["open", str(temp_file)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    @patch("platform.system")
    @patch("PyQt6.QtGui.QDesktopServices.openUrl", return_value=False)
    def test_safe_open_windows(self, mock_open_url, mock_system, temp_file):
        """Test opening file on Windows."""
        mock_system.return_value = "Windows"

        # Mock os.startfile for Windows
        with patch("os.startfile", create=True) as mock_startfile:
            result = safe_open(temp_file)

            assert result is True
            mock_startfile.assert_called_once_with(str(temp_file))

    @patch("subprocess.Popen")
    @patch("PyQt6.QtGui.QDesktopServices.openUrl", return_value=False)
    def test_safe_open_subprocess_error(self, mock_open_url, mock_popen, temp_file):
        """Test handling subprocess error."""
        import subprocess

        mock_popen.side_effect = OSError("Failed to execute")

        with pytest.raises(FileSearchError, match="Failed to open file"):
            # Force Linux path for consistent testing
            with patch("platform.system", return_value="Linux"):
                safe_open(temp_file)


class TestRevealFileInFolder:
    """Test cases for reveal_file_in_folder function."""

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

    def test_alias_exists(self):
        """Test that open_containing_folder alias exists and works."""
        assert open_containing_folder is reveal_file_in_folder

    def test_reveal_file_not_found(self):
        """Test revealing non-existent path."""
        with pytest.raises(FileSearchError, match="Path does not exist"):
            reveal_file_in_folder("/nonexistent/path/file.txt")

    @patch("platform.system")
    @patch("shutil.which")
    @patch("subprocess.Popen")
    def test_reveal_file_linux_nautilus(
        self, mock_popen, mock_which, mock_system, temp_file
    ):
        """Test revealing file on Linux with nautilus."""
        mock_system.return_value = "Linux"
        mock_which.side_effect = (
            lambda x: "/usr/bin/nautilus" if x == "nautilus" else None
        )
        mock_popen.return_value = Mock()

        result = reveal_file_in_folder(temp_file)

        assert result is True
        mock_popen.assert_called_once_with(
            ["nautilus", "--select", str(temp_file)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    @patch("platform.system")
    @patch("shutil.which")
    @patch("subprocess.Popen")
    def test_reveal_file_linux_dolphin(
        self, mock_popen, mock_which, mock_system, temp_file
    ):
        """Test revealing file on Linux with dolphin."""
        mock_system.return_value = "Linux"
        mock_which.side_effect = (
            lambda x: "/usr/bin/dolphin" if x == "dolphin" else None
        )
        mock_popen.return_value = Mock()

        result = reveal_file_in_folder(temp_file)

        assert result is True
        mock_popen.assert_called_once_with(
            ["dolphin", "--select", str(temp_file)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    @patch("platform.system")
    @patch("shutil.which")
    @patch("subprocess.Popen")
    def test_reveal_file_linux_fallback(
        self, mock_popen, mock_which, mock_system, temp_file
    ):
        """Test revealing file on Linux fallback to xdg-open."""
        mock_system.return_value = "Linux"
        mock_which.return_value = None  # No specific file manager found
        mock_popen.return_value = Mock()

        result = reveal_file_in_folder(temp_file)

        assert result is True
        mock_popen.assert_called_once_with(
            ["xdg-open", str(temp_file.parent)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    @patch("platform.system")
    @patch("subprocess.Popen")
    def test_reveal_directory_linux(self, mock_popen, mock_system, tmpdir):
        """Test revealing directory on Linux (always xdg-open fallback logic)."""
        mock_system.return_value = "Linux"
        mock_popen.return_value = Mock()

        result = reveal_file_in_folder(Path(tmpdir))

        assert result is True
        # For directories, it falls through to the fallback logic
        mock_popen.assert_called_once_with(
            ["xdg-open", str(Path(tmpdir))],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    @patch("platform.system")
    @patch("subprocess.Popen")
    def test_reveal_file_macos(self, mock_popen, mock_system, temp_file):
        """Test revealing file on macOS."""
        mock_system.return_value = "Darwin"
        mock_popen.return_value = Mock()

        result = reveal_file_in_folder(temp_file)

        assert result is True
        mock_popen.assert_called_once_with(
            ["open", "-R", str(temp_file)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    @patch("platform.system")
    @patch("subprocess.Popen")
    def test_reveal_directory_macos(self, mock_popen, mock_system, tmpdir):
        """Test revealing directory on macOS."""
        mock_system.return_value = "Darwin"
        mock_popen.return_value = Mock()

        result = reveal_file_in_folder(Path(tmpdir))

        assert result is True
        mock_popen.assert_called_once_with(
            ["open", str(Path(tmpdir))],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    @patch("platform.system")
    def test_reveal_file_windows(self, mock_system, temp_file):
        """Test revealing file on Windows."""
        mock_system.return_value = "Windows"

        with patch("subprocess.Popen") as mock_popen:
            mock_popen.return_value = Mock()

            result = reveal_file_in_folder(temp_file)

            assert result is True
            mock_popen.assert_called_once_with(
                ["explorer", "/select,", str(temp_file)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

    @patch("platform.system")
    def test_reveal_directory_windows(self, mock_system, tmpdir):
        """Test revealing directory on Windows."""
        mock_system.return_value = "Windows"

        with patch("subprocess.Popen") as mock_popen:
            mock_popen.return_value = Mock()

            result = reveal_file_in_folder(Path(tmpdir))

            assert result is True
            mock_popen.assert_called_once_with(
                ["explorer", str(Path(tmpdir))],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
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


class TestPathNormalizationAndValidation:
    """Test cases for normalize_path and validate_directory functions."""

    @pytest.fixture(autouse=True)
    def setup_env(self, monkeypatch):
        """Set up environment variables for testing."""
        self.home_dir = Path.home()
        self.test_dir = self.home_dir / "test_dir_for_filesearch"
        self.test_dir.mkdir(exist_ok=True)
        self.test_file = self.test_dir / "test_file.txt"
        self.test_file.touch(exist_ok=True)

        # Mock environment variables
        monkeypatch.setenv("HOME", str(self.home_dir))
        monkeypatch.setenv("USERPROFILE", str(self.home_dir))
        monkeypatch.setenv("TEST_VAR", str(self.test_dir))

        # Ensure the test directory is readable
        os.chmod(self.test_dir, 0o755)

        yield

        # Cleanup
        if self.test_dir.exists():
            self.test_file.unlink(missing_ok=True)
            self.test_dir.rmdir()

    # --- normalize_path tests ---

    def test_normalize_path_tilde(self):
        """Test path normalization with '~' shortcut."""
        normalized = normalize_path("~")
        assert normalized == self.home_dir.resolve()

    def test_normalize_path_env_var_home(self):
        """Test path normalization with $HOME environment variable."""
        normalized = normalize_path("$HOME")
        assert normalized == self.home_dir.resolve()

    def test_normalize_path_env_var_custom(self):
        """Test path normalization with a custom environment variable."""
        normalized = normalize_path("$TEST_VAR")
        assert normalized == self.test_dir.resolve()

    def test_normalize_path_mixed_case_windows_env(self):
        """Test path normalization with %USERPROFILE% (Windows style)."""
        # On Linux/macOS, os.path.expandvars handles %VAR% as $VAR
        normalized = normalize_path("%USERPROFILE%")
        assert normalized == self.home_dir.resolve()

    def test_normalize_path_absolute(self):
        """Test path normalization for an already absolute path."""
        abs_path = self.test_dir.resolve()
        normalized = normalize_path(str(abs_path))
        assert normalized == abs_path

    def test_normalize_path_network_unc(self):
        """Test path normalization for UNC/network paths (AC #6.3)."""
        # Test cross-platform network path support
        network_path = "//server/share/folder"
        normalized = normalize_path(network_path)
        # pathlib.Path handles network paths cross-platform
        assert isinstance(normalized, Path)
        # Should normalize without error
        assert str(normalized).endswith("server/share/folder")

    # --- validate_directory tests ---

    def test_validate_directory_valid(self):
        """Test validation for a valid, existing, and readable directory."""
        error = validate_directory(self.test_dir.resolve())
        assert error is None

    def test_validate_directory_nonexistent(self):
        """Test validation for a non-existent path."""
        non_existent_path = self.test_dir / "non_existent_folder"
        error = validate_directory(non_existent_path)
        assert error == "Directory does not exist."

    def test_validate_directory_is_file(self):
        """Test validation for a path that is a file, not a directory."""
        error = validate_directory(self.test_file)
        assert error == "Path is not a directory."

    @pytest.mark.skipif(
        platform.system() == "Windows",
        reason="Permission tests are unreliable on Windows",
    )
    def test_validate_directory_permission_denied(self):
        """Test validation for a directory with no read permission."""
        # Create a temporary directory with no read permission
        temp_dir_path = self.test_dir / "no_read_perm"
        temp_dir_path.mkdir()

        # Remove read permission for the current user
        os.chmod(temp_dir_path, 0o300)  # Write/Execute only

        try:
            error = validate_directory(temp_dir_path)
            assert error == "Permission denied: Cannot read directory contents."
        finally:
            # Restore permissions for cleanup
            os.chmod(temp_dir_path, 0o755)
            temp_dir_path.rmdir()
