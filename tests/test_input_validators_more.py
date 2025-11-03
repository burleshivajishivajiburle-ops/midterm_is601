import pytest
from datetime import datetime

from app.input_validators import InputValidator
from app.exceptions import ValidationError


def test_validate_integer_non_integer_float():
    with pytest.raises(ValidationError):
        InputValidator.validate_integer(1.5)
    assert InputValidator.validate_integer(2.0) == 2


def test_validate_calculation_id_and_file_path():
    with pytest.raises(ValidationError):
        InputValidator.validate_calculation_id(123)
    with pytest.raises(ValidationError):
        InputValidator.validate_calculation_id(" ")
    with pytest.raises(ValidationError):
        InputValidator.validate_file_path(123)
    with pytest.raises(ValidationError):
        InputValidator.validate_file_path(" ")


def test_validate_positive_and_non_zero_number():
    with pytest.raises(ValidationError):
        InputValidator.validate_positive_number(0)
    assert InputValidator.validate_positive_number(1) == 1
    with pytest.raises(ValidationError):
        InputValidator.validate_non_zero_number(0)
    assert InputValidator.validate_non_zero_number(3) == 3


def test_validate_precision_boundaries():
    assert InputValidator.validate_precision(None) >= 0
    with pytest.raises(ValidationError):
        InputValidator.validate_precision(-1)
    with pytest.raises(ValidationError):
        InputValidator.validate_precision(100)


def test_parse_calculation_input_power_and_standard():
    op, a, b = InputValidator.parse_calculation_input("2 ** 3")
    assert op == "power" and a == 2 and b == 3
    op2, a2, b2 = InputValidator.parse_calculation_input("add 5 3")
    assert op2 == "add" and a2 == 5 and b2 == 3


def test_validate_operation_name_errors():
    with pytest.raises(ValidationError):
        InputValidator.validate_operation_name(123)
    with pytest.raises(ValidationError):
        InputValidator.validate_operation_name("")
    with pytest.raises(ValidationError):
        InputValidator.validate_operation_name("bad name!")
    with pytest.raises(ValidationError):
        InputValidator.validate_operation_name("unknownop")


def test_division_power_root_validators():
    with pytest.raises(ValidationError):
        InputValidator.validate_division_operands(1, 0)
    with pytest.raises(ValidationError):
        InputValidator.validate_power_operands(0, -1)
    with pytest.raises(ValidationError):
        InputValidator.validate_power_operands(-2, 0.5)
    with pytest.raises(ValidationError):
        InputValidator.validate_root_operands(-8, 2)
    with pytest.raises(ValidationError):
        InputValidator.validate_root_operands(-8, 2.5)
