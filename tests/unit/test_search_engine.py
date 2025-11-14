"""Unit tests for the search engine module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from filesearch.core.exceptions import SearchError
from filesearch.core.search_engine import FileSearchEngine, search_files


class TestFileSearchEngine:
    """Test cases for FileSearchEngine class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory with test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create test files
            (tmp_path / "test1.txt").write_text("content1")
            (tmp_path / "test2.py").write_text("content2")
            (tmp_path / "data.json").write_text('{"key": "value"}')
            (tmp_path / "README.md").write_text("# README")
            
            # Create subdirectories with files
            subdir = tmp_path / "subdir"
            subdir.mkdir()
            (subdir / "nested.txt").write_text("nested content")
            (subdir / "script.py").write_text("print('hello')")
            
            yield tmp_path
    
    @pytest.fixture
    def search_engine(self):
        """Create a FileSearchEngine instance for testing."""
        return FileSearchEngine(max_workers=2, max_results=100)
    
    def test_init_default_values(self):
        """Test default initialization values."""
        engine = FileSearchEngine()
        assert engine.max_workers == 4
        assert engine.max_results == 1000
        assert engine._cancelled is False
        assert engine._executor is None
    
    def test_init_custom_values(self):
        """Test initialization with custom values."""
        engine = FileSearchEngine(max_workers=8, max_results=500)
        assert engine.max_workers == 8
        assert engine.max_results == 500
    
    def test_cancel(self, search_engine):
        """Test search cancellation."""
        assert search_engine._cancelled is False
        search_engine.cancel()
        assert search_engine._cancelled is True
    
    def test_reset_cancel_state(self, search_engine):
        """Test resetting cancellation state."""
        search_engine.cancel()
        assert search_engine._cancelled is True
        search_engine._reset_cancel_state()
        assert search_engine._cancelled is False
    
    def test_match_pattern_exact(self, search_engine):
        """Test exact pattern matching."""
        assert search_engine._match_pattern("test.txt", "test.txt") is True
        assert search_engine._match_pattern("test.txt", "other.txt") is False
    
    def test_match_pattern_wildcard(self, search_engine):
        """Test wildcard pattern matching."""
        assert search_engine._match_pattern("test.txt", "*.txt") is True
        assert search_engine._match_pattern("test.py", "*.txt") is False
        assert search_engine._match_pattern("test.txt", "test.*") is True
        assert search_engine._match_pattern("other.txt", "test.*") is False
    
    def test_match_pattern_case_insensitive(self, search_engine):
        """Test case-insensitive pattern matching."""
        assert search_engine._match_pattern("Test.TXT", "*.txt") is True
        assert search_engine._match_pattern("TEST.PY", "*.py") is True
        assert search_engine._match_pattern("test.TXT", "*.TXT") is True
    
    def test_search_with_txt_files(self, search_engine, temp_dir):
        """Test searching for .txt files."""
        results = list(search_engine.search(temp_dir, "*.txt"))
        
        assert len(results) == 2
        result_names = {r.name for r in results}
        assert result_names == {"test1.txt", "nested.txt"}
    
    def test_search_with_py_files(self, search_engine, temp_dir):
        """Test searching for .py files."""
        results = list(search_engine.search(temp_dir, "*.py"))
        
        assert len(results) == 2
        result_names = {r.name for r in results}
        assert result_names == {"test2.py", "script.py"}
    
    def test_search_with_specific_filename(self, search_engine, temp_dir):
        """Test searching for specific filename."""
        results = list(search_engine.search(temp_dir, "README.md"))
        
        assert len(results) == 1
        assert results[0].name == "README.md"
    
    def test_search_no_matches(self, search_engine, temp_dir):
        """Test search with no matching files."""
        results = list(search_engine.search(temp_dir, "*.nonexistent"))
        
        assert len(results) == 0
    
    def test_search_nonexistent_directory(self, search_engine):
        """Test searching in non-existent directory."""
        with pytest.raises(SearchError, match="Directory does not exist"):
            list(search_engine.search(Path("/nonexistent/path"), "*.txt"))
    
    def test_search_file_not_directory(self, search_engine, temp_dir):
        """Test searching in a file instead of directory."""
        file_path = temp_dir / "test1.txt"
        
        with pytest.raises(SearchError, match="Path is not a directory"):
            list(search_engine.search(file_path, "*.txt"))
    
    def test_search_empty_query(self, search_engine, temp_dir):
        """Test search with empty query."""
        with pytest.raises(ValueError, match="Directory and query must not be empty"):
            list(search_engine.search(temp_dir, ""))
    
    def test_search_empty_directory(self, search_engine):
        """Test search in empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results = list(search_engine.search(Path(tmpdir), "*.txt"))
            assert len(results) == 0
    
    def test_search_with_early_termination(self, temp_dir):
        """Test early termination when max_results is reached."""
        # Create many files to test early termination
        for i in range(20):
            (temp_dir / f"test{i}.txt").write_text(f"content{i}")
        
        engine = FileSearchEngine(max_workers=2, max_results=5)
        results = list(engine.search(temp_dir, "*.txt"))
        
        # Should stop at max_results
        assert len(results) == 5
        assert engine._cancelled is True  # Should be cancelled after reaching limit
    
    def test_search_cancellation(self, search_engine, temp_dir):
        """Test search cancellation during execution."""
        # Create many files to ensure search takes some time
        for i in range(50):
            (temp_dir / f"test{i}.txt").write_text(f"content{i}")
        
        # Start search in a way we can cancel it
        results = []
        search_gen = search_engine.search(temp_dir, "*.txt")
        
        # Get a few results
        for _ in range(3):
            try:
                results.append(next(search_gen))
            except StopIteration:
                break
        
        # Cancel the search
        search_engine.cancel()
        
        # Try to get more results (should stop due to cancellation)
        remaining_results = list(search_gen)
        
        # Should have stopped early due to cancellation
        assert len(remaining_results) == 0
        assert search_engine._cancelled is True
    
    def test_search_permission_denied(self, search_engine, temp_dir):
        """Test search with permission denied errors."""
        # Create a subdirectory and make it inaccessible (if possible)
        restricted_dir = temp_dir / "restricted"
        restricted_dir.mkdir()
        
        # Try to make it inaccessible (this may not work on all systems)
        try:
            os.chmod(restricted_dir, 0o000)
            
            # Should not raise exception, just skip inaccessible directories
            results = list(search_engine.search(temp_dir, "*.txt"))
            # Should still find other files
            assert len(results) >= 2  # At least the files we created
            
        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(restricted_dir, 0o755)
            except:
                pass
    
    def test_search_unicode_filenames(self, search_engine, temp_dir):
        """Test search with Unicode filenames."""
        # Create files with Unicode names
        unicode_file = temp_dir / "测试文件.txt"
        unicode_file.write_text("Unicode content")
        
        emoji_file = temp_dir / "📄文档.txt"
        emoji_file.write_text("Emoji filename")
        
        results = list(search_engine.search(temp_dir, "*.txt"))
        
        # Should find all .txt files including Unicode ones
        result_names = {r.name for r in results}
        assert "测试文件.txt" in result_names
        assert "📄文档.txt" in result_names
    
    def test_search_generator_pattern(self, search_engine, temp_dir):
        """Test that search uses generator pattern correctly."""
        # Create many files
        for i in range(20):
            (temp_dir / f"test{i}.txt").write_text(f"content{i}")
        
        # Get generator
        search_gen = search_engine.search(temp_dir, "*.txt")
        
        # Should be a generator
        assert hasattr(search_gen, '__iter__')
        assert hasattr(search_gen, '__next__')
        
        # Should yield results one by one
        count = 0
        for result in search_gen:
            count += 1
            assert isinstance(result, Path)
            if count >= 5:  # Just test first 5
                break
        
        assert count == 5
    
    def test_search_with_string_path(self, search_engine, temp_dir):
        """Test search with string path instead of Path object."""
        results = list(search_engine.search(str(temp_dir), "*.txt"))
        
        assert len(results) == 2
        result_names = {r.name for r in results}
        assert result_names == {"test1.txt", "nested.txt"}
    
    def test_search_nested_directories(self, search_engine, temp_dir):
        """Test search in deeply nested directory structure."""
        # Create nested structure
        nested = temp_dir
        for i in range(5):
            nested = nested / f"level{i}"
            nested.mkdir()
            (nested / f"file{i}.txt").write_text(f"content{i}")
        
        results = list(search_engine.search(temp_dir, "*.txt"))
        
        # Should find files at all levels
        assert len(results) >= 7  # 2 original + 5 nested
        
        # Check that nested files are found
        result_paths = {str(r) for r in results}
        assert any("level0" in path for path in result_paths)
        assert any("level4" in path for path in result_paths)


class TestSearchFilesFunction:
    """Test cases for the convenience search_files function."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory with test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "test1.txt").write_text("content1")
            (tmp_path / "test2.py").write_text("content2")
            yield tmp_path
    
    def test_search_files_convenience(self, temp_dir):
        """Test convenience function for searching files."""
        results = list(search_files(temp_dir, "*.txt", max_results=10, max_workers=2))
        
        assert len(results) == 1
        assert results[0].name == "test1.txt"
    
    def test_search_files_default_params(self, temp_dir):
        """Test convenience function with default parameters."""
        results = list(search_files(temp_dir, "*.py"))
        
        assert len(results) == 1
        assert results[0].name == "test2.py"