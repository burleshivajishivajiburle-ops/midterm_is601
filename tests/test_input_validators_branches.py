import pytest

from app.input_validators import InputValidator, ValidationError


def test_command_input_too_long():
    s = "x" * 1001
    with pytest.raises(ValidationError):
        InputValidator.validate_command_input(s)


def test_parse_string_to_number_failure_paths():
    # validate_numeric_input will call _parse_string_to_number and raise for bad formats
    with pytest.raises(ValidationError):
        InputValidator.validate_numeric_input("not-a-number")
    # Use a clearly invalid format that should fail across parsers
    with pytest.raises(ValidationError):
        InputValidator.validate_numeric_input("1..0")


def test_parse_calculation_input_invalid_number_and_format():
    # invalid number operand in standard notation
    with pytest.raises(ValidationError):
        InputValidator.parse_calculation_input("add 1 a")

    # missing operands
    with pytest.raises(ValidationError):
        InputValidator.parse_calculation_input("add 1")
