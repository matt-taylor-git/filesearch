"""Opt-in tests of File Search through real operating-system processes."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import platformdirs
import pytest

from filesearch import APP_AUTHOR, APP_INTERNAL_NAME, __version__


def _subprocess_environment() -> dict[str, str]:
    """Return an isolated environment suitable for a child application."""
    environment = os.environ.copy()
    environment["QT_QPA_PLATFORM"] = "offscreen"
    return environment


def test_module_entrypoint_reports_version_from_child_process(tmp_path: Path) -> None:
    """The public module entrypoint runs successfully in a fresh process."""
    completed = subprocess.run(
        [sys.executable, "-m", "filesearch", "--version"],
        cwd=tmp_path,
        env=_subprocess_environment(),
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout == f"File Search v{__version__}\n"
    assert completed.stderr == ""


@pytest.mark.timeout(30)
def test_application_process_initializes_real_gui_runtime(
    tmp_path: Path, hermetic_user_environment: Path
) -> None:
    """The production composition root reaches its Qt event loop without mocks."""
    environment = _subprocess_environment()
    log_dir = Path(platformdirs.user_log_dir(APP_INTERNAL_NAME, APP_AUTHOR))
    log_file = log_dir / "filesearch.log"
    log_file.unlink(missing_ok=True)
    process = subprocess.Popen(
        [sys.executable, "-m", "filesearch"],
        cwd=tmp_path,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            if process.poll() is not None:
                stderr = process.communicate(timeout=1)[1]
                pytest.fail(
                    f"File Search exited before initialization "
                    f"(code {process.returncode}):\n{stderr}"
                )
            if log_file.exists() and "Application initialized successfully" in (
                log_file.read_text(encoding="utf-8")
            ):
                break
            time.sleep(0.05)
        else:
            pytest.fail(f"File Search did not initialize; expected log at {log_file}")

        assert process.poll() is None
        assert log_file.is_relative_to(hermetic_user_environment)
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate(timeout=5)
