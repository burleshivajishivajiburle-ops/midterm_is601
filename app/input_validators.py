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
    def validate_number(value: Any) -> Union[int, float, Decimal]:
        """
        Validate a number, preserving Decimal for high-precision strings.
        
        This differs from validate_numeric_input by returning Decimal for
        string inputs that represent numbers (including scientific notation),
        which some tests expect for extremely large/small values.
        """
        if value is None:
            raise ValidationError(value, "Input cannot be None", "Expected numeric value")
        
        # Pass through native numeric types
        if isinstance(value, (int, float)):
            return value
        
        if isinstance(value, str):
            s = value.strip()
            if not s:
                raise ValidationError(value, "Empty string is not a valid number", "Non-empty numeric string required")
            try:
                # Use Decimal to preserve precision and to support scientific notation
                return Decimal(s)
            except InvalidOperation:
                raise ValidationError(value, "Invalid number format", "Examples: '123', '45.67', '1e-3'")
        
        # Unsupported type
        raise ValidationError(value, "Invalid number format", "Expected int, float, or numeric string")
    
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
            f"Invalid number format '{value}'",
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
            raise ValidationError(operation_name, "Operation must be a string", "String operation name required")
        
        if not isinstance(operation_name, str):
            raise ValidationError(
                operation_name, 
                f"Operation must be a string, got {type(operation_name).__name__}",
                "String operation name required"
            )
        
        cleaned = operation_name.strip().lower()
        
        if not cleaned:
            raise ValidationError(operation_name, "Operation cannot be empty", "Non-empty string required")
        
        # Basic format validation (alphanumeric and underscore only)
        if not re.match(r'^[a-z][a-z0-9_]*$', cleaned):
            raise ValidationError(
                operation_name,
                "Invalid operation name format",
                "Must start with letter, contain only letters, numbers, and underscores"
            )
        
        # Check if operation is supported (import here to avoid circular import)
        from .operations import OperationFactory
        available_operations = OperationFactory.get_available_operations()
        
        if cleaned not in available_operations:
            available_ops = ", ".join(available_operations)
            raise ValidationError(
                operation_name,
                f"Invalid operation '{cleaned}'",
                f"Available operations: {available_ops}"
            )
        
        return cleaned
    
    @staticmethod
    def validate_percentage_operands(value: Any, total: Any) -> Tuple[Number, Number]:
        """Validate operands for percentage operation with non-zero total."""
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
    
    # Note: a legacy variant of parse_calculation_input previously existed here returning
    # (operation, [operand1, operand2]). It has been removed in favor of the
    # canonical implementation defined later that returns (operation, operand1, operand2)
    # to eliminate dead code and improve coverage clarity.
    
    @staticmethod
    def validate_positive_number(value: Any, max_value: float = DEFAULT_MAX_INPUT_VALUE) -> Number:
        """
        Validate that input is a positive number.
        
        Args:
            value: The input value to validate
            max_value: Maximum allowed value
            
        Returns:
            Number: Validated positive number
            
        Raises:
            ValidationError: If value is not positive
        """
        validated = InputValidator.validate_numeric_input(value, max_value=max_value, min_value=0, allow_negative=False)
        
        if validated <= 0:
            raise ValidationError(
                value,
                f"Number must be positive, got {validated}",
                "Positive number required (greater than 0)"
            )
        
        return validated
    
    @staticmethod
    def validate_non_zero_number(value: Any, 
                                max_value: float = DEFAULT_MAX_INPUT_VALUE,
                                min_value: float = DEFAULT_MIN_INPUT_VALUE) -> Number:
        """
        Validate that input is a non-zero number.
        
        Args:
            value: The input value to validate
            max_value: Maximum allowed value
            min_value: Minimum allowed value
            
        Returns:
            Number: Validated non-zero number
            
        Raises:
            ValidationError: If value is zero
        """
        validated = InputValidator.validate_numeric_input(value, max_value=max_value, min_value=min_value)
        
        if validated == 0:
            # For generic non-zero validation, raise a ValidationError with a clear message
            raise ValidationError(value, "Number cannot be zero", "Non-zero numeric value required")
        
        return validated
    
    @staticmethod
    def validate_integer(value: Any, min_value: Number = float('-inf'), max_value: Number = float('inf')) -> int:
        """
        Validate that a value is an integer.
        
        Args:
            value: Value to validate
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            
        Returns:
            int: Validated integer value
            
        Raises:
            ValidationError: If value is not a valid integer
        """
        # First validate as numeric
        numeric_value = InputValidator.validate_numeric_input(value, min_value=min_value, max_value=max_value)
        
        # Check if it's actually an integer
        if isinstance(numeric_value, float) and not numeric_value.is_integer():
            raise ValidationError(
                value,
                f"Value {numeric_value} is not an integer",
                "Number must be an integer"
            )
        
        return int(numeric_value)
    
    @staticmethod
    def validate_calculation_id(value: Any) -> str:
        """
        Validate a calculation ID.
        
        Args:
            value: Value to validate
            
        Returns:
            str: Validated calculation ID
            
        Raises:
            ValidationError: If value is not a valid calculation ID
        """
        if not isinstance(value, str):
            raise ValidationError(
                value,
                f"Calculation ID must be a string, got {type(value).__name__}",
                "Calculation ID must be a string"
            )
        
        id_str = value.strip()
        if not id_str:
            raise ValidationError(
                value,
                "Calculation ID cannot be empty",
                "Calculation ID cannot be empty"
            )
        
        return id_str
    
    @staticmethod
    def validate_file_path(value: Any) -> str:
        """
        Validate a file path.
        
        Args:
            value: Value to validate
            
        Returns:
            str: Validated file path
            
        Raises:
            ValidationError: If value is not a valid file path
        """
        if not isinstance(value, str):
            raise ValidationError(
                value,
                f"File path must be a string, got {type(value).__name__}",
                "File path must be a string"
            )
        
        path_str = value.strip()
        if not path_str:
            raise ValidationError(
                value,
                "File path cannot be empty",
                "File path cannot be empty"
            )
        
        return path_str
    
    @staticmethod
    def validate_division_operands(operand1: Any, operand2: Any) -> Tuple[Number, Number]:
        """
        Validate operands for division operation.
        
        Args:
            operand1: First operand (dividend)
            operand2: Second operand (divisor)
            
        Returns:
            Tuple[Number, Number]: Validated operands
            
        Raises:
            ValidationError: If operands are invalid for division
        """
        dividend = InputValidator.validate_numeric_input(operand1)
        divisor = InputValidator.validate_numeric_input(operand2)
        
        if divisor == 0:
            # Align message with tests
            raise ValidationError(operand2, "Division by zero is not allowed", "Non-zero divisor required")
        
        return dividend, divisor
    
    @staticmethod
    def validate_power_operands(base: Any, exponent: Any) -> Tuple[Number, Number]:
        """
        Validate operands for power operation.
        
        Args:
            base: Base value
            exponent: Exponent value
            
        Returns:
            Tuple[Number, Number]: Validated operands
            
        Raises:
            ValidationError: If operands are invalid for power operation
        """
        base_val = InputValidator.validate_numeric_input(base)
        exp_val = InputValidator.validate_numeric_input(exponent)
        
        if base_val == 0 and exp_val == 0:
            raise ValidationError(
                [base, exponent],
                "0^0 is mathematically undefined",
                "Use different base or exponent values"
            )

        # Check for problematic combinations
        if base_val == 0 and exp_val < 0:
            raise ValidationError(
                [base, exponent],
                "Zero cannot be raised to a negative power",
                "Base cannot be zero when exponent is negative"
            )
        
        # Guard against unreasonably large exponents that could overflow downstream
        if abs(float(exp_val)) > 1000:
            raise ValidationError(
                exponent,
                f"Exponent {exp_val} is too large",
                "Exponent must be between -1000 and 1000"
            )

        if base_val < 0 and not isinstance(exp_val, int) and not exp_val.is_integer():
            raise ValidationError(
                [base, exponent],
                "Cannot raise negative number to non-integer power",
                "Negative base requires integer exponent"
            )
        
        return base_val, exp_val
    
    @staticmethod
    def validate_root_operands(radicand: Any, index: Any) -> Tuple[Number, Number]:
        """
        Validate operands for root operation.
        
        Args:
            radicand: Number to find root of
            index: Root index (e.g., 2 for square root)
            
        Returns:
            Tuple[Number, Number]: Validated operands
            
        Raises:
            ValidationError: If operands are invalid for root operation
        """
        radicand_val = InputValidator.validate_numeric_input(radicand)
        index_val = InputValidator.validate_numeric_input(index)
        
        if index_val == 0:
            raise ValidationError(index, "Root index cannot be zero", "Non-zero index required")
        
        # Check for even roots of negative numbers
        if radicand_val < 0:
            index_float = float(index_val)

            # Fractional indices of negative numbers would produce complex results
            if not index_float.is_integer():
                raise ValidationError(
                    [radicand, index],
                    "Fractional roots of negative numbers are not real",
                    "Use integer root index for negative numbers"
                )

            if int(index_float) % 2 == 0:
                raise ValidationError(
                    [radicand, index],
                    "Cannot take even root of negative number",
                    "Even roots of negative numbers are not allowed"
                )
        
        return radicand_val, index_val
    
    @staticmethod
    def parse_calculation_input(input_str: str) -> Tuple[str, Number, Number]:
        """
        Parse calculation input string into operation and operands.
        
        Args:
            input_str: Input string to parse (e.g., "5 + 3", "add 5 3")
            
        Returns:
            Tuple[str, Number, Number]: Operation name and operands
            
        Raises:
            ValidationError: If input cannot be parsed
        """
        if not isinstance(input_str, str):
            raise ValidationError(
                input_str,
                f"Input must be a string, got {type(input_str).__name__}",
                "Input must be a string"
            )
        
        input_str = input_str.strip()
        if not input_str:
            raise ValidationError(
                input_str,
                "Input cannot be empty",
                "Input cannot be empty"
            )
        
        # Try mathematical notation first (supports scientific notation and '**')
        import re
        number = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?"
        # First, try to capture '**' explicitly
        pattern_power = rf"^\s*({number})\s*(\*\*)\s*({number})\s*$"
        m_power = re.match(pattern_power, input_str, flags=re.IGNORECASE)
        if m_power:
            op1_str, _, op2_str = m_power.groups()
            try:
                op1 = InputValidator.validate_numeric_input(op1_str)
                op2 = InputValidator.validate_numeric_input(op2_str)
            except ValidationError:
                raise ValidationError(input_str, "Invalid number", "Operands must be numeric")
            return "power", op1, op2
        
        # Then single-char operators
        pattern_ops = rf"^\s*({number})\s*([+\-*/%\^])\s*({number})\s*$"
        m = re.match(pattern_ops, input_str, flags=re.IGNORECASE)
        if m:
            op1_str, operator, op2_str = m.groups()
            operator_map = {
                '+': 'add',
                '-': 'subtract',
                '*': 'multiply',
                '/': 'divide',
                '%': 'modulus',
                '^': 'power',
            }
            if operator not in operator_map:
                raise ValidationError(input_str, "Unsupported mathematical operator", "Use +, -, *, /, %, or **")
            try:
                op1 = InputValidator.validate_numeric_input(op1_str)
                op2 = InputValidator.validate_numeric_input(op2_str)
            except ValidationError:
                raise ValidationError(input_str, "Invalid number", "Operands must be numeric")
            return operator_map[operator], op1, op2

        # If it looks like number <op> number with an unsupported operator, raise a clear error
        pattern_anyop = rf"^\s*({number})\s*(\S+)\s*({number})\s*$"
        m_any = re.match(pattern_anyop, input_str, flags=re.IGNORECASE)
        if m_any:
            raise ValidationError(input_str, "Unsupported mathematical operator", "Use +, -, *, /, %, or **")
        
        # Try standard notation (e.g., "add 5 3")
        parts = input_str.split()
        if len(parts) != 3:
            raise ValidationError(
                input_str,
                "Invalid input format",
                "Expected: 'operation operand1 operand2' or 'operand1 operator operand2'"
            )
        
        operation_str, operand1_str, operand2_str = parts
        operation = InputValidator.validate_operation_name(operation_str)
        try:
            operand1 = InputValidator.validate_numeric_input(operand1_str)
            operand2 = InputValidator.validate_numeric_input(operand2_str)
        except ValidationError:
            raise ValidationError(input_str, "Invalid number", "Operands must be numeric")
        
        return operation, operand1, operand2
    
    # Aliases for backward compatibility with Calculator class
    @staticmethod
    def validate_division_operation(operand1: Any, operand2: Any) -> Tuple[Number, Number]:
        """Alias for validate_division_operands for backward compatibility."""
        return InputValidator.validate_division_operands(operand1, operand2)
    
    @staticmethod
    def validate_power_operation(base: Any, exponent: Any) -> Tuple[Number, Number]:
        """Alias for validate_power_operands for backward compatibility."""
        return InputValidator.validate_power_operands(base, exponent)
    
    @staticmethod
    def validate_root_operation(radicand: Any, index: Any) -> Tuple[Number, Number]:
        """Alias for validate_root_operands for backward compatibility."""
        return InputValidator.validate_root_operands(radicand, index)
    
    @staticmethod
    def validate_percentage_operation(value: Any, percentage: Any) -> Tuple[Number, Number]:
        """Alias for validate_percentage_operands for backward compatibility."""
        return InputValidator.validate_percentage_operands(value, percentage)