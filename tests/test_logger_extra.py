from pathlib import Path
import logging
import pytest

from app.logger import Subject, Observer, LoggingObserver, AutoSaveObserver, CalculatorSubject
from app.exceptions import CalculatorError


def test_subject_rejects_invalid_observer():
    class BadObserver:
        pass

    sub = Subject()
    with pytest.raises(CalculatorError):
        sub.attach(BadObserver())


class _DummyObserver(Observer):
    def __init__(self):
        self.events = []
    def update(self, event_type, data):
        self.events.append((event_type, data))


def test_subject_attach_detach_and_notify():
    sub = Subject()
    d = _DummyObserver()
    sub.attach(d)
    assert sub.get_observer_count() == 1
    sub.notify("calculation", {"ok": True})
    assert d.events and d.events[0][0] == "calculation"
    sub.detach(d)
    assert sub.get_observer_count() == 0


def test_logging_observer_logs_to_file(tmp_path):
    log_file = tmp_path / "calc.log"
    obs = LoggingObserver(log_file=str(log_file), log_level="INFO")

    # calculation success
    obs.update("calculation", {"calculation": {"operation": "add", "operands": [1,2], "result": 3, "expression": "1+2"}})
    # calculation failure
    obs.update("calculation", {"calculation": {"operation": "add", "operands": [1,2], "result": None, "expression": "1/0", "error": "boom"}})
    # error
    obs.update("error", {"error_type": "ValueError", "error_message": "bad", "context": {"a": 1}})
    # undo/redo/clear
    obs.update("undo", {"previous_state": {"x": 1}})
    obs.update("redo", {"next_state": {"x": 2}})
    obs.update("clear", {"clear_type": "history"})

    assert log_file.exists()
    text = log_file.read_text()
    assert "CALCULATION:" in text and "ERROR [ValueError]" in text and "CLEAR:" in text

    # set_log_level path
    obs.set_log_level("DEBUG")
    assert logging.getLevelName(obs.logger.level) == "DEBUG"

    # Unknown event falls through and __str__ works
    obs.update("custom_event", {"foo": "bar"})
    assert "LoggingObserver(" in str(obs)


def test_logging_observer_console_mode(tmp_path):
    # Ensure stream handler path is exercised (no file)
    obs = LoggingObserver(log_file=None, log_level="INFO")
    obs.update("calculation_complete", {"calculation": {"result": 1, "expression": "1+0"}})



def test_autosave_observer_saves_and_reports(tmp_path):
    save_csv = tmp_path / "auto.csv"
    obs = AutoSaveObserver(save_file=str(save_csv), save_frequency=1, max_entries=10)

    # Send two calculation events
    for i in range(2):
        obs.update("calculation", {"calculation": {"operation": "add", "operands": [i, i], "result": i*2, "expression": f"{i}+{i}"}})
    assert save_csv.exists()

    # Stats should reflect file
    stats = obs.get_save_stats()
    assert stats["file_exists"] is True and stats["entry_count"] >= 2

    # Force save specific rows
    obs.force_save([
        {"operation": "add", "operand_a": 1, "operand_b": 2, "result": 3, "expression": "1+2", "id": "x"}
    ])
    assert save_csv.exists()

    # Clear history behavior
    obs.update("clear", {"clear_type": "history"})
    stats2 = obs.get_save_stats()
    assert stats2["file_exists"] is True
    assert "frequency" in str(obs)


def test_autosave_update_handles_errors(tmp_path, capsys, monkeypatch):
    save_csv = tmp_path / "auto2.csv"
    obs = AutoSaveObserver(save_file=str(save_csv), save_frequency=1, max_entries=10)

    def boom(data):
        raise ValueError("fail")

    monkeypatch.setattr(obs, "_handle_calculation", boom)
    obs.update("calculation", {"calculation": {}})
    out = capsys.readouterr().out
    assert "AutoSaveObserver error" in out


def test_autosave_get_save_stats_error(tmp_path, monkeypatch):
    save_csv = tmp_path / "auto3.csv"
    obs = AutoSaveObserver(save_file=str(save_csv), save_frequency=1, max_entries=10)
    save_csv.write_text("col1\nvalue")

    import app.logger as logger_module

    def bad_read_csv(path):
        raise ValueError("broken")

    monkeypatch.setattr(logger_module.pd, "read_csv", bad_read_csv)
    stats = obs.get_save_stats()
    assert stats["file_exists"] is True and "error" in stats


def test_calculator_subject_event_names(tmp_path):
    sub = CalculatorSubject()
    d = _DummyObserver()
    sub.attach(d)

    sub.notify_calculation({"operation": "add", "operands": [1,2], "result": 3, "expression": "1+2"})
    sub.notify_error("ValueError", "bad", {"a": 1})
    sub.notify_undo({"x": 1})
    sub.notify_redo({"x": 2})
    sub.notify_clear("history")

    # Should have received 5 events
    assert len(d.events) == 5
