"""Application-owned paths and desktop effects used at the composition root."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, Sequence


class DesktopEffects(Protocol):
    """Effects that may contact the user's graphical desktop."""

    def open_file(self, path: Path) -> None:
        """Open a file with its associated application."""

    def reveal_file(self, path: Path) -> None:
        """Reveal a file or directory in the platform file manager."""

    def open_with(self, path: Path, application: dict[str, Any]) -> None:
        """Open a file with a selected application."""

    def choose_directory(
        self, parent: Any, initial: Path, *, title: str = "Select Search Directory"
    ) -> Path | None:
        """Choose a directory, or return None when cancelled."""

    def choose_application(self, parent: Any) -> Path | None:
        """Choose an application executable, or return None when cancelled."""

    def copy_text(self, text: str) -> None:
        """Copy text to the desktop clipboard."""

    def copy_files(self, paths: Sequence[Path]) -> None:
        """Copy file references to the desktop clipboard."""

    def confirm(
        self, parent: Any, title: str, message: str, *, default_yes: bool = False
    ) -> bool:
        """Display a yes/no confirmation."""

    def show_error(self, parent: Any, title: str, message: str) -> None:
        """Display an error dialog."""

    def show_warning(self, parent: Any, title: str, message: str) -> None:
        """Display a warning dialog."""

    def show_info(self, parent: Any, title: str, message: str) -> None:
        """Display an informational dialog."""

    def choose_color(self, parent: Any, initial: str, title: str) -> str | None:
        """Choose a color, or return None when cancelled."""

    def beep(self) -> None:
        """Play the desktop notification sound."""

    def show_properties(self, parent: Any, path: Path) -> None:
        """Display file properties."""

    def confirm_executable(self, parent: Any, message: str) -> tuple[bool, bool]:
        """Return whether to open and whether to remember the file extension."""


@dataclass(frozen=True)
class ApplicationRuntime:
    """Runtime dependencies shared by application components.

    Tests construct this object with temporary paths and a recording effects
    implementation. Production creates it once at the application entrypoint.
    """

    home_dir: Path
    config_dir: Path
    log_dir: Path
    desktop_effects: DesktopEffects
