import os
import logging
from pathlib import Path
import pytest

from app.logger import Subject, LoggingObserver, AutoSaveObserver, CalculatorSubject
from app.exceptions import FileOperationError, CalculatorError


def test_subject_attach_detach_and_notify_error_swallow(monkeypatch):
    s = Subject()

    class Bad:
        def update(self, *args, **kwargs):
            raise RuntimeError("boom")

    b = Bad()
    s.attach(b)
    assert s.get_observer_count() == 1

    # During pytest, errors are swallowed silently
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "1")
    s.notify("calculation", {"calculation": {"operation": "add", "operands": [1, 2], "result": 3, "expression": "1+2", "id": "x"}})
    # No exception raised

    s.detach(b)
    assert s.get_observer_count() == 0

    # Without pytest env, errors should be logged via logging (no exception)
    s.attach(b)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    s.notify("calculation", {"calculation": {"operation": "add", "operands": [1, 2], "result": 3, "expression": "1+2", "id": "x"}})


def test_logging_observer_paths_and_levels(tmp_path):
    log_file = tmp_path / "app.log"
    lo = LoggingObserver(log_file=str(log_file), log_level="DEBUG")

    # calculation success and failure
    lo.update("calculation", {"calculation": {"operation": "add", "operands": [1,2], "result": 3, "expression": "1+2"}})
    lo.update("calculation", {"calculation": {"operation": "divide", "operands": [1,0], "result": None, "expression": "1/0", "error": "Division by zero"}})

    # error, undo, redo, clear, and unknown
    lo.update("error", {"error_type": "X", "error_message": "bad", "context": {"a": 1}})
    lo.update("undo_performed", {"previous_state": {"x": 1}})
    lo.update("redo_performed", {"next_state": {"x": 2}})
    lo.update("clear", {"clear_type": "history"})
    lo.update("something_else", {"foo": "bar"})

    # change level
    lo.set_log_level("INFO")

    assert log_file.exists() and log_file.stat().st_size > 0


def test_autosave_observer_save_and_errors(tmp_path, monkeypatch):
    save_file = tmp_path / "hist" / "h.csv"
    ao = AutoSaveObserver(save_file=str(save_file), save_frequency=1, max_entries=2)

    # successful save on calculation events
    ao.update("calculation", {"calculation": {"id": "1", "operation": "add", "operands": [1,2], "result": 3, "expression": "1+2"}})
    ao.update("calculation", {"calculation": {"id": "2", "operation": "add", "operands": [3,4], "result": 7, "expression": "3+4"}})

    stats = ao.get_save_stats()
    assert stats["file_exists"] is True and stats["entry_count"] >= 1

    # clear history path
    ao.update("clear", {"clear_type": "history"})

    # force error by monkeypatching to_csv
    import pandas as pd
    real_to_csv = pd.DataFrame.to_csv

    def bad_to_csv(self, *args, **kwargs):
        raise OSError("deny")

    try:
        pd.DataFrame.to_csv = bad_to_csv
        with pytest.raises(FileOperationError):
            ao.force_save([{"id": "3", "operation": "add", "operand_a": 1, "operand_b": 2, "result": 3, "expression": "1+2"}])
    finally:
        pd.DataFrame.to_csv = real_to_csv


def test_calculator_subject_event_names():
    cs = CalculatorSubject()
    # Just ensure it doesn't raise and increments counters
    cs.notify_calculation({"operation": "add", "operands": [1,2], "result": 3, "expression": "1+2", "id": "x"})
    cs.notify_error("Type", "msg", {"c": 1})
    cs.notify_undo({"prev": 1})
    cs.notify_redo({"next": 2})
    cs.notify_clear("all")
    assert cs.get_calculation_count() == 1
    cs.reset_calculation_count()
    assert cs.get_calculation_count() == 0
