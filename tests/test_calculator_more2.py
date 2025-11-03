import os
import tempfile
from pathlib import Path
import pytest

from app.calculator import Calculator
from app.calculator_config import CalculatorConfig
from app.exceptions import ValidationError


def test_init_disables_logging_and_autosave_under_pytest_env(monkeypatch):
    # Start with a config that would enable both
    cfg = CalculatorConfig(env_file=None, auto_create_dirs=False)
    cfg.set_config_value("CALCULATOR_ENABLE_AUTO_SAVE", True)
    cfg.set_config_value("CALCULATOR_ENABLE_LOGGING", True)

    # Simulate pytest environment
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "x::y (call)")

    c = Calculator(config=cfg)
    assert c.config.is_auto_save_enabled() is False
    assert c.config.is_logging_enabled() is False


def test_calculate_respects_max_input_limits(monkeypatch):
    cfg = CalculatorConfig(env_file=None, auto_create_dirs=False)
    # Override max input value to a tiny number to force validation failure
    monkeypatch.setattr(cfg, "get_max_input_value", lambda: 10)
    c = Calculator(config=cfg)

    with pytest.raises(ValidationError):
        c.calculate("add", 20, 1)


def test_get_statistics_and_available_operations_and_wrappers(tmp_path):
    cfg = CalculatorConfig(env_file=None, auto_create_dirs=False)
    c = Calculator(config=cfg)

    # Exercise available operations
    ops = c.get_available_operations()
    assert isinstance(ops, list) and "add" in ops

    # Make a couple of entries and test get_statistics structure
    c.calculate("add", 1, 2)
    c.calculate("multiply", 2, 3)
    stats = c.get_statistics()
    assert "session" in stats and "history" in stats and "undo_redo" in stats and "configuration" in stats

    # Test export_history and load_history wrappers
    csv_path = tmp_path / "hist.csv"
    json_path = tmp_path / "hist.json"
    c.export_history(str(csv_path), format="csv")
    c.export_history(str(json_path), format="json")
    assert csv_path.exists() and json_path.exists()

    # Clear and then load back via wrapper
    c.clear_history()
    c.load_history(str(csv_path))
    assert len(c.history.get_all_calculations()) >= 1


def test_save_state_fallback_to_save_memento(monkeypatch):
    cfg = CalculatorConfig(env_file=None, auto_create_dirs=False)
    # Ensure undo/redo is enabled
    cfg.set_config_value("CALCULATOR_ENABLE_UNDO_REDO", True)
    c = Calculator(config=cfg)

    called = {"fallback": False}

    def boom_save_state(_originator):
        raise RuntimeError("nope")

    def capture_save_memento(m):
        called["fallback"] = True

    monkeypatch.setattr(c.caretaker, "save_state", boom_save_state, raising=True)
    monkeypatch.setattr(c.caretaker, "save_memento", capture_save_memento, raising=True)

    # Trigger _save_state indirectly via a calculation
    c.calculate("add", 1, 1)
    assert called["fallback"] is True


def test_export_and_load_history_excel(tmp_path):
    # Also cover excel branch via calculator wrapper when openpyxl is available
    cfg = CalculatorConfig(env_file=None, auto_create_dirs=False)
    c = Calculator(config=cfg)
    c.calculate("add", 3, 4)
    xlsx = tmp_path / "hist.xlsx"
    c.export_history(str(xlsx), format="excel")
    assert xlsx.exists() and xlsx.stat().st_size > 0
