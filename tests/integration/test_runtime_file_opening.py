"""End-to-end coverage of desktop effects through application composition."""

from filesearch.core.config_manager import ConfigManager
from filesearch.models.search_result import SearchResult
from filesearch.ui.main_window import MainWindow


def test_result_open_flows_through_runtime_boundary(
    qtbot, tmp_path, application_runtime, desktop_effects
):
    """A result activation reaches the injected desktop-effects adapter."""
    home_dir = tmp_path / "home"
    home_dir.mkdir(exist_ok=True)
    file_path = home_dir / "notes.txt"
    file_path.write_text("hermetic", encoding="utf-8")
    config = ConfigManager(runtime=application_runtime, watch_config=False)
    window = MainWindow(config_manager=config, runtime=application_runtime)
    qtbot.addWidget(window)
    result = SearchResult(
        path=file_path,
        size=file_path.stat().st_size,
        modified=file_path.stat().st_mtime,
    )

    window._on_file_open_requested(result)

    assert desktop_effects.opened_files == [file_path]
    assert config.get("recent_files.opened_files") == [str(file_path)]
