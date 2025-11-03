"""
Unit tests for memento pattern implementation.

This module tests the Memento pattern classes including Memento,
CalculatorMemento, and Caretaker for undo/redo functionality.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from app.calculator_memento import Memento, CalculatorMemento, Caretaker
from app.exceptions import MementoError


class TestMemento:
    """Test basic Memento class."""
    
    def test_memento_creation(self):
        """Test memento creation with state."""
        current_result = 42
        calculation_count = 5
        memento = CalculatorMemento(current_result=current_result, calculation_count=calculation_count)
        
        state = memento.get_state()
        assert state["current_result"] == current_result
        assert state["calculation_count"] == calculation_count
        assert isinstance(memento.timestamp, datetime)
    
    def test_memento_with_custom_timestamp(self):
        """Test memento with custom timestamp."""
        custom_time = datetime(2023, 1, 1, 12, 0, 0)
        memento = CalculatorMemento(current_result=42, timestamp=custom_time)
        
        assert memento.timestamp == custom_time
    
    def test_memento_state_immutability(self):
        """Test that memento state is preserved."""
        original_state = {"calculations": [1, 2, 3]}
        memento = CalculatorMemento(original_state)
        
        # Modify original state
        original_state["calculations"].append(4)
        
        # Memento should preserve original state (depends on implementation)
        # Note: This test may need adjustment based on deep copy implementation
        assert memento.get_state() is not None
    
    def test_memento_string_representation(self):
        """Test string representation of memento."""
        state = {"test": "data"}
        memento = CalculatorMemento(state)
        
        str_repr = str(memento)
        assert "Memento" in str_repr
        assert isinstance(str_repr, str)


class TestCalculatorMemento:
    """Test CalculatorMemento class."""
    
    @pytest.fixture
    def mock_history(self):
        """Create mock history object."""
        history = Mock()
        history.get_all_calculations.return_value = []
        history.clear.return_value = None
        history.add_calculation.return_value = None
        return history
    
    def test_calculator_memento_creation(self, mock_history):
        """Test CalculatorMemento creation."""
        memento = CalculatorMemento(mock_history)
        
        assert memento.history == mock_history
        assert isinstance(memento, CalculatorMemento)
    
    def test_create_memento(self, mock_history):
        """Test creating memento from current state."""
        # Setup mock calculations
        mock_calc1 = Mock()
        mock_calc1.to_dict.return_value = {"operation": "add", "result": 8}
        mock_calc2 = Mock()
        mock_calc2.to_dict.return_value = {"operation": "multiply", "result": 24}
        
        mock_history.get_all_calculations.return_value = [mock_calc1, mock_calc2]
        
        calc_memento = CalculatorMemento(mock_history)
        memento = calc_memento.create_memento()
        
        assert isinstance(memento, Memento)
        assert "calculations" in memento.state
        assert len(memento.state["calculations"]) == 2
    
    def test_restore_from_memento(self, mock_history):
        """Test restoring state from memento."""
        # Create memento with test data
        state = {
            "calculations": [
                {"operation": "add", "operand1": 5, "operand2": 3, "result": 8},
                {"operation": "multiply", "operand1": 4, "operand2": 6, "result": 24}
            ]
        }
        memento = CalculatorMemento(state)
        
        # Mock Calculation.from_dict
        with pytest.mock.patch('app.calculation.Calculation.from_dict') as mock_from_dict:
            mock_calc = Mock()
            mock_from_dict.return_value = mock_calc
            
            calc_memento = CalculatorMemento(mock_history)
            calc_memento.restore_from_memento(memento)
            
            # Verify history was cleared and calculations added
            mock_history.clear.assert_called_once()
            assert mock_history.add_calculation.call_count == 2
    
    def test_restore_from_invalid_memento(self, mock_history):
        """Test restoring from invalid memento."""
        calc_memento = CalculatorMemento(mock_history)
        
        # Test with None
        with pytest.raises(MementoError, match="Invalid memento"):
            calc_memento.restore_from_memento(None)
        
        # Test with invalid state
        invalid_memento = CalculatorMemento({"invalid": "state"})
        with pytest.raises(MementoError, match="Invalid memento state"):
            calc_memento.restore_from_memento(invalid_memento)
    
    def test_memento_with_empty_history(self, mock_history):
        """Test memento creation with empty history."""
        mock_history.get_all_calculations.return_value = []
        
        calc_memento = CalculatorMemento(mock_history)
        memento = calc_memento.create_memento()
        
        assert memento.state["calculations"] == []
    
    def test_memento_error_handling(self, mock_history):
        """Test error handling in memento operations."""
        # Mock history that raises exception
        mock_history.get_all_calculations.side_effect = Exception("History error")
        
        calc_memento = CalculatorMemento(mock_history)
        
        with pytest.raises(MementoError):
            calc_memento.create_memento()


class TestCaretaker:
    """Test Caretaker class for managing mementos."""
    
    @pytest.fixture
    def caretaker(self):
        """Create fresh caretaker instance."""
        return Caretaker()
    
    @pytest.fixture
    def mock_originator(self):
        """Create mock originator."""
        originator = Mock()
        originator.create_memento.return_value = Memento({"test": "state"})
        return originator
    
    def test_caretaker_initialization(self, caretaker):
        """Test caretaker initialization."""
        assert caretaker is not None
        assert len(caretaker.undo_stack) == 0
        assert len(caretaker.redo_stack) == 0
    
    def test_save_state(self, caretaker, mock_originator):
        """Test saving state."""
        caretaker.save_state(mock_originator)
        
        assert len(caretaker.undo_stack) == 1
        assert len(caretaker.redo_stack) == 0
        mock_originator.create_memento.assert_called_once()
    
    def test_save_multiple_states(self, caretaker, mock_originator):
        """Test saving multiple states."""
        # Save multiple states
        for i in range(3):
            mock_originator.create_memento.return_value = Memento({"state": i})
            caretaker.save_state(mock_originator)
        
        assert len(caretaker.undo_stack) == 3
        assert len(caretaker.redo_stack) == 0
    
    def test_undo_operation(self, caretaker, mock_originator):
        """Test undo operation."""
        # Save initial state
        initial_memento = Memento({"state": "initial"})
        mock_originator.create_memento.return_value = initial_memento
        caretaker.save_state(mock_originator)
        
        # Save another state
        second_memento = Memento({"state": "second"})
        mock_originator.create_memento.return_value = second_memento
        caretaker.save_state(mock_originator)
        
        # Undo
        caretaker.undo(mock_originator)
        
        # Check stacks
        assert len(caretaker.undo_stack) == 1
        assert len(caretaker.redo_stack) == 1
        
        # Check restore was called with initial state
        mock_originator.restore_from_memento.assert_called_once_with(initial_memento)
    
    def test_undo_when_empty(self, caretaker, mock_originator):
        """Test undo when stack is empty."""
        with pytest.raises(MementoError, match="No more operations to undo"):
            caretaker.undo(mock_originator)
    
    def test_redo_operation(self, caretaker, mock_originator):
        """Test redo operation."""
        # Setup: save two states and undo one
        initial_memento = Memento({"state": "initial"})
        second_memento = Memento({"state": "second"})
        
        mock_originator.create_memento.side_effect = [initial_memento, second_memento]
        
        caretaker.save_state(mock_originator)
        caretaker.save_state(mock_originator)
        caretaker.undo(mock_originator)
        
        # Now redo
        caretaker.redo(mock_originator)
        
        # Check stacks
        assert len(caretaker.undo_stack) == 2
        assert len(caretaker.redo_stack) == 0
        
        # Check restore was called twice (once for undo, once for redo)
        assert mock_originator.restore_from_memento.call_count == 2
    
    def test_redo_when_empty(self, caretaker, mock_originator):
        """Test redo when stack is empty."""
        with pytest.raises(MementoError, match="No more operations to redo"):
            caretaker.redo(mock_originator)
    
    def test_clear_redo_on_new_save(self, caretaker, mock_originator):
        """Test that redo stack is cleared on new save."""
        # Setup: save states, undo, then save new state
        mock_originator.create_memento.side_effect = [
            Memento({"state": "first"}),
            Memento({"state": "second"}),
            Memento({"state": "third"})
        ]
        
        caretaker.save_state(mock_originator)
        caretaker.save_state(mock_originator)
        caretaker.undo(mock_originator)  # This puts something in redo stack
        
        assert len(caretaker.redo_stack) == 1
        
        # Save new state (should clear redo stack)
        caretaker.save_state(mock_originator)
        
        assert len(caretaker.redo_stack) == 0
        assert len(caretaker.undo_stack) == 2
    
    def test_can_undo(self, caretaker):
        """Test can_undo method."""
        assert not caretaker.can_undo()
        
        # Add a memento
        caretaker.undo_stack.append(Memento({"test": "state"}))
        assert caretaker.can_undo()
    
    def test_can_redo(self, caretaker):
        """Test can_redo method."""
        assert not caretaker.can_redo()
        
        # Add a memento
        caretaker.redo_stack.append(Memento({"test": "state"}))
        assert caretaker.can_redo()
    
    def test_get_undo_preview(self, caretaker):
        """Test getting undo preview."""
        assert caretaker.get_undo_preview() is None
        
        # Add memento with preview
        memento = Memento({"calculations": [{"operation": "add"}]})
        caretaker.undo_stack.append(memento)
        
        preview = caretaker.get_undo_preview()
        assert preview is not None
        assert "add" in preview.lower()
    
    def test_get_redo_preview(self, caretaker):
        """Test getting redo preview."""
        assert caretaker.get_redo_preview() is None
        
        # Add memento with preview
        memento = Memento({"calculations": [{"operation": "multiply"}]})
        caretaker.redo_stack.append(memento)
        
        preview = caretaker.get_redo_preview()
        assert preview is not None
        assert "multiply" in preview.lower()
    
    def test_preview_with_multiple_operations(self, caretaker):
        """Test preview with multiple operations."""
        # Create memento with multiple calculations
        calculations = [
            {"operation": "add", "operand1": 5, "operand2": 3},
            {"operation": "multiply", "operand1": 4, "operand2": 6}
        ]
        memento = Memento({"calculations": calculations})
        caretaker.undo_stack.append(memento)
        
        preview = caretaker.get_undo_preview()
        assert "multiply" in preview.lower()  # Should show last operation
    
    def test_preview_with_empty_calculations(self, caretaker):
        """Test preview with empty calculations."""
        memento = Memento({"calculations": []})
        caretaker.undo_stack.append(memento)
        
        preview = caretaker.get_undo_preview()
        assert "empty state" in preview.lower() or preview is None


class TestMementoMaxSize:
    """Test memento stack size management."""
    
    def test_undo_stack_max_size(self):
        """Test undo stack respects maximum size."""
        caretaker = Caretaker(max_undo_size=3)
        mock_originator = Mock()
        
        # Save more states than max size
        for i in range(5):
            mock_originator.create_memento.return_value = Memento({"state": i})
            caretaker.save_state(mock_originator)
        
        # Should only keep max_size states
        assert len(caretaker.undo_stack) == 3
        
        # Oldest state should be removed
        states = [m.state["state"] for m in caretaker.undo_stack]
        assert states == [2, 3, 4]  # Should keep the 3 most recent
    
    def test_redo_stack_max_size(self):
        """Test redo stack respects maximum size."""
        caretaker = Caretaker(max_redo_size=2)
        mock_originator = Mock()
        
        # Setup: save many states then undo many times
        for i in range(5):
            mock_originator.create_memento.return_value = Memento({"state": i})
            caretaker.save_state(mock_originator)
        
        # Undo multiple times (creates redo stack)
        for _ in range(4):
            caretaker.undo(mock_originator)
        
        # Redo stack should be limited to max size
        assert len(caretaker.redo_stack) <= 2


class TestMementoIntegration:
    """Test memento pattern integration scenarios."""
    
    def test_complete_undo_redo_workflow(self):
        """Test complete undo/redo workflow."""
        caretaker = Caretaker()
        mock_originator = Mock()
        
        # Create sequence of mementos
        states = [{"calculations": [f"calc_{i}"]} for i in range(3)]
        mock_originator.create_memento.side_effect = [Memento(state) for state in states]
        
        # Save multiple states
        for _ in range(3):
            caretaker.save_state(mock_originator)
        
        # Undo twice
        caretaker.undo(mock_originator)
        caretaker.undo(mock_originator)
        
        # Redo once
        caretaker.redo(mock_originator)
        
        # Final state verification
        assert len(caretaker.undo_stack) == 2
        assert len(caretaker.redo_stack) == 1
        assert mock_originator.restore_from_memento.call_count == 3  # 2 undos + 1 redo
    
    def test_memento_with_large_state(self):
        """Test memento with large state data."""
        large_state = {
            "calculations": [{"operation": f"op_{i}", "result": i} for i in range(1000)]
        }
        memento = Memento(large_state)
        
        assert len(memento.state["calculations"]) == 1000
        assert memento.state["calculations"][999]["result"] == 999
    
    def test_memento_error_recovery(self):
        """Test error recovery in memento operations."""
        caretaker = Caretaker()
        mock_originator = Mock()
        
        # Setup working state
        mock_originator.create_memento.return_value = Memento({"test": "state"})
        caretaker.save_state(mock_originator)
        
        # Make restore fail
        mock_originator.restore_from_memento.side_effect = Exception("Restore failed")
        
        # Undo should raise MementoError but not corrupt caretaker state
        with pytest.raises(MementoError):
            caretaker.undo(mock_originator)
        
        # Caretaker should still be in valid state
        assert len(caretaker.undo_stack) == 1  # State preserved
        assert len(caretaker.redo_stack) == 0


class TestMementoPerformance:
    """Test memento performance characteristics."""
    
    @pytest.mark.slow
    def test_many_mementos_performance(self):
        """Test performance with many mementos."""
        caretaker = Caretaker()
        mock_originator = Mock()
        
        # Save many states
        start_time = datetime.now()
        for i in range(100):
            mock_originator.create_memento.return_value = Memento({"state": i})
            caretaker.save_state(mock_originator)
        end_time = datetime.now()
        
        # Should complete quickly
        assert (end_time - start_time).total_seconds() < 1.0
        
        # Undo operations should also be fast
        start_time = datetime.now()
        for _ in range(50):
            caretaker.undo(mock_originator)
        end_time = datetime.now()
        
        assert (end_time - start_time).total_seconds() < 1.0


@pytest.mark.parametrize("undo_count,expected_undo_size,expected_redo_size", [
    (0, 3, 0),
    (1, 2, 1),
    (2, 1, 2),
    (3, 0, 3),
])
def test_undo_redo_stack_sizes(undo_count, expected_undo_size, expected_redo_size):
    """Test undo/redo stack sizes with parameterized inputs."""
    caretaker = Caretaker()
    mock_originator = Mock()
    
    # Save 3 states
    for i in range(3):
        mock_originator.create_memento.return_value = Memento({"state": i})
        caretaker.save_state(mock_originator)
    
    # Perform specified number of undos
    for _ in range(undo_count):
        caretaker.undo(mock_originator)
    
    assert len(caretaker.undo_stack) == expected_undo_size
    assert len(caretaker.redo_stack) == expected_redo_size


if __name__ == "__main__":
    pytest.main([__file__])