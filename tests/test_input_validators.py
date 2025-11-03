"""
Unit tests for input validation module.

This module tests the InputValidator class and all validation methods
for ensuring robust input handling across the calculator application.
"""

import pytest
from decimal import Decimal
from app.input_validators import InputValidator
from app.exceptions import ValidationError


class TestBasicValidation:
    """Test basic validation methods."""
    
    def test_validate_operation_valid(self):
        """Test validation of valid operations."""
        validator = InputValidator()
        
        # Valid operations
        assert validator.validate_operation_name("add") == "add"
        assert validator.validate_operation_name("ADD") == "add"
        assert validator.validate_operation_name("  subtract  ") == "subtract"
        assert validator.validate_operation_name("Multiply") == "multiply"
    
    def test_validate_operation_invalid(self):
        """Test validation of invalid operations."""
        validator = InputValidator()
        
        with pytest.raises(ValidationError, match="Invalid operation"):
            validator.validate_operation_name("invalid_op")
        
        with pytest.raises(ValidationError, match="Operation cannot be empty"):
            validator.validate_operation_name("")
        
        with pytest.raises(ValidationError, match="Operation cannot be empty"):
            validator.validate_operation_name("   ")
        
        with pytest.raises(ValidationError, match="Operation must be a string"):
            validator.validate_operation_name(None)
        
        with pytest.raises(ValidationError, match="Operation must be a string"):
            validator.validate_operation_name(123)
    
    def test_validate_number_valid(self):
        """Test validation of valid numbers."""
        validator = InputValidator()
        
        # Integers
        assert validator.validate_numeric_input(5) == 5
        assert validator.validate_numeric_input(0) == 0
        assert validator.validate_numeric_input(-10) == -10
        
        # Floats
        assert validator.validate_numeric_input(3.14) == 3.14
        assert validator.validate_numeric_input(-2.5) == -2.5
        
        # Decimal strings
        result = validator.validate_numeric_input("5.5")
        assert isinstance(result, float)
        assert result == 5.5
        
        # Integer strings  
        result = validator.validate_numeric_input("42")
        assert result == 42
    
    def test_validate_number_invalid(self):
        """Test validation of invalid numbers."""
        validator = InputValidator()
        
        with pytest.raises(ValidationError, match="Invalid number format"):
            validator.validate_numeric_input("not_a_number")
        
        with pytest.raises(ValidationError, match="Empty string is not a valid number"):
            validator.validate_numeric_input("")
        
        with pytest.raises(ValidationError, match="Input cannot be None"):
            validator.validate_numeric_input(None)
        
        with pytest.raises(ValidationError, match="Invalid number format"):
            validator.validate_numeric_input("3.14.15")
    
    def test_validate_positive_number(self):
        """Test validation of positive numbers."""
        validator = InputValidator()
        
        # Valid positive numbers
        assert validator.validate_positive_number(5) == 5
        assert validator.validate_positive_number(3.14) == 3.14
        assert validator.validate_positive_number("2.5") == 2.5
        
        # Invalid (non-positive) numbers
        with pytest.raises(ValidationError, match="Number must be positive"):
            validator.validate_positive_number(0)
        
        with pytest.raises(ValidationError, match="Negative values are not allowed"):
            validator.validate_positive_number(-5)
        
        with pytest.raises(ValidationError, match="Negative values are not allowed"):
            validator.validate_positive_number("-2.5")
    
    def test_validate_non_zero_number(self):
        """Test validation of non-zero numbers."""
        validator = InputValidator()
        
        # Valid non-zero numbers
        assert validator.validate_non_zero_number(5) == 5
        assert validator.validate_non_zero_number(-3) == -3
        assert validator.validate_non_zero_number(0.001) == 0.001
        
        # Invalid (zero) numbers
        with pytest.raises(ValidationError, match="Number cannot be zero"):
            validator.validate_non_zero_number(0)
        
        with pytest.raises(ValidationError, match="Number cannot be zero"):
            validator.validate_non_zero_number(0.0)
        
        with pytest.raises(ValidationError, match="Number cannot be zero"):
            validator.validate_non_zero_number("0")


class TestSpecializedValidation:
    """Test specialized validation methods."""
    
    def test_validate_integer(self):
        """Test integer validation."""
        validator = InputValidator()
        
        # Valid integers
        assert validator.validate_integer(5) == 5
        assert validator.validate_integer(-10) == -10
        assert validator.validate_integer("42") == 42
        assert validator.validate_integer("0") == 0
        
        # Invalid (non-integer) numbers
        with pytest.raises(ValidationError, match="Number must be an integer"):
            validator.validate_integer(3.14)
        
        with pytest.raises(ValidationError, match="Number must be an integer"):
            validator.validate_integer("3.5")
        
        with pytest.raises(ValidationError, match="Invalid number format"):
            validator.validate_integer("not_a_number")
    
    def test_validate_calculation_id(self):
        """Test calculation ID validation."""
        validator = InputValidator()
        
        # Valid IDs
        assert validator.validate_calculation_id("calc-123") == "calc-123"
        assert validator.validate_calculation_id("test_id") == "test_id"
        assert validator.validate_calculation_id("abc123") == "abc123"
        
        # Invalid IDs
        with pytest.raises(ValidationError, match="Calculation ID cannot be empty"):
            validator.validate_calculation_id("")
        
        with pytest.raises(ValidationError, match="Calculation ID cannot be empty"):
            validator.validate_calculation_id("   ")
        
        with pytest.raises(ValidationError, match="Calculation ID must be a string"):
            validator.validate_calculation_id(None)
        
        with pytest.raises(ValidationError, match="Calculation ID must be a string"):
            validator.validate_calculation_id(123)
    
    def test_validate_file_path(self):
        """Test file path validation."""
        validator = InputValidator()
        
        # Valid paths
        assert validator.validate_file_path("test.txt") == "test.txt"
        assert validator.validate_file_path("/path/to/file.csv") == "/path/to/file.csv"
        assert validator.validate_file_path("C:\\Windows\\file.txt") == "C:\\Windows\\file.txt"
        
        # Invalid paths
        with pytest.raises(ValidationError, match="File path cannot be empty"):
            validator.validate_file_path("")
        
        with pytest.raises(ValidationError, match="File path cannot be empty"):
            validator.validate_file_path("   ")
        
        with pytest.raises(ValidationError, match="File path must be a string"):
            validator.validate_file_path(None)


class TestOperationSpecificValidation:
    """Test operation-specific validation methods."""
    
    def test_validate_division_operands(self):
        """Test division-specific validation."""
        validator = InputValidator()
        
        # Valid division
        dividend, divisor = validator.validate_division_operands(10, 2)
        assert dividend == 10
        assert divisor == 2
        
        # Division by zero
        with pytest.raises(ValidationError, match="Division by zero is not allowed"):
            validator.validate_division_operands(10, 0)
        
        with pytest.raises(ValidationError, match="Division by zero is not allowed"):
            validator.validate_division_operands(5, 0.0)
    
    def test_validate_power_operands(self):
        """Test power operation validation."""
        validator = InputValidator()
        
        # Valid power operations
        base, exponent = validator.validate_power_operands(2, 3)
        assert base == 2
        assert exponent == 3
        
        base, exponent = validator.validate_power_operands(5, 0)
        assert base == 5
        assert exponent == 0
        
        # Invalid: 0 to negative power
        with pytest.raises(ValidationError, match="Zero cannot be raised to a negative power"):
            validator.validate_power_operands(0, -1)
        
        with pytest.raises(ValidationError, match="Zero cannot be raised to a negative power"):
            validator.validate_power_operands(0, -0.5)
    
    def test_validate_root_operands(self):
        """Test root operation validation."""
        validator = InputValidator()
        
        # Valid root operations
        radicand, index = validator.validate_root_operands(9, 2)
        assert radicand == 9
        assert index == 2
        
        radicand, index = validator.validate_root_operands(-8, 3)  # Odd root of negative
        assert radicand == -8
        assert index == 3
        
        # Invalid: zero root index
        with pytest.raises(ValidationError, match="Root index cannot be zero"):
            validator.validate_root_operands(16, 0)
        
        # Invalid: even root of negative
        with pytest.raises(ValidationError, match="Cannot take even root of negative number"):
            validator.validate_root_operands(-4, 2)
        
        with pytest.raises(ValidationError, match="Cannot take even root of negative number"):
            validator.validate_root_operands(-9, 4)


class TestInputParsing:
    """Test input parsing functionality."""
    
    def test_parse_calculation_input_standard(self):
        """Test parsing standard calculation input."""
        validator = InputValidator()
        
        # Standard format: operation operand1 operand2
        operation, operand1, operand2 = validator.parse_calculation_input("add 5 3")
        assert operation == "add"
        assert operand1 == 5
        assert operand2 == 3
        
        # With extra whitespace
        operation, operand1, operand2 = validator.parse_calculation_input("  multiply   4   6  ")
        assert operation == "multiply"
        assert operand1 == 4
        assert operand2 == 6
    
    def test_parse_calculation_input_mathematical(self):
        """Test parsing mathematical expressions."""
        validator = InputValidator()
        
        # Basic arithmetic expressions
        operation, operand1, operand2 = validator.parse_calculation_input("5 + 3")
        assert operation == "add"
        assert operand1 == 5
        assert operand2 == 3
        
        operation, operand1, operand2 = validator.parse_calculation_input("10 - 4")
        assert operation == "subtract"
        assert operand1 == 10
        assert operand2 == 4
        
        operation, operand1, operand2 = validator.parse_calculation_input("7 * 8")
        assert operation == "multiply"
        assert operand1 == 7
        assert operand2 == 8
        
        operation, operand1, operand2 = validator.parse_calculation_input("15 / 3")
        assert operation == "divide"
        assert operand1 == 15
        assert operand2 == 3
        
        operation, operand1, operand2 = validator.parse_calculation_input("2 ** 3")
        assert operation == "power"
        assert operand1 == 2
        assert operand2 == 3
        
        operation, operand1, operand2 = validator.parse_calculation_input("17 % 5")
        assert operation == "modulus"
        assert operand1 == 17
        assert operand2 == 5
    
    def test_parse_calculation_input_with_decimals(self):
        """Test parsing input with decimal numbers."""
        validator = InputValidator()
        
        operation, operand1, operand2 = validator.parse_calculation_input("3.14 + 2.86")
        assert operation == "add"
        assert operand1 == 3.14
        assert operand2 == 2.86
        
        operation, operand1, operand2 = validator.parse_calculation_input("add 10.5 2.5")
        assert operation == "add"
        assert operand1 == 10.5
        assert operand2 == 2.5
    
    def test_parse_calculation_input_with_negatives(self):
        """Test parsing input with negative numbers."""
        validator = InputValidator()
        
        operation, operand1, operand2 = validator.parse_calculation_input("-5 + 3")
        assert operation == "add"
        assert operand1 == -5
        assert operand2 == 3
        
        operation, operand1, operand2 = validator.parse_calculation_input("add -10 -5")
        assert operation == "add"
        assert operand1 == -10
        assert operand2 == -5
    
    def test_parse_calculation_input_invalid(self):
        """Test parsing invalid input."""
        validator = InputValidator()
        
        # Too few arguments
        with pytest.raises(ValidationError, match="Invalid input format"):
            validator.parse_calculation_input("add 5")
        
        # Too many arguments
        with pytest.raises(ValidationError, match="Invalid input format"):
            validator.parse_calculation_input("add 5 3 2")
        
        # Invalid operation
        with pytest.raises(ValidationError, match="Unsupported mathematical operator"):
            validator.parse_calculation_input("5 & 3")
        
        # Invalid numbers
        with pytest.raises(ValidationError, match="Invalid number"):
            validator.parse_calculation_input("add abc 3")
        
        # Empty input
        with pytest.raises(ValidationError, match="Input cannot be empty"):
            validator.parse_calculation_input("")
        
        with pytest.raises(ValidationError, match="Input cannot be empty"):
            validator.parse_calculation_input("   ")


class TestValidationErrorMessages:
    """Test validation error messages are helpful."""
    
    def test_operation_error_messages(self):
        """Test operation validation error messages."""
        validator = InputValidator()
        
        try:
            validator.validate_operation_name("invalid_op")
        except ValidationError as e:
            assert "Invalid operation" in str(e)
            assert "Available operations:" in str(e)
    
    def test_number_error_messages(self):
        """Test number validation error messages."""
        validator = InputValidator()
        
        try:
            validator.validate_number("not_a_number")
        except ValidationError as e:
            assert "Invalid number format" in str(e)
    
    def test_division_error_messages(self):
        """Test division validation error messages."""
        validator = InputValidator()
        
        try:
            validator.validate_division_operands(10, 0)
        except ValidationError as e:
            assert "Division by zero is not allowed" in str(e)
    
    def test_root_error_messages(self):
        """Test root validation error messages."""
        validator = InputValidator()
        
        try:
            validator.validate_root_operands(-4, 2)
        except ValidationError as e:
            assert "Cannot take even root of negative number" in str(e)


class TestValidationEdgeCases:
    """Test validation edge cases."""
    
    def test_very_large_numbers(self):
        """Test validation of very large numbers."""
        validator = InputValidator()
        
        large_num = 1e100
        assert validator.validate_number(large_num) == large_num
        
        # Should handle string representation of large numbers
        large_str = "1" + "0" * 100
        result = validator.validate_number(large_str)
        assert isinstance(result, Decimal)
    
    def test_very_small_numbers(self):
        """Test validation of very small numbers."""
        validator = InputValidator()
        
        small_num = 1e-100
        assert validator.validate_number(small_num) == small_num
        
        # Should handle string representation of small numbers
        result = validator.validate_number("1e-100")
        assert isinstance(result, Decimal)
    
    def test_scientific_notation(self):
        """Test validation of scientific notation."""
        validator = InputValidator()
        
        # Standard scientific notation
        result = validator.parse_calculation_input("1e6 + 2e3")
        assert result[0] == "add"
        assert result[1] == 1e6
        assert result[2] == 2e3
        
        # Negative exponents
        result = validator.parse_calculation_input("1e-3 * 1e-2")
        assert result[0] == "multiply"
        assert result[1] == 1e-3
        assert result[2] == 1e-2
    
    def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters."""
        validator = InputValidator()
        
        # Should reject unicode mathematical symbols
        with pytest.raises(ValidationError):
            validator.parse_calculation_input("5 × 3")  # Unicode multiplication
        
        with pytest.raises(ValidationError):
            validator.parse_calculation_input("10 ÷ 2")  # Unicode division
    
    def test_whitespace_handling(self):
        """Test various whitespace scenarios."""
        validator = InputValidator()
        
        # Tabs and multiple spaces
        result = validator.parse_calculation_input("\t5\t+\t\t3\t")
        assert result == ("add", 5, 3)
        
        # Mixed whitespace
        result = validator.parse_calculation_input("  add   10   5  ")
        assert result == ("add", 10, 5)


@pytest.mark.parametrize("input_str,expected_op,expected_a,expected_b", [
    ("add 1 2", "add", 1, 2),
    ("1 + 2", "add", 1, 2),
    ("subtract 10 5", "subtract", 10, 5),
    ("10 - 5", "subtract", 10, 5),
    ("multiply 3 4", "multiply", 3, 4),
    ("3 * 4", "multiply", 3, 4),
    ("divide 15 3", "divide", 15, 3),
    ("15 / 3", "divide", 15, 3),
    ("power 2 3", "power", 2, 3),
    ("2 ** 3", "power", 2, 3),
    ("modulus 17 5", "modulus", 17, 5),
    ("17 % 5", "modulus", 17, 5),
])
def test_parse_calculation_input_parametrized(input_str, expected_op, expected_a, expected_b):
    """Test parsing with parametrized inputs."""
    validator = InputValidator()
    operation, operand1, operand2 = validator.parse_calculation_input(input_str)
    
    assert operation == expected_op
    assert operand1 == expected_a
    assert operand2 == expected_b


class TestValidatorIntegration:
    """Test validator integration with other components."""
    
    def test_validator_with_calculation_builder(self):
        """Test validator integration with calculation builder."""
        validator = InputValidator()
        
        # Parse input and validate components
        operation, operand1, operand2 = validator.parse_calculation_input("add 5 3")
        
        # Validate individual components
        validated_op = validator.validate_operation_name(operation)
        validated_op1 = validator.validate_number(operand1)
        validated_op2 = validator.validate_number(operand2)
        
        assert validated_op == "add"
        assert validated_op1 == 5
        assert validated_op2 == 3
    
    def test_validator_error_context(self):
        """Test that validator provides helpful error context."""
        validator = InputValidator()
        
        try:
            validator.validate_root_operands(-4, 2)
        except ValidationError as e:
            # Error should contain context about what went wrong
            error_msg = str(e)
            assert "even root" in error_msg
            assert "negative number" in error_msg


if __name__ == "__main__":
    pytest.main([__file__])