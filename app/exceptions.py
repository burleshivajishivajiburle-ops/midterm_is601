"""
Custom exception classes for the advanced calculator application.

This module defines specific exception types for different error scenarios
that can occur during calculator operations, providing clear error messages
and proper error handling throughout the application.
"""


class CalculatorError(Exception):
    """Base exception class for all calculator-related errors."""
    
    def __init__(self, message: str, error_code: str = None):
        """
        Initialize the calculator error.
        
        Args:
            message (str): Human-readable error message
            error_code (str, optional): Specific error code for logging/debugging
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
    
    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class OperationError(CalculatorError):
    """Exception raised when an arithmetic operation cannot be performed."""
    
    def __init__(self, operation: str, operands: list, reason: str):
        """
        Initialize the operation error.
        
        Args:
            operation (str): The operation that failed
            operands (list): The operands used in the operation
            reason (str): Why the operation failed
        """
        message = f"Operation '{operation}' failed with operands {operands}: {reason}"
        super().__init__(message, "OP_ERROR")
        self.operation = operation
        self.operands = operands
        self.reason = reason


class ValidationError(CalculatorError):
    """Exception raised when input validation fails."""
    
    def __init__(self, input_value, validation_rule: str, expected_format: str = None):
        """
        Initialize the validation error.
        
        Args:
            input_value: The invalid input value
            validation_rule (str): The validation rule that was violated
            expected_format (str, optional): The expected input format
        """
        message = f"Invalid input '{input_value}': {validation_rule}"
        if expected_format:
            message += f". Expected format: {expected_format}"
        super().__init__(message, "VAL_ERROR")
        self.input_value = input_value
        self.validation_rule = validation_rule
        self.expected_format = expected_format


class DivisionByZeroError(OperationError):
    """Exception raised when attempting to divide by zero."""
    
    def __init__(self, operands: list):
        """
        Initialize the division by zero error.
        
        Args:
            operands (list): The operands where division by zero occurred
        """
        super().__init__(
            operation="division", 
            operands=operands, 
            reason="Division by zero is undefined"
        )


class InvalidRootError(OperationError):
    """Exception raised when attempting invalid root operations."""
    
    def __init__(self, operands: list, reason: str = "Invalid root operation"):
        """
        Initialize the invalid root error.
        
        Args:
            operands (list): The operands used in the root operation
            reason (str): Specific reason for the error
        """
        super().__init__(
            operation="root", 
            operands=operands, 
            reason=reason
        )


class OverflowError(OperationError):
    """Exception raised when a calculation result exceeds system limits."""
    
    def __init__(self, operation: str, operands: list):
        """
        Initialize the overflow error.
        
        Args:
            operation (str): The operation that caused overflow
            operands (list): The operands that caused overflow
        """
        super().__init__(
            operation=operation, 
            operands=operands, 
            reason="Result exceeds maximum allowed value"
        )


class ConfigurationError(CalculatorError):
    """Exception raised when configuration loading or validation fails."""
    
    def __init__(self, config_key: str, reason: str):
        """
        Initialize the configuration error.
        
        Args:
            config_key (str): The configuration key that caused the error
            reason (str): Why the configuration is invalid
        """
        message = f"Configuration error for '{config_key}': {reason}"
        super().__init__(message, "CONFIG_ERROR")
        self.config_key = config_key
        self.reason = reason


class HistoryError(CalculatorError):
    """Exception raised when history operations fail."""
    
    def __init__(self, operation: str, reason: str):
        """
        Initialize the history error.
        
        Args:
            operation (str): The history operation that failed
            reason (str): Why the operation failed
        """
        message = f"History {operation} failed: {reason}"
        super().__init__(message, "HIST_ERROR")
        self.operation = operation
        self.reason = reason


class FileOperationError(CalculatorError):
    """Exception raised when file operations fail."""
    
    def __init__(self, file_path: str, operation: str, reason: str):
        """
        Initialize the file operation error.
        
        Args:
            file_path (str): Path to the file that caused the error
            operation (str): The file operation that failed (read/write/save/load)
            reason (str): Why the operation failed
        """
        message = f"File {operation} failed for '{file_path}': {reason}"
        super().__init__(message, "FILE_ERROR")
        self.file_path = file_path
        self.operation = operation
        self.reason = reason


class MementoError(CalculatorError):
    """Exception raised when memento pattern operations fail."""
    
    def __init__(self, operation: str, reason: str):
        """
        Initialize the memento error.
        
        Args:
            operation (str): The memento operation that failed (undo/redo/save/restore)
            reason (str): Why the operation failed
        """
        message = f"Memento {operation} failed: {reason}"
        super().__init__(message, "MEMENTO_ERROR")
        self.operation = operation
        self.reason = reason