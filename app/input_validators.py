"""
Input validation functions for the calculator application.

This module provides comprehensive input validation functions to ensure
that user inputs are numerical, within allowed ranges, and safe for
mathematical operations. It includes validators for different input types
and operation-specific validations.
"""

import re
import math
from typing import Union, Any, Optional, Tuple, List
from decimal import Decimal, InvalidOperation

from .exceptions import ValidationError

# Type alias for numeric types
Number = Union[int, float]

# Configuration constants (will be loaded from config later)
DEFAULT_MAX_INPUT_VALUE = 1e15
DEFAULT_MIN_INPUT_VALUE = -1e15
DEFAULT_PRECISION = 15
DEFAULT_MAX_INTEGER_DIGITS = 10


class InputValidator:
    """
    Comprehensive input validator for calculator operations.
    
    Provides static methods for validating various types of inputs
    including numeric values, operation names, and operation-specific
    constraints.
    """
    
    @staticmethod
    def validate_numeric_input(value: Any, 
                             max_value: float = DEFAULT_MAX_INPUT_VALUE,
                             min_value: float = DEFAULT_MIN_INPUT_VALUE,
                             allow_negative: bool = True) -> Number:
        """
        Validate and convert input to a numeric value.
        
        Args:
            value: The input value to validate
            max_value (float): Maximum allowed value
            min_value (float): Minimum allowed value
            allow_negative (bool): Whether negative values are allowed
            
        Returns:
            Number: Validated numeric value
            
        Raises:
            ValidationError: If input is not numeric or out of range
        """
        if value is None:
            raise ValidationError(value, "Input cannot be None", "Expected numeric value")
        
        # Handle string inputs
        if isinstance(value, str):
            value = InputValidator._parse_string_to_number(value)
        
        # Validate type
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError(
                value, 
                f"Invalid input type: {type(value).__name__}", 
                "Expected int, float, or numeric string"
            )
        
        # Convert to float for validation
        try:
            numeric_value = float(value)
        except (ValueError, OverflowError) as e:
            raise ValidationError(value, f"Cannot convert to number: {str(e)}", "Valid numeric format required")
        
        # Check for special values
        if math.isnan(numeric_value):
            raise ValidationError(value, "NaN (Not a Number) is not allowed", "Finite numeric value required")
        
        if math.isinf(numeric_value):
            raise ValidationError(value, "Infinite values are not allowed", "Finite numeric value required")
        
        # Check negative values
        if not allow_negative and numeric_value < 0:
            raise ValidationError(value, "Negative values are not allowed", "Positive numeric value required")
        
        # Check range
        if numeric_value > max_value:
            raise ValidationError(
                value, 
                f"Value {numeric_value} exceeds maximum allowed value {max_value}",
                f"Value must be ≤ {max_value}"
            )
        
        if numeric_value < min_value:
            raise ValidationError(
                value, 
                f"Value {numeric_value} is below minimum allowed value {min_value}",
                f"Value must be ≥ {min_value}"
            )
        
        # Return appropriate type (preserve int if possible)
        if isinstance(value, int) or (isinstance(value, float) and value.is_integer()):
            return int(numeric_value)
        return numeric_value
    
    @staticmethod
    def _parse_string_to_number(value: str) -> Number:
        """
        Parse string input to numeric value with comprehensive format support.
        
        Args:
            value (str): String to parse
            
        Returns:
            Number: Parsed numeric value
            
        Raises:
            ValidationError: If string cannot be parsed as number
        """
        if not isinstance(value, str):
            raise ValidationError(value, "Expected string input", "String representation of number")
        
        # Clean the input
        cleaned = value.strip()
        
        if not cleaned:
            raise ValidationError(value, "Empty string is not a valid number", "Non-empty numeric string required")
        
        # Handle common number formats
        try:
            # Remove common formatting characters
            cleaned = cleaned.replace(',', '')  # Remove thousands separators
            cleaned = cleaned.replace(' ', '')  # Remove spaces
            
            # Handle scientific notation
            if 'e' in cleaned.lower():
                return float(cleaned)
            
            # Handle decimal numbers
            if '.' in cleaned:
                return float(cleaned)
            
            # Handle integers
            return int(cleaned)
            
        except ValueError:
            # Try with Decimal for better precision
            try:
                decimal_value = Decimal(cleaned)
                return float(decimal_value)
            except InvalidOperation:
                pass
        
        raise ValidationError(
            value, 
            f"Cannot parse '{value}' as a number",
            "Examples: '123', '45.67', '1.23e-4', '-89'"
        )
    
    @staticmethod
    def validate_operation_name(operation_name: Any) -> str:
        """
        Validate operation name input.
        
        Args:
            operation_name: The operation name to validate
            
        Returns:
            str: Validated and normalized operation name
            
        Raises:
            ValidationError: If operation name is invalid
        """
        if operation_name is None:
            raise ValidationError(operation_name, "Operation name cannot be None", "String operation name required")
        
        if not isinstance(operation_name, str):
            raise ValidationError(
                operation_name, 
                f"Operation name must be string, got {type(operation_name).__name__}",
                "String operation name required"
            )
        
        cleaned = operation_name.strip().lower()
        
        if not cleaned:
            raise ValidationError(operation_name, "Operation name cannot be empty", "Non-empty string required")
        
        # Basic format validation (alphanumeric and underscore only)
        if not re.match(r'^[a-z][a-z0-9_]*$', cleaned):
            raise ValidationError(
                operation_name,
                "Invalid operation name format",
                "Must start with letter, contain only letters, numbers, and underscores"
            )
        
        return cleaned
    
    @staticmethod
    def validate_division_operation(dividend: Number, divisor: Number) -> Tuple[Number, Number]:
        """
        Validate inputs for division operations.
        
        Args:
            dividend (Number): The number to be divided
            divisor (Number): The number to divide by
            
        Returns:
            Tuple[Number, Number]: Validated dividend and divisor
            
        Raises:
            ValidationError: If divisor is zero or inputs are invalid
        """
        validated_dividend = InputValidator.validate_numeric_input(dividend)
        validated_divisor = InputValidator.validate_numeric_input(divisor)
        
        if validated_divisor == 0:
            raise ValidationError(divisor, "Division by zero is not allowed", "Non-zero divisor required")
        
        return validated_dividend, validated_divisor
    
    @staticmethod
    def validate_power_operation(base: Number, exponent: Number) -> Tuple[Number, Number]:
        """
        Validate inputs for power operations.
        
        Args:
            base (Number): The base number
            exponent (Number): The exponent
            
        Returns:
            Tuple[Number, Number]: Validated base and exponent
            
        Raises:
            ValidationError: If combination would result in invalid operation
        """
        validated_base = InputValidator.validate_numeric_input(base)
        validated_exponent = InputValidator.validate_numeric_input(exponent)
        
        # Check for 0^0 case
        if validated_base == 0 and validated_exponent == 0:
            raise ValidationError(
                [base, exponent],
                "0^0 is mathematically undefined",
                "Use different base or exponent values"
            )
        
        # Check for 0^negative case
        if validated_base == 0 and validated_exponent < 0:
            raise ValidationError(
                [base, exponent],
                "0 raised to negative power is undefined (division by zero)",
                "Use positive exponent with zero base"
            )
        
        # Check for potentially problematic large exponents
        if abs(validated_exponent) > 1000:
            raise ValidationError(
                exponent,
                f"Exponent {validated_exponent} is too large",
                "Exponent must be between -1000 and 1000"
            )
        
        return validated_base, validated_exponent
    
    @staticmethod
    def validate_root_operation(radicand: Number, index: Number) -> Tuple[Number, Number]:
        """
        Validate inputs for root operations.
        
        Args:
            radicand (Number): The number to find the root of
            index (Number): The root index (2 for square root, 3 for cube root, etc.)
            
        Returns:
            Tuple[Number, Number]: Validated radicand and index
            
        Raises:
            ValidationError: If combination would result in invalid operation
        """
        validated_radicand = InputValidator.validate_numeric_input(radicand)
        validated_index = InputValidator.validate_numeric_input(index)
        
        # Check for zero index
        if validated_index == 0:
            raise ValidationError(index, "Root index cannot be zero", "Non-zero index required")
        
        # Check for even root of negative number
        if validated_radicand < 0 and validated_index % 2 == 0:
            raise ValidationError(
                [radicand, index],
                f"Even root (index {validated_index}) of negative number is not real",
                "Use odd root index for negative numbers, or positive radicand"
            )
        
        # Check for fractional index with negative radicand
        if validated_radicand < 0 and not float(validated_index).is_integer():
            raise ValidationError(
                [radicand, index],
                "Fractional root of negative number may not be real",
                "Use integer root index for negative radicand"
            )
        
        return validated_radicand, validated_index
    
    @staticmethod
    def validate_percentage_operation(value: Number, total: Number) -> Tuple[Number, Number]:
        """
        Validate inputs for percentage operations.
        
        Args:
            value (Number): The value to calculate percentage for
            total (Number): The total value (base for percentage)
            
        Returns:
            Tuple[Number, Number]: Validated value and total
            
        Raises:
            ValidationError: If total is zero or inputs are invalid
        """
        validated_value = InputValidator.validate_numeric_input(value)
        validated_total = InputValidator.validate_numeric_input(total)
        
        if validated_total == 0:
            raise ValidationError(total, "Cannot calculate percentage with zero total", "Non-zero total required")
        
        return validated_value, validated_total
    
    @staticmethod
    def validate_precision(precision: Any) -> int:
        """
        Validate precision value for result formatting.
        
        Args:
            precision: The precision value to validate
            
        Returns:
            int: Validated precision value
            
        Raises:
            ValidationError: If precision is invalid
        """
        if precision is None:
            return DEFAULT_PRECISION
        
        try:
            precision_int = int(precision)
        except (ValueError, TypeError):
            raise ValidationError(
                precision,
                f"Precision must be an integer, got {type(precision).__name__}",
                "Integer precision value required"
            )
        
        if precision_int < 0:
            raise ValidationError(precision, "Precision cannot be negative", "Non-negative integer required")
        
        if precision_int > 50:
            raise ValidationError(
                precision,
                f"Precision {precision_int} is too high",
                "Maximum precision is 50 decimal places"
            )
        
        return precision_int
    
    @staticmethod
    def validate_command_input(command: Any) -> str:
        """
        Validate command line input.
        
        Args:
            command: The command input to validate
            
        Returns:
            str: Validated and cleaned command
            
        Raises:
            ValidationError: If command is invalid
        """
        if command is None:
            raise ValidationError(command, "Command cannot be None", "String command required")
        
        if not isinstance(command, str):
            raise ValidationError(
                command,
                f"Command must be string, got {type(command).__name__}",
                "String command required"
            )
        
        cleaned = command.strip()
        
        if not cleaned:
            raise ValidationError(command, "Command cannot be empty", "Non-empty command required")
        
        # Check for reasonable length
        if len(cleaned) > 1000:
            raise ValidationError(
                command,
                f"Command too long ({len(cleaned)} characters)",
                "Commands must be less than 1000 characters"
            )
        
        return cleaned
    
    @staticmethod
    def parse_calculation_input(input_string: str) -> Tuple[str, List[Number]]:
        """
        Parse a calculation input string into operation and operands.
        
        Args:
            input_string (str): Input string like "add 5 3" or "5 + 3"
            
        Returns:
            Tuple[str, List[Number]]: Operation name and list of operands
            
        Raises:
            ValidationError: If input cannot be parsed
        """
        cleaned = InputValidator.validate_command_input(input_string)
        
        # Handle mathematical notation (e.g., "5 + 3")
        math_patterns = {
            r'([+-]?\d*\.?\d+)\s*\+\s*([+-]?\d*\.?\d+)': 'add',
            r'([+-]?\d*\.?\d+)\s*-\s*([+-]?\d*\.?\d+)': 'subtract',
            r'([+-]?\d*\.?\d+)\s*\*\s*([+-]?\d*\.?\d+)': 'multiply',
            r'([+-]?\d*\.?\d+)\s*/\s*([+-]?\d*\.?\d+)': 'divide',
            r'([+-]?\d*\.?\d+)\s*\*\*\s*([+-]?\d*\.?\d+)': 'power',
            r'([+-]?\d*\.?\d+)\s*%\s*([+-]?\d*\.?\d+)': 'modulus',
            r'([+-]?\d*\.?\d+)\s*//\s*([+-]?\d*\.?\d+)': 'int_divide',
        }
        
        for pattern, operation in math_patterns.items():
            match = re.match(pattern, cleaned)
            if match:
                operand1 = InputValidator.validate_numeric_input(match.group(1))
                operand2 = InputValidator.validate_numeric_input(match.group(2))
                return operation, [operand1, operand2]
        
        # Handle command notation (e.g., "add 5 3")
        parts = cleaned.split()
        
        if len(parts) < 3:
            raise ValidationError(
                input_string,
                "Invalid calculation format",
                "Expected: 'operation operand1 operand2' or 'operand1 operator operand2'"
            )
        
        operation = InputValidator.validate_operation_name(parts[0])
        
        try:
            operand1 = InputValidator.validate_numeric_input(parts[1])
            operand2 = InputValidator.validate_numeric_input(parts[2])
        except (IndexError, ValidationError) as e:
            raise ValidationError(
                input_string,
                f"Invalid operands: {str(e)}",
                "Expected two numeric operands after operation name"
            )
        
        return operation, [operand1, operand2]