"""
Calculation class for handling individual calculations.

This module provides the Calculation class that represents a single calculation
with its operation, operands, result, and metadata. It supports serialization
for history management and provides a clean interface for calculation operations.
"""

from datetime import datetime
from typing import Union, List, Dict, Any, Optional
import uuid

from .operations import Operation, OperationFactory
from .exceptions import CalculatorError, OperationError, ValidationError

# Type alias for numeric types
Number = Union[int, float]


class Calculation:
    """
    Represents a single calculation with operation, operands, and result.
    
    This class encapsulates all information about a calculation including:
    - The operation performed
    - The operands used
    - The result obtained
    - Metadata like timestamp and unique ID
    """
    
    def __init__(self, operation_name: str, operand_a: Number, operand_b: Number):
        """
        Initialize a new calculation.
        
        Args:
            operation_name (str): Name of the operation to perform
            operand_a (Number): First operand
            operand_b (Number): Second operand
            
        Raises:
            ValidationError: If operation name is invalid
            OperationError: If calculation fails
        """
        self.id = str(uuid.uuid4())
        self.timestamp = datetime.now()
        self.operation_name = operation_name.lower().strip()
        self.operand_a = operand_a
        self.operand_b = operand_b
        self.result: Optional[Number] = None
        self.error: Optional[str] = None
        self.operation: Optional[Operation] = None
        
        # Perform the calculation
        self._execute_calculation()

    # --- Compatibility aliases for tests expecting different attribute names ---
    @property
    def operand1(self) -> Number:
        """Alias for first operand (test compatibility)."""
        return self.operand_a

    @property
    def operand2(self) -> Number:
        """Alias for second operand (test compatibility)."""
        return self.operand_b

    @property
    def calculation_id(self) -> str:
        """Alias for calculation ID (test compatibility)."""
        return self.id
    
    def _execute_calculation(self) -> None:
        """
        Execute the calculation and store the result or error.
        
        Raises:
            ValidationError: If operation name is invalid
            OperationError: If calculation fails
        """
        try:
            # Create operation instance using factory
            self.operation = OperationFactory.create_operation(self.operation_name)
            
            # Execute the operation
            self.result = self.operation.execute(self.operand_a, self.operand_b)
            
        except CalculatorError as e:
            self.error = str(e)
            raise
        except Exception as e:
            # Catch any unexpected errors
            self.error = f"Unexpected error: {str(e)}"
            raise OperationError(
                self.operation_name, 
                [self.operand_a, self.operand_b], 
                f"Unexpected error: {str(e)}"
            )
    
    def is_successful(self) -> bool:
        """
        Check if the calculation was successful.
        
        Returns:
            bool: True if calculation succeeded, False otherwise
        """
        return self.result is not None and self.error is None
    
    def get_formatted_expression(self) -> str:
        """
        Get a formatted string representation of the calculation expression.
        
        Returns:
            str: Formatted expression like "5 + 3 = 8"
        """
        operation_symbols = {
            "add": "+",
            "subtract": "-", 
            "multiply": "*",
            "divide": "/",
            "power": "**",
            "root": "root",
            "modulus": "%",
            "int_divide": "//",
            "percent": "% of",
            "abs_diff": "abs_diff"
        }
        
        symbol = operation_symbols.get(self.operation_name, self.operation_name)
        
        if self.operation_name == "root":
            expression = f"{self.operand_b}√{self.operand_a}"
        elif self.operation_name == "percent":
            expression = f"{self.operand_a} {symbol} {self.operand_b}"
        elif self.operation_name == "abs_diff":
            expression = f"|{self.operand_a} - {self.operand_b}|"
        else:
            expression = f"{self.operand_a} {symbol} {self.operand_b}"
        
        if self.is_successful():
            return f"{expression} = {self.result}"
        else:
            return f"{expression} = ERROR: {self.error}"
    
    def get_formatted_result(self, precision: int = 6) -> str:
        """
        Get formatted result with specified precision.
        
        Args:
            precision (int): Number of decimal places for formatting
            
        Returns:
            str: Formatted result or error message
        """
        if self.is_successful():
            if isinstance(self.result, float):
                # Round to avoid floating point precision issues
                if self.result == int(self.result):
                    return str(int(self.result))
                else:
                    return f"{self.result:.{precision}f}".rstrip('0').rstrip('.')
            else:
                return str(self.result)
        else:
            return f"ERROR: {self.error}"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert calculation to dictionary for serialization.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the calculation
        """
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "operation": self.operation_name,
            "operand_a": self.operand_a,
            "operand_b": self.operand_b,
            "result": self.result,
            "error": self.error,
            "expression": self.get_formatted_expression()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Calculation':
        """
        Create calculation instance from dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary containing calculation data
            
        Returns:
            Calculation: New calculation instance
            
        Raises:
            ValidationError: If dictionary data is invalid
        """
        try:
            # Create a new calculation but don't execute it
            calc = cls.__new__(cls)
            
            calc.id = data.get("id", str(uuid.uuid4()))
            calc.timestamp = datetime.fromisoformat(data["timestamp"])
            calc.operation_name = data["operation"]
            calc.operand_a = data["operand_a"]
            calc.operand_b = data["operand_b"]
            calc.result = data.get("result")
            calc.error = data.get("error")
            
            # Recreate operation instance if needed
            if calc.result is not None:
                try:
                    calc.operation = OperationFactory.create_operation(calc.operation_name)
                except Exception:
                    calc.operation = None
            
            return calc
            
        except (KeyError, ValueError, TypeError) as e:
            raise ValidationError(
                data,
                f"Invalid calculation data: {str(e)}",
                "Dictionary must contain: timestamp, operation, operand_a, operand_b"
            )
    
    def copy(self) -> 'Calculation':
        """
        Create a copy of this calculation with a new ID and timestamp.
        
        Returns:
            Calculation: New calculation instance with same operands and operation
        """
        return Calculation(self.operation_name, self.operand_a, self.operand_b)
    
    def __str__(self) -> str:
        """String representation of the calculation."""
        return self.get_formatted_expression()
    
    def __repr__(self) -> str:
        """Developer representation of the calculation."""
        return (f"Calculation(id='{self.id}', "
                f"operation='{self.operation_name}', "
                f"operands=[{self.operand_a}, {self.operand_b}], "
                f"result={self.result}, "
                f"timestamp='{self.timestamp.isoformat()}')")
    
    def __eq__(self, other) -> bool:
        """
        Check equality with another calculation.
        
        Args:
            other: Another calculation to compare with
            
        Returns:
            bool: True if calculations are equivalent
        """
        if not isinstance(other, Calculation):
            return False
        
        return (self.operation_name == other.operation_name and
                self.operand_a == other.operand_a and
                self.operand_b == other.operand_b and
                self.result == other.result)
    
    def __hash__(self) -> int:
        """
        Generate hash for the calculation.
        
        Returns:
            int: Hash value based on operation and operands
        """
        return hash((self.operation_name, self.operand_a, self.operand_b))


class CalculationBuilder:
    """
    Builder pattern for creating calculations with validation.
    
    Provides a fluent interface for building calculations step by step
    with comprehensive validation at each step.
    """
    
    def __init__(self):
        """Initialize the builder."""
        self.operation_name: Optional[str] = None
        self.operand_a: Optional[Number] = None
        self.operand_b: Optional[Number] = None
    
    def operation(self, operation_name: str) -> 'CalculationBuilder':
        """
        Set the operation name.
        
        Args:
            operation_name (str): Name of the operation
            
        Returns:
            CalculationBuilder: This builder instance for chaining
            
        Raises:
            ValidationError: If operation name is invalid
        """
        available_operations = OperationFactory.get_available_operations()
        if operation_name.lower().strip() not in available_operations:
            raise ValidationError(
                operation_name,
                "Invalid operation name",
                f"Available operations: {', '.join(available_operations)}"
            )
        
        self.operation_name = operation_name.lower().strip()
        return self
    
    def operands(self, a: Number, b: Number) -> 'CalculationBuilder':
        """
        Set both operands.
        
        Args:
            a (Number): First operand
            b (Number): Second operand
            
        Returns:
            CalculationBuilder: This builder instance for chaining
            
        Raises:
            ValidationError: If operands are not numeric
        """
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise ValidationError(
                [a, b],
                "Operands must be numeric",
                "Expected int or float values"
            )
        
        self.operand_a = a
        self.operand_b = b
        return self
    
    def first_operand(self, a: Number) -> 'CalculationBuilder':
        """
        Set the first operand.
        
        Args:
            a (Number): First operand
            
        Returns:
            CalculationBuilder: This builder instance for chaining
        """
        if not isinstance(a, (int, float)):
            raise ValidationError(a, "First operand must be numeric", "Expected int or float")
        
        self.operand_a = a
        return self
    
    def second_operand(self, b: Number) -> 'CalculationBuilder':
        """
        Set the second operand.
        
        Args:
            b (Number): Second operand
            
        Returns:
            CalculationBuilder: This builder instance for chaining
        """
        if not isinstance(b, (int, float)):
            raise ValidationError(b, "Second operand must be numeric", "Expected int or float")
        
        self.operand_b = b
        return self
    
    def build(self) -> Calculation:
        """
        Build the calculation.
        
        Returns:
            Calculation: New calculation instance
            
        Raises:
            ValidationError: If required parameters are missing
        """
        if self.operation_name is None:
            raise ValidationError(None, "Operation name is required", "Call operation() first")
        
        if self.operand_a is None:
            raise ValidationError(None, "First operand is required", "Call first_operand() or operands()")
        
        if self.operand_b is None:
            raise ValidationError(None, "Second operand is required", "Call second_operand() or operands()")
        
        return Calculation(self.operation_name, self.operand_a, self.operand_b)