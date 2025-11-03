import pytest
from datetime import datetime

from app.calculation import Calculation, CalculationBuilder
from app.exceptions import OperationError, ValidationError
from app import operations as operations_module


def test_unexpected_exception_in_factory_raises_operation_error(monkeypatch):
    # Force factory to raise a non-CalculatorError to hit unexpected-exception branch
    def boom(_name):
        raise ValueError("factory blew up")

    monkeypatch.setattr(operations_module.OperationFactory, "create_operation", staticmethod(boom))

    with pytest.raises(OperationError) as ei:
        Calculation("add", 1, 2)
    assert "Unexpected error" in str(ei.value)


def test_unexpected_exception_in_execute_raises_operation_error(monkeypatch):
    # Return a fake operation whose execute raises a non-CalculatorError
    class FakeOp:
        name = "fake"
        def execute(self, a, b):
            raise RuntimeError("exec boom")

    monkeypatch.setattr(operations_module.OperationFactory, "create_operation", staticmethod(lambda name: FakeOp()))

    with pytest.raises(OperationError) as ei:
        Calculation("add", 1, 2)
    assert "Unexpected error" in str(ei.value)


def test_formatted_result_int_like_float_and_error_formatting():
    # Use from_dict to avoid executing any operation
    base = {
        "timestamp": datetime.now().isoformat(),
        "operation": "add",
        "operand_a": 2,
        "operand_b": 2,
        "id": "x1",
    }
    # 1) float that is equivalent to int should format without decimals
    calc_ok = Calculation.from_dict({**base, "result": 4.0, "error": None})
    assert calc_ok.get_formatted_result() == "4"

    # 2) error path should prefix with ERROR:
    calc_err = Calculation.from_dict({**base, "result": None, "error": "Boom"})
    assert calc_err.get_formatted_result().startswith("ERROR: Boom")
    assert "ERROR: Boom" in calc_err.get_formatted_expression()


def test_formatted_expression_percent_and_unknown_operation():
    # percent operation should use "% of" wording
    calc_percent = Calculation("percent", 50, 20)
    # Percentage operation returns a as percentage of b -> (50/20)*100 = 250
    assert calc_percent.get_formatted_expression() == "50 % of 20 = 250.0"

    # Unknown operation should fall back to using the name literally in the expression
    data = {
        "timestamp": datetime.now().isoformat(),
        "operation": "weirdop",
        "operand_a": 1,
        "operand_b": 2,
        "result": 42,
        "error": None,
        "id": "abc",
    }
    calc_unknown = Calculation.from_dict(data)
    # from_dict should tolerate unknown operation by leaving calc.operation as None
    assert getattr(calc_unknown, "operation", None) in (None,)
    assert calc_unknown.get_formatted_expression() == "1 weirdop 2 = 42"


def test_from_dict_invalid_data_message():
    with pytest.raises(ValidationError) as ei:
        Calculation.from_dict({"operation": "add", "operand_a": 1})  # missing required fields
    assert "Dictionary must contain" in str(ei.value)


def test_calculation_equality_with_non_calculation():
    calc = Calculation("add", 1, 2)
    assert calc != object()


def test_builder_first_operand_type_validation():
    builder = CalculationBuilder().operation("add")
    with pytest.raises(ValidationError, match="First operand must be numeric"):
        builder.first_operand("not-a-number")
