"""Tests for ResultsView UI component."""

from pathlib import Path

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from filesearch.models.search_result import SearchResult
from filesearch.ui.results_view import ResultsView


@pytest.fixture
def app():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def results_view(app):
    """Create ResultsView instance for tests."""
    view = ResultsView()
    yield view
    view.deleteLater()


@pytest.fixture
def sample_results():
    """Create sample SearchResult instances for testing."""
    return [
        SearchResult(
            path=Path("/home/user/document.txt"),
            size=1024,
            modified=1609488000.0,  # 2021-01-01
            plugin_source=None,
        ),
        SearchResult(
            path=Path("/home/user/image.jpg"),
            size=2048000,
            modified=1609574400.0,  # 2021-01-02
            plugin_source=None,
        ),
        SearchResult(
            path=Path("/home/user/folder"),
            size=0,
            modified=1609660800.0,  # 2021-01-03
            plugin_source=None,
        ),
    ]


def test_results_view_initialization(results_view):
    """Test ResultsView initializes correctly."""
    assert results_view is not None
    assert results_view.minimumHeight() == 200
    assert results_view.model() is not None


def test_add_single_result(results_view, sample_results):
    """Test adding a single result to the view."""
    result = sample_results[0]
    results_view.add_result(result)

    model = results_view.model()
    assert model.rowCount() == 1

    index = model.index(0, 0)
    displayed_result = index.data(Qt.ItemDataRole.UserRole)
    assert displayed_result == result
    assert index.data(Qt.ItemDataRole.DisplayRole) == result.get_display_name()


def test_set_results(results_view, sample_results):
    """Test setting multiple results at once."""
    results_view.set_results(sample_results)

    model = results_view.model()
    assert model.rowCount() == 3

    for i, expected_result in enumerate(sample_results):
        index = model.index(i, 0)
        actual_result = index.data(Qt.ItemDataRole.UserRole)
        assert actual_result == expected_result


def test_clear_results(results_view, sample_results):
    """Test clearing results."""
    results_view.set_results(sample_results)
    assert results_view.model().rowCount() == 3

    results_view.clear_results()
    # Should show empty state message
    assert results_view.model().rowCount() == 1
    index = results_view.model().index(0, 0)
    assert "Enter a search term" in index.data(Qt.ItemDataRole.DisplayRole)


def test_get_selected_result_no_selection(results_view, sample_results):
    """Test getting selected result when nothing is selected."""
    results_view.set_results(sample_results)
    assert results_view.get_selected_result() is None


def test_get_selected_result_with_selection(results_view, sample_results, qtbot):
    """Test getting selected result when item is selected."""
    results_view.set_results(sample_results)

    # Select first item
    index = results_view.model().index(0, 0)
    results_view.setCurrentIndex(index)

    selected = results_view.get_selected_result()
    assert selected == sample_results[0]


def test_performance_large_result_set(results_view):
    """Test performance with large result set."""
    # Create 1000 results
    large_results = []
    for i in range(1000):
        result = SearchResult(
            path=Path(f"/test/file_{i}.txt"),
            size=1024 + i,
            modified=1609459200.0 + i,
            plugin_source=None,
        )
        large_results.append(result)

    import time

    start_time = time.time()
    results_view.set_results(large_results)
    end_time = time.time()

    duration = end_time - start_time
    assert duration < 0.1  # Less than 100ms
    # With virtual scrolling, only first batch should be loaded initially
    assert results_view.model().rowCount() == 100  # Initial batch size
    # But all results should be stored in the model
    assert len(results_view.model().get_all_results()) == 1000


def test_search_result_display_methods(sample_results):
    """Test SearchResult display methods."""
    result = sample_results[0]  # document.txt, 1024 bytes

    assert result.get_display_name() == "document.txt"
    assert result.get_display_size() == "1.0 KiB"
    assert result.get_display_date() == "Jan 01, 2021"

    # Test folder
    folder_result = sample_results[2]
    assert folder_result.get_display_size() == "Folder"


def test_empty_state_messages(results_view):
    """Test different empty state messages."""
    # Initially empty
    model = results_view.model()
    assert model.rowCount() == 0

    # After clearing results
    results_view.clear_results()
    assert model.rowCount() == 1
    index = model.index(0, 0)
    assert "Enter a search term" in index.data(Qt.ItemDataRole.DisplayRole)

    # After setting empty results
    results_view.set_results([])
    assert model.rowCount() == 1
    index = model.index(0, 0)
    assert "No files found" in index.data(Qt.ItemDataRole.DisplayRole)
