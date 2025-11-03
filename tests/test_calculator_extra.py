import os
import re
from pathlib import Path
import pytest

from app.calculator import Calculator
from app.calculator_config import CalculatorConfig
from app.exceptions import ValidationError, DivisionByZeroError, MementoError


def make_calc(cfg=None):
    cfg = cfg or CalculatorConfig(env_file=None, auto_create_dirs=False)
    # Ensure features enabled for observer-related code paths
    cfg.set_config_value("CALCULATOR_ENABLE_UNDO_REDO", True)
    return Calculator(config=cfg)


def test_calculate_from_string_and_errors(tmp_path):
    cfg = CalculatorConfig(env_file=None, auto_create_dirs=False)
    c = make_calc(cfg)

    r = c.calculate_from_string("2 ** 3")
    assert r["result"] == 8

    r = c.calculate_from_string("4 + 5")
    assert r["result"] == 9

    # parse error
    with pytest.raises(ValidationError):
        c.calculate_from_string("bad input")

    # division by zero propagates mapped exception
    with pytest.raises(DivisionByZeroError):
        c.calculate("divide", 1, 0)


def test_undo_redo_and_previews(tmp_path):
    c = make_calc()
    c.calculate("add", 1, 2)
    c.calculate("multiply", 3, 4)

    up = c.get_undo_preview()
    assert up and up.startswith("Undo:")

    res = c.undo()
    assert res["success"] is True
    rp = c.get_redo_preview()
    assert rp and rp.startswith("Redo:")

    rr = c.redo()
    assert rr["success"] is True

    # undo when none
    c.clear_history()
    with pytest.raises(MementoError):
        c.undo()


def test_clear_and_export_load_and_search(tmp_path):
    c = make_calc()
    c.calculate("add", 1, 2)
    c.calculate("subtract", 5, 3)

    # search criteria on operation/result
    hits = c.search_calculations(operation="add")
    assert hits and hits[-1].operation.name == "add"

    # export and load via Calculator helpers
    out = tmp_path / "hist.csv"
    c.export_history(str(out), format="csv")
    assert out.exists()

    c2 = make_calc()
    c2.load_history(str(out))
    assert len(c2.get_history(10)) >= 2

    # clear memory/history/all
    c2.clear_memory()
    assert c2.current_result is None
    c2.clear_history()
    assert len(c2.get_history(10)) == 0
    c2.clear_all()
    assert c2.calculation_count == 0


def test_misc_helpers_and_observers(tmp_path):
    c = make_calc()
    # observers property and methods
    class Dummy:
        def update(self, *args, **kwargs):
            pass
    d = Dummy()
    c.add_observer(d)
    assert d in c.observers
    c.remove_observer(d)

    # last calc and get by id
    c.calculate("add", 2, 3)
    last = c.get_last_calculation()
    assert last and last.result == 5
    got = c.get_calculation_by_id(last.id)
    assert got and got.result == last.result

    # repr/str are informative
    assert isinstance(str(c), str)
    assert isinstance(repr(c), str)


def test_calculator_additional_operations_and_search(tmp_path):
    c = make_calc()
    root_res = c.calculate("root", 27, 3)
    assert root_res["result"] == 3
    pct_res = c.calculate("percent", 25, 100)
    assert pct_res["result"] == 25

    filtered = c.search_history(operation="root")
    assert filtered and filtered[0]["operation"] == "root"

    stats = c.get_statistics()
    assert stats["session"]["calculation_count"] >= 2
    assert c.search_calculations(result=pct_res["result"])


def test_restore_memento_with_corrupt_data(tmp_path):
    c = make_calc()
    c.calculate("add", 1, 2)
    memento = c.create_memento()

    # Corrupt the underlying state to exercise error handling branches
    memento._state["last_calculation"] = "not-a-dict"  # type: ignore[attr-defined]
    memento._state["additional_state"] = {"history": "broken"}  # type: ignore[attr-defined]

    c.restore_memento(memento)
    assert c.last_calculation is None
