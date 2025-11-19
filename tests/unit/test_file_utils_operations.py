"""Unit tests for file operations (rename, delete, etc.)."""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from filesearch.core.exceptions import FileSearchError
from filesearch.core.file_utils import delete_file, rename_file, validate_filename


class TestRenameOperations:
    """Test cases for file renaming operations."""

    def test_validate_filename_valid(self):
        """Test validation of valid filenames."""
        assert validate_filename("test.txt") is None
        assert validate_filename("my_file 1.jpg") is None
        assert validate_filename("Archive.tar.gz") is None

    def test_validate_filename_invalid_empty(self):
        """Test validation of empty filenames."""
        assert validate_filename("") == "Filename cannot be empty"
        assert validate_filename("   ") == "Filename cannot be empty"

    def test_validate_filename_invalid_chars(self):
        """Test validation of filenames with invalid characters."""
        # On Unix, only / is invalid usually (and null byte)
        # But our implementation might enforce stricter rules or platform specific
        # We explicitly check for / in the code
        assert validate_filename("test/file") is not None

        # If on Windows, check for other chars
        import platform

        if platform.system() == "Windows":
            assert validate_filename("test:file") is not None
            assert validate_filename("test*file") is not None

    def test_validate_filename_dots(self):
        """Test validation of . and .."""
        assert validate_filename(".") == "Invalid filename"
        assert validate_filename("..") == "Invalid filename"

    def test_rename_file_success(self, tmp_path):
        """Test successful file rename."""
        original_file = tmp_path / "original.txt"
        original_file.write_text("content")

        new_name = "renamed.txt"
        new_path = rename_file(original_file, new_name)

        assert new_path.name == new_name
        assert new_path.exists()
        assert not original_file.exists()
        assert new_path.read_text() == "content"

    def test_rename_file_collision(self, tmp_path):
        """Test rename collision prevention."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("content1")

        file2 = tmp_path / "file2.txt"
        file2.write_text("content2")

        with pytest.raises(FileSearchError, match="already exists"):
            rename_file(file1, "file2.txt")

    def test_rename_file_invalid_name(self, tmp_path):
        """Test rename with invalid name."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("content")

        with pytest.raises(FileSearchError, match="Filename cannot be empty"):
            rename_file(file1, "")


class TestDeleteOperations:
    """Test cases for file deletion operations."""

    def test_delete_file_permanent(self, tmp_path):
        """Test permanent deletion."""
        file1 = tmp_path / "delete_me.txt"
        file1.write_text("bye")

        delete_file(file1, permanent=True)

        assert not file1.exists()

    def test_delete_directory_permanent(self, tmp_path):
        """Test permanent directory deletion."""
        dir1 = tmp_path / "delete_dir"
        dir1.mkdir()
        (dir1 / "file.txt").write_text("content")

        delete_file(dir1, permanent=True)

        assert not dir1.exists()

    @patch("send2trash.send2trash")
    def test_delete_file_trash(self, mock_send2trash, tmp_path):
        """Test moving to trash."""
        file1 = tmp_path / "trash_me.txt"
        file1.write_text("recycle")

        delete_file(file1, permanent=False)

        mock_send2trash.assert_called_once_with(file1)
        # Note: real send2trash would remove the file, but mock doesn't unless side_effect is set
        # So we just assert it was called

    def test_delete_nonexistent(self, tmp_path):
        """Test deleting non-existent file."""
        file1 = tmp_path / "ghost.txt"

        with pytest.raises(FileSearchError, match="Path does not exist"):
            delete_file(file1)
