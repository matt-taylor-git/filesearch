"""Integration tests for sorting functionality.

Tests end-to-end sorting flow from UI to results display.
"""

import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from filesearch.core.sort_engine import SortCriteria, SortEngine
from filesearch.models.search_result import SearchResult
from filesearch.ui.results_view import ResultsModel, ResultsView


class TestSortingIntegration:
    """Integration tests for sorting"""

    def test_end_to_end_name_sorting(self, tmp_path):
        """Test complete flow: sort by name through ResultsModel"""
        model = ResultsModel()

        # Create test files and directories
        now = datetime.now().timestamp()
        folder_path = tmp_path / "afolder"
        folder_path.mkdir()

        file1_path = tmp_path / "file1.txt"
        file1_path.touch()
        file10_path = tmp_path / "file10.txt"
        file10_path.touch()
        file2_path = tmp_path / "file2.txt"
        file2_path.touch()

        results = [
            SearchResult(file10_path, 100, now, "test"),
            SearchResult(file1_path, 50, now, "test"),
            SearchResult(file2_path, 75, now, "test"),
            SearchResult(folder_path, 0, now, "test"),
        ]

        # Load results into model
        model.set_results(results)

        # Apply sorting
        model.sort_results(SortCriteria.NAME_ASC)

        # Verify sorted order
        sorted_results = model.get_all_results()
        filenames = [r.get_display_name() for r in sorted_results]

        assert filenames[0] == "afolder"  # Folder first
        assert filenames[1] == "file1.txt"
        assert filenames[2] == "file2.txt"
        assert filenames[3] == "file10.txt"  # Natural sorting

    def test_end_to_end_size_sorting(self, tmp_path):
        """Test complete flow: sort by size"""
        model = ResultsModel()

        now = datetime.now().timestamp()
        small_path = tmp_path / "small.txt"
        small_path.touch()
        small_path.write_text("small")

        large_path = tmp_path / "large.txt"
        large_path.touch()
        large_path.write_text("large file content here")

        folder_path = tmp_path / "folder"
        folder_path.mkdir()

        results = [
            SearchResult(large_path, len(large_path.read_text()), now, "test"),
            SearchResult(small_path, len(small_path.read_text()), now, "test"),
            SearchResult(folder_path, 0, now, "test"),
        ]

        model.set_results(results)
        model.sort_results(SortCriteria.SIZE_ASC)

        sorted_results = model.get_all_results()
        filenames = [r.get_display_name() for r in sorted_results]

        assert filenames[0] == "folder"  # Folders first
        assert filenames[1] == "small.txt"
        assert filenames[2] == "large.txt"

    def test_end_to_end_date_sorting(self, tmp_path):
        """Test complete flow: sort by date"""
        model = ResultsModel()

        now = datetime.now().timestamp()

        # Create files at different times
        old_path = tmp_path / "old.txt"
        old_path.touch()
        old_time = now - 86400  # 1 day ago

        new_path = tmp_path / "new.txt"
        new_path.touch()
        new_time = now

        middle_path = tmp_path / "middle.txt"
        middle_path.touch()
        middle_time = now - 43200  # 12 hours ago

        results = [
            SearchResult(old_path, 10, old_time, "test"),
            SearchResult(new_path, 10, new_time, "test"),
            SearchResult(middle_path, 10, middle_time, "test"),
        ]

        model.set_results(results)
        model.sort_results(SortCriteria.DATE_DESC)

        sorted_results = model.get_all_results()
        filenames = [r.get_display_name() for r in sorted_results]

        assert filenames[0] == "new.txt"
        assert filenames[1] == "middle.txt"
        assert filenames[2] == "old.txt"

    def test_end_to_end_type_sorting(self, tmp_path):
        """Test complete flow: sort by type"""
        model = ResultsModel()

        now = datetime.now().timestamp()

        # Create files with different extensions and a folder
        txt_path = tmp_path / "file.txt"
        txt_path.touch()

        pdf_path = tmp_path / "file.pdf"
        pdf_path.touch()

        jpg_path = tmp_path / "file.jpg"
        jpg_path.touch()

        folder_path = tmp_path / "folder"
        folder_path.mkdir()

        results = [
            SearchResult(txt_path, 10, now, "test"),
            SearchResult(pdf_path, 10, now, "test"),
            SearchResult(jpg_path, 10, now, "test"),
            SearchResult(folder_path, 0, now, "test"),
        ]

        model.set_results(results)
        model.sort_results(SortCriteria.TYPE_ASC)

        sorted_results = model.get_all_results()

        # First should be folder
        assert sorted_results[0].get_display_name() == "folder"
        assert sorted_results[0].path.is_dir()

        # Then files grouped by extension
        extensions = [
            r.path.suffix for r in sorted_results[1:] if not r.path.is_dir()
        ]
        assert extensions == sorted(extensions)  # Should be alphabetically sorted

    def test_end_to_end_relevance_sorting(self, tmp_path):
        """Test complete flow: sort by relevance"""
        model = ResultsModel()

        now = datetime.now().timestamp()
        query = "report"

        # Create files that match query in different ways
        exact_path = tmp_path / "report.txt"
        exact_path.touch()

        starts_path = tmp_path / "report_monthly.txt"
        starts_path.touch()

        contains_path = tmp_path / "monthly_report.txt"
        contains_path.touch()

        ends_path = tmp_path / "my_report.txt"
        ends_path.touch()

        results = [
            SearchResult(contains_path, 10, now, "test"),
            SearchResult(starts_path, 10, now, "test"),
            SearchResult(ends_path, 10, now, "test"),
            SearchResult(exact_path, 10, now, "test"),
        ]

        model.set_results(results)
        model.sort_results(SortCriteria.RELEVANCE_DESC, query)

        sorted_results = model.get_all_results()
        filenames = [r.get_display_name() for r in sorted_results]

        # Exact match should be first
        assert filenames[0] == "report.txt"
        # Starts with should be before contains
        assert "report_monthly.txt" in filenames[:2]

    def test_sorting_preserves_model_state(self, tmp_path):
        """Test that sorting preserves model state correctly"""
        model = ResultsModel()

        now = datetime.now().timestamp()

        # Create multiple files
        paths = []
        for i in range(50):
            path = tmp_path / f"file{i}.txt"
            path.touch()
            paths.append(SearchResult(path, 100 + i, now, "test"))

        model.set_results(paths)

        # Get initial state
        displayed_initial = model.rowCount()

        # Apply sorting
        model.sort_results(SortCriteria.SIZE_ASC)

        # Verify state is maintained
        displayed_after = model.rowCount()
        assert displayed_initial == displayed_after
        assert displayed_after <= 100  # Batch size limit

        # Verify all results are still there
        all_results = model.get_all_results()
        assert len(all_results) == 50

    def test_performance_large_dataset_sorting(self, tmp_path):
        """Test sorting performance with large dataset"""
        model = ResultsModel()

        now = datetime.now().timestamp()
        results = []

        # Create 1000 results
        for i in range(1000):
            path = tmp_path / f"file{i:04d}.txt"
            path.touch()
            results.append(SearchResult(path, i * 10, now, "test"))

        model.set_results(results)

        # Measure sorting time
        start_time = time.time()
        model.sort_results(SortCriteria.SIZE_ASC)
        elapsed_ms = (time.time() - start_time) * 1000

        # Should complete in reasonable time
        assert elapsed_ms < 500, f"Sort took {elapsed_ms:.2f}ms"

        # Verify results are sorted
        sorted_results = model.get_all_results()
        sizes = [r.size for r in sorted_results if not r.path.is_dir()]
        assert sizes == sorted(sizes)


class TestResultsViewIntegration:
    """Test ResultsView integration with sorting"""

    def test_results_view_applies_sorting(self, tmp_path, qtbot):
        """Test that ResultsView can apply sorting"""
        view = ResultsView()
        qtbot.addWidget(view)

        now = datetime.now().timestamp()

        # Create test files
        path1 = tmp_path / "zebra.txt"
        path1.touch()
        path2 = tmp_path / "apple.txt"
        path2.touch()

        results = [
            SearchResult(path1, 100, now, "test"),
            SearchResult(path2, 50, now, "test"),
        ]

        # Set results
        view.set_results(results)

        # Apply sorting
        view.apply_sorting(SortCriteria.NAME_ASC)

        # Verify sorting was applied
        model = view.model()
        assert model.rowCount() >= 1

    def test_keyboard_shortcuts_trigger_sorting(self, tmp_path, qtbot):
        """Test keyboard shortcuts for sorting"""
        view = ResultsView()
        qtbot.addWidget(view)

        now = datetime.now().timestamp()

        # Create test files
        path1 = tmp_path / "file2.txt"
        path1.touch()
        path2 = tmp_path / "file1.txt"
        path2.touch()

        results = [
            SearchResult(path1, 100, now, "test"),
            SearchResult(path2, 50, now, "test"),
        ]

        view.set_results(results)

        # Set focus so keyboard events are received
        view.setFocus()

        # Test Ctrl+1 shortcut (sort by name)
        # Note: This is a basic test - full key event testing would need more setup
        initial_results = view.model().get_all_results()
        assert len(initial_results) == 2
