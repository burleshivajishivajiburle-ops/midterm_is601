import pytest
from datetime import datetime

from app.calculator import Calculator
from app.calculator_memento import CalculatorMemento
from app.exceptions import MementoError
from app import input_validators as validators_module


def test_calculate_from_string_fallback_list_shape(monkeypatch):
    # Simulate parse_calculation_input returning a generic list shape
    monkeypatch.setattr(validators_module.InputValidator, "parse_calculation_input", staticmethod(lambda s: ["add", 2, 3]))
    calc = Calculator()
    res = calc.calculate_from_string("ignored")
    assert res["result"] == 5


def test_calculate_from_string_legacy_tuple_shape(monkeypatch):
    # Simulate legacy (op, [a, b]) tuple shape
    monkeypatch.setattr(validators_module.InputValidator, "parse_calculation_input", staticmethod(lambda s: ("add", [2, 3])))
    calc = Calculator()
    res = calc.calculate_from_string("ignored")
    assert res["result"] == 5


def test_create_memento_handles_history_exception(monkeypatch):
    c = Calculator()
    # Cause history.get_all_calculations to raise so Calculator.create_memento falls back to []
    monkeypatch.setattr(c.history, "get_all_calculations", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    m = c.create_memento()
    assert isinstance(m, CalculatorMemento)
    state = m.get_state()
    assert isinstance(state, dict)
    assert (state.get("additional_state") or {}).get("history") == []


def test_restore_memento_invalid_type_raises():
    c = Calculator()
    with pytest.raises(MementoError, match="Invalid memento type"):
        c.restore_memento(object())  # type: ignore[arg-type]


def test_restore_memento_snapshot_rebuild_and_trim(monkeypatch):
    c = Calculator()
    # Build a snapshot with two entries
    snapshot_entry = {
        "id": "e1",
        "timestamp": datetime.now().isoformat(),
        "operation": "add",
        "operand_a": 1,
        "operand_b": 2,
        "result": 3,
        "error": None,
        "expression": "1 + 2 = 3",
        "duration_ms": 0,
    }
    m = CalculatorMemento(
        current_result=3,
        calculation_count=2,
        last_calculation=snapshot_entry,
        additional_state={"history": [snapshot_entry, {**snapshot_entry, "id": "e2"}]},
    )
    c.restore_memento(m)
    assert len(c.history.get_all_calculations()) == 2

    # Now exercise the trim path (no snapshot -> trims to count)
    # First add three calculations
    c.calculate("add", 1, 1)
    c.calculate("add", 2, 2)
    c.calculate("add", 3, 3)
    # Create a memento with count 2 and no history snapshot
    m2 = CalculatorMemento(current_result=None, calculation_count=2, last_calculation=None, additional_state={})
    c.restore_memento(m2)
    assert len(c.history.get_all_calculations()) == 2


def test_clear_all_and_clear_memory_notify_and_state(monkeypatch):
    c = Calculator()
    c.calculate("add", 1, 2)

    cleared = {"memory": False, "all": False}

    def capture(kind):
        cleared[kind] = True

    monkeypatch.setattr(c.subject, "notify_clear", capture)

    c.clear_memory()
    assert c.current_result is None and c.last_calculation is None
    assert cleared["memory"] is True

    # Add some more and then clear all
    c.calculate("add", 2, 3)
    c.clear_all()
    assert c.current_result is None and c.last_calculation is None and c.calculation_count == 0
    assert cleared["all"] is True
