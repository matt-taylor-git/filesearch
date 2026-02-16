"""Context menu handler mixin for MainWindow."""

from enum import Enum
from pathlib import Path
from typing import List

from loguru import logger
from PyQt6.QtCore import QMimeData, QPoint, Qt, QUrl
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QApplication,
    QMenu,
    QMessageBox,
    QStyle,
)

from filesearch.core.exceptions import FileSearchError
from filesearch.core.file_utils import (
    delete_file,
    get_associated_applications,
    open_containing_folder,
    open_with_application,
)
from filesearch.models.search_result import SearchResult


class ContextMenuAction(Enum):
    """Enum for context menu actions to ensure type safety and consistency."""

    OPEN = "Open"
    OPEN_WITH = "Open With..."
    OPEN_CONTAINING_FOLDER = "Open Containing Folder"
    COPY_PATH_TO_CLIPBOARD = "Copy Path to Clipboard"
    COPY_FILE_TO_CLIPBOARD = "Copy File to Clipboard"
    PROPERTIES = "Properties"
    DELETE = "Delete"
    RENAME = "Rename"


class ContextMenuHandlerMixin:
    """Mixin class that provides context menu functionality for MainWindow.

    This mixin expects the host class to have:
    - self.results_view: ResultsView instance
    - self.safe_status_message(str): method
    - self._on_file_open_requested(SearchResult): method
    - self.open_selected_folder(Path): method
    - self.config_manager: ConfigManager instance
    """

    # Alias the enum on the class so self.ContextMenuAction works unchanged
    ContextMenuAction = ContextMenuAction

    def _setup_context_menu(self) -> None:
        """Sets up the context menu infrastructure."""
        self.setAccessibleName("Main Window")
        self.results_view.setAccessibleName("Search Results List")
        self.results_view.setAccessibleDescription(
            "List of files matching the search query. Use arrow keys to "
            "navigate, Enter to open, and Context Menu key for options."
        )

    def _on_context_menu_requested(self, pos: QPoint) -> None:
        """Handles the request to display a context menu for search results.

        Args:
            pos: The global position where the context menu should appear.
        """
        selected_indexes = self.results_view.selectionModel().selectedIndexes()
        selected_results = [
            self.results_view.model().data(index, Qt.ItemDataRole.UserRole)
            for index in selected_indexes
            if index.isValid()
        ]

        if not selected_results:
            return

        menu = self._create_context_menu(selected_results)
        menu.exec(pos)

    def _create_context_menu(self, selected_results: List[SearchResult]) -> QMenu:
        """Creates and populates the context menu based on selected results.

        Args:
            selected_results: A list of SearchResult objects currently selected.

        Returns:
            A QMenu instance ready to be displayed.
        """
        menu = QMenu(self)

        # AC1: Open (default action, bold text)
        open_action = menu.addAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton),
            self.ContextMenuAction.OPEN.value,
        )
        open_action.triggered.connect(
            lambda: self._on_context_menu_action(self.ContextMenuAction.OPEN)
        )
        font = open_action.font()
        font.setBold(True)
        open_action.setFont(font)

        # AC4: Open With... Submenu
        open_with_menu = QMenu("Open With...", self)
        open_with_action = menu.addMenu(open_with_menu)
        open_with_action.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon)
        )

        if len(selected_results) == 1:
            open_with_menu.aboutToShow.connect(
                lambda: self._populate_open_with_menu(
                    open_with_menu, selected_results[0]
                )
            )
        else:
            open_with_action.setEnabled(False)

        # AC5: Open Containing Folder
        open_folder_action = menu.addAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon),
            self.ContextMenuAction.OPEN_CONTAINING_FOLDER.value,
        )
        open_folder_action.triggered.connect(
            lambda: self._on_context_menu_action(
                self.ContextMenuAction.OPEN_CONTAINING_FOLDER
            )
        )
        open_folder_action.setShortcut("Ctrl+Shift+O")

        menu.addSeparator()

        # AC6: Copy Path to Clipboard
        copy_path_action = menu.addAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton),
            self.ContextMenuAction.COPY_PATH_TO_CLIPBOARD.value,
        )
        copy_path_action.triggered.connect(
            lambda: self._on_context_menu_action(
                self.ContextMenuAction.COPY_PATH_TO_CLIPBOARD
            )
        )
        copy_path_action.setShortcut("Ctrl+Shift+C")

        # AC7: Copy File to Clipboard
        copy_file_action = menu.addAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon),
            self.ContextMenuAction.COPY_FILE_TO_CLIPBOARD.value,
        )
        copy_file_action.triggered.connect(
            lambda: self._on_context_menu_action(
                self.ContextMenuAction.COPY_FILE_TO_CLIPBOARD
            )
        )

        menu.addSeparator()

        # AC8: Properties Dialog
        properties_action = menu.addAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation),
            self.ContextMenuAction.PROPERTIES.value,
        )
        properties_action.triggered.connect(
            lambda: self._on_context_menu_action(self.ContextMenuAction.PROPERTIES)
        )
        properties_action.setShortcut("Alt+Return")

        # AC9: Delete with Confirmation
        delete_action = menu.addAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon),
            self.ContextMenuAction.DELETE.value,
        )
        delete_action.triggered.connect(
            lambda: self._on_context_menu_action(self.ContextMenuAction.DELETE)
        )
        delete_action.setShortcut(Qt.Key.Key_Delete)

        # AC10: Rename with Validation
        rename_action = menu.addAction(
            self.style().standardIcon(QStyle.StandardPixmap.SP_LineEditClearButton),
            self.ContextMenuAction.RENAME.value,
        )
        rename_action.triggered.connect(
            lambda: self._on_context_menu_action(self.ContextMenuAction.RENAME)
        )
        rename_action.setShortcut(Qt.Key.Key_F2)

        # AC11: Multi-Selection Support
        is_single_selection = len(selected_results) == 1
        open_with_action.setEnabled(is_single_selection)
        properties_action.setEnabled(is_single_selection)
        rename_action.setEnabled(is_single_selection)

        return menu

    def _populate_open_with_menu(self, menu: QMenu, result: SearchResult) -> None:
        """Populate the Open With submenu with available applications.

        Args:
            menu: The menu to populate
            result: The search result to find apps for
        """
        menu.clear()

        apps = get_associated_applications(result.path)

        for app in apps:
            action = menu.addAction(app["name"])
            action.triggered.connect(
                lambda checked, a=app: self._handle_open_with_app(a, result)
            )

        if apps:
            menu.addSeparator()

        choose_action = menu.addAction("Choose another application...")
        choose_action.triggered.connect(lambda: self._handle_choose_application(result))

    def _handle_open_with_app(self, app_info: dict, result: SearchResult) -> None:
        """Handle opening file with a specific application.

        Args:
            app_info: Application info dictionary
            result: SearchResult object
        """
        try:
            self.safe_status_message(
                f"Opening {result.path.name} with {app_info['name']}..."
            )
            open_with_application(result.path, app_info)
            self.safe_status_message(
                f"Opened {result.path.name} with {app_info['name']}"
            )
            logger.info(
                f"Opened file {result.path} with application {app_info['name']}"
            )
        except Exception as e:
            self.safe_status_message(f"Failed to open with {app_info['name']}: {e}")
            logger.error(f"Error opening {result.path} with {app_info['name']}: {e}")

    def _handle_choose_application(self, result: SearchResult) -> None:
        """Handle "Choose another application..." action.

        Args:
            result: SearchResult object
        """
        from PyQt6.QtWidgets import QFileDialog

        file_dialog = QFileDialog(self, "Choose Application")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                executable = selected_files[0]
                app_info = {"name": Path(executable).name, "command": executable}
                self._handle_open_with_app(app_info, result)

    def _on_context_menu_action(self, action: ContextMenuAction) -> None:
        """Routes context menu actions to their respective handlers.

        Args:
            action: The ContextMenuAction enum value representing the chosen action.
        """
        selected_indexes = self.results_view.selectionModel().selectedIndexes()
        selected_results = [
            self.results_view.model().data(index, Qt.ItemDataRole.UserRole)
            for index in selected_indexes
            if index.isValid()
        ]

        if not selected_results:
            self.safe_status_message("No item selected for action.")
            return

        handler_map = {
            self.ContextMenuAction.OPEN: self._handle_context_open,
            self.ContextMenuAction.OPEN_WITH: self._handle_context_open_with,
            self.ContextMenuAction.OPEN_CONTAINING_FOLDER: (
                self._handle_context_open_containing_folder
            ),
            self.ContextMenuAction.COPY_PATH_TO_CLIPBOARD: (
                self._handle_context_copy_path
            ),
            self.ContextMenuAction.COPY_FILE_TO_CLIPBOARD: (
                self._handle_context_copy_file
            ),
            self.ContextMenuAction.PROPERTIES: self._handle_context_properties,
            self.ContextMenuAction.DELETE: self._handle_context_delete,
            self.ContextMenuAction.RENAME: self._handle_context_rename,
        }

        handler = handler_map.get(action)
        if handler:
            try:
                handler(selected_results)
            except Exception as e:
                logger.error(f"Error executing context menu action {action}: {e}")
                self.safe_status_message(f"Error: {str(e)}")
        else:
            logger.warning(f"Unknown context menu action: {action}")

    def _handle_context_open(self, selected_results: List[SearchResult]) -> None:
        """Handle Open action - open files with default application."""
        for result in selected_results:
            self._on_file_open_requested(result)

    def _handle_context_open_with(self, selected_results: List[SearchResult]) -> None:
        """Handle Open With... submenu action."""
        if len(selected_results) != 1:
            self.safe_status_message(
                "Open With... only supported for single selection."
            )
            return

        result = selected_results[0]
        self.safe_status_message(
            f"Open With... not yet implemented for {result.path.name}"
        )

    def _handle_context_open_containing_folder(
        self, selected_results: List[SearchResult]
    ) -> None:
        """Handle Open Containing Folder action."""
        if not selected_results:
            return

        result = selected_results[0]
        try:
            open_containing_folder(result.path)
            self.safe_status_message("Opened containing folder")
            logger.info(f"Opened containing folder for {result.path}")
        except FileSearchError as e:
            self.safe_status_message(f"Failed to open containing folder: {e}")
            logger.error(f"Error opening containing folder for {result.path}: {e}")

    def _handle_context_copy_path(self, selected_results: List[SearchResult]) -> None:
        """Handle Copy Path to Clipboard action."""
        try:
            clipboard = QGuiApplication.clipboard()
            if len(selected_results) == 1:
                path_text = str(selected_results[0].path)
            else:
                paths = [str(result.path) for result in selected_results]
                path_text = "\n".join(paths)

            clipboard.setText(path_text)
            self.safe_status_message("Path copied to clipboard")
            logger.info(f"Copied {len(selected_results)} path(s) to clipboard")
        except Exception as e:
            self.safe_status_message(f"Failed to copy path: {e}")
            logger.error(f"Error copying path to clipboard: {e}")

    def _handle_context_copy_file(self, selected_results: List[SearchResult]) -> None:
        """Handle Copy File to Clipboard action."""
        try:
            clipboard = QGuiApplication.clipboard()

            missing_files = []
            for result in selected_results:
                if not result.path.exists():
                    missing_files.append(result.path.name)

            if missing_files:
                if len(missing_files) == 1:
                    self.safe_status_message(
                        f"File no longer exists: {missing_files[0]}"
                    )
                else:
                    self.safe_status_message(
                        f"{len(missing_files)} files no longer exist"
                    )
                return

            if len(selected_results) == 1:
                file_path = selected_results[0].path
                file_url = QUrl.fromLocalFile(str(file_path))
                mime_data = QMimeData()
                mime_data.setUrls([file_url])
                clipboard.setMimeData(mime_data)
            else:
                urls = [QUrl.fromLocalFile(str(r.path)) for r in selected_results]
                mime_data = QMimeData()
                mime_data.setUrls(urls)
                clipboard.setMimeData(mime_data)

            self.safe_status_message("File copied to clipboard")
            logger.info(f"Copied {len(selected_results)} file(s) to clipboard")
        except Exception as e:
            self.safe_status_message(f"Failed to copy: {e}")
            logger.error(f"Error copying file to clipboard: {e}")

            try:
                self._handle_context_copy_path(selected_results)
                self.safe_status_message(
                    "Failed to copy file object, copied path instead"
                )
            except Exception:
                pass

    def _handle_context_properties(self, selected_results: List[SearchResult]) -> None:
        """Handle Properties dialog action."""
        if len(selected_results) != 1:
            self.safe_status_message("Properties only supported for single selection.")
            return

        result = selected_results[0]
        try:
            from filesearch.ui.dialogs.properties_dialog import PropertiesDialog

            dialog = PropertiesDialog(result.path, self)
            dialog.exec()
            logger.info(f"Showed properties dialog for {result.path}")
        except Exception as e:
            self.safe_status_message(f"Failed to show properties: {e}")
            logger.error(f"Error showing properties dialog for {result.path}: {e}")

    def _handle_context_delete(self, selected_results: List[SearchResult]) -> None:
        """Handle Delete action with confirmation."""
        try:
            modifiers = QApplication.keyboardModifiers()
            permanent_delete = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)

            if len(selected_results) == 1:
                item_name = selected_results[0].path.name
            else:
                item_name = f"{len(selected_results)} items"

            if permanent_delete:
                message = (
                    f"Permanently delete {item_name}? This action cannot be undone."
                )
                title = "Confirm Permanent Delete"
            else:
                message = f"Move {item_name} to trash?"
                title = "Confirm Delete"

            reply = QMessageBox.question(
                self,
                title,
                message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply != QMessageBox.StandardButton.Yes:
                self.safe_status_message("Delete cancelled")
                return

            self._perform_delete(selected_results, permanent_delete)

        except Exception as e:
            self.safe_status_message(f"Delete failed: {e}")
            logger.error(f"Error in delete operation: {e}")

    def _perform_delete(
        self, selected_results: List[SearchResult], permanent: bool
    ) -> None:
        """Perform the actual delete operation."""
        deleted_count = 0
        errors = []

        for result in selected_results:
            try:
                delete_file(result.path, permanent)
                deleted_count += 1
                self._remove_result_from_view(result)
            except Exception as e:
                errors.append(f"{result.path.name}: {str(e)}")

        if errors:
            if len(errors) == 1:
                self.safe_status_message(f"Error: {errors[0]}")
            else:
                self.safe_status_message(f"Failed to delete {len(errors)} items")
                logger.error(f"Delete errors: {errors}")
        elif deleted_count > 0:
            action = "permanently deleted" if permanent else "moved to trash"
            self.safe_status_message(f"Successfully {action} {deleted_count} items")

    def _remove_result_from_view(self, result: SearchResult) -> None:
        """Remove a result from the view's model."""
        model = self.results_view.model()
        if hasattr(model, "remove_result"):
            model.remove_result(result)

    def _handle_context_rename(self, selected_results: List[SearchResult]) -> None:
        """Handle Rename action with inline editing."""
        if len(selected_results) != 1:
            self.safe_status_message("Rename only supported for single selection.")
            return

        current_index = self.results_view.currentIndex()
        if current_index.isValid():
            self.results_view.edit(current_index)
            self.safe_status_message(f"Renaming {selected_results[0].path.name}")
        else:
            self.safe_status_message("Could not start rename: invalid selection")
