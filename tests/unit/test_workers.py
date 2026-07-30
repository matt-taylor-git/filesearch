"""Behavioral tests for background worker signal contracts."""

from unittest.mock import Mock

from filesearch.core.exceptions import FileSearchError, SearchError
from filesearch.ui.search_worker import SearchWorker
from filesearch.ui.storage_worker import StorageWorker


def test_search_worker_emits_results_progress_and_completion(tmp_path):
    engine = Mock()
    engine.search.return_value = ({"name": f"file-{index}"} for index in range(10))
    worker = SearchWorker(engine, tmp_path, "file")
    results = []
    progress = []
    completed = []
    worker.result_found.connect(lambda result, number: results.append((result, number)))
    worker.progress_update.connect(
        lambda percent, path, count: progress.append((percent, path, count))
    )
    worker.search_complete.connect(lambda files, dirs: completed.append((files, dirs)))

    worker.run()

    assert results[-1] == ({"name": "file-9"}, 10)
    assert progress == [(50, str(tmp_path), 10)]
    assert completed == [(10, 0)]


def test_search_worker_stop_cancels_search_and_emits_stopped(tmp_path):
    engine = Mock()
    worker = SearchWorker(engine, tmp_path, "file")

    def results_stopping_after_first():
        yield {"name": "first"}
        worker.stop()
        yield {"name": "ignored"}

    engine.search.return_value = results_stopping_after_first()
    stopped = []
    worker.search_stopped.connect(lambda files, dirs: stopped.append((files, dirs)))

    worker.run()

    engine.cancel.assert_called_once_with()
    assert stopped == [(1, 0)]


def test_search_worker_distinguishes_expected_and_unexpected_errors(tmp_path):
    engine = Mock()
    worker = SearchWorker(engine, tmp_path, "file")
    errors = []
    worker.error_occurred.connect(lambda message, code: errors.append((message, code)))

    engine.search.side_effect = FileSearchError("search failed")
    worker.run()
    engine.search.side_effect = RuntimeError("broken")
    worker.run()

    assert errors == [("search failed", 1), ("Unexpected error: broken", 2)]


def test_storage_worker_forwards_progress_and_completes(tmp_path):
    analyzer = Mock()
    analyzer.is_cancelled.return_value = False
    result = object()

    def analyze(root, progress):
        progress(str(root / "child"), 3, 1)
        return result

    analyzer.analyze.side_effect = analyze
    worker = StorageWorker(analyzer, tmp_path)
    progress_updates = []
    completed = []
    worker.progress_update.connect(
        lambda path, count, skipped: progress_updates.append((path, count, skipped))
    )
    worker.analysis_complete.connect(completed.append)

    worker.run()

    assert progress_updates == [(str(tmp_path / "child"), 3, 1)]
    assert completed == [result]


def test_storage_worker_emits_cancellation_and_errors(tmp_path):
    analyzer = Mock()
    worker = StorageWorker(analyzer, tmp_path)
    cancelled = []
    errors = []
    worker.analysis_cancelled.connect(lambda: cancelled.append(True))
    worker.analysis_error.connect(errors.append)

    analyzer.analyze.return_value = object()
    analyzer.is_cancelled.return_value = True
    worker.run()

    analyzer.analyze.side_effect = SearchError("cancelled by user")
    worker.run()

    analyzer.analyze.side_effect = SearchError("unreadable")
    analyzer.is_cancelled.return_value = False
    worker.run()

    analyzer.analyze.side_effect = RuntimeError("broken")
    worker.run()

    assert cancelled == [True, True]
    assert errors == ["unreadable", "Unexpected error: broken"]


def test_storage_worker_stop_requests_cancellation(tmp_path):
    analyzer = Mock()
    worker = StorageWorker(analyzer, tmp_path)

    worker.stop()

    analyzer.cancel.assert_called_once_with()
