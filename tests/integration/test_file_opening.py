"""Integration tests for file opening functionality.

Tests the complete workflow from UI interaction to file opening,
including security warnings and error handling.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PyQt6.QtCore import QModelIndex, Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest

from filesearch.core.config_manager import ConfigManager
from filesearch.core.file_utils import safe_open
from filesearch.core.security_manager import SecurityManager
from filesearch.models.search_result import SearchResult
from filesearch.ui.main_window import MainWindow
from filesearch.ui.results_view import ResultsView


class TestFileOpeningIntegration:
    """Integration tests for file opening workflow."""

    def test_double_click_triggers_file_open(self, tmp_path):
        """Test that double-clicking a result triggers file opening."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        
        # Create search result
        result = SearchResult(
            path=test_file,
            size=test_file.stat().st_size,
            modified=test_file.stat().st_mtime
        )
        
        # Create UI components
        app = QApplication([])
        results_view = ResultsView()
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

    def test_enter_key_triggers_file_open(self, tmp_path):
        """Test that Enter key triggers file opening."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        
        # Create search result
        result = SearchResult(
            path=test_file,
            size=test_file.stat().st_size,
            modified=test_file.stat().st_mtime
        )
        
        # Create UI components
        app = QApplication([])
        results_view = ResultsView()
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

    def test_double_click_disabled_during_search(self, tmp_path):
        """Test that double-click is disabled during search."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        
        # Create search result
        result = SearchResult(
            path=test_file,
            size=test_file.stat().st_size,
            modified=test_file.stat().st_mtime
        )
        
        # Create UI components
        app = QApplication([])
        results_view = ResultsView()
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

    def test_executable_warning_shows_dialog(self, tmp_path):
        """Test that executable files show security warning."""
        # Create test executable file
        test_file = tmp_path / "test.exe"
        test_file.write_text("fake executable")
        
        # Create search result
        result = SearchResult(
            path=test_file,
            size=test_file.stat().st_size,
            modified=test_file.stat().st_mtime
        )
        
        # Create main window with config
        config_manager = ConfigManager()
        main_window = MainWindow(config_manager)
        
        # Mock the warning dialog to capture user choice
        with patch('PyQt6.QtWidgets.QMessageBox.exec') as mock_exec:
            mock_exec.return_value = 1041  # QMessageBox.Open
            
            # Trigger file open request
            main_window._on_file_open_requested(result)
            
            # Verify dialog was shown
            mock_exec.assert_called_once()

    def test_non_executable_opens_directly(self, tmp_path):
        """Test that non-executable files open without warning."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        
        # Create search result
        result = SearchResult(
            path=test_file,
            size=test_file.stat().st_size,
            modified=test_file.stat().st_mtime
        )
        
        # Create main window with config
        config_manager = ConfigManager()
        main_window = MainWindow(config_manager)
        
        # Mock safe_open to track calls
        with patch('filesearch.ui.main_window.safe_open') as mock_safe_open:
            mock_safe_open.return_value = True
            
            # Trigger file open request
            main_window._on_file_open_requested(result)
            
            # Verify file was opened directly
            mock_safe_open.assert_called_once_with(test_file)

    def test_error_handling_shows_fallback_dialog(self, tmp_path):
        """Test that file opening errors show fallback dialog."""
        # Create search result for non-existent file
        test_file = tmp_path / "nonexistent.txt"
        result = SearchResult(
            path=test_file,
            query="test",
            relevance_score=1.0
        )
        
        # Create main window with config
        config_manager = ConfigManager()
        main_window = MainWindow(config_manager)
        
        # Mock safe_open to raise error
        with patch('filesearch.ui.main_window.safe_open') as mock_safe_open:
            from filesearch.core.exceptions import FileSearchError
            mock_safe_open.side_effect = FileSearchError("File does not exist")
            
            # Mock the fallback dialog
            with patch('PyQt6.QtWidgets.QMessageBox.question') as mock_question:
                mock_question.return_value = 16384  # QMessageBox.Yes
                
                # Trigger file open request
                main_window._on_file_open_requested(result)
                
                # Verify fallback dialog was shown
                mock_question.assert_called_once()

    def test_recent_file_added_to_config(self, tmp_path):
        """Test that opened files are added to recent list."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        
        # Create search result
        result = SearchResult(
            path=test_file,
            size=test_file.stat().st_size,
            modified=test_file.stat().st_mtime
        )
        
        # Create main window with config
        config_manager = ConfigManager()
        main_window = MainWindow(config_manager)
        
        # Mock safe_open to succeed
        with patch('filesearch.ui.main_window.safe_open') as mock_safe_open:
            mock_safe_open.return_value = True
            
            # Trigger file open request
            main_window._on_file_open_requested(result)
            
            # Verify file was added to recent list
            recent_files = config_manager.get_recent_files()
            assert test_file in recent_files

    def test_always_allow_preference_saved(self, tmp_path):
        """Test that 'always allow' preferences are saved."""
        # Create test executable file
        test_file = tmp_path / "test.exe"
        test_file.write_text("fake executable")
        
        # Create search result
        result = SearchResult(
            path=test_file,
            size=test_file.stat().st_size,
            modified=test_file.stat().st_mtime
        )
        
        # Create main window with config
        config_manager = ConfigManager()
        main_window = MainWindow(config_manager)
        
        # Mock warning dialog with 'always allow' checked
        with patch('PyQt6.QtWidgets.QMessageBox.exec') as mock_exec:
            with patch('PyQt6.QtWidgets.QCheckBox.isChecked') as mock_checked:
                mock_checked.return_value = True
                mock_exec.return_value = 1041  # QMessageBox.Open
                
                # Trigger file open request
                main_window._on_file_open_requested(result)
                
                # Verify preference was saved
                allowed_extensions = config_manager.get("security.allowed_executable_extensions", [])
                assert ".exe" in allowed_extensions


class TestFileOpeningWithRealFiles:
    """Tests with actual file operations where possible."""

    def test_safe_open_text_file(self, tmp_path):
        """Test opening a text file with safe_open."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        
        # Test opening (should not raise exception)
        try:
            result = safe_open(test_file)
            assert result is True
        except Exception as e:
            pytest.fail(f"safe_open raised unexpected exception: {e}")

    def test_safe_open_nonexistent_file(self, tmp_path):
        """Test safe_open with non-existent file."""
        # Test opening non-existent file
        test_file = tmp_path / "nonexistent.txt"
        
        # Should raise FileSearchError
        with pytest.raises(Exception):  # FileSearchError or subclass
            safe_open(test_file)

    def test_security_manager_executable_detection(self, tmp_path):
        """Test executable file detection."""
        # Create security manager
        security_manager = SecurityManager()
        
        # Test with executable extension
        exe_file = tmp_path / "test.exe"
        exe_file.write_text("fake exe")
        assert security_manager.is_executable(exe_file) is True
        
        # Test with non-executable extension
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Hello, World!")
        assert security_manager.is_executable(txt_file) is False
        
        # Test with non-existent file
        non_existent = tmp_path / "nonexistent.exe"
        assert security_manager.is_executable(non_existent) is False

    def test_security_manager_warning_logic(self, tmp_path):
        """Test security warning logic."""
        # Create security manager
        security_manager = SecurityManager()
        
        # Create executable file
        exe_file = tmp_path / "test.exe"
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
        security_manager.allow_extension(".exe")
        should_warn, message = security_manager.should_warn_before_opening(exe_file)
        assert should_warn is False
        assert message == ""
        
        # Test blocked extension
        security_manager.block_extension(".exe")
        should_warn, message = security_manager.should_warn_before_opening(exe_file)
        assert should_warn is True
        assert "blocked by your preferences" in message.lower()


if __name__ == "__main__":
    pytest.main([__file__])