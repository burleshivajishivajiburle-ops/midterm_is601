"""
Operations module implementing the Factory Design Pattern for arithmetic operations.

This module provides a factory for creating different arithmetic operation instances.
Each operation takes exactly two numerical inputs and returns the correct result.
All operations handle invalid inputs gracefully with appropriate error messages.
"""

from abc import ABC, abstractmethod
from typing import Union, Type, Dict
import math

from .exceptions import (
    OperationError, 
    DivisionByZeroError, 
    InvalidRootError, 
    OverflowError,
    ValidationError
)

# Type alias for numeric types
Number = Union[int, float]


class Operation(ABC):
    """Abstract base class for all arithmetic operations."""
    
    def __init__(self, name: str):
        """
        Initialize the operation with a name.
        
        Args:
            name (str): The name of the operation
        """
        self.name = name
    
    @abstractmethod
    def execute(self, a: Number, b: Number) -> Number:
        """
        Execute the operation with two operands.
        
        Args:
            a (Number): First operand
            b (Number): Second operand
            
        Returns:
            Number: Result of the operation
            
        Raises:
            OperationError: If the operation cannot be performed
        """
        pass
    
    def __str__(self) -> str:
        """Return string representation of the operation."""
        return self.name


class AddOperation(Operation):
    """Addition operation: a + b"""
    
    def __init__(self):
        super().__init__("add")
    
    def execute(self, a: Number, b: Number) -> Number:
        """Add two numbers."""
        try:
            result = a + b
            # Check for overflow
            if abs(result) > 1e308:  # Python float max
                raise OverflowError("add", [a, b])
            return result
        except (TypeError, ValueError) as e:
            raise OperationError("add", [a, b], f"Invalid operands: {str(e)}")


class SubtractOperation(Operation):
    """Subtraction operation: a - b"""
    
    def __init__(self):
        super().__init__("subtract")
    
    def execute(self, a: Number, b: Number) -> Number:
        """Subtract b from a."""
        try:
            result = a - b
            if abs(result) > 1e308:
                raise OverflowError("subtract", [a, b])
            return result
        except (TypeError, ValueError) as e:
            raise OperationError("subtract", [a, b], f"Invalid operands: {str(e)}")


class MultiplyOperation(Operation):
    """Multiplication operation: a * b"""
    
    def __init__(self):
        super().__init__("multiply")
    
    def execute(self, a: Number, b: Number) -> Number:
        """Multiply two numbers."""
        try:
            result = a * b
            if abs(result) > 1e308:
                raise OverflowError("multiply", [a, b])
            return result
        except (TypeError, ValueError) as e:
            raise OperationError("multiply", [a, b], f"Invalid operands: {str(e)}")


class DivideOperation(Operation):
    """Division operation: a / b"""
    
    def __init__(self):
        super().__init__("divide")
    
    def execute(self, a: Number, b: Number) -> Number:
        """Divide a by b."""
        if b == 0:
            raise DivisionByZeroError([a, b])
        
        try:
            result = a / b
            if abs(result) > 1e308:
                raise OverflowError("divide", [a, b])
            return result
        except (TypeError, ValueError) as e:
            raise OperationError("divide", [a, b], f"Invalid operands: {str(e)}")


class PowerOperation(Operation):
    """Power operation: a ** b (a raised to the power of b)"""
    
    def __init__(self):
        super().__init__("power")
    
    def execute(self, a: Number, b: Number) -> Number:
        """Raise a to the power of b."""
        try:
            # Handle special cases
            if a == 0 and b < 0:
                raise OperationError("power", [a, b], "0 cannot be raised to a negative power")
            
            result = a ** b
            
            # Check for overflow or invalid results
            if math.isnan(result) or math.isinf(result):
                raise OverflowError("power", [a, b])
            
            return result
        except (TypeError, ValueError, OverflowError) as e:
            if isinstance(e, OverflowError):
                raise
            raise OperationError("power", [a, b], f"Invalid power operation: {str(e)}")


class RootOperation(Operation):
    """Root operation: a ** (1/b) (b-th root of a)"""
    
    def __init__(self):
        super().__init__("root")
    
    def execute(self, a: Number, b: Number) -> Number:
        """Calculate the b-th root of a."""
        if b == 0:
            raise InvalidRootError([a, b], "Root index cannot be zero")
        
        # Check for even root of negative number
        if a < 0 and b % 2 == 0:
            raise InvalidRootError([a, b], "Even root of negative number is not real")
        
        try:
            if a < 0 and b % 2 == 1:
                # Handle odd roots of negative numbers
                result = -(abs(a) ** (1/b))
            else:
                result = a ** (1/b)
            
            if math.isnan(result) or math.isinf(result):
                raise InvalidRootError([a, b], "Result is not a real number")
            
            return result
        except (TypeError, ValueError, ZeroDivisionError) as e:
            raise InvalidRootError([a, b], f"Invalid root operation: {str(e)}")


class ModulusOperation(Operation):
    """Modulus operation: a % b (remainder of a divided by b)"""
    
    def __init__(self):
        super().__init__("modulus")
    
    def execute(self, a: Number, b: Number) -> Number:
        """Calculate a modulo b."""
        if b == 0:
            raise DivisionByZeroError([a, b])
        
        try:
            return a % b
        except (TypeError, ValueError) as e:
            raise OperationError("modulus", [a, b], f"Invalid modulus operation: {str(e)}")


class IntegerDivisionOperation(Operation):
    """Integer division operation: a // b (floor division)"""
    
    def __init__(self):
        super().__init__("int_divide")
    
    def execute(self, a: Number, b: Number) -> Number:
        """Perform integer division of a by b."""
        if b == 0:
            raise DivisionByZeroError([a, b])
        
        try:
            return a // b
        except (TypeError, ValueError) as e:
            raise OperationError("int_divide", [a, b], f"Invalid integer division: {str(e)}")


class PercentageOperation(Operation):
    """Percentage operation: (a / b) * 100 (a as percentage of b)"""
    
    def __init__(self):
        super().__init__("percent")
    
    def execute(self, a: Number, b: Number) -> Number:
        """Calculate a as percentage of b."""
        if b == 0:
            raise DivisionByZeroError([a, b])
        
        try:
            result = (a / b) * 100
            if abs(result) > 1e308:
                raise OverflowError("percent", [a, b])
            return result
        except (TypeError, ValueError) as e:
            raise OperationError("percent", [a, b], f"Invalid percentage calculation: {str(e)}")


class AbsoluteDifferenceOperation(Operation):
    """Absolute difference operation: |a - b|"""
    
    def __init__(self):
        super().__init__("abs_diff")
    
    def execute(self, a: Number, b: Number) -> Number:
        """Calculate absolute difference between a and b."""
        try:
            return abs(a - b)
        except (TypeError, ValueError) as e:
            raise OperationError("abs_diff", [a, b], f"Invalid absolute difference: {str(e)}")


class OperationFactory:
    """
    Factory class for creating arithmetic operation instances.
    
    Implements the Factory Design Pattern to manage the creation of 
    different operation instances based on operation names.
    """
    
    # Registry of available operations
    _operations: Dict[str, Type[Operation]] = {
        "add": AddOperation,
        "subtract": SubtractOperation,
        "multiply": MultiplyOperation,
        "divide": DivideOperation,
        "power": PowerOperation,
        "root": RootOperation,
        "modulus": ModulusOperation,
        "int_divide": IntegerDivisionOperation,
        "percent": PercentageOperation,
        "abs_diff": AbsoluteDifferenceOperation,
    }
    
    @classmethod
    def create_operation(cls, operation_name: str) -> Operation:
        """
        Create an operation instance based on the operation name.
        
        Args:
            operation_name (str): Name of the operation to create
            
        Returns:
            Operation: Instance of the requested operation
            
        Raises:
            ValidationError: If the operation name is not supported
        """
        operation_name = operation_name.lower().strip()
        
        if operation_name not in cls._operations:
            available_ops = ", ".join(cls._operations.keys())
            raise ValidationError(
                operation_name,
                f"Unsupported operation",
                f"Available operations: {available_ops}"
            )
        
        return cls._operations[operation_name]()
    
    @classmethod
    def get_available_operations(cls) -> list:
        """
        Get list of all available operation names.
        
        Returns:
            list: List of available operation names
        """
        return list(cls._operations.keys())
    
    @classmethod
    def register_operation(cls, name: str, operation_class: Type[Operation]):
        """
        Register a new operation class with the factory.
        
        Args:
            name (str): Name to register the operation under
            operation_class (Type[Operation]): Operation class to register
            
        Raises:
            ValidationError: If the operation class is invalid
        """
        if not issubclass(operation_class, Operation):
            raise ValidationError(
                operation_class,
                "Invalid operation class",
                "Must inherit from Operation base class"
            )
        
        cls._operations[name.lower().strip()] = operation_class