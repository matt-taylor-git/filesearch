"""Unit tests for the main module.

This module tests the main application entry point and core functionality.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from filesearch import __version__, get_project_root, get_version
from filesearch.main import main, parse_arguments, setup_logging


class TestVersionInfo:
    """Test version information functions."""

    def test_version_constant(self):
        """Test version constant."""
        assert __version__ == "0.1.0"
        assert isinstance(__version__, str)

    def test_get_version(self):
        """Test get_version function."""
        version = get_version()
        assert version == "0.1.0"
        assert isinstance(version, str)

    def test_get_project_root(self):
        """Test get_project_root function."""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.is_absolute()
        # Should point to project root, not src directory
        assert (root / "src" / "filesearch").exists() or (root / "pyproject.toml").exists()


class TestArgumentParsing:
    """Test command-line argument parsing."""

    def test_parse_arguments_help(self):
        """Test --help argument."""
        with patch.object(sys, "argv", ["filesearch", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                parse_arguments()
            assert exc_info.value.code == 0

    def test_parse_arguments_version(self):
        """Test --version argument."""
        with patch.object(sys, "argv", ["filesearch", "--version"]):
            with pytest.raises(SystemExit) as exc_info:
                parse_arguments()
            assert exc_info.value.code == 0

    def test_parse_arguments_debug(self):
        """Test --debug argument."""
        with patch.object(sys, "argv", ["filesearch", "--debug"]):
            result = parse_arguments()
            assert result == "DEBUG"

    def test_parse_arguments_info(self):
        """Test --info argument."""
        with patch.object(sys, "argv", ["filesearch", "--info"]):
            result = parse_arguments()
            assert result == "INFO"

    def test_parse_arguments_warning(self):
        """Test --warning argument."""
        with patch.object(sys, "argv", ["filesearch", "--warning"]):
            result = parse_arguments()
            assert result == "WARNING"

    def test_parse_arguments_error(self):
        """Test --error argument."""
        with patch.object(sys, "argv", ["filesearch", "--error"]):
            result = parse_arguments()
            assert result == "ERROR"

    def test_parse_arguments_no_args(self):
        """Test no arguments."""
        with patch.object(sys, "argv", ["filesearch"]):
            result = parse_arguments()
            assert result is None

    def test_parse_arguments_unknown(self):
        """Test unknown argument."""
        with patch.object(sys, "argv", ["filesearch", "--unknown"]):
            with pytest.raises(SystemExit) as exc_info:
                parse_arguments()
            assert exc_info.value.code == 1

    def test_parse_arguments_short_help(self):
        """Test -h short help argument."""
        with patch.object(sys, "argv", ["filesearch", "-h"]):
            with pytest.raises(SystemExit) as exc_info:
                parse_arguments()
            assert exc_info.value.code == 0

    def test_parse_arguments_short_version(self):
        """Test -v short version argument."""
        with patch.object(sys, "argv", ["filesearch", "-v"]):
            with pytest.raises(SystemExit) as exc_info:
                parse_arguments()
            assert exc_info.value.code == 0


class TestLoggingSetup:
    """Test logging configuration."""

    def test_setup_logging_creates_log_directory(self, tmp_path):
        """Test that setup_logging creates log directory."""
        with patch("filesearch.main.get_project_root", return_value=tmp_path):
            setup_logging("INFO")
            log_dir = tmp_path / "logs"
            assert log_dir.exists()
            assert log_dir.is_dir()

    def test_setup_logging_info_level(self, tmp_path):
        """Test logging setup with INFO level."""
        with patch("filesearch.main.get_project_root", return_value=tmp_path):
            setup_logging("INFO")
            # Should not raise any exceptions

    def test_setup_logging_debug_level(self, tmp_path):
        """Test logging setup with DEBUG level."""
        with patch("filesearch.main.get_project_root", return_value=tmp_path):
            setup_logging("DEBUG")
            # Should not raise any exceptions

    def test_setup_logging_warning_level(self, tmp_path):
        """Test logging setup with WARNING level."""
        with patch("filesearch.main.get_project_root", return_value=tmp_path):
            setup_logging("WARNING")
            # Should not raise any exceptions

    def test_setup_logging_error_level(self, tmp_path):
        """Test logging setup with ERROR level."""
        with patch("filesearch.main.get_project_root", return_value=tmp_path):
            setup_logging("ERROR")
            # Should not raise any exceptions


class TestMainFunction:
    """Test the main application entry point."""

    def test_main_help(self):
        """Test main with --help argument."""
        with patch.object(sys, "argv", ["filesearch", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_main_version(self):
        """Test main with --version argument."""
        with patch.object(sys, "argv", ["filesearch", "--version"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_main_success(self, tmp_path):
        """Test successful main execution."""
        with patch.object(sys, "argv", ["filesearch"]):
            with patch("filesearch.main.get_project_root", return_value=tmp_path):
                result = main()
                assert result == 0

    def test_main_with_debug_logging(self, tmp_path):
        """Test main with debug logging."""
        with patch.object(sys, "argv", ["filesearch", "--debug"]):
            with patch("filesearch.main.get_project_root", return_value=tmp_path):
                result = main()
                assert result == 0

    def test_main_error_handling(self, tmp_path):
        """Test main error handling."""
        with patch.object(sys, "argv", ["filesearch"]):
            with patch("filesearch.main.get_project_root", return_value=tmp_path):
                with patch("filesearch.main.setup_logging", side_effect=Exception("Test error")):
                    result = main()
                    assert result == 1


class TestPathHandling:
    """Test cross-platform path handling."""

    def test_pathlib_usage_in_init(self):
        """Test that pathlib.Path is used in __init__.py."""
        from filesearch import get_project_root
        result = get_project_root()
        assert isinstance(result, Path)

    def test_pathlib_usage_in_main(self):
        """Test that pathlib.Path is used in main.py."""
        from filesearch.main import setup_logging
        # The function should use pathlib internally
        # This test ensures no ImportError occurs

    def test_cross_platform_path_compatibility(self):
        """Test path operations work cross-platform."""
        root = get_project_root()
        # These operations should work on all platforms
        src_path = root / "src" / "filesearch"
        assert isinstance(src_path, Path)
        # Path should handle separators correctly
        str_path = str(src_path)
        assert isinstance(str_path, str)
