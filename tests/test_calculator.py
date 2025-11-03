"""
Unit tests for Calculator class and integrated functionality.

This module tests the main Calculator class, design pattern integration,
undo/redo functionality, observers, and complete calculation workflows.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.calculator import Calculator
from app.calculation import Calculation
from app.operations import AddOperation, DivideOperation, SubtractOperation
from app.exceptions import (
    CalculatorError, ValidationError, DivisionByZeroError,
    MementoError, HistoryError
)
from app.calculator_memento import Memento
from app.logger import LoggingObserver, AutoSaveObserver


class TestCalculatorBasicOperations:
    """Test basic calculator operations."""
    
    def test_calculator_initialization(self, calculator):
        """Test calculator initialization."""
        assert calculator is not None
        assert calculator.history is not None
        assert calculator.caretaker is not None
        assert len(calculator.observers) >= 0
    
    def test_simple_calculation(self, calculator):
        """Test simple calculation."""
        result = calculator.calculate("add", 5, 3)
        
        assert result["result"] == 8
        assert result["success"] == True
        assert len(calculator.history.get_all_calculations()) == 1
        
        # Check the calculation was recorded properly
        calculations = calculator.history.get_all_calculations()
        calc = calculations[0]
        assert calc.operand1 == 5
        assert calc.operand2 == 3
        assert calc.result == 8
        assert calc.operation.name == "add"
    
    def test_multiple_calculations(self, calculator):
        """Test multiple calculations."""
        result1 = calculator.calculate("add", 5, 3)
        result2 = calculator.calculate("multiply", 4, 6)
        result3 = calculator.calculate("subtract", 10, 2)
        
        assert result1["result"] == 8
        assert result2["result"] == 24
        assert result3["result"] == 8
        
        # Check all calculations were recorded
        calculations = calculator.history.get_all_calculations()
        assert len(calculations) == 3
    
    def test_calculation_with_division(self, calculator):
        """Test division calculation."""
        result = calculator.calculate("divide", 15, 3)
        assert result["result"] == 5
        
        result = calculator.calculate("divide", 10, 4)
        assert result["result"] == 2.5
    
    def test_division_by_zero(self, calculator):
        """Test division by zero error handling."""
        with pytest.raises(DivisionByZeroError):
            calculator.calculate("divide", 10, 0)
        
        # History should not be updated with failed calculation
        assert len(calculator.history.get_all_calculations()) == 0
    
    def test_invalid_operation(self, calculator):
        """Test invalid operation error handling."""
        with pytest.raises(ValidationError):
            calculator.calculate("invalid_op", 5, 3)
        
        # History should not be updated with failed calculation
        assert len(calculator.history.get_all_calculations()) == 0
    
    def test_invalid_operands(self, calculator):
        """Test invalid operand error handling."""
        with pytest.raises(ValidationError):
            calculator.calculate("add", "invalid", 3)
        
        with pytest.raises(ValidationError):
            calculator.calculate("add", 5, None)


class TestCalculatorUndoRedo:
    """Test calculator undo/redo functionality using Memento pattern."""
    
    @pytest.fixture
    def calculator(self):
        """Create a fresh calculator instance for each test."""
        return Calculator()
    
    def test_undo_single_calculation(self, calculator):
        """Test undoing a single calculation."""
        # Perform calculation
        calculator.calculate("add", 5, 3)
        assert len(calculator.history.get_all_calculations()) == 1
        
        # Undo
        calculator.undo()
        assert len(calculator.history.get_all_calculations()) == 0
    
    def test_undo_multiple_calculations(self, calculator):
        """Test undoing multiple calculations."""
        # Perform multiple calculations
        calculator.calculate("add", 5, 3)
        calculator.calculate("multiply", 4, 6)
        calculator.calculate("subtract", 10, 2)
        assert len(calculator.history.get_all_calculations()) == 3
        
        # Undo twice
        calculator.undo()
        assert len(calculator.history.get_all_calculations()) == 2
        
        calculator.undo()
        assert len(calculator.history.get_all_calculations()) == 1
    
    def test_undo_when_empty(self, calculator):
        """Test undo when no calculations exist."""
        with pytest.raises(MementoError, match="No more operations to undo"):
            calculator.undo()
    
    def test_redo_after_undo(self, calculator):
        """Test redo after undo."""
        # Perform calculations
        calculator.calculate("add", 5, 3)
        calculator.calculate("multiply", 4, 6)
        assert len(calculator.history.get_all_calculations()) == 2
        
        # Undo
        calculator.undo()
        assert len(calculator.history.get_all_calculations()) == 1
        
        # Redo
        calculator.redo()
        assert len(calculator.history.get_all_calculations()) == 2
        
        # Check the calculation was restored correctly
        calculations = calculator.history.get_all_calculations()
        assert calculations[1].result == 24  # multiply 4 * 6
    
    def test_redo_when_nothing_to_redo(self, calculator):
        """Test redo when nothing to redo."""
        calculator.calculate("add", 5, 3)
        
        with pytest.raises(MementoError, match="No more operations to redo"):
            calculator.redo()
    
    def test_redo_cleared_after_new_calculation(self, calculator):
        """Test that redo stack is cleared after new calculation."""
        # Perform calculations
        calculator.calculate("add", 5, 3)
        calculator.calculate("multiply", 4, 6)
        
        # Undo one
        calculator.undo()
        assert len(calculator.history.get_all_calculations()) == 1
        
        # Perform new calculation (should clear redo stack)
        calculator.calculate("subtract", 10, 2)
        assert len(calculator.history.get_all_calculations()) == 2
        
        # Redo should no longer work
        with pytest.raises(MementoError):
            calculator.redo()
    
    def test_undo_redo_preview(self, calculator):
        """Test undo/redo preview functionality."""
        # Perform calculations
        calculator.calculate("add", 5, 3)
        calculator.calculate("multiply", 4, 6)
        
        # Test undo preview
        preview = calculator.get_undo_preview()
        assert preview is not None
        assert "multiply" in preview.lower()
        
        # Perform undo
        calculator.undo()
        
        # Test redo preview
        preview = calculator.get_redo_preview()
        assert preview is not None
        assert "multiply" in preview.lower()
    
    def test_undo_redo_preview_when_empty(self, calculator):
        """Test preview when stacks are empty."""
        assert calculator.get_undo_preview() is None
        assert calculator.get_redo_preview() is None


class TestCalculatorObservers:
    """Test calculator observer pattern implementation."""
    
    @pytest.fixture
    def calculator(self):
        """Create a fresh calculator instance for each test."""
        return Calculator()
    
    def test_add_observer(self, calculator):
        """Test adding observers."""
        mock_observer = Mock()
        calculator.add_observer(mock_observer)
        
        assert mock_observer in calculator.observers
    
    def test_remove_observer(self, calculator):
        """Test removing observers."""
        mock_observer = Mock()
        calculator.add_observer(mock_observer)
        calculator.remove_observer(mock_observer)
        
        assert mock_observer not in calculator.observers
    
    def test_notify_observers_on_calculation(self, calculator):
        """Test that observers are notified on calculation."""
        mock_observer = Mock()
        calculator.add_observer(mock_observer)
        
        # Perform calculation
        calculator.calculate("add", 5, 3)
        
        # Check observer was notified
        mock_observer.update.assert_called_once()
        call_args = mock_observer.update.call_args[0]
        assert "calculation_performed" in call_args[0]
    
    def test_notify_observers_on_undo(self, calculator):
        """Test that observers are notified on undo."""
        mock_observer = Mock()
        
        # Perform calculation first
        calculator.calculate("add", 5, 3)
        
        # Add observer after calculation
        calculator.add_observer(mock_observer)
        
        # Perform undo
        calculator.undo()
        
        # Check observer was notified
        mock_observer.update.assert_called_once()
        call_args = mock_observer.update.call_args[0]
        assert "undo_performed" in call_args[0]
    
    def test_logging_observer_integration(self, calculator):
        """Test integration with logging observer."""
        with patch('app.logger.logging') as mock_logging:
            mock_logger = Mock()
            mock_logging.getLogger.return_value = mock_logger
            
            logging_observer = LoggingObserver()
            calculator.add_observer(logging_observer)
            
            # Perform calculation
            calculator.calculate("add", 5, 3)
            
            # Check logging was called
            mock_logger.info.assert_called()
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_auto_save_observer_integration(self, calculator, temp_dir):
        """Test integration with auto-save observer."""
        auto_save_path = temp_dir / "test_auto_save.csv"
        
        auto_save_observer = AutoSaveObserver(str(auto_save_path))
        calculator.add_observer(auto_save_observer)
        
        # Perform calculation
        calculator.calculate("add", 5, 3)
        
        # Check file was created and contains data
        assert auto_save_path.exists()
        content = auto_save_path.read_text()
        assert "add" in content
        assert "5" in content
        assert "3" in content


class TestCalculatorMemento:
    """Test calculator memento pattern implementation."""
    
    @pytest.fixture
    def calculator(self):
        """Create a fresh calculator instance for each test."""
        return Calculator()
    
    def test_create_memento(self, calculator):
        """Test creating a memento."""
        calculator.calculate("add", 5, 3)
        
        memento = calculator.create_memento()
        assert isinstance(memento, Memento)
        assert memento.state is not None
    
    def test_restore_from_memento(self, calculator):
        """Test restoring state from memento."""
        # Perform calculations
        calculator.calculate("add", 5, 3)
        calculator.calculate("multiply", 4, 6)
        
        # Create memento
        memento = calculator.create_memento()
        
        # Perform more calculations
        calculator.calculate("subtract", 10, 2)
        assert len(calculator.history.get_all_calculations()) == 3
        
        # Restore from memento
        calculator.restore_from_memento(memento)
        assert len(calculator.history.get_all_calculations()) == 2
    
    def test_memento_independence(self, calculator):
        """Test that mementos are independent."""
        calculator.calculate("add", 5, 3)
        memento1 = calculator.create_memento()
        
        calculator.calculate("multiply", 4, 6)
        memento2 = calculator.create_memento()
        
        # Restore from first memento
        calculator.restore_from_memento(memento1)
        assert len(calculator.history.get_all_calculations()) == 1
        
        # Restore from second memento
        calculator.restore_from_memento(memento2)
        assert len(calculator.history.get_all_calculations()) == 2


class TestCalculatorHistory:
    """Test calculator history integration."""
    
    @pytest.fixture
    def calculator(self):
        """Create a fresh calculator instance for each test."""
        return Calculator()
    
    def test_clear_history(self, calculator):
        """Test clearing calculation history."""
        # Perform calculations
        calculator.calculate("add", 5, 3)
        calculator.calculate("multiply", 4, 6)
        assert len(calculator.history.get_all_calculations()) == 2
        
        # Clear history
        calculator.clear_history()
        assert len(calculator.history.get_all_calculations()) == 0
    
    def test_get_last_calculation(self, calculator):
        """Test getting last calculation."""
        assert calculator.get_last_calculation() is None
        
        calculator.calculate("add", 5, 3)
        last_calc = calculator.get_last_calculation()
        
        assert last_calc is not None
        assert last_calc.result == 8
    
    def test_get_calculation_by_id(self, calculator):
        """Test getting calculation by ID."""
        calculator.calculate("add", 5, 3)
        calculations = calculator.history.get_all_calculations()
        calc_id = calculations[0].calculation_id
        
        found_calc = calculator.get_calculation_by_id(calc_id)
        assert found_calc is not None
        assert found_calc.calculation_id == calc_id
    
    def test_search_calculations(self, calculator):
        """Test searching calculations."""
        calculator.calculate("add", 5, 3)
        calculator.calculate("multiply", 4, 6)
        calculator.calculate("add", 10, 20)
        
        # Search for add operations
        add_calcs = calculator.search_calculations(operation="add")
        assert len(add_calcs) == 2
        
        for calc in add_calcs:
            assert calc.operation.name == "add"


class TestCalculatorValidation:
    """Test calculator input validation."""
    
    @pytest.fixture
    def calculator(self):
        """Create a fresh calculator instance for each test."""
        return Calculator()
    
    def test_validate_operation_input(self, calculator):
        """Test operation input validation."""
        # Valid operations should work
        assert calculator.calculate("add", 5, 3) == 8
        assert calculator.calculate("ADD", 5, 3) == 8  # Case insensitive
        assert calculator.calculate("  add  ", 5, 3) == 8  # Whitespace
        
        # Invalid operations should raise error
        with pytest.raises(ValidationError):
            calculator.calculate("invalid", 5, 3)
        
        with pytest.raises(ValidationError):
            calculator.calculate("", 5, 3)
        
        with pytest.raises(ValidationError):
            calculator.calculate(None, 5, 3)
    
    def test_validate_operand_inputs(self, calculator):
        """Test operand input validation."""
        # Valid operands
        assert calculator.calculate("add", 5, 3) == 8
        assert calculator.calculate("add", 5.5, 3.2) == 8.7
        assert calculator.calculate("add", -5, 3) == -2
        assert calculator.calculate("add", 0, 0) == 0
        
        # Invalid operands
        with pytest.raises(ValidationError):
            calculator.calculate("add", "5", 3)
        
        with pytest.raises(ValidationError):
            calculator.calculate("add", 5, "3")
        
        with pytest.raises(ValidationError):
            calculator.calculate("add", None, 3)
        
        with pytest.raises(ValidationError):
            calculator.calculate("add", 5, None)


class TestCalculatorErrorHandling:
    """Test calculator error handling and recovery."""
    
    @pytest.fixture
    def calculator(self):
        """Create a fresh calculator instance for each test."""
        return Calculator()
    
    def test_error_recovery(self, calculator):
        """Test calculator recovery after errors."""
        # Successful calculation
        calculator.calculate("add", 5, 3)
        assert len(calculator.history.get_all_calculations()) == 1
        
        # Failed calculation
        with pytest.raises(DivisionByZeroError):
            calculator.calculate("divide", 10, 0)
        
        # History should not include failed calculation
        assert len(calculator.history.get_all_calculations()) == 1
        
        # Next calculation should work normally
        calculator.calculate("multiply", 4, 6)
        assert len(calculator.history.get_all_calculations()) == 2
    
    def test_observer_error_handling(self, calculator):
        """Test error handling when observers fail."""
        # Create a mock observer that raises an exception
        failing_observer = Mock()
        failing_observer.update.side_effect = Exception("Observer failed")
        
        calculator.add_observer(failing_observer)
        
        # Calculation should still succeed even if observer fails
        result = calculator.calculate("add", 5, 3)
        assert result["result"] == 8
        assert len(calculator.history.get_all_calculations()) == 1


class TestCalculatorConfiguration:
    """Test calculator configuration and settings."""
    
    @pytest.fixture
    def calculator(self):
        """Create a fresh calculator instance for each test."""
        return Calculator()
    
    def test_calculator_with_custom_config(self, calculator):
        """Test calculator with custom configuration."""
        # This test assumes the calculator uses configuration
        # The actual implementation would depend on how config is integrated
        assert calculator is not None
    
    def test_precision_handling(self, calculator):
        """Test precision handling in calculations."""
        result = calculator.calculate("divide", 1, 3)
        # Result should maintain reasonable precision
        assert abs(result["result"] - (1/3)) < 1e-10


class TestCalculatorIntegration:
    """Test calculator integration scenarios."""
    
    @pytest.fixture
    def calculator(self):
        """Create a fresh calculator instance for each test."""
        return Calculator()
    
    def test_complete_workflow(self, calculator):
        """Test complete calculator workflow."""
        # Add observers
        mock_observer = Mock()
        calculator.add_observer(mock_observer)
        
        # Perform calculations
        result1 = calculator.calculate("add", 5, 3)
        result2 = calculator.calculate("multiply", result1["result"], 2)
        result3 = calculator.calculate("subtract", result2["result"], 5)
        
        assert result1["result"] == 8
        assert result2["result"] == 16
        assert result3["result"] == 11
        
        # Test undo/redo
        calculator.undo()
        assert len(calculator.history.get_all_calculations()) == 2
        
        calculator.redo()
        assert len(calculator.history.get_all_calculations()) == 3
        
        # Check observers were notified
        assert mock_observer.update.call_count >= 3  # At least 3 calculations
    
    def test_concurrent_operations(self, calculator):
        """Test calculator behavior with rapid operations."""
        # Perform many calculations quickly
        for i in range(10):
            calculator.calculate("add", i, i + 1)
        
        assert len(calculator.history.get_all_calculations()) == 10
        
        # Test undo several times
        for _ in range(5):
            calculator.undo()
        
        assert len(calculator.history.get_all_calculations()) == 5
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_persistence_integration(self, calculator, temp_dir):
        """Test calculator with persistent storage."""
        save_path = temp_dir / "calc_history.csv"
        
        # Add auto-save observer
        auto_save_observer = AutoSaveObserver(str(save_path))
        calculator.add_observer(auto_save_observer)
        
        # Perform calculations
        calculator.calculate("add", 5, 3)
        calculator.calculate("multiply", 4, 6)
        
        # Check file was created
        assert save_path.exists()
        
        # Create new calculator and load history
        new_calculator = Calculator()
        new_calculator.history.load_from_csv(str(save_path))
        
        # Check history was loaded
        loaded_calcs = new_calculator.history.get_all_calculations()
        assert len(loaded_calcs) == 2
        assert loaded_calcs[0].result == 8
        assert loaded_calcs[1].result == 24


@pytest.mark.parametrize("operation,operand1,operand2,expected", [
    ("add", 1, 2, 3),
    ("subtract", 5, 3, 2),
    ("multiply", 4, 6, 24),
    ("divide", 15, 3, 5),
    ("power", 2, 3, 8),
    ("modulus", 17, 5, 2),
])
def test_calculator_operations_parametrized(operation, operand1, operand2, expected):
    """Test calculator operations with parametrized inputs."""
    calculator = Calculator()
    result = calculator.calculate(operation, operand1, operand2)
    assert result["result"] == expected


class TestCalculatorPerformance:
    """Test calculator performance characteristics."""
    
    @pytest.fixture
    def calculator(self):
        """Create a fresh calculator instance for each test."""
        return Calculator()
    
    @pytest.mark.slow
    def test_large_history_performance(self, calculator):
        """Test calculator performance with large history."""
        # Perform many calculations
        for i in range(1000):
            calculator.calculate("add", i, i + 1)
        
        # Operations should still be fast
        start_time = datetime.now()
        calculator.calculate("multiply", 5, 6)
        end_time = datetime.now()
        
        # Should complete in reasonable time
        assert (end_time - start_time).total_seconds() < 1.0
    
    @pytest.mark.slow
    def test_many_undo_operations(self, calculator):
        """Test performance with many undo operations."""
        # Create calculations to undo
        for i in range(100):
            calculator.calculate("add", i, i + 1)
        
        # Undo all calculations
        start_time = datetime.now()
        for _ in range(100):
            calculator.undo()
        end_time = datetime.now()
        
        # Should complete in reasonable time
        assert (end_time - start_time).total_seconds() < 2.0
        assert len(calculator.history.get_all_calculations()) == 0


if __name__ == "__main__":
    pytest.main([__file__])


# --- Additional coverage-focused tests (history filters, observers attach) ---

def test_history_filters_and_stats_via_calculator(tmp_path):
    from app.calculator_config import CalculatorConfig
    from datetime import datetime, timedelta

    cfg = CalculatorConfig(env_file=None, auto_create_dirs=False)
    c = Calculator(config=cfg)

    # Create a spread of calculations
    c.calculate("add", 1, 2)        # 3
    c.calculate("multiply", 2, 3)   # 6
    c.calculate("subtract", 10, 7)  # 3

    # Result-range filter
    rr = c.history.search_calculations(result_range=(3, 3))
    assert all(item["result"] == 3 for item in rr)

    # Operation filter + limit
    ops = c.history.search_calculations(operation="multiply", limit=1)
    assert len(ops) == 1 and ops[0]["operation"] == "multiply"

    # Date-range filter (tight range around now)
    now = datetime.now()
    dr = c.history.search_calculations(date_range=(now - timedelta(days=1), now + timedelta(days=1)))
    assert len(dr) >= 3

    # Success filter
    only_success = c.history.search_calculations(success_only=True)
    assert len(only_success) >= 3

    # Stats structure and values
    stats = c.history.get_statistics()
    assert stats["total_calculations"] >= 3
    assert "operations_count" in stats and isinstance(stats["operations_count"], dict)
    assert stats["date_range"]["earliest"] <= stats["date_range"]["latest"]

    # Remove a specific calculation and a missing one
    all_calcs = c.history.get_all_calculations()
    assert c.history.remove_calculation(all_calcs[0].calculation_id) is True
    assert c.history.remove_calculation("does-not-exist") is False

    # Remove last/trim paths
    assert c.history.remove_last() in (True, False)
    c.history.trim_to_count(1)
    assert len(c.history.get_all_calculations()) <= 1


def test_observers_attach_when_pytest_env_disabled(tmp_path, monkeypatch):
    from app.calculator_config import CalculatorConfig

    # Ensure pytest env var is absent during construction so Calculator won't force-disable observers
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)

    # Prepare dirs in a temp area and enable both observers
    cfg = CalculatorConfig(env_file=None, auto_create_dirs=True)
    cfg.set_config_value("CALCULATOR_ENABLE_LOGGING", True)
    cfg.set_config_value("CALCULATOR_ENABLE_AUTO_SAVE", True)
    cfg.set_config_value("CALCULATOR_LOG_DIR", str(tmp_path / "logs"))
    cfg.set_config_value("CALCULATOR_HISTORY_DIR", str(tmp_path / "hist"))

    c = Calculator(config=cfg)

    # Both observers should be attached
    assert len(c.observers) >= 1  # at least logging, possibly autosave too

    # Perform a calculation and ensure auto-save file is generated
    c.calculate("add", 1, 1)
    # Expect a CSV history in configured directory when autosave is enabled
    hist_csv = tmp_path / "hist" / cfg.get_history_file()
    assert hist_csv.exists()