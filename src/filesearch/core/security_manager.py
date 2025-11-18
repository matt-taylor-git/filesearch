"""Security manager for file opening operations.

This module provides security checks and warnings for potentially dangerous
file operations, particularly executable files.
"""

import os
from pathlib import Path
from typing import List, Optional, Set, Tuple

from loguru import logger

from filesearch.core.exceptions import FileSearchError


class SecurityManager:
    """Manages security checks for file operations.
    
    Provides executable file detection, security warnings, and user preference
    management for potentially dangerous file operations.
    """
    
    # Default executable file extensions by platform
    WINDOWS_EXECUTABLE_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.scr', '.msi', '.msp', '.msu',
        '.ps1', '.vbs', '.js', '.wsf', '.wsh'
    }
    
    UNIX_EXECUTABLE_EXTENSIONS = {
        '.sh', '.bash', '.zsh', '.csh', '.tcsh', '.ksh', '.py', '.pl',
        '.rb', '.php', '.run', '.bin'
    }
    
    MAC_EXECUTABLE_EXTENSIONS = {
        '.app', '.command', '.scpt', '.workflow', '.pkg', '.dmg',
        '.mpkg'
    }
    
    def __init__(self, config_manager=None):
        """Initialize the security manager.
        
        Args:
            config_manager: Optional config manager for user preferences
        """
        self.config_manager = config_manager
        self._executable_extensions = self._get_platform_executable_extensions()
        self._allowed_extensions: Set[str] = set()
        self._blocked_extensions: Set[str] = set()
        
        # Load user preferences if config manager is available
        if self.config_manager:
            self._load_user_preferences()
    
    def _get_platform_executable_extensions(self) -> Set[str]:
        """Get executable file extensions for the current platform.
        
        Returns:
            Set of executable file extensions for current platform
        """
        import platform
        
        system = platform.system()
        extensions = set()
        
        if system == "Windows":
            extensions.update(self.WINDOWS_EXECUTABLE_EXTENSIONS)
        elif system == "Darwin":  # macOS
            extensions.update(self.MAC_EXECUTABLE_EXTENSIONS)
            extensions.update(self.UNIX_EXECUTABLE_EXTENSIONS)
        else:  # Linux and other Unix-like
            extensions.update(self.UNIX_EXECUTABLE_EXTENSIONS)
        
        logger.debug(f"Platform {system} executable extensions: {sorted(extensions)}")
        return extensions
    
    def is_executable(self, path: Path) -> bool:
        """Check if a file is potentially executable.
        
        Args:
            path: Path to the file to check
            
        Returns:
            True if the file is potentially executable, False otherwise
        """
        try:
            if not path.exists() or not path.is_file():
                return False
            
            # Check file extension
            extension = path.suffix.lower()
            if extension in self._executable_extensions:
                return True
            
            # Check if file has execute permissions (Unix-like systems)
            if os.name == 'posix':  # Unix-like systems
                if os.access(path, os.X_OK):
                    # Additional check: make sure it's actually an executable
                    # and not just a data file with execute bits set
                    try:
                        # Read first few bytes to check for executable signatures
                        with open(path, 'rb') as f:
                            header = f.read(4)
                        
                        # Common executable signatures
                        elf_signatures = {b'\x7fELF'}  # Linux ELF
                        pe_signatures = {b'MZ\x90\x00', b'MZ'}  # Windows PE
                        mach_o_signatures = {b'\xfe\xed\xfa\xce', b'\xfe\xed\xfa\xcf', 
                                           b'\xce\xfa\xed\xfe', b'\xcf\xfa\xed\xfe'}  # macOS Mach-O
                        
                        if (header in elf_signatures or 
                            header in pe_signatures or 
                            header in mach_o_signatures):
                            return True
                    except (OSError, IOError):
                        pass
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking if file is executable {path}: {e}")
            return False
    
    def should_warn_before_opening(self, path: Path) -> Tuple[bool, str]:
        """Check if a warning should be shown before opening a file.
        
        Args:
            path: Path to the file to check
            
        Returns:
            Tuple of (should_warn, warning_message)
        """
        if not self.is_executable(path):
            return False, ""
        
        # Check user preferences
        extension = path.suffix.lower()
        
        if extension in self._allowed_extensions:
            logger.debug(f"Extension {extension} is in allowed list, no warning needed")
            return False, ""
        
        if extension in self._blocked_extensions:
            logger.debug(f"Extension {extension} is in blocked list")
            return True, f"This executable file type ({extension}) is blocked by your preferences."
        
        # Default warning for executable files
        return True, f"This is an executable file ({extension}). Open anyway?"
    
    def allow_extension(self, extension: str) -> None:
        """Add an extension to the allowed list.
        
        Args:
            extension: File extension to allow (e.g., '.exe')
        """
        extension = extension.lower()
        if not extension.startswith('.'):
            extension = '.' + extension
        
        self._allowed_extensions.add(extension)
        self._blocked_extensions.discard(extension)
        
        logger.info(f"Added extension {extension} to allowed list")
        
        # Save preference if config manager is available
        if self.config_manager:
            self._save_user_preferences()
    
    def block_extension(self, extension: str) -> None:
        """Add an extension to the blocked list.
        
        Args:
            extension: File extension to block (e.g., '.exe')
        """
        extension = extension.lower()
        if not extension.startswith('.'):
            extension = '.' + extension
        
        self._blocked_extensions.add(extension)
        self._allowed_extensions.discard(extension)
        
        logger.info(f"Added extension {extension} to blocked list")
        
        # Save preference if config manager is available
        if self.config_manager:
            self._save_user_preferences()
    
    def get_executable_extensions(self) -> List[str]:
        """Get list of executable file extensions for current platform.
        
        Returns:
            Sorted list of executable file extensions
        """
        return sorted(self._executable_extensions)
    
    def get_allowed_extensions(self) -> List[str]:
        """Get list of user-allowed executable extensions.
        
        Returns:
            Sorted list of allowed extensions
        """
        return sorted(self._allowed_extensions)
    
    def get_blocked_extensions(self) -> List[str]:
        """Get list of user-blocked executable extensions.
        
        Returns:
            Sorted list of blocked extensions
        """
        return sorted(self._blocked_extensions)
    
    def _load_user_preferences(self) -> None:
        """Load user preferences from config manager."""
        if not self.config_manager:
            return
        
        try:
            # Load allowed extensions
            allowed = self.config_manager.get('security.allowed_executable_extensions', [])
            self._allowed_extensions = set(allowed)
            
            # Load blocked extensions
            blocked = self.config_manager.get('security.blocked_executable_extensions', [])
            self._blocked_extensions = set(blocked)
            
            logger.debug(f"Loaded security preferences: allowed={len(self._allowed_extensions)}, blocked={len(self._blocked_extensions)}")
            
        except Exception as e:
            logger.warning(f"Failed to load security preferences: {e}")
    
    def _save_user_preferences(self) -> None:
        """Save user preferences to config manager."""
        if not self.config_manager:
            return
        
        try:
            # Save allowed extensions
            self.config_manager.set('security.allowed_executable_extensions', 
                                   list(self._allowed_extensions))
            
            # Save blocked extensions
            self.config_manager.set('security.blocked_executable_extensions', 
                                   list(self._blocked_extensions))
            
            logger.debug("Saved security preferences")
            
        except Exception as e:
            logger.warning(f"Failed to save security preferences: {e}")


# Global security manager instance
_security_manager: Optional[SecurityManager] = None


def get_security_manager(config_manager=None) -> SecurityManager:
    """Get the global security manager instance.
    
    Args:
        config_manager: Optional config manager for user preferences
        
    Returns:
        SecurityManager instance
    """
    global _security_manager
    
    if _security_manager is None:
        _security_manager = SecurityManager(config_manager)
    
    return _security_manager


def is_executable_file(path: Path) -> bool:
    """Convenience function to check if a file is executable.
    
    Args:
        path: Path to the file to check
        
    Returns:
        True if the file is potentially executable, False otherwise
    """
    security_manager = get_security_manager()
    return security_manager.is_executable(path)


def should_warn_before_opening_file(path: Path) -> Tuple[bool, str]:
    """Convenience function to check if a warning should be shown.
    
    Args:
        path: Path to the file to check
        
    Returns:
        Tuple of (should_warn, warning_message)
    """
    security_manager = get_security_manager()
    return security_manager.should_warn_before_opening(path)