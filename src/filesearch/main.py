"""Main application entry point for File Search.

This module provides the main entry point for the File Search application.
It handles command-line arguments, initializes the application, and starts
the GUI event loop.
"""

import sys
from typing import Optional

from loguru import logger

from filesearch import (
    APP_AUTHOR,
    APP_DISPLAY_NAME,
    APP_INTERNAL_NAME,
    __version__,
    get_project_root,
)
from filesearch.core.runtime_paths import ensure_log_dir, get_app_icon_path


def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging with rotating file handler.

    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR).
    """
    log_dir = ensure_log_dir(APP_INTERNAL_NAME, APP_AUTHOR)

    # Remove default handler
    logger.remove()

    # Add file handler with rotation
    logger.add(
        log_dir / "filesearch.log",
        level=log_level,
        rotation="5 MB",
        retention="10 days",
        compression="zip",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        ),
    )

    # Windowed packaged builds may not provide a console stream.
    if sys.stderr is not None and hasattr(sys.stderr, "write"):
        logger.add(
            sys.stderr,
            level=log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>",
        )

    logger.info("Logging initialized with level: {}", log_level)
    logger.info("Log directory: {}", log_dir)


def parse_arguments() -> Optional[str]:
    """Parse command-line arguments.

    Returns:
        Optional[str]: The log level if specified, otherwise None.
    """
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["--help", "-h"]:
            print("File Search - A cross-platform file search application")
            print()
            print("Usage:")
            print("  filesearch [options]")
            print()
            print("Options:")
            print("  --help, -h     Show this help message")
            print("  --version, -v  Show version information")
            print("  --debug        Enable debug logging")
            print("  --info         Enable info logging (default)")
            print("  --warning      Enable warning logging only")
            print("  --error        Enable error logging only")
            sys.exit(0)
        elif arg in ["--version", "-v"]:
            print(f"File Search v{__version__}")
            sys.exit(0)
        elif arg == "--debug":
            return "DEBUG"
        elif arg == "--info":
            return "INFO"
        elif arg == "--warning":
            return "WARNING"
        elif arg == "--error":
            return "ERROR"
        else:
            print(f"Unknown option: {arg}")
            print("Use --help for usage information")
            sys.exit(1)
    return None


def main() -> int:
    """Main application entry point.

    Returns:
        int: Exit code (0 for success, non-zero for error).
    """
    try:
        # Parse command-line arguments
        log_level = parse_arguments()
        if log_level is None:
            log_level = "INFO"

        # Setup logging
        setup_logging(log_level)

        logger.info("Starting File Search v{}", __version__)
        logger.info("Project root: {}", get_project_root())

        # Initialize and start the GUI application
        logger.info("Initializing GUI application")

        from PyQt6.QtCore import QTimer
        from PyQt6.QtGui import QIcon
        from PyQt6.QtWidgets import QApplication

        from filesearch.core.config_manager import ConfigManager
        from filesearch.plugins.plugin_manager import PluginManager
        from filesearch.ui.main_window import MainWindow

        app = QApplication(sys.argv)
        app.setApplicationName(APP_DISPLAY_NAME)
        app.setApplicationDisplayName(APP_DISPLAY_NAME)
        app.setOrganizationName(APP_AUTHOR)

        from filesearch.ui.theme import apply_theme

        apply_theme(app)

        icon_path = get_app_icon_path()
        app_icon = QIcon(str(icon_path))
        if not app_icon.isNull():
            app.setWindowIcon(app_icon)
            logger.info("Application icon loaded from {}", icon_path)
        else:
            logger.warning("Application icon could not be loaded from {}", icon_path)

        # Initialize components
        config_manager = ConfigManager()
        plugin_manager = PluginManager(config_manager)

        # Load plugins
        loaded_plugins = plugin_manager.load_plugins()
        logger.info("Loaded {} plugins", len(loaded_plugins))

        window = MainWindow(config_manager, plugin_manager)
        if not app_icon.isNull():
            window.setWindowIcon(app_icon)
        window.show()

        def ensure_window_visible() -> None:
            window.showNormal()
            window.raise_()
            window.activateWindow()

        QTimer.singleShot(0, ensure_window_visible)

        logger.info("Application initialized successfully")
        return app.exec()

    except Exception as e:
        try:
            from PyQt6.QtWidgets import QApplication, QMessageBox

            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)

            QMessageBox.critical(
                None,
                APP_DISPLAY_NAME,
                (
                    "File Search could not start.\n\n"
                    f"{type(e).__name__}: {e}\n\n"
                    "See the log file for more details."
                ),
            )
        except Exception:
            pass
        logger.exception("Fatal error in main application: {}", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
