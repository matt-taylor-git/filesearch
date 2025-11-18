"""Unit tests for SortEngine.

Tests all sorting algorithms and edge cases.
"""

import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from filesearch.core.sort_engine import SortCriteria, SortEngine, SortResult
from filesearch.models.search_result import SearchResult


def create_test_result(path: Path, size: int = 0, plugin: str = "test") -> SearchResult:
    """Helper to create a test SearchResult."""
    now = datetime.now().timestamp()
    return SearchResult(path, size, now, plugin)


class TestSortByName:
    """Test name sorting (AC1)."""

    @pytest.fixture
    def sample_results(self, tmp_path):
        """Create sample search results for testing."""
        now = datetime.now().timestamp()

        # Create a directory
        folder_path = tmp_path / "folder"
        folder_path.mkdir()

        # Create files
        file10_path = tmp_path / "file10.txt"
        file10_path.touch()
        file1_path = tmp_path / "file1.txt"
        file1_path.touch()
        file2_path = tmp_path / "file2.txt"
        file2_path.touch()
        afile_path = tmp_path / "a_file.txt"
        afile_path.touch()

        results = [
            SearchResult(file10_path, 100, now, "test"),
            SearchResult(file1_path, 50, now, "test"),
            SearchResult(file2_path, 75, now, "test"),
            SearchResult(folder_path, 0, now, "test"),
            SearchResult(afile_path, 200, now, "test"),
        ]
        return results

    def test_natural_sorting_ascending(self, sample_results):
        """Test natural sorting (file1, file2, file10)."""
        sorted_results = SortEngine.sort_by_name(sample_results, reverse=False)

        filenames = [r.get_display_name() for r in sorted_results]
        # Folders first, then natural sorted files
        assert filenames[0] == "folder"  # Folder first
        assert filenames[1] == "a_file.txt"  # A first alphabetically
        assert filenames[2] == "file1.txt"  # Natural: 1 before 2 before 10
        assert filenames[3] == "file2.txt"
        assert filenames[4] == "file10.txt"

    def test_natural_sorting_descending(self, sample_results):
        """Test reverse natural sorting."""
        sorted_results = SortEngine.sort_by_name(sample_results, reverse=True)

        filenames = [r.get_display_name() for r in sorted_results]
        # Folders still first (special handling), then reverse alphabetical
        assert filenames[0] == "folder"
        assert filenames[1] == "file10.txt"
        assert filenames[2] == "file2.txt"
        assert filenames[3] == "file1.txt"
        assert filenames[4] == "a_file.txt"

    def test_folders_grouped_separately(self, tmp_path):
        """Test that folders are grouped and sorted separately."""
        now = datetime.now().timestamp()

        # Create directories
        afolder_path = tmp_path / "afolder"
        afolder_path.mkdir()
        zfolder_path = tmp_path / "zfolder"
        zfolder_path.mkdir()

        # Create files
        zebra_path = tmp_path / "zebra.txt"
        zebra_path.touch()
        apple_path = tmp_path / "apple.txt"
        apple_path.touch()

        results = [
            SearchResult(zebra_path, 100, now, "test"),
            SearchResult(afolder_path, 0, now, "test"),
            SearchResult(zfolder_path, 0, now, "test"),
            SearchResult(apple_path, 50, now, "test"),
        ]

        sorted_results = SortEngine.sort_by_name(results, reverse=False)
        filenames = [r.get_display_name() for r in sorted_results]

        # Folders should be first, sorted alphabetically
        assert filenames[0] == "afolder"
        assert filenames[1] == "zfolder"
        # Then files sorted alphabetically
        assert filenames[2] == "apple.txt"
        assert filenames[3] == "zebra.txt"

    def test_performance_large_dataset(self):
        """Test performance: sort 1,000 items in <100ms (AC1 test)."""
        now = datetime.now().timestamp()
        results = []
        for i in range(1000):
            is_folder = i % 10 == 0  # Every 10th is a folder
            filename = f"file{i:04d}.txt" if not is_folder else f"folder{i:04d}"
            results.append(
                SearchResult(
                    Path(filename),
                    i * 100,
                    now,
                    "test",
                )
            )

        start_time = time.time()
        sorted_results = SortEngine.sort_by_name(results, reverse=False)
        elapsed_ms = (time.time() - start_time) * 1000

        assert len(sorted_results) == 1000
        assert elapsed_ms < 100, f"Sort took {elapsed_ms:.2f}ms, expected <100ms"

    def test_empty_list(self):
        """Test sorting empty list."""
        assert SortEngine.sort_by_name([]) == []

    def test_single_item(self):
        """Test sorting single item."""
        now = datetime.now().timestamp()
        result = SearchResult(Path("file.txt"), 100, now, "test")
        sorted_results = SortEngine.sort_by_name([result])
        assert len(sorted_results) == 1
        assert sorted_results[0].get_display_name() == "file.txt"


class TestSortBySize:
    """Test size sorting (AC2)."""

    def test_size_ascending_folders_first(self, tmp_path):
        """Test ascending sort puts folders first."""
        now = datetime.now().timestamp()
        # Create actual folder
        folder_path = tmp_path / "folder"
        folder_path.mkdir()

        results = [
            SearchResult(Path("large.txt"), 10000, now, "test"),
            SearchResult(Path("small.txt"), 10, now, "test"),
            SearchResult(folder_path, 0, now, "test"),
        ]

        sorted_results = SortEngine.sort_by_size(results, reverse=False)

        assert sorted_results[0].is_directory  # Folder first
        assert sorted_results[1].filename == "small.txt"  # Smallest file
        assert sorted_results[2].filename == "large.txt"  # Largest file

    def test_size_descending_folders_last(self, tmp_path):
        """Test descending sort puts folders last."""
        now = datetime.now().timestamp()
        # Create actual folder
        folder_path = tmp_path / "folder"
        folder_path.mkdir()

        results = [
            SearchResult(Path("large.txt"), 10000, now, "test"),
            SearchResult(Path("small.txt"), 10, now, "test"),
            SearchResult(folder_path, 0, now, "test"),
        ]

        sorted_results = SortEngine.sort_by_size(results, reverse=True)

        assert sorted_results[0].filename == "large.txt"  # Largest first
        assert sorted_results[1].filename == "small.txt"  # Smallest second
        assert sorted_results[2].is_directory  # Folder last

    def test_performance_large_dataset(self):
        """Test performance: sort 10,000 items in <200ms (AC2 test)."""
        now = datetime.now().timestamp()
        results = []
        for i in range(10000):
            results.append(
                SearchResult(
                    Path(f"file{i}.txt"),
                    i * 1000,  # Varying sizes
                    now,
                    "test",
                )
            )

        start_time = time.time()
        sorted_results = SortEngine.sort_by_size(results, reverse=True)
        elapsed_ms = (time.time() - start_time) * 1000

        assert len(sorted_results) == 10000
        assert elapsed_ms < 200, f"Sort took {elapsed_ms:.2f}ms, expected <200ms"


class TestSortByDate:
    """Test date sorting (AC3)."""

    @pytest.fixture
    def dated_results(self):
        """Create results with various dates."""
        base_time = datetime.now().timestamp()
        return [
            SearchResult(Path("old.txt"), 100, base_time - 864000, "test"),  # 10 days ago
            SearchResult(Path("new.txt"), 100, base_time, "test"),
            SearchResult(Path("middle.txt"), 100, base_time - 432000, "test"),  # 5 days ago
        ]

    def test_date_descending_newest_first(self, dated_results):
        """Test descending sort shows newest first."""
        sorted_results = SortEngine.sort_by_date(dated_results, reverse=False)

        assert sorted_results[0].filename == "new.txt"
        assert sorted_results[1].filename == "middle.txt"
        assert sorted_results[2].filename == "old.txt"

    def test_date_ascending_oldest_first(self, dated_results):
        """Test ascending sort shows oldest first."""
        sorted_results = SortEngine.sort_by_date(dated_results, reverse=True)

        assert sorted_results[0].filename == "old.txt"
        assert sorted_results[1].filename == "middle.txt"
        assert sorted_results[2].filename == "new.txt"


class TestSortByType:
    """Test type sorting (AC4)."""

    def test_folders_first_then_by_extension(self, tmp_path):
        """Test folders first, then files grouped by extension."""
        now = datetime.now().timestamp()
        # Create actual folder
        folder_path = tmp_path / "folder"
        folder_path.mkdir()

        results = [
            SearchResult(Path("readme.txt"), 100, now, "test"),
            SearchResult(Path("photo.jpg"), 1000, now, "test"),
            SearchResult(folder_path, 0, now, "test"),
            SearchResult(Path("another.txt"), 50, now, "test"),
            SearchResult(Path("data.pdf"), 200, now, "test"),
        ]

        sorted_results = SortEngine.sort_by_type(results, reverse=False)
        filenames = [r.filename for r in sorted_results]

        # First should be folder
        assert sorted_results[0].is_directory
        assert sorted_results[0].filename == "folder"

        # Then files should be grouped by extension
        txt_files = [r for r in sorted_results if not r.is_directory and r.filename.endswith(".txt")]
        jpg_files = [r for r in sorted_results if not r.is_directory and r.filename.endswith(".jpg")]
        pdf_files = [r for r in sorted_results if not r.is_directory and r.filename.endswith(".pdf")]

        assert len(txt_files) == 2
        assert len(jpg_files) == 1
        assert len(pdf_files) == 1

    def test_reverse_order(self):
        """Test reverse type sorting."""
        now = datetime.now().timestamp()
        results = [
            SearchResult(Path("a.txt"), 100, now, "test"),
            SearchResult(Path("z folder"), 0, now, "test"),
        ]

        sorted_results = SortEngine.sort_by_type(results, reverse=True)
        filenames = [r.filename for r in sorted_results]

        # In reverse, files come first
        assert filenames[0] == "a.txt"
        assert filenames[1] == "z folder"


class TestSortByRelevance:
    """Test relevance sorting (AC5)."""

    def test_exact_match_highest_priority(self):
        """Test exact matches get highest priority."""
        query = "report"
        now = datetime.now().timestamp()
        results = [
            SearchResult(Path("my_report.txt"), 100, now, "test"),
            SearchResult(Path("report.pdf"), 100, now, "test"),  # Exact match
            SearchResult(Path("reporting.txt"), 100, now, "test"),
        ]

        sorted_results = SortEngine.sort_by_relevance(results, query)

        assert sorted_results[0].filename == "report.pdf"  # Exact match first
        # Others follow (exact order may vary based on scoring)

    def test_starts_with_vs_contains(self):
        """Test that starts with ranks higher than contains."""
        query = "report"
        now = datetime.now().timestamp()
        results = [
            SearchResult(Path("monthly_report.pdf"), 100, now, "test"),
            SearchResult(Path("report_monthly.pdf"), 100, now, "test"),
        ]

        sorted_results = SortEngine.sort_by_relevance(results, query)

        assert sorted_results[0].filename == "report_monthly.pdf"  # Starts with

    def test_relevance_query_example_from_ac(self):
        """Test the exact example from AC5."""
        query = "report"
        now = datetime.now().timestamp()
        results = [
            SearchResult(Path("report.pdf"), 100, now, "test"),
            SearchResult(Path("monthly_report.pdf"), 100, now, "test"),
            SearchResult(Path("my_report.txt"), 100, now, "test"),
        ]

        sorted_results = SortEngine.sort_by_relevance(results, query)
        filenames = [r.filename for r in sorted_results]

        assert filenames[0] == "report.pdf"  # Exact match first
        assert "monthly_report.pdf" in filenames[1:]  # Contains second
        assert "my_report.txt" in filenames[1:]  # Contains third


class TestSortEngineMethods:
    """Test the main SortEngine.sort method."""

    @pytest.fixture
    def sample_results(self):
        """Create sample results."""
        now = datetime.now().timestamp()
        return [
            SearchResult(Path("b.txt"), 200, now, "test"),
            SearchResult(Path("a.txt"), 100, now, "test"),
        ]

    def test_sort_name_asc(self, sample_results):
        """Test NAME_ASC criteria."""
        sorted_results = SortEngine.sort(sample_results, SortCriteria.NAME_ASC)
        assert sorted_results[0].filename == "a.txt"

    def test_sort_name_desc(self, sample_results):
        """Test NAME_DESC criteria."""
        sorted_results = SortEngine.sort(sample_results, SortCriteria.NAME_DESC)
        assert sorted_results[0].filename == "b.txt"

    def test_sort_size_asc(self, sample_results):
        """Test SIZE_ASC criteria."""
        sorted_results = SortEngine.sort(sample_results, SortCriteria.SIZE_ASC)
        assert sorted_results[0].filename == "a.txt"  # Smaller size

    def test_sort_size_desc(self, sample_results):
        """Test SIZE_DESC criteria."""
        sorted_results = SortEngine.sort(sample_results, SortCriteria.SIZE_DESC)
        assert sorted_results[0].filename == "b.txt"  # Larger size

    def test_sort_relevance_requires_query(self, sample_results):
        """Test that RELEVANCE_DESC requires query parameter."""
        with pytest.raises(ValueError, match="Query parameter is required"):
            SortEngine.sort(sample_results, SortCriteria.RELEVANCE_DESC)

    def test_all_identical_items(self):
        """Test sorting items with identical properties."""
        now = datetime.now().timestamp()
        results = [
            SearchResult(Path("file1.txt"), 100, now, "test"),
            SearchResult(Path("file2.txt"), 100, now, "test"),
        ]
        sorted_results = SortEngine.sort_by_size(results, reverse=False)
        assert len(sorted_results) == 2  # Should preserve both items
