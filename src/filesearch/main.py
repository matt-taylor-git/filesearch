"""Main application entry point for File Search.

This module provides the main entry point for the File Search application.
It handles command-line arguments, initializes the application, and starts
the GUI event loop.
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from filesearch import __version__, get_project_root


def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging with rotating file handler.

    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR).
    """
    # Create logs directory if it doesn't exist
    log_dir = get_project_root() / "logs"
    log_dir.mkdir(exist_ok=True)

    # Remove default handler
    logger.remove()

    # Add console handler
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>",
    )

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

    logger.info("Logging initialized with level: {}", log_level)


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

        from PyQt6.QtWidgets import QApplication

        from filesearch.core.config_manager import ConfigManager
        from filesearch.plugins.plugin_manager import PluginManager
        from filesearch.ui.main_window import MainWindow

        # Initialize components
        config_manager = ConfigManager()
        plugin_manager = PluginManager(config_manager)

        # Load plugins
        loaded_plugins = plugin_manager.load_plugins()
        logger.info("Loaded {} plugins", len(loaded_plugins))

        # Create and show main window
        app = QApplication(sys.argv)
        window = MainWindow(config_manager, plugin_manager)
        window.show()

        logger.info("Application initialized successfully")
        return app.exec()

    except Exception as e:
        logger.exception("Fatal error in main application: {}", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
