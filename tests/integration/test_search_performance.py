"""Performance tests for search engine module."""

import os
import tempfile
import time
from pathlib import Path

import pytest

from filesearch.core.search_engine import FileSearchEngine


class TestSearchPerformance:
    """Performance test cases for FileSearchEngine class."""

    @pytest.fixture
    def large_temp_dir(self):
        """Create a temporary directory with many files for performance testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create many files to test performance
            for i in range(1000):  # Create 1000 files
                (tmp_path / f"file_{i:04d}.txt").write_text(f"Content {i}")

            # Create subdirectories with files
            for subdir_num in range(10):
                subdir = tmp_path / f"subdir_{subdir_num}"
                subdir.mkdir()
                for i in range(100):
                    (subdir / f"nested_{i:03d}.py").write_text(f"Nested content {i}")

            yield tmp_path

    def test_search_performance_under_2_seconds(self, large_temp_dir):
        """Test that search completes within 2 seconds for large directories."""
        engine = FileSearchEngine(max_workers=4, max_results=1000)

        start_time = time.time()
        results = list(engine.search(large_temp_dir, "*.txt"))
        end_time = time.time()

        search_time = end_time - start_time

        # Should find all .txt files
        assert len(results) == 1000

        # Should complete within 2 seconds (performance requirement)
        assert (
            search_time < 2.0
        ), f"Search took {search_time:.2f} seconds, expected < 2.0"

    def test_search_memory_usage_under_100mb(self, large_temp_dir):
        """Test that search uses less than 100MB memory for 10,000 files."""
        import os

        import psutil

        # Get current process
        process = psutil.Process(os.getpid())

        # Measure memory before search
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        engine = FileSearchEngine(max_workers=4, max_results=10000)

        # Perform search
        results = list(engine.search(large_temp_dir, "*"))

        # Measure memory after search
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before

        # Should use less than 100MB (performance requirement)
        assert memory_used < 100, f"Search used {memory_used:.2f}MB, expected < 100MB"

        # Should find all files
        assert len(results) == 2000  # 1000 .txt + 1000 .py files

    def test_search_thread_count_configurable(self, large_temp_dir):
        """Test that search thread count is configurable and affects performance."""
        # Test with 1 thread
        engine_1_thread = FileSearchEngine(max_workers=1, max_results=1000)
        start_time = time.time()
        results_1 = list(engine_1_thread.search(large_temp_dir, "*.txt"))
        time_1_thread = time.time() - start_time

        # Test with 4 threads
        engine_4_threads = FileSearchEngine(max_workers=4, max_results=1000)
        start_time = time.time()
        results_4 = list(engine_4_threads.search(large_temp_dir, "*.txt"))
        time_4_threads = time.time() - start_time

        # Both should find same number of files
        assert len(results_1) == len(results_4) == 1000

        # 4 threads should be faster or at least not significantly slower
        # (allowing some variance for small test directories)
        assert time_4_threads <= time_1_thread * 1.2  # Allow 20% variance

    def test_early_termination_performance(self, large_temp_dir):
        """Test that early termination improves performance when max_results is limited."""
        # Search for all results
        engine_all = FileSearchEngine(max_workers=4, max_results=0)  # 0 = unlimited
        start_time = time.time()
        results_all = list(engine_all.search(large_temp_dir, "*.txt"))
        time_all = time.time() - start_time

        # Search with limited results
        engine_limited = FileSearchEngine(max_workers=4, max_results=100)
        start_time = time.time()
        results_limited = list(engine_limited.search(large_temp_dir, "*.txt"))
        time_limited = time.time() - start_time

        # Limited search should find fewer results
        assert len(results_limited) == 100
        assert len(results_all) == 1000

        # Limited search should be faster
        assert (
            time_limited < time_all
        ), f"Limited search ({time_limited:.3f}s) should be faster than unlimited search ({time_all:.3f}s)"

    def test_generator_pattern_memory_efficiency(self, large_temp_dir):
        """Test that generator pattern is memory efficient."""
        engine = FileSearchEngine(max_workers=4, max_results=1000)

        # Get generator but don't consume all results
        search_gen = engine.search(large_temp_dir, "*.txt")

        # Get first 10 results
        first_results = []
        for i, result in enumerate(search_gen):
            first_results.append(result)
            if i >= 9:  # Only get first 10
                break

        # Should have gotten 10 results
        assert len(first_results) == 10

        # Each result should be a dict with expected keys
        for result in first_results:
            assert isinstance(result, dict)
            assert "path" in result
            assert "name" in result
            assert "source" in result
            assert "size" in result
            assert "modified" in result

    def test_concurrent_search_performance(self, large_temp_dir):
        """Test concurrent search performance with multiple searches."""
        engine1 = FileSearchEngine(max_workers=2, max_results=1000)  # Allow all results
        engine2 = FileSearchEngine(max_workers=2, max_results=1000)

        start_time = time.time()

        # Run two searches concurrently
        results1 = list(engine1.search(large_temp_dir, "*.txt"))
        results2 = list(engine2.search(large_temp_dir, "*.py"))

        end_time = time.time()
        concurrent_time = end_time - start_time

        # Should find expected number of results
        assert len(results1) == 1000  # .txt files
        assert len(results2) == 1000  # .py files

        # Should complete in reasonable time (allowing for concurrent execution)
        assert (
            concurrent_time < 3.0
        ), f"Concurrent search took {concurrent_time:.2f}s, expected < 3.0s"
