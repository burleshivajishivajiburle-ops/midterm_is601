import logging
import pytest

from app.calculator import Calculator
from app.calculator_config import CalculatorConfig


def test_calculator_observer_setup_failure(monkeypatch):
    # Force FileHandler to raise to exercise observer setup failure path
    cfg = CalculatorConfig(env_file=None, auto_create_dirs=False)
    cfg.set_config_value("CALCULATOR_ENABLE_LOGGING", True)
    cfg.set_config_value("CALCULATOR_ENABLE_AUTO_SAVE", False)

    class BoomHandler(logging.FileHandler):
        def __init__(self, *args, **kwargs):
            raise RuntimeError("no file handler")

    monkeypatch.setattr(logging, "FileHandler", BoomHandler)

    # Should not raise; internal warning path is exercised
    Calculator(config=cfg)


def test_calculator_undo_redo_previews_missing_operation(monkeypatch):
    # Build a calculator and manually clear operation attribute on last calc to hit fallback branch
    cfg = CalculatorConfig(env_file=None, auto_create_dirs=False)
    calc = Calculator(config=cfg)
    calc.calculate("add", 1, 2)

    # Remove operation object to trigger alternate preview formatting
    last = calc.get_last_calculation()
    last.operation = None

    assert calc.get_undo_preview() and calc.get_undo_preview().startswith("Undo:")

    # Undo then redo to re-populate redo stack
    calc.undo()
    assert calc.get_redo_preview() and calc.get_redo_preview().startswith("Redo:")


def test_calculator_error_paths_and_notify(tmp_path):
    cfg = CalculatorConfig(env_file=None, auto_create_dirs=False)
    c = Calculator(config=cfg)

    # String operands should raise ValidationError and trigger error notify path
    with pytest.raises(Exception):
        c.calculate("add", "a", 1)

    # Unsupported operation name
    with pytest.raises(Exception):
        c.calculate("unknownop", 1, 2)
