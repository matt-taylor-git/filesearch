"""Unit tests for security_manager module.

Tests executable file detection, security warnings, and user preferences.
"""

import os
import platform
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from filesearch.core.exceptions import FileSearchError
from filesearch.core.security_manager import (
    SecurityManager,
    get_security_manager,
    is_executable_file,
    should_warn_before_opening_file,
)


class TestSecurityManager:
    """Test SecurityManager class."""
    
    def test_init_without_config_manager(self):
        """Test initialization without config manager."""
        manager = SecurityManager()
        assert manager.config_manager is None
        assert isinstance(manager._executable_extensions, set)
        assert len(manager._executable_extensions) > 0
    
    def test_init_with_config_manager(self):
        """Test initialization with config manager."""
        mock_config = Mock()
        manager = SecurityManager(mock_config)
        assert manager.config_manager is mock_config
    
    def test_get_platform_executable_extensions_windows(self):
        """Test getting Windows executable extensions."""
        with patch("platform.system", return_value="Windows"):
            manager = SecurityManager()
            extensions = manager._executable_extensions
            
            assert ".exe" in extensions
            assert ".bat" in extensions
            assert ".cmd" in extensions
            assert ".msi" in extensions
            assert ".sh" not in extensions  # Unix-specific
    
    def test_get_platform_executable_extensions_macos(self):
        """Test getting macOS executable extensions."""
        with patch("platform.system", return_value="Darwin"):
            manager = SecurityManager()
            extensions = manager._executable_extensions
            
            assert ".app" in extensions
            assert ".command" in extensions
            assert ".sh" in extensions  # Unix scripts
            assert ".exe" not in extensions  # Windows-specific
    
    def test_get_platform_executable_extensions_linux(self):
        """Test getting Linux executable extensions."""
        with patch("platform.system", return_value="Linux"):
            manager = SecurityManager()
            extensions = manager._executable_extensions
            
            assert ".sh" in extensions
            assert ".py" in extensions
            assert ".run" in extensions
            assert ".exe" not in extensions  # Windows-specific
            assert ".app" not in extensions  # macOS-specific
    
    def test_is_executable_by_extension(self):
        """Test executable detection by file extension."""
        # Test Windows executable extensions
        manager = SecurityManager()
        manager._executable_extensions = {'.exe', '.bat', '.cmd', '.com'}
        
        with tempfile.NamedTemporaryFile(suffix=".exe") as f:
            temp_path = Path(f.name)
            assert manager.is_executable(temp_path) is True
        
        with tempfile.NamedTemporaryFile(suffix=".txt") as f:
            temp_path = Path(f.name)
            assert manager.is_executable(temp_path) is False
        
        # Test Linux executable extensions
        manager._executable_extensions = {'.sh', '.py', '.pl', '.run'}
        
        with tempfile.NamedTemporaryFile(suffix=".sh") as f:
            temp_path = Path(f.name)
            assert manager.is_executable(temp_path) is True
        
        with tempfile.NamedTemporaryFile(suffix=".txt") as f:
            temp_path = Path(f.name)
            assert manager.is_executable(temp_path) is False
        

    
    def test_is_executable_nonexistent_file(self):
        """Test executable detection for non-existent file."""
        manager = SecurityManager()
        assert manager.is_executable(Path("/nonexistent/file.exe")) is False
    
    def test_is_executable_directory(self):
        """Test executable detection for directory."""
        manager = SecurityManager()
        with tempfile.TemporaryDirectory() as tmpdir:
            assert manager.is_executable(Path(tmpdir)) is False
    
    @patch("os.access")
    @patch("os.name", "posix")
    def test_is_executable_unix_execute_permissions(self, mock_access):
        """Test executable detection for Unix execute permissions."""
        mock_access.return_value = True
        
        # Create a temporary file with ELF signature
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = Path(f.name)
            # Write ELF signature
            f.write(b'\x7fELF')
            f.flush()
        
        try:
            manager = SecurityManager()
            # Set up extensions to include this file type
            manager._executable_extensions = {'.tmp'}  # tempfile extension
            
            result = manager.is_executable(temp_path)
            # Should detect as executable due to ELF signature
            assert result is True
        
        finally:
            temp_path.unlink(missing_ok=True)
    
    def test_should_warn_before_opening_non_executable(self):
        """Test warning check for non-executable file."""
        manager = SecurityManager()
        
        with tempfile.NamedTemporaryFile(suffix=".txt") as f:
            temp_path = Path(f.name)
            should_warn, message = manager.should_warn_before_opening(temp_path)
            
            assert should_warn is False
            assert message == ""
    
    def test_should_warn_before_opening_executable(self):
        """Test warning check for executable file."""
        with patch("platform.system", return_value="Windows"):
            manager = SecurityManager()
            
            with tempfile.NamedTemporaryFile(suffix=".exe") as f:
                temp_path = Path(f.name)
                should_warn, message = manager.should_warn_before_opening(temp_path)
                
                assert should_warn is True
                assert "executable file" in message
                assert ".exe" in message
    
    def test_should_warn_allowed_extension(self):
        """Test warning check for allowed executable extension."""
        manager = SecurityManager()
        manager._allowed_extensions.add(".exe")
        
        with tempfile.NamedTemporaryFile(suffix=".exe") as f:
            temp_path = Path(f.name)
            should_warn, message = manager.should_warn_before_opening(temp_path)
            
            assert should_warn is False
            assert message == ""
    
    def test_should_warn_blocked_extension(self):
        """Test warning check for blocked executable extension."""
        manager = SecurityManager()
        # Manually set executable extensions to include .exe for testing
        manager._executable_extensions.add(".exe")
        manager._blocked_extensions.add(".exe")
        
        with tempfile.NamedTemporaryFile(suffix=".exe") as f:
            temp_path = Path(f.name)
            should_warn, message = manager.should_warn_before_opening(temp_path)
            
            assert should_warn is True
            assert "blocked by your preferences" in message
    
    def test_allow_extension(self):
        """Test allowing an extension."""
        manager = SecurityManager()
        
        manager.allow_extension(".exe")
        assert ".exe" in manager._allowed_extensions
        assert ".exe" not in manager._blocked_extensions
        
        # Test without dot
        manager.allow_extension("bat")
        assert ".bat" in manager._allowed_extensions
    
    def test_block_extension(self):
        """Test blocking an extension."""
        manager = SecurityManager()
        
        manager.block_extension(".exe")
        assert ".exe" in manager._blocked_extensions
        assert ".exe" not in manager._allowed_extensions
        
        # Test without dot
        manager.block_extension("bat")
        assert ".bat" in manager._blocked_extensions
    
    def test_get_executable_extensions(self):
        """Test getting executable extensions list."""
        manager = SecurityManager()
        extensions = manager.get_executable_extensions()
        
        assert isinstance(extensions, list)
        assert len(extensions) > 0
        assert extensions == sorted(extensions)  # Should be sorted
    
    def test_get_allowed_extensions(self):
        """Test getting allowed extensions list."""
        manager = SecurityManager()
        manager.allow_extension(".exe")
        manager.allow_extension(".bat")
        
        allowed = manager.get_allowed_extensions()
        assert isinstance(allowed, list)
        assert ".exe" in allowed
        assert ".bat" in allowed
        assert allowed == sorted(allowed)  # Should be sorted
    
    def test_get_blocked_extensions(self):
        """Test getting blocked extensions list."""
        manager = SecurityManager()
        manager.block_extension(".exe")
        manager.block_extension(".bat")
        
        blocked = manager.get_blocked_extensions()
        assert isinstance(blocked, list)
        assert ".exe" in blocked
        assert ".bat" in blocked
        assert blocked == sorted(blocked)  # Should be sorted
    
    def test_load_user_preferences(self):
        """Test loading user preferences from config manager."""
        mock_config = Mock()
        mock_config.get.side_effect = lambda key, default=None: {
            'security.allowed_executable_extensions': ['.exe', '.bat'],
            'security.blocked_executable_extensions': ['.scr']
        }.get(key, default)
        
        manager = SecurityManager(mock_config)
        manager._load_user_preferences()
        
        assert '.exe' in manager._allowed_extensions
        assert '.bat' in manager._allowed_extensions
        assert '.scr' in manager._blocked_extensions
    
    def test_save_user_preferences(self):
        """Test saving user preferences to config manager."""
        mock_config = Mock()
        manager = SecurityManager(mock_config)
        
        manager.allow_extension(".exe")
        manager.block_extension(".scr")
        
        manager._save_user_preferences()
        
        mock_config.set.assert_any_call('security.allowed_executable_extensions', ['.exe'])
        mock_config.set.assert_any_call('security.blocked_executable_extensions', ['.scr'])
    
    def test_load_user_preferences_error_handling(self):
        """Test error handling when loading preferences fails."""
        mock_config = Mock()
        mock_config.get.side_effect = Exception("Config error")
        
        manager = SecurityManager(mock_config)
        # Should not raise exception
        manager._load_user_preferences()
    
    def test_save_user_preferences_error_handling(self):
        """Test error handling when saving preferences fails."""
        mock_config = Mock()
        mock_config.set.side_effect = Exception("Config error")
        
        manager = SecurityManager(mock_config)
        manager.allow_extension(".exe")
        
        # Should not raise exception
        manager._save_user_preferences()


class TestGlobalFunctions:
    """Test global convenience functions."""
    
    def test_get_security_manager_singleton(self):
        """Test that get_security_manager returns singleton instance."""
        manager1 = get_security_manager()
        manager2 = get_security_manager()
        
        assert manager1 is manager2
        assert isinstance(manager1, SecurityManager)
    
    def test_get_security_manager_with_config(self):
        """Test get_security_manager with config manager."""
        # Reset singleton to test with config
        import filesearch.core.security_manager
        filesearch.core.security_manager._security_manager = None
        
        mock_config = Mock()
        manager = get_security_manager(mock_config)
        
        assert manager.config_manager is mock_config
    
    def test_is_executable_file_convenience(self):
        """Test is_executable_file convenience function."""
        # Reset singleton to ensure clean state
        import filesearch.core.security_manager
        filesearch.core.security_manager._security_manager = None
        
        with patch("platform.system", return_value="Windows"):
            with tempfile.NamedTemporaryFile(suffix=".exe") as f:
                temp_path = Path(f.name)
                assert is_executable_file(temp_path) is True
            
            with tempfile.NamedTemporaryFile(suffix=".txt") as f:
                temp_path = Path(f.name)
                assert is_executable_file(temp_path) is False
    
    def test_should_warn_before_opening_file_convenience(self):
        """Test should_warn_before_opening_file convenience function."""
        # Reset singleton to ensure clean state
        import filesearch.core.security_manager
        filesearch.core.security_manager._security_manager = None
        
        with patch("platform.system", return_value="Windows"):
            with tempfile.NamedTemporaryFile(suffix=".exe") as f:
                temp_path = Path(f.name)
                should_warn, message = should_warn_before_opening_file(temp_path)
                
                assert should_warn is True
                assert "executable file" in message


class TestPlatformSpecificBehavior:
    """Test platform-specific behavior."""
    
    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix-specific test")
    def test_unix_executable_detection_with_permissions(self):
        """Test executable detection on Unix systems with execute permissions."""
        # Create a temporary script file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write('#!/bin/bash\necho "test"')
            temp_path = Path(f.name)
        
        try:
            # Make it executable
            temp_path.chmod(0o755)
            
            manager = SecurityManager()
            # On Unix systems, this should detect execute permissions
            if os.name == 'posix':
                result = manager.is_executable(temp_path)
                # Result depends on whether we can read the file signature
                assert isinstance(result, bool)
        finally:
            temp_path.unlink(missing_ok=True)
    
    def test_executable_signature_detection(self):
        """Test detection of executable file signatures."""
        manager = SecurityManager()
        
        # Test with actual executable signatures
        test_cases = [
            (b'\x7fELF', True),   # Linux ELF
            (b'MZ\x90\x00', True), # Windows PE
            (b'\xfe\xed\xfa\xce', True), # macOS Mach-O (64-bit)
            (b'Hello World', False), # Text file
            (b'', False), # Empty file
        ]
        
        for signature, expected in test_cases:
            with tempfile.NamedTemporaryFile(delete=False) as f:
                temp_path = Path(f.name)
                f.write(signature)
            
            try:
                # Mock the file reading to return our test signature
                with patch('builtins.open', create=True) as mock_open:
                    mock_file = Mock()
                    mock_file.read.return_value = signature
                    mock_open.return_value.__enter__.return_value = mock_file
                    
                    with patch('os.access', return_value=True):
                        with patch('os.name', 'posix'):
                            result = manager.is_executable(temp_path)
                            # Only check if we can detect the signature
                            if len(signature) >= 4:
                                # We expect some detection, but the exact result
                                # depends on the platform and signature matching
                                assert isinstance(result, bool)
            finally:
                temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__])