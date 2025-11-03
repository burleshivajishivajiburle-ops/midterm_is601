import pytest
from decimal import Decimal

from app.input_validators import InputValidator, ValidationError


def test_validate_numeric_input_formats_and_ranges():
    # Strings with commas/spaces and scientific notation
    assert InputValidator.validate_numeric_input("1,234") == 1234
    assert InputValidator.validate_numeric_input("  12 34 ") == 1234
    assert InputValidator.validate_numeric_input("1e3") == 1000.0
    # Preserve int when integer-looking
    assert isinstance(InputValidator.validate_numeric_input(5.0), int)

    # Negatives disallowed
    with pytest.raises(ValidationError):
        InputValidator.validate_numeric_input(-1, allow_negative=False)

    # Out of range
    with pytest.raises(ValidationError):
        InputValidator.validate_numeric_input(1e20, max_value=1e5)
    with pytest.raises(ValidationError):
        InputValidator.validate_numeric_input(-1e6, min_value=-1000)


def test_validate_number_and_operation_name_and_precision():
    # validate_number returns Decimal for strings
    assert isinstance(InputValidator.validate_number("1.23e2"), Decimal)
    with pytest.raises(ValidationError):
        InputValidator.validate_number("")

    # operation name cleanup and invalids
    with pytest.raises(ValidationError):
        InputValidator.validate_operation_name(None)
    with pytest.raises(ValidationError):
        InputValidator.validate_operation_name(" not@valid ")
    with pytest.raises(ValidationError):
        InputValidator.validate_operation_name("unknownop")

    # precision
    assert InputValidator.validate_precision(None) == 15
    assert InputValidator.validate_precision(5) == 5
    with pytest.raises(ValidationError):
        InputValidator.validate_precision(-1)
    with pytest.raises(ValidationError):
        InputValidator.validate_precision(100)
    with pytest.raises(ValidationError):
        InputValidator.validate_precision("bad")


def test_divide_power_root_percent_and_helpers():
    # division
    with pytest.raises(ValidationError):
        InputValidator.validate_division_operation(10, 0)

    # power edge cases: disallow invalid exponent combinations
    with pytest.raises(ValidationError):
        InputValidator.validate_power_operation(0, -1)
    with pytest.raises(ValidationError):
        InputValidator.validate_power_operands(0, 0)
    with pytest.raises(ValidationError):
        InputValidator.validate_power_operands(2, 1001)

    # root edge cases
    with pytest.raises(ValidationError):
        InputValidator.validate_root_operation(9, 0)
    with pytest.raises(ValidationError):
        InputValidator.validate_root_operation(-8, 2)
    # Note: fractional root index with negative radicand is permitted in current implementation

    # percentage: current implementation allows zero percentage base/value without raising
    with pytest.raises(ValidationError):
        InputValidator.validate_percentage_operands(10, 0)
    assert InputValidator.validate_percentage_operands(25, 100) == (25, 100)

    # positive/non-zero/integer
    with pytest.raises(ValidationError):
        InputValidator.validate_positive_number(0)
    assert InputValidator.validate_positive_number(1) == 1

    with pytest.raises(ValidationError):
        InputValidator.validate_non_zero_number(0)
    assert InputValidator.validate_non_zero_number(2) == 2

    with pytest.raises(ValidationError):
        InputValidator.validate_integer(1.5)
    assert InputValidator.validate_integer("10") == 10


def test_command_and_parse_input_variants():
    # command validation
    with pytest.raises(ValidationError):
        InputValidator.validate_command_input(None)
    with pytest.raises(ValidationError):
        InputValidator.validate_command_input(123)
    with pytest.raises(ValidationError):
        InputValidator.validate_command_input("")
    with pytest.raises(ValidationError):
        InputValidator.validate_command_input("x" * 1001)

    # parse with '**' and operators, plus unsupported operator
    op, a, b = InputValidator.parse_calculation_input("2 ** 3")
    assert op == "power" and a == 2 and b == 3

    op, a, b = InputValidator.parse_calculation_input("4 + 5")
    assert op == "add" and a == 4 and b == 5

    op, a, b = InputValidator.parse_calculation_input("6 ^ 2")
    assert op == "power" and a == 6 and b == 2

    with pytest.raises(ValidationError):
        InputValidator.parse_calculation_input("1 @ 2")

    # parse standard notation
    with pytest.raises(ValidationError):
        InputValidator.parse_calculation_input("add 1")

    # file path and id validators
    assert InputValidator.validate_file_path(" foo.txt ") == "foo.txt"
    assert InputValidator.validate_calculation_id(" id ") == "id"
