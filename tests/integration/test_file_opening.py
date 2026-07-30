"""Integration tests for file opening functionality.

Tests the complete workflow from UI interaction to file opening,
including security warnings and error handling.
"""

import platform
from pathlib import Path
from typing import Any

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

import filesearch.core.security_manager
from filesearch.core.config_manager import ConfigManager
from filesearch.core.exceptions import FileSearchError
from filesearch.core.file_utils import safe_open
from filesearch.core.security_manager import SecurityManager
from filesearch.models.search_result import SearchResult
from filesearch.ui.main_window import MainWindow
from filesearch.ui.results_view import ResultsView


class TestFileOpeningIntegration:
    """Integration tests for file opening workflow."""

    EXECUTABLE_EXT = ".exe" if platform.system() == "Windows" else ".sh"

    @pytest.fixture(autouse=True)
    def reset_security_manager(self):
        """Reset singleton security manager between tests."""
        filesearch.core.security_manager._security_manager = None
        yield
        filesearch.core.security_manager._security_manager = None

    def test_double_click_triggers_file_open(
        self, tmp_path: Path, desktop_effects: Any, qtbot: Any
    ) -> None:
        """Test that double-clicking a result triggers file opening."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        # Create search result
        result = SearchResult(
            path=test_file,
            size=test_file.stat().st_size,
            modified=test_file.stat().st_mtime,
        )

        # Create UI components
        results_view = ResultsView(desktop_effects=desktop_effects)
        qtbot.addWidget(results_view)
        results_view.set_results([result])

        # Track file open requests
        file_opened = False

        def on_file_open(search_result):
            nonlocal file_opened
            if search_result.path == test_file:
                file_opened = True

        results_view.file_open_requested.connect(on_file_open)

        # Simulate double-click
        index = results_view.model().index(0, 0)
        results_view.doubleClicked.emit(index)

        # Verify file was opened
        assert file_opened

    def test_enter_key_triggers_file_open(
        self, tmp_path: Path, desktop_effects: Any, qtbot: Any
    ) -> None:
        """Test that Enter key triggers file opening."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        # Create search result
        result = SearchResult(
            path=test_file,
            size=test_file.stat().st_size,
            modified=test_file.stat().st_mtime,
        )

        # Create UI components
        results_view = ResultsView(desktop_effects=desktop_effects)
        qtbot.addWidget(results_view)
        results_view.set_results([result])

        # Track file open requests
        file_opened = False

        def on_file_open(search_result):
            nonlocal file_opened
            if search_result.path == test_file:
                file_opened = True

        results_view.file_open_requested.connect(on_file_open)

        # Select first item and simulate Enter key
        index = results_view.model().index(0, 0)
        results_view.setCurrentIndex(index)

        # Simulate Enter key press
        QTest.keyClick(results_view, Qt.Key.Key_Enter)

        # Verify file was opened
        assert file_opened

    def test_double_click_disabled_during_search(
        self, tmp_path: Path, desktop_effects: Any, qtbot: Any
    ) -> None:
        """Test that double-click is disabled during search."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        # Create search result
        result = SearchResult(
            path=test_file,
            size=test_file.stat().st_size,
            modified=test_file.stat().st_mtime,
        )

        # Create UI components
        results_view = ResultsView(desktop_effects=desktop_effects)
        qtbot.addWidget(results_view)
        results_view.set_results([result])

        # Set searching state
        results_view.set_search_active(True)

        # Track file open requests
        file_opened = False

        def on_file_open(search_result):
            nonlocal file_opened
            file_opened = True

        results_view.file_open_requested.connect(on_file_open)

        # Simulate double-click
        index = results_view.model().index(0, 0)
        results_view.doubleClicked.emit(index)

        # Verify file was NOT opened
        assert not file_opened

    def test_executable_warning_uses_runtime_boundary(
        self, tmp_path, application_runtime, desktop_effects, qtbot
    ):
        """Test that executable files show security warning."""
        # Create test executable file
        test_file = tmp_path / f"test{self.EXECUTABLE_EXT}"
        test_file.write_text("fake executable")

        # Create search result
        result = SearchResult(
            path=test_file,
            size=test_file.stat().st_size,
            modified=test_file.stat().st_mtime,
        )

        config_manager = ConfigManager(runtime=application_runtime, watch_config=False)
        main_window = MainWindow(config_manager, runtime=application_runtime)
        qtbot.addWidget(main_window)
        desktop_effects.executable_response = (True, False)

        main_window._on_file_open_requested(result)

        assert len(desktop_effects.executable_prompts) == 1
        assert desktop_effects.opened_files == [test_file]

    def test_always_allow_preference_saved(
        self, tmp_path, application_runtime, desktop_effects, qtbot
    ):
        """Test that 'always allow' preferences are saved."""
        # Create test executable file
        test_file = tmp_path / f"test{self.EXECUTABLE_EXT}"
        test_file.write_text("fake executable")

        # Create search result
        result = SearchResult(
            path=test_file,
            size=test_file.stat().st_size,
            modified=test_file.stat().st_mtime,
        )

        config_manager = ConfigManager(runtime=application_runtime, watch_config=False)
        main_window = MainWindow(config_manager, runtime=application_runtime)
        qtbot.addWidget(main_window)
        desktop_effects.executable_response = (True, True)

        main_window._on_file_open_requested(result)

        allowed_extensions = config_manager.get(
            "security.allowed_executable_extensions", []
        )
        assert self.EXECUTABLE_EXT in allowed_extensions


class TestFileOpeningWithRealFiles:
    """Tests with actual file operations where possible."""

    EXECUTABLE_EXT = ".exe" if platform.system() == "Windows" else ".sh"

    def test_safe_open_nonexistent_file(self, tmp_path):
        """Test safe_open with non-existent file."""
        # Test opening non-existent file
        test_file = tmp_path / "nonexistent.txt"

        # Should raise FileSearchError
        with pytest.raises(FileSearchError, match="File does not exist"):
            safe_open(test_file)

    def test_security_manager_executable_detection(self, tmp_path):
        """Test executable file detection."""
        # Create security manager
        security_manager = SecurityManager()

        # Test with executable extension
        exe_file = tmp_path / f"test{self.EXECUTABLE_EXT}"
        exe_file.write_text("fake exe")
        assert security_manager.is_executable(exe_file) is True

        # Test with non-executable extension
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Hello, World!")
        assert security_manager.is_executable(txt_file) is False

        # Test with non-existent file
        non_existent = tmp_path / f"nonexistent{self.EXECUTABLE_EXT}"
        assert security_manager.is_executable(non_existent) is False

    def test_security_manager_warning_logic(self, tmp_path):
        """Test security warning logic."""
        # Create security manager
        security_manager = SecurityManager()

        # Create executable file
        exe_file = tmp_path / f"test{self.EXECUTABLE_EXT}"
        exe_file.write_text("fake exe")

        # Should warn for executable
        should_warn, message = security_manager.should_warn_before_opening(exe_file)
        assert should_warn is True
        assert "executable file" in message.lower()

        # Should not warn for non-executable
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Hello, World!")
        should_warn, message = security_manager.should_warn_before_opening(txt_file)
        assert should_warn is False
        assert message == ""

        # Test allowed extension
        security_manager.allow_extension(self.EXECUTABLE_EXT)
        should_warn, message = security_manager.should_warn_before_opening(exe_file)
        assert should_warn is False
        assert message == ""

        # Test blocked extension
        security_manager.block_extension(self.EXECUTABLE_EXT)
        should_warn, message = security_manager.should_warn_before_opening(exe_file)
        assert should_warn is True
        assert "blocked by your preferences" in message.lower()


if __name__ == "__main__":
    pytest.main([__file__])
