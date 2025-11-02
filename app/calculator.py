"""
Main Calculator class integrating all features.

This module provides the main Calculator class that integrates all design patterns
and features: Factory pattern operations, Memento pattern undo/redo, Observer pattern
logging/auto-save, comprehensive configuration management, and history management.
"""

import time
from datetime import datetime
from typing import Union, Optional, List, Dict, Any

from .calculation import Calculation, CalculationBuilder
from .operations import OperationFactory
from .input_validators import InputValidator
from .calculator_memento import CalculatorMemento, Caretaker, Originator
from .logger import CalculatorSubject, LoggingObserver, AutoSaveObserver
from .calculator_config import CalculatorConfig, get_config
from .history import CalculationHistory
from .exceptions import (
    CalculatorError, 
    OperationError, 
    ValidationError, 
    MementoError,
    ConfigurationError
)

# Type aliases
Number = Union[int, float]
CalculationResult = Dict[str, Any]


class Calculator(Originator):
    """
    Advanced Calculator with comprehensive features.
    
    Integrates all design patterns and features:
    - Factory pattern for operations
    - Memento pattern for undo/redo
    - Observer pattern for logging and auto-save
    - Configuration management
    - History management with pandas serialization
    - Robust error handling and input validation
    """
    
    def __init__(self, config: Optional[CalculatorConfig] = None):
        """
        Initialize the calculator with all integrated features.
        
        Args:
            config (CalculatorConfig, optional): Configuration instance
        """
        # Configuration
        self.config = config or get_config()
        
        # Current state
        self.current_result: Optional[Number] = None
        self.last_calculation: Optional[Calculation] = None
        self.calculation_count: int = 0
        
        # Memento pattern for undo/redo
        self.caretaker = Caretaker(max_history_size=self.config.get_memento_max_size())
        
        # Observer pattern setup
        self.subject = CalculatorSubject()
        self._setup_observers()
        
        # History management
        self.history = CalculationHistory(
            history_file=self.config.get_history_file_path() if self.config.is_auto_save_enabled() else None,
            max_entries=self.config.get_max_history_size(),
            auto_save=self.config.is_auto_save_enabled()
        )
        
        # Save initial state
        if self.config.is_undo_redo_enabled():
            self._save_state()
    
    def _setup_observers(self) -> None:
        """Setup observers for logging and auto-save functionality."""
        try:
            # Setup logging observer if enabled
            if self.config.is_logging_enabled():
                logging_observer = LoggingObserver(
                    log_file=self.config.get_log_file_path(),
                    log_level=self.config.get_log_level(),
                    log_format=self.config.get_log_format()
                )
                self.subject.attach(logging_observer)
            
            # Setup auto-save observer if enabled
            if self.config.is_auto_save_enabled():
                autosave_observer = AutoSaveObserver(
                    save_file=self.config.get_history_file_path(),
                    save_frequency=1,  # Save after each calculation
                    max_entries=self.config.get_max_history_size()
                )
                self.subject.attach(autosave_observer)
                
        except Exception as e:
            # Don't fail initialization if observers fail
            print(f"Warning: Failed to setup observers: {e}")
    
    def calculate(self, operation: str, operand_a: Number, operand_b: Number) -> CalculationResult:
        """
        Perform a calculation with comprehensive error handling and state management.
        
        Args:
            operation (str): Operation name
            operand_a (Number): First operand
            operand_b (Number): Second operand
            
        Returns:
            CalculationResult: Detailed calculation result
            
        Raises:
            CalculatorError: If calculation fails
        """
        start_time = time.time()
        
        try:
            # Validate inputs
            validated_operation = InputValidator.validate_operation_name(operation)
            validated_a = InputValidator.validate_numeric_input(
                operand_a, 
                max_value=self.config.get_max_input_value(),
                min_value=-self.config.get_max_input_value()
            )
            validated_b = InputValidator.validate_numeric_input(
                operand_b,
                max_value=self.config.get_max_input_value(), 
                min_value=-self.config.get_max_input_value()
            )
            
            # Perform operation-specific validation
            if validated_operation in ["divide", "modulus", "int_divide"]:
                InputValidator.validate_division_operation(validated_a, validated_b)
            elif validated_operation == "power":
                InputValidator.validate_power_operation(validated_a, validated_b)
            elif validated_operation == "root":
                InputValidator.validate_root_operation(validated_a, validated_b)
            elif validated_operation == "percent":
                InputValidator.validate_percentage_operation(validated_a, validated_b)
            
            # Save current state before calculation (for undo)
            if self.config.is_undo_redo_enabled():
                self._save_state()
            
            # Create and execute calculation
            calculation = Calculation(validated_operation, validated_a, validated_b)
            
            # Update calculator state
            self.current_result = calculation.result
            self.last_calculation = calculation
            self.calculation_count += 1
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Prepare result data
            result_data = {
                "calculation": calculation,
                "result": calculation.result,
                "expression": calculation.get_formatted_expression(),
                "success": calculation.is_successful(),
                "operation": validated_operation,
                "operands": [validated_a, validated_b],
                "duration_ms": round(duration_ms, 2),
                "calculation_count": self.calculation_count
            }
            
            # Add to history
            self._add_to_history(calculation, duration_ms)
            
            # Notify observers
            self.subject.notify_calculation(calculation.to_dict())
            
            return result_data
            
        except Exception as e:
            # Calculate duration even for errors
            duration_ms = (time.time() - start_time) * 1000
            
            # Create error result
            error_data = {
                "calculation": None,
                "result": None,
                "expression": f"{operand_a} {operation} {operand_b} = ERROR",
                "success": False,
                "operation": operation,
                "operands": [operand_a, operand_b],
                "error": str(e),
                "duration_ms": round(duration_ms, 2),
                "calculation_count": self.calculation_count
            }
            
            # Notify observers of error
            self.subject.notify_error(
                type(e).__name__,
                str(e),
                {"operation": operation, "operands": [operand_a, operand_b]}
            )
            
            # Re-raise the exception
            raise
    
    def calculate_from_string(self, input_string: str) -> CalculationResult:
        """
        Perform calculation from string input.
        
        Args:
            input_string (str): Input like "5 + 3" or "add 5 3"
            
        Returns:
            CalculationResult: Calculation result
        """
        try:
            operation, operands = InputValidator.parse_calculation_input(input_string)
            return self.calculate(operation, operands[0], operands[1])
        except Exception as e:
            raise ValidationError(
                input_string,
                f"Failed to parse calculation: {str(e)}",
                "Use format like '5 + 3' or 'add 5 3'"
            )
    
    def undo(self) -> Optional[Dict[str, Any]]:
        """
        Undo the last calculation.
        
        Returns:
            Optional[Dict[str, Any]]: Previous state or None if no undo available
            
        Raises:
            MementoError: If undo operation fails
        """
        if not self.config.is_undo_redo_enabled():
            raise MementoError("undo", "Undo/redo functionality is disabled")
        
        try:
            if not self.caretaker.can_undo():
                return None
            
            # Perform undo
            previous_memento = self.caretaker.undo()
            
            # Restore state
            self.restore_memento(previous_memento)
            
            # Prepare result
            result = {
                "success": True,
                "current_result": self.current_result,
                "calculation_count": self.calculation_count,
                "message": "Successfully undone last calculation"
            }
            
            # Notify observers
            self.subject.notify_undo(result)
            
            return result
            
        except Exception as e:
            raise MementoError("undo", f"Undo operation failed: {str(e)}")
    
    def redo(self) -> Optional[Dict[str, Any]]:
        """
        Redo the last undone calculation.
        
        Returns:
            Optional[Dict[str, Any]]: Next state or None if no redo available
            
        Raises:
            MementoError: If redo operation fails
        """
        if not self.config.is_undo_redo_enabled():
            raise MementoError("redo", "Undo/redo functionality is disabled")
        
        try:
            if not self.caretaker.can_redo():
                return None
            
            # Perform redo
            next_memento = self.caretaker.redo()
            
            # Restore state
            self.restore_memento(next_memento)
            
            # Prepare result
            result = {
                "success": True,
                "current_result": self.current_result,
                "calculation_count": self.calculation_count,
                "message": "Successfully redone calculation"
            }
            
            # Notify observers
            self.subject.notify_redo(result)
            
            return result
            
        except Exception as e:
            raise MementoError("redo", f"Redo operation failed: {str(e)}")
    
    def clear_memory(self) -> None:
        """Clear the current result and reset calculator state."""
        self.current_result = None
        self.last_calculation = None
        
        # Save state after clearing
        if self.config.is_undo_redo_enabled():
            self._save_state()
        
        # Notify observers
        self.subject.notify_clear("memory")
    
    def clear_history(self) -> None:
        """Clear all calculation history."""
        self.history.clear_history()
        
        # Notify observers
        self.subject.notify_clear("history")
    
    def clear_all(self) -> None:
        """Clear everything (memory, history, undo stack)."""
        self.current_result = None
        self.last_calculation = None
        self.calculation_count = 0
        
        self.history.clear_history()
        
        if self.config.is_undo_redo_enabled():
            self.caretaker.clear_history()
            self._save_state()
        
        # Notify observers
        self.subject.notify_clear("all")
    
    def get_history(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent calculation history.
        
        Args:
            count (int): Number of recent calculations to retrieve
            
        Returns:
            List[Dict[str, Any]]: Recent calculations
        """
        return self.history.get_recent_calculations(count)
    
    def search_history(self, **filters) -> List[Dict[str, Any]]:
        """
        Search calculation history with filters.
        
        Args:
            **filters: Search filters (operation, result_range, date_range, etc.)
            
        Returns:
            List[Dict[str, Any]]: Filtered calculations
        """
        return self.history.search_calculations(**filters)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive calculator statistics.
        
        Returns:
            Dict[str, Any]: Statistics including history and session info
        """
        history_stats = self.history.get_statistics()
        memento_stats = self.caretaker.get_history_summary()
        
        return {
            "session": {
                "current_result": self.current_result,
                "calculation_count": self.calculation_count,
                "last_calculation": self.last_calculation.get_formatted_expression() if self.last_calculation else None,
                "session_start": datetime.now().isoformat()
            },
            "history": history_stats,
            "undo_redo": memento_stats,
            "configuration": {
                "precision": self.config.get_precision(),
                "max_history_size": self.config.get_max_history_size(),
                "features_enabled": {
                    "logging": self.config.is_logging_enabled(),
                    "auto_save": self.config.is_auto_save_enabled(),
                    "undo_redo": self.config.is_undo_redo_enabled()
                }
            }
        }
    
    def get_available_operations(self) -> List[str]:
        """Get list of all available operations."""
        return OperationFactory.get_available_operations()
    
    def export_history(self, file_path: str, format: str = "csv") -> None:
        """
        Export calculation history to file.
        
        Args:
            file_path (str): Output file path
            format (str): Export format (csv, json, excel)
        """
        self.history.export_history(file_path, format)
    
    def load_history(self, file_path: str) -> None:
        """
        Load calculation history from file.
        
        Args:
            file_path (str): Input file path
        """
        self.history.load_history(file_path)
    
    # Memento pattern implementation
    def create_memento(self) -> CalculatorMemento:
        """Create a memento of the current calculator state."""
        return CalculatorMemento(
            current_result=self.current_result,
            last_calculation=self.last_calculation.to_dict() if self.last_calculation else None,
            calculation_count=self.calculation_count
        )
    
    def restore_memento(self, memento: CalculatorMemento) -> None:
        """Restore calculator state from a memento."""
        if not isinstance(memento, CalculatorMemento):
            raise MementoError("restore", "Invalid memento type")
        
        self.current_result = memento.current_result
        self.calculation_count = memento.calculation_count
        
        # Restore last calculation if available
        if memento.last_calculation:
            try:
                from .calculation import Calculation
                self.last_calculation = Calculation.from_dict(memento.last_calculation)
            except Exception:
                self.last_calculation = None
        else:
            self.last_calculation = None
    
    def _save_state(self) -> None:
        """Save current state as memento."""
        if self.config.is_undo_redo_enabled():
            memento = self.create_memento()
            self.caretaker.save_memento(memento)
    
    def _add_to_history(self, calculation: Calculation, duration_ms: float) -> None:
        """Add calculation to history."""
        calc_dict = calculation.to_dict()
        calc_dict["duration_ms"] = duration_ms
        self.history.add_calculation(calc_dict)
    
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return (self.config.is_undo_redo_enabled() and 
                self.caretaker.can_undo())
    
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return (self.config.is_undo_redo_enabled() and 
                self.caretaker.can_redo())
    
    def get_undo_preview(self) -> Optional[str]:
        """Get preview of what will be undone."""
        if self.can_undo():
            return self.caretaker.get_undo_preview()
        return None
    
    def get_redo_preview(self) -> Optional[str]:
        """Get preview of what will be redone."""
        if self.can_redo():
            return self.caretaker.get_redo_preview()
        return None
    
    def __str__(self) -> str:
        """String representation of the calculator."""
        return f"Calculator(result={self.current_result}, calculations={self.calculation_count})"
    
    def __repr__(self) -> str:
        """Developer representation of the calculator."""
        return (f"Calculator(current_result={self.current_result}, "
                f"calculation_count={self.calculation_count}, "
                f"history_entries={len(self.history)}, "
                f"undo_available={self.can_undo()}, "
                f"redo_available={self.can_redo()})")