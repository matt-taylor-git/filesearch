"""Custom exception classes for File Search application.

This module defines the exception hierarchy for the File Search application.
All custom exceptions inherit from FileSearchError, allowing for consistent
error handling throughout the application.
"""

from typing import Optional, Any


class FileSearchError(Exception):
    """Base exception for all File Search application errors.
    
    This is the base class for all custom exceptions in the File Search
    application. It provides a consistent interface for error handling
    and logging.
    
    Args:
        message: Human-readable error message
        details: Additional error details (optional)
        cause: The underlying exception that caused this error (optional)
    """
    
    def __init__(self, message: str, details: Optional[Any] = None, 
                 cause: Optional[Exception] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details
        self.cause = cause
    
    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.details:
            return f"{self.message} (details: {self.details})"
        return self.message


class SearchError(FileSearchError):
    """Exception raised for errors during search operations.
    
    This exception is raised when search operations fail, such as:
    - Permission errors accessing directories
    - Invalid search patterns
    - Search provider failures
    
    Args:
        message: Human-readable error message
        path: The path that caused the error (optional)
        pattern: The search pattern that failed (optional)
        details: Additional error details (optional)
        cause: The underlying exception that caused this error (optional)
    """
    
    def __init__(self, message: str, path: Optional[str] = None,
                 pattern: Optional[str] = None, details: Optional[Any] = None,
                 cause: Optional[Exception] = None) -> None:
        super().__init__(message, details, cause)
        self.path = path
        self.pattern = pattern


class PluginError(FileSearchError):
    """Exception raised for plugin-related errors.
    
    This exception is raised when plugin operations fail, such as:
    - Plugin loading failures
    - Plugin initialization errors
    - Plugin execution errors
    - Missing plugin dependencies
    
    Args:
        message: Human-readable error message
        plugin_name: Name of the plugin that caused the error (optional)
        details: Additional error details (optional)
        cause: The underlying exception that caused this error (optional)
    """
    
    def __init__(self, message: str, plugin_name: Optional[str] = None,
                 details: Optional[Any] = None, 
                 cause: Optional[Exception] = None) -> None:
        super().__init__(message, details, cause)
        self.plugin_name = plugin_name


class ConfigError(FileSearchError):
    """Exception raised for configuration-related errors.
    
    This exception is raised when configuration operations fail, such as:
    - Invalid configuration files
    - Missing required configuration
    - Configuration validation errors
    - Configuration file access errors
    
    Args:
        message: Human-readable error message
        config_file: Path to the configuration file (optional)
        config_key: The configuration key that caused the error (optional)
        details: Additional error details (optional)
        cause: The underlying exception that caused this error (optional)
    """
    
    def __init__(self, message: str, config_file: Optional[str] = None,
                 config_key: Optional[str] = None, details: Optional[Any] = None,
                 cause: Optional[Exception] = None) -> None:
        super().__init__(message, details, cause)
        self.config_file = config_file
        self.config_key = config_key


class UIError(FileSearchError):
    """Exception raised for UI-related errors.
    
    This exception is raised when UI operations fail, such as:
    - UI component initialization errors
    - Event handling errors
    - Resource loading failures
    
    Args:
        message: Human-readable error message
        component: Name of the UI component that caused the error (optional)
        details: Additional error details (optional)
        cause: The underlying exception that caused this error (optional)
    """
    
    def __init__(self, message: str, component: Optional[str] = None,
                 details: Optional[Any] = None, 
                 cause: Optional[Exception] = None) -> None:
        super().__init__(message, details, cause)
        self.component = component


__all__ = [
    "FileSearchError",
    "SearchError", 
    "PluginError",
    "ConfigError",
    "UIError",
]