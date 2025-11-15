"""File utilities module for file system operations.

This module provides utility functions for file information retrieval,
cross-platform file opening, and directory navigation.
"""

import os
import platform
import subprocess
from pathlib import Path
from typing import Dict, Optional, Union

from loguru import logger

from filesearch.core.exceptions import FileSearchError


def get_file_info(path: Union[str, Path]) -> Dict[str, Union[str, int, float]]:
    """Get comprehensive file information.

    Args:
        path: Path to the file

    Returns:
        Dictionary containing file information:
            - 'path': Full file path as string
            - 'name': File name
            - 'size': File size in bytes
            - 'modified': Modification timestamp
            - 'type': File extension or 'directory'
            - 'is_directory': Boolean indicating if path is directory

    Raises:
        FileSearchError: If file does not exist or cannot be accessed

    Example:
        >>> info = get_file_info("/path/to/file.txt")
        >>> print(f"Size: {info['size']} bytes")
    """
    try:
        file_path = Path(path)

        if not file_path.exists():
            raise FileSearchError(f"File does not exist: {path}")

        stat = file_path.stat()

        info = {
            "path": str(file_path.resolve()),
            "name": file_path.name,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "type": "directory" if file_path.is_dir() else file_path.suffix or "file",
            "is_directory": file_path.is_dir(),
        }

        logger.debug(f"File info retrieved for {path}: {info}")
        return info

    except OSError as e:
        logger.error(f"Error accessing file {path}: {e}")
        raise FileSearchError(f"Cannot access file {path}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error getting file info for {path}: {e}")
        raise FileSearchError(f"Error getting file info for {path}: {e}")


def safe_open(path: Union[str, Path]) -> bool:
    """Open a file with the system default application.

    Args:
        path: Path to the file to open

    Returns:
        True if file was opened successfully, False otherwise

    Raises:
        FileSearchError: If file does not exist or cannot be opened

    Note:
        Uses platform-specific methods:
        - Windows: os.startfile()
        - macOS: open command
        - Linux: xdg-open command

    Example:
        >>> success = safe_open("/path/to/document.pdf")
        >>> if success:
        ...     print("File opened successfully")
    """
    try:
        file_path = Path(path)

        if not file_path.exists():
            raise FileSearchError(f"File does not exist: {path}")

        if not file_path.is_file():
            raise FileSearchError(f"Path is not a file: {path}")

        system = platform.system()

        if system == "Windows":
            os.startfile(str(file_path))
            logger.info(f"Opened file with default application (Windows): {path}")

        elif system == "Darwin":  # macOS
            subprocess.run(["open", str(file_path)], check=True)
            logger.info(f"Opened file with default application (macOS): {path}")

        else:  # Linux and other Unix-like
            subprocess.run(["xdg-open", str(file_path)], check=True)
            logger.info(f"Opened file with default application (Linux): {path}")

        return True

    except FileNotFoundError:
        logger.error(f"File not found: {path}")
        raise FileSearchError(f"File not found: {path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to open file {path}: {e}")
        raise FileSearchError(f"Failed to open file {path}: {e}")
    except OSError as e:
        logger.error(f"OS error opening file {path}: {e}")
        raise FileSearchError(f"OS error opening file {path}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error opening file {path}: {e}")
        raise FileSearchError(f"Error opening file {path}: {e}")


def open_containing_folder(path: Union[str, Path]) -> bool:
    """Open the containing folder of a file in the file manager.

    Args:
        path: Path to a file or directory

    Returns:
        True if folder was opened successfully, False otherwise

    Raises:
        FileSearchError: If path does not exist or folder cannot be opened

    Note:
        Uses platform-specific methods:
        - Windows: explorer /select
        - macOS: open -R (reveals file in Finder)
        - Linux: xdg-open (opens directory)

    Example:
        >>> success = open_containing_folder("/path/to/file.txt")
        >>> if success:
        ...     print("Folder opened successfully")
    """
    try:
        file_path = Path(path)

        if not file_path.exists():
            raise FileSearchError(f"Path does not exist: {path}")

        # Get the containing directory
        if file_path.is_file():
            folder_path = file_path.parent
        else:
            folder_path = file_path

        system = platform.system()

        if system == "Windows":
            if file_path.is_file():
                # Try to select the file in Explorer
                subprocess.run(["explorer", "/select," + str(file_path)], check=True)
            else:
                subprocess.run(["explorer", str(folder_path)], check=True)
            logger.info(f"Opened containing folder (Windows): {folder_path}")

        elif system == "Darwin":  # macOS
            if file_path.is_file():
                # Reveal file in Finder
                subprocess.run(["open", "-R", str(file_path)], check=True)
            else:
                subprocess.run(["open", str(folder_path)], check=True)
            logger.info(f"Opened containing folder (macOS): {folder_path}")

        else:  # Linux and other Unix-like
            subprocess.run(["xdg-open", str(folder_path)], check=True)
            logger.info(f"Opened containing folder (Linux): {folder_path}")

        return True

    except FileNotFoundError:
        logger.error(f"Path not found: {path}")
        raise FileSearchError(f"Path not found: {path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to open folder for {path}: {e}")
        raise FileSearchError(f"Failed to open folder for {path}: {e}")
    except OSError as e:
        logger.error(f"OS error opening folder for {path}: {e}")
        raise FileSearchError(f"OS error opening folder for {path}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error opening folder for {path}: {e}")
        raise FileSearchError(f"Error opening folder for {path}: {e}")


# Convenience functions for common operations


def get_file_size(path: Union[str, Path]) -> int:
    """Get file size in bytes.

    Args:
        path: Path to the file

    Returns:
        File size in bytes

    Raises:
        FileSearchError: If file does not exist or cannot be accessed
    """
    info = get_file_info(path)
    return info["size"]


def get_file_modified_time(path: Union[str, Path]) -> float:
    """Get file modification timestamp.

    Args:
        path: Path to the file

    Returns:
        Modification timestamp as float

    Raises:
        FileSearchError: If file does not exist or cannot be accessed
    """
    info = get_file_info(path)
    return info["modified"]


def is_directory(path: Union[str, Path]) -> bool:
    """Check if path is a directory.

    Args:
        path: Path to check

    Returns:
        True if path is a directory, False otherwise

    Raises:
        FileSearchError: If path does not exist
    """
    info = get_file_info(path)
    return info["is_directory"]


def normalize_path(path: str) -> Path:
    """Normalize a path string by expanding user shortcuts and environment variables.

    Supports cross-platform network paths (UNC on Windows, NFS/SMB on Linux/Mac).

    Args:
        path: The path string to normalize.

    Returns:
        A Path object representing the normalized, absolute path.
    """
    # AC: Expand user shortcuts: ~, %USERPROFILE%, $HOME
    # Dev Note: Use os.path.expanduser and os.path.expandvars
    # Handle Windows-style %VAR% by converting to $VAR for cross-platform compatibility
    import re

    path = re.sub(r"%([^%]+)%", r"$\1", path)
    expanded_path = os.path.expanduser(path)
    expanded_path = os.path.expandvars(expanded_path)

    # Use pathlib.Path for cross-platform path handling
    return Path(expanded_path).resolve()


def validate_directory(path: Path) -> Optional[str]:
    """Validate if a Path object points to an existing, readable directory.

    Args:
        path: The Path object to validate.

    Returns:
        None if the directory is valid, otherwise a string error message.
    """
    if not path.exists():
        # AC: Show error state for invalid paths (red border, tooltip: "Directory does not exist")
        return "Directory does not exist."

    if not path.is_dir():
        return "Path is not a directory."

    # AC: Check read permissions and show error if denied
    if not os.access(path, os.R_OK):
        return "Permission denied: Cannot read directory contents."

    return None
