"""File utilities module for file system operations.

This module provides utility functions for file information retrieval,
cross-platform file opening, and directory navigation.
"""

import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union

from loguru import logger
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices

from filesearch.core.exceptions import FileSearchError


def get_file_info(path: Union[str, Path]) -> Dict[str, Union[str, int, float, bool]]:
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


def safe_open(
    path: Union[str, Path], security_manager=None, force_open: bool = False
) -> bool:
    """Open a file with the system default application.

    Args:
        path: Path to the file to open
        security_manager: Optional security manager for executable warnings
        force_open: If True, skip security warnings and open directly

    Returns:
        True if file was opened successfully, False otherwise

    Raises:
        FileSearchError: If file does not exist or cannot be opened

    Note:
        Uses platform-specific methods:
        - Windows: os.startfile()
        - macOS: open command
        - Linux: xdg-open command
        - Cross-platform fallback: QDesktopServices.openUrl()

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

        # Security check for executable files
        if not force_open and security_manager:
            should_warn, warning_message = security_manager.should_warn_before_opening(
                file_path
            )
            if should_warn:
                logger.warning(
                    f"Security warning for executable file {path}: {warning_message}"
                )
                # Return a special indicator that user confirmation is needed
                # The UI layer should handle showing the warning dialog
                raise FileSearchError(f"SECURITY_WARNING:{warning_message}")

        success = False
        # Use Qt's QDesktopServices as primary method - it's non-blocking and cross-platform
        try:
            url = QUrl.fromLocalFile(str(file_path.resolve()))
            success = QDesktopServices.openUrl(url)
            if success:
                logger.info(f"Opened file with QDesktopServices: {path}")
            else:
                logger.warning(
                    "QDesktopServices.openUrl returned False, trying platform-specific methods"
                )
                # Try platform-specific methods as fallback, but use non-blocking approach
                system = platform.system()

                if system == "Windows":
                    try:
                        # Use os.startfile for Windows (non-blocking)
                        os.startfile(str(file_path))  # type: ignore[attr-defined]
                        logger.info(f"Opened file with os.startfile (Windows): {path}")
                        success = True
                    except (AttributeError, OSError) as e:
                        logger.warning(f"Windows os.startfile failed: {e}")
                        # Use Popen for non-blocking subprocess
                        subprocess.Popen(
                            ["cmd", "/c", "start", "", str(file_path)],
                            shell=True,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        logger.info(f"Opened file with cmd start (Windows): {path}")
                        success = True

                elif system == "Darwin":  # macOS
                    # Use Popen for non-blocking subprocess
                    subprocess.Popen(
                        ["open", str(file_path)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    logger.info(f"Opened file with open command (macOS): {path}")
                    success = True

                else:  # Linux and other Unix-like
                    # Use Popen for non-blocking subprocess
                    subprocess.Popen(
                        ["xdg-open", str(file_path)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    logger.info(f"Opened file with xdg-open (Linux): {path}")
                    success = True

        except Exception as e:
            logger.error(f"Error opening file: {e}")

        if not success:
            raise FileSearchError(
                f"Failed to open file {path} with all available methods"
            )

        return True

    except FileSearchError:
        # Re-raise our own exceptions
        raise
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

        # Use Popen for non-blocking subprocess calls to prevent UI freezing
        if system == "Windows":
            if file_path.is_file():
                # Try to select the file in Explorer
                subprocess.Popen(
                    ["explorer", "/select,", str(file_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                subprocess.Popen(
                    ["explorer", str(folder_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            logger.info(f"Opened containing folder (Windows): {folder_path}")

        elif system == "Darwin":  # macOS
            if file_path.is_file():
                # Reveal file in Finder
                subprocess.Popen(
                    ["open", "-R", str(file_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                subprocess.Popen(
                    ["open", str(folder_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            logger.info(f"Opened containing folder (macOS): {folder_path}")

        else:  # Linux and other Unix-like
            subprocess.Popen(
                ["xdg-open", str(folder_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info(f"Opened containing folder (Linux): {folder_path}")

        return True

    except FileNotFoundError:
        logger.error(f"Path not found: {path}")
        raise FileSearchError(f"Path not found: {path}")
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
    return int(info["size"])


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
    return float(info["modified"])


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
    return bool(info["is_directory"])


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


def get_associated_applications(path: Union[str, Path]) -> List[Dict[str, str]]:
    """Get list of applications associated with the file type.

    Args:
        path: Path to the file

    Returns:
        List of dictionaries containing 'name' and 'command'/'id' for each application.
        Example: [{'name': 'Text Editor', 'id': 'org.gnome.TextEditor.desktop'}]
    """
    apps = []
    file_path = Path(path)
    if not file_path.exists():
        return apps

    system = platform.system()

    try:
        if system == "Linux":
            # Use gio to find associated apps
            # 1. Get MIME type
            # Using check_output with error handling
            try:
                mime_type = (
                    subprocess.check_output(
                        [
                            "gio",
                            "info",
                            "-a",
                            "standard::content-type",
                            "--no-follow-symlinks",
                            str(file_path),
                        ],
                        stderr=subprocess.DEVNULL,
                    )
                    .decode("utf-8")
                    .strip()
                )
            except subprocess.CalledProcessError:
                return apps

            # Parse output like "standard::content-type: text/plain"
            import re

            match = re.search(r"standard::content-type:\s+(\S+)", mime_type)
            if match:
                mime_type_str = match.group(1)

                # 2. Get apps for MIME type
                try:
                    output = subprocess.check_output(
                        ["gio", "mime", mime_type_str], stderr=subprocess.DEVNULL
                    ).decode("utf-8")
                except subprocess.CalledProcessError:
                    return apps

                # Parse output
                desktop_ids = []
                for line in output.splitlines():
                    line = line.strip()
                    if line.endswith(".desktop"):
                        # Extract desktop ID
                        desktop_id = line.split()[-1]
                        if desktop_id not in desktop_ids:
                            desktop_ids.append(desktop_id)

                # 3. Get display names for apps
                for app_id in desktop_ids:
                    try:
                        # minimal effort name extraction
                        name = app_id.replace(".desktop", "").split(".")[-1]
                        apps.append({"name": name, "id": app_id, "type": "desktop_id"})
                    except Exception:
                        continue

    except Exception as e:
        logger.warning(f"Error detecting applications: {e}")

    return apps


def open_with_application(path: Union[str, Path], app_info: Dict[str, str]) -> bool:
    """Open file with specific application.

    Args:
        path: Path to file
        app_info: Application info dictionary from get_associated_applications

    Returns:
        True if successful
    """
    file_path = Path(path)
    system = platform.system()

    try:
        if system == "Linux" and app_info.get("type") == "desktop_id":
            subprocess.Popen(
                ["gio", "launch", app_info["id"], str(file_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True

        # Fallback for direct commands
        if "command" in app_info:
            subprocess.Popen(
                [app_info["command"], str(file_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True

        return False

    except Exception as e:
        logger.error(f"Error opening with application: {e}")
        raise FileSearchError(f"Failed to open with application: {e}")


def validate_filename(name: str) -> Optional[str]:
    """Validate a filename.

    Args:
        name: The filename to validate

    Returns:
        None if valid, error message string otherwise
    """
    if not name or not name.strip():
        return "Filename cannot be empty"

    # Check for invalid characters
    # Windows: < > : " / \ | ? *
    # Unix: / (and null byte)
    invalid_chars = '<>:"/\\|?*' if platform.system() == "Windows" else "/"

    for char in invalid_chars:
        if char in name:
            return f"Filename cannot contain: {char}"

    if name.strip() == "." or name.strip() == "..":
        return "Invalid filename"

    return None


def rename_file(path: Path, new_name: str) -> Path:
    """Rename a file or directory.

    Args:
        path: Current path
        new_name: New filename

    Returns:
        Path object to the renamed file

    Raises:
        FileSearchError: If rename fails
    """
    try:
        # Validate name
        error = validate_filename(new_name)
        if error:
            raise FileSearchError(error)

        new_path = path.parent / new_name

        if new_path.exists():
            raise FileSearchError(f"A file with name '{new_name}' already exists")

        path.rename(new_path)
        logger.info(f"Renamed {path} to {new_path}")
        return new_path

    except OSError as e:
        logger.error(f"OS error renaming {path}: {e}")
        raise FileSearchError(f"Failed to rename: {e}")
    except Exception as e:
        if isinstance(e, FileSearchError):
            raise
        logger.error(f"Unexpected error renaming {path}: {e}")
        raise FileSearchError(f"Error renaming file: {e}")


def delete_file(path: Path, permanent: bool = False) -> None:
    """Delete a file or directory.

    Args:
        path: Path to delete
        permanent: If True, delete permanently; otherwise move to trash

    Raises:
        FileSearchError: If deletion fails
    """
    if not path.exists():
        raise FileSearchError(f"Path does not exist: {path}")

    try:
        if permanent:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                os.remove(path)
            logger.info(f"Permanently deleted: {path}")
        else:
            from send2trash import send2trash

            send2trash(path)
            logger.info(f"Moved to trash: {path}")

    except OSError as e:
        logger.error(f"OS error deleting {path}: {e}")
        raise FileSearchError(f"Failed to delete: {e}")
    except Exception as e:
        if isinstance(e, FileSearchError):
            raise
        logger.error(f"Unexpected error deleting {path}: {e}")
        raise FileSearchError(f"Error deleting file: {e}")
