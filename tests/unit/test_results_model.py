"""Behavioral tests for the search-results model public Qt API."""

from pathlib import Path

from PyQt6.QtCore import Qt

from filesearch.core.sort_engine import SortCriteria
from filesearch.models.search_result import SearchResult
from filesearch.ui.results_model import ResultsModel


def make_result(path: Path, *, size: int = 10, modified: float = 0) -> SearchResult:
    return SearchResult(path=path, size=size, modified=modified)


def test_model_exposes_result_roles_and_editable_flags(tmp_path):
    path = tmp_path / "report.txt"
    path.write_text("content")
    result = make_result(path, size=7)
    model = ResultsModel()
    model.add_result(result)
    index = model.index(0)

    assert model.rowCount() == 1
    assert model.data(index) == "report.txt"
    assert model.data(index, Qt.ItemDataRole.UserRole) is result
    assert "Size: 7.0 B" in model.data(index, Qt.ItemDataRole.ToolTipRole)
    assert model.flags(index) & Qt.ItemFlag.ItemIsEditable
    assert model.data(model.index(1)) is None


def test_model_renames_a_result_and_reports_rename_errors(tmp_path, qtbot):
    original = tmp_path / "draft.txt"
    original.write_text("content")
    collision = tmp_path / "existing.txt"
    collision.write_text("content")
    model = ResultsModel()
    model.add_result(make_result(original))
    index = model.index(0)

    with qtbot.waitSignal(model.dataChanged):
        assert model.setData(index, "final.txt") is True
    assert model.data(index) == "final.txt"
    assert (tmp_path / "final.txt").exists()
    assert model.setData(index, "final.txt") is False

    with qtbot.waitSignal(model.error_occurred) as blocker:
        assert model.setData(index, "existing.txt") is False
    assert "exists" in blocker.args[0]
    assert model.setData(index, "ignored", Qt.ItemDataRole.DisplayRole) is False


def test_model_filters_adds_removes_and_clears_results(tmp_path):
    text = make_result(tmp_path / "a.TXT")
    python = make_result(tmp_path / "b.py")
    model = ResultsModel()

    model.set_extension_filter([".txt"])
    model.add_result(python)
    model.add_result(text)
    assert model.get_all_results() == [text]
    assert model.remove_result(python) is False
    assert model.remove_result(text) is True
    assert model.rowCount() == 0

    model.set_results([text, python])
    assert model.get_all_results() == [text]
    model.set_extension_filter([])
    assert model.get_all_results() == [text, python]
    model.clear()
    assert model.get_all_results() == []


def test_model_fetches_large_result_sets_in_batches(tmp_path):
    results = [make_result(tmp_path / f"item-{index:03}.txt") for index in range(205)]
    model = ResultsModel()
    model.set_results(results)

    assert model.rowCount() == 100
    assert model.canFetchMore() is True
    model.fetchMore()
    assert model.rowCount() == 200
    model.fetchMore()
    assert model.rowCount() == 205
    assert model.canFetchMore() is False
    model.fetchMore()
    assert model.rowCount() == 205

    child = model.index(0)
    assert model.canFetchMore(child) is False
    model.fetchMore(child)
    assert model.rowCount() == 205


def test_model_sorts_results_and_remembers_the_query(tmp_path):
    first = make_result(tmp_path / "zebra.txt")
    second = make_result(tmp_path / "alpha.txt")
    model = ResultsModel()
    model.set_results([first, second])

    model.sort_results(SortCriteria.NAME_ASC, "alp")

    assert model.get_all_results() == [second, first]
    assert model.get_current_sort_criteria() is SortCriteria.NAME_ASC
    assert model.get_sort_query() == "alp"

    empty = ResultsModel()
    empty.sort_results(SortCriteria.NAME_ASC)
    assert empty.get_current_sort_criteria() is None
