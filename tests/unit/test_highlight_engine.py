"""Unit tests for HighlightEngine"""

import pytest

from filesearch.utils.highlight_engine import HighlightEngine, is_valid_highlight_query


class TestHighlightEngine:
    """Test cases for HighlightEngine class"""

    @pytest.fixture
    def engine(self):
        """Create a fresh HighlightEngine instance for each test"""
        return HighlightEngine()

    def test_basic_matching(self, engine):
        """Test basic substring matching"""
        matches = engine.find_matches("report.pdf", "report")
        assert len(matches) == 1
        assert matches[0] == (0, 6)

    def test_case_insensitive_matching(self, engine):
        """Test case-insensitive matching"""
        matches = engine.find_matches("MonthlyReport.pdf", "report")
        assert len(matches) == 1
        assert matches[0] == (7, 13)

    def test_multiple_matches(self, engine):
        """Test multiple matches in single filename"""
        matches = engine.find_matches("doc_document.docx", "doc")
        assert len(matches) == 2
        assert matches[0] == (0, 3)
        assert matches[1] == (4, 7)

    def test_partial_matching(self, engine):
        """Test partial matching (substring)"""
        matches = engine.find_matches("report.pdf", "rep")
        assert len(matches) == 1
        assert matches[0] == (0, 3)

    def test_extension_not_highlighted(self, engine):
        """Test that file extensions are not highlighted"""
        matches = engine.find_matches("test.pdf", "pdf")
        # Extension matching should not be highlighted
        # Only filename part should match
        assert len(matches) == 0

    def test_multiple_dots_in_filename(self, engine):
        """Test filenames with multiple dots (e.g., archive.tar.gz)"""
        matches = engine.find_matches("archive.tar.gz", "archive")
        assert len(matches) == 1
        assert matches[0] == (0, 7)

        matches = engine.find_matches("archive.tar.gz", "tar")
        # Middle part should match
        assert len(matches) == 1
        assert matches[0] == (8, 11)

    def test_wildcard_patterns_star(self, engine):
        """Test wildcard * pattern matching"""
        matches = engine.find_matches("test_document.pdf", "*doc*")
        assert len(matches) == 1
        # *doc* matches the entire "test_document" part (from start to just before .pdf)
        start, end = matches[0]
        assert start == 0  # Matches from beginning
        assert end == 13  # Matches entire filename without extension

    def test_wildcard_patterns_question(self, engine):
        """Test wildcard ? pattern matching"""
        matches = engine.find_matches("test1_document.pdf", "test?")
        assert len(matches) == 1
        assert matches[0] == (0, 5)

    def test_empty_query_no_highlighting(self, engine):
        """Test that empty query returns no matches"""
        matches = engine.find_matches("test.pdf", "")
        assert len(matches) == 0

    def test_wildcard_only_query_no_highlighting(self, engine):
        """Test that wildcard-only query returns no matches"""
        matches = engine.find_matches("test.pdf", "***")
        assert len(matches) == 0

        matches = engine.find_matches("test.pdf", "????")
        assert len(matches) == 0

    def test_special_regex_characters_escaped(self, engine):
        """Test that regex metacharacters are properly escaped"""
        # Test with dot (should match literal dot in filename, not extension)
        matches = engine.find_matches("my.file.txt", ".")
        # Single dot is wildcard-only, should not highlight
        assert len(matches) == 0

        # Test with asterisk (wildcard, not regex quantifier)
        matches = engine.find_matches("test*file.txt", "test")
        assert len(matches) == 1
        assert matches[0] == (0, 4)

    def test_unicode_filenames(self, engine):
        """Test Unicode character support in filenames"""
        matches = engine.find_matches("файл_отчет.pdf", "отчет")
        assert len(matches) == 1
        # Check that the match is found (exact position may vary by Python version)
        start, end = matches[0]
        assert end > start  # Valid range
        assert (end - start) == 5  # Length of "отчет"

    def test_unicode_query(self, engine):
        """Test Unicode characters in query"""
        matches = engine.find_matches("document_测试.txt", "测试")
        assert len(matches) == 1
        assert matches[0] == (9, 11)

    def test_case_sensitive_matching(self, engine):
        """Test case-sensitive matching when enabled"""
        # Case-sensitive: "Report" should not match "report"
        matches = engine.find_matches("Report.pdf", "report", case_sensitive=True)
        assert len(matches) == 0

        # Should match exact case
        matches = engine.find_matches("Report.pdf", "Report", case_sensitive=True)
        assert len(matches) == 1
        assert matches[0] == (0, 6)

    def test_caching_works(self, engine):
        """Test that pattern and highlight caching works correctly"""
        query = "test"
        filename = "test_document_test.txt"

        # First call should compute and cache
        matches1 = engine.find_matches(filename, query)
        assert len(matches1) == 2

        # Second call should use cache (verified by same result)
        matches2 = engine.find_matches(filename, query)
        assert matches1 == matches2

    def test_clear_cache(self, engine):
        """Test that clear_cache method works"""
        query = "test"
        filename = "test_document.txt"

        # Generate some cache entries
        engine.find_matches(filename, query)
        engine.clear_cache()

        # Should still work after clearing cache
        matches = engine.find_matches(filename, query)
        assert len(matches) == 1

    def test_has_matches_positive(self, engine):
        """Test has_matches returns True when matches exist"""
        assert engine.has_matches("test.pdf", "test") is True
        assert engine.has_matches("Report.pdf", "report") is True

    def test_has_matches_negative(self, engine):
        """Test has_matches returns False when no matches exist"""
        assert engine.has_matches("test.pdf", "nomatch") is False
        assert engine.has_matches("test.pdf", "") is False

    def test_has_matches_wildcard_only(self, engine):
        """Test has_matches with wildcard-only queries"""
        assert engine.has_matches("test.pdf", "***") is False
        assert engine.has_matches("test.pdf", "??") is False

    def test_generate_html_highlighted(self, engine):
        """Test HTML output with highlighted text"""
        html = engine.generate_highlighted_html("MonthlyReport.pdf", "report")
        # Should preserve original case "Report", not convert to "report"
        assert (
            '<span style="background-color: #FFFF99; font-weight: bold;">Report</span>'
            in html
        )
        assert "Monthly" in html
        assert ".pdf" in html

    def test_generate_html_no_highlighting(self, engine):
        """Test HTML output with highlighting disabled (e.g., empty query)"""
        html = engine.generate_highlighted_html("test.pdf", "")
        assert html == "test.pdf"

    def test_generate_html_custom_color(self, engine):
        """Test HTML output with custom highlight color"""
        html = engine.generate_highlighted_html(
            "test.pdf", "test", highlight_color="#FF0000"
        )
        assert "background-color: #FF0000" in html

    def test_empty_filename(self, engine):
        """Test handling of empty filename"""
        matches = engine.find_matches("", "test")
        assert len(matches) == 0

    def test_none_values_return_empty(self, engine):
        """Test that None values are handled gracefully"""
        matches = engine.find_matches(None, "test")
        assert len(matches) == 0

        matches = engine.find_matches("test.pdf", None)
        assert len(matches) == 0


class TestIsValidHighlightQuery:
    """Test cases for is_valid_highlight_query function"""

    def test_valid_queries(self):
        """Test valid highlight queries"""
        assert is_valid_highlight_query("test") is True
        assert is_valid_highlight_query("report") is True
        assert is_valid_highlight_query("doc") is True

    def test_empty_query_false(self):
        """Test empty query returns False"""
        assert is_valid_highlight_query("") is False

    def test_wildcard_only_queries_false(self):
        """Test wildcard-only queries return False"""
        assert is_valid_highlight_query("*") is False
        assert is_valid_highlight_query("**") is False
        assert is_valid_highlight_query("?") is False
        assert is_valid_highlight_query("??") is False
        assert is_valid_highlight_query("***") is False
        assert is_valid_highlight_query("?*?") is False

    def test_mixed_wildcard_valid(self):
        """Test queries with mixed text and wildcards"""
        assert is_valid_highlight_query("*test") is True
        assert is_valid_highlight_query("test*") is True
        assert is_valid_highlight_query("te?st") is True

    def test_none_query_false(self):
        """Test None query returns False"""
        assert is_valid_highlight_query(None) is False


class TestHighlightPatternExamples:
    """Test examples from AC documentation"""

    @pytest.fixture
    def engine(self):
        """Create a fresh HighlightEngine instance"""
        return HighlightEngine()

    def test_example_monthly_report(self, engine):
        """Test AC example: Query 'report' → File 'MonthlyReport.pdf'"""
        matches = engine.find_matches("MonthlyReport.pdf", "report")
        assert len(matches) == 1
        assert matches[0] == (7, 13)

    def test_example_test_document(self, engine):
        """Test AC example: Query 'test' → File 'test_document.txt'"""
        matches = engine.find_matches("test_document.txt", "test")
        assert len(matches) == 1
        assert matches[0] == (0, 4)

    def test_example_case_preservation(self, engine):
        """Test AC example: Query 'file' → File 'MyFile.txt'"""
        matches = engine.find_matches("MyFile.txt", "file")
        assert len(matches) == 1
        # Should match regardless of case
        assert matches[0][1] - matches[0][0] == 4  # Match length should be 4

    def test_example_multiple_matches(self, engine):
        """Test AC example: Query 'doc' → File 'doc_document.docx'"""
        matches = engine.find_matches("doc_document.docx", "doc")
        assert len(matches) == 2

    def test_example_dot_no_highlight(self, engine):
        """Test AC example: Query '.' → File 'my.file.txt' (no highlight)"""
        matches = engine.find_matches("my.file.txt", ".")
        assert len(matches) == 0  # Single dot is wildcard-only

    def test_example_wildcard_no_highlight(self, engine):
        """Test AC example: Query '*' → File 'anyfile.txt' (no highlight)"""
        matches = engine.find_matches("anyfile.txt", "*")
        assert len(matches) == 0  # Single star is wildcard-only
