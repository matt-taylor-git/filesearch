"""Tests for runtime resource and log path helpers."""

from pathlib import Path
from unittest.mock import patch

from filesearch.core.runtime_paths import (
    ensure_log_dir,
    get_app_icon_path,
    get_log_dir,
    get_resource_path,
)


def test_get_resource_path_resolves_packaged_icon():
    """Resources should resolve from the installed package tree."""
    icon_path = get_resource_path("resources", "icons", "app_icon.png")

    assert icon_path.exists()
    assert icon_path.name == "app_icon.png"


def test_get_app_icon_path_points_to_existing_png():
    """Runtime icon helper should return the checked-in icon asset."""
    icon_path = get_app_icon_path()

    assert icon_path.exists()
    assert icon_path.suffix == ".png"


def test_get_log_dir_uses_platformdirs():
    """Log path resolution should defer to platformdirs, not the repo root."""
    expected = Path(r"C:\Users\example\AppData\Local\filesearch\filesearch\Logs")
    with patch("platformdirs.user_log_dir", return_value=str(expected)):
        resolved = get_log_dir()

    assert resolved == expected
    assert "codeprojects" not in str(resolved)


def test_ensure_log_dir_creates_user_log_directory():
    """ensure_log_dir should create the resolved log folder."""
    expected = Path(r"C:\Users\example\AppData\Local\filesearch\filesearch\Logs")
    with patch("platformdirs.user_log_dir", return_value=str(expected)):
        with patch.object(Path, "mkdir") as mock_mkdir:
            created = ensure_log_dir()

    assert created == expected
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
