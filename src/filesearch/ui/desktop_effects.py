"""Production implementation of effects that contact the graphical desktop."""

from pathlib import Path
from typing import Any, Sequence

from PyQt6.QtCore import QMimeData, QUrl
from PyQt6.QtGui import QColor, QGuiApplication
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QFileDialog,
    QMessageBox,
)

from filesearch.core.file_utils import (
    open_with_application,
    reveal_file_in_folder,
    safe_open,
)


class QtDesktopEffects:
    """Perform desktop operations using the platform and Qt integrations."""

    def open_file(self, path: Path) -> None:
        """Open a file with its associated application."""
        safe_open(path)

    def reveal_file(self, path: Path) -> None:
        """Reveal a file or directory in the platform file manager."""
        reveal_file_in_folder(path)

    def open_with(self, path: Path, application: dict[str, Any]) -> None:
        """Open a file with an explicitly selected application."""
        open_with_application(path, application)

    def choose_directory(
        self, parent: Any, initial: Path, *, title: str = "Select Search Directory"
    ) -> Path | None:
        """Show the application folder picker."""
        selected = QFileDialog.getExistingDirectory(
            parent,
            title,
            str(initial),
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks,
        )
        return Path(selected) if selected else None

    def choose_application(self, parent: Any) -> Path | None:
        """Show an executable picker."""
        dialog = QFileDialog(parent, "Choose Application")
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        if not dialog.exec():
            return None
        selected = dialog.selectedFiles()
        return Path(selected[0]) if selected else None

    def copy_text(self, text: str) -> None:
        """Copy plain text to the Qt clipboard."""
        clipboard = QGuiApplication.clipboard()
        if clipboard is None:
            raise RuntimeError("Clipboard is unavailable")
        clipboard.setText(text)

    def copy_files(self, paths: Sequence[Path]) -> None:
        """Copy file URLs to the Qt clipboard."""
        clipboard = QGuiApplication.clipboard()
        if clipboard is None:
            raise RuntimeError("Clipboard is unavailable")
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile(str(path)) for path in paths])
        clipboard.setMimeData(mime_data)

    def confirm(
        self, parent: Any, title: str, message: str, *, default_yes: bool = False
    ) -> bool:
        """Show a yes/no confirmation dialog."""
        default = (
            QMessageBox.StandardButton.Yes
            if default_yes
            else QMessageBox.StandardButton.No
        )
        reply = QMessageBox.question(
            parent,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            default,
        )
        return reply == QMessageBox.StandardButton.Yes

    def show_error(self, parent: Any, title: str, message: str) -> None:
        """Show a critical error dialog."""
        QMessageBox.critical(parent, title, message)

    def show_warning(self, parent: Any, title: str, message: str) -> None:
        """Show a warning dialog."""
        QMessageBox.warning(parent, title, message)

    def show_info(self, parent: Any, title: str, message: str) -> None:
        """Show an informational dialog."""
        QMessageBox.information(parent, title, message)

    def choose_color(self, parent: Any, initial: str, title: str) -> str | None:
        """Show the Qt color picker."""
        color = QColorDialog.getColor(QColor(initial), parent, title)
        return color.name() if color.isValid() else None

    def beep(self) -> None:
        """Play the Qt application notification sound."""
        QApplication.beep()

    def show_properties(self, parent: Any, path: Path) -> None:
        """Show the application's properties dialog."""
        from filesearch.ui.dialogs.properties_dialog import PropertiesDialog

        PropertiesDialog(path, parent).exec()

    def confirm_executable(self, parent: Any, message: str) -> tuple[bool, bool]:
        """Show the executable security warning."""
        dialog = QMessageBox(parent)
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setWindowTitle("Security Warning")
        dialog.setText(message)
        checkbox = QCheckBox("Always open files of this type")
        dialog.setCheckBox(checkbox)
        dialog.setStandardButtons(
            QMessageBox.StandardButton.Open | QMessageBox.StandardButton.Cancel
        )
        dialog.setDefaultButton(QMessageBox.StandardButton.Cancel)
        approved = dialog.exec() == QMessageBox.StandardButton.Open
        return approved, approved and checkbox.isChecked()
