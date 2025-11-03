import re
import pytest

from app.exceptions import (
    CalculatorError,
    OperationError,
    ValidationError,
    DivisionByZeroError,
    InvalidRootError,
    OverflowError,
    ConfigurationError,
    HistoryError,
    FileOperationError,
    MementoError,
)


def test_exception_messages_and_fields():
    e = CalculatorError("base", error_code="BASE")
    assert str(e).startswith("[BASE]")
    # Without an error_code, no bracket prefix
    e2 = CalculatorError("base")
    assert str(e2) == "base"

    e = OperationError("add", [1, 2], "oops")
    s = str(e)
    assert "Operation 'add' failed" in s and "[OP_ERROR]" in s

    e = ValidationError("x", "must be int", "int")
    s = str(e)
    assert "Invalid input 'x'" in s and "must be int" in s and "int" in s and "[VAL_ERROR]" in s

    e = DivisionByZeroError([1, 0])
    assert "division" in str(e).lower()

    e = InvalidRootError([9, 0], reason="bad root")
    assert "bad root" in str(e)

    e = OverflowError("power", [2, 10000])
    assert "exceeds" in str(e)

    e = ConfigurationError("CALCULATOR_PRECISION", "bad")
    assert "CONFIG_ERROR" in str(e)

    e = HistoryError("get", "not found")
    assert "HIST_ERROR" in str(e)

    e = FileOperationError("/tmp/x", "save", "disk full")
    assert "FILE_ERROR" in str(e) and "/tmp/x" in str(e)

    e = MementoError("undo", "no more")
    assert "MEMENTO_ERROR" in str(e)
