import io
import os
import pandas as pd
import pytest

from app.history import CalculationHistory
from app.exceptions import FileOperationError, ValidationError


def test_history_empty_behaviors(tmp_path):
    h = CalculationHistory(history_file=None, auto_save=False)
    assert h.get_recent_calculations(5) == []
    assert h.get_all_calculations() == []
    assert h.get_last_calculation() is None
    assert h.remove_last() is False
    h.trim_to_count(10)  # should no-op safely


def test_save_without_file_raises():
    h = CalculationHistory(history_file=None, auto_save=False)
    with pytest.raises(FileOperationError):
        h.save_history()


def test_load_history_empty_file(tmp_path):
    p = tmp_path / "empty.csv"
    p.write_text("")
    h = CalculationHistory(history_file=str(p), auto_save=False)
    # load_history is called in __init__ when file exists; ensure no crash and history empty
    assert h.is_empty()


def test_export_invalid_format_and_filters(tmp_path):
    h = CalculationHistory(history_file=str(tmp_path / "h.csv"), auto_save=False)
    # seed one entry
    h.add_calculation({
        "id": "1",
        "timestamp": pd.Timestamp.now().isoformat(),
        "operation": "add",
        "operand_a": 1,
        "operand_b": 2,
        "result": 3,
        "expression": "1 + 2 = 3",
        "error": None,
        "duration_ms": 0,
    })
    # Unsupported format
    with pytest.raises(FileOperationError):
        h.export_history(str(tmp_path / "out.bad"), format="xml")
    # Supported with filters
    h.export_history(str(tmp_path / "out.csv"), format="csv", filters={"operation": "add", "success_only": True})
    h.export_history(str(tmp_path / "out.json"), format="json")


def test_get_operation_history_and_dunder(tmp_path):
    h = CalculationHistory(history_file=str(tmp_path / "h.csv"), auto_save=False)
    # Add two operations
    h.add_calculation({
        "id": "2",
        "timestamp": pd.Timestamp.now().isoformat(),
        "operation": "multiply",
        "operand_a": 2,
        "operand_b": 3,
        "result": 6,
        "expression": "2 * 3 = 6",
        "error": None,
        "duration_ms": 0,
    })
    h.add_calculation({
        "id": "3",
        "timestamp": pd.Timestamp.now().isoformat(),
        "operation": "multiply",
        "operand_a": 3,
        "operand_b": 4,
        "result": 12,
        "expression": "3 * 4 = 12",
        "error": None,
        "duration_ms": 0,
    })
    hist = h.get_operation_history("multiply", limit=1)
    assert len(hist) == 1
    assert "CalculationHistory(" in str(h)
    repr(h)
