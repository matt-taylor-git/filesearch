"""File Search - A cross-platform file search application.

This package provides a fast, extensible file search application with a modern
GUI interface built using PyQt6. It supports plugin architecture for custom
search providers and result processors.

Version: 0.1.0
"""

__version__ = "0.1.0"
__author__ = "FileSearch Team"
__email__ = "team@filesearch.dev"
__description__ = "A cross-platform file search application with extensible plugin architecture"
__license__ = "MIT"

from pathlib import Path
from typing import Union


def get_project_root() -> Path:
    """Get the project root directory.
    
    Returns:
        Path: The absolute path to the project root directory.
    """
    return Path(__file__).parent.parent.parent


def get_version() -> str:
    """Get the current version of the application.
    
    Returns:
        str: The version string (e.g., "0.1.0").
    """
    return __version__


__all__ = [
    "__version__",
    "__author__", 
    "__description__",
    "get_project_root",
    "get_version",
]
