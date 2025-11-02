"""
Memento pattern implementation for undo/redo functionality.

This module implements the Memento design pattern to provide undo/redo
capabilities for calculator operations. It allows users to revert the last
calculation or redo an undone calculation while maintaining the history
stack accurately.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from copy import deepcopy
import json

from .exceptions import MementoError, ValidationError

# Type alias for memento data
MementoData = Dict[str, Any]


class Memento(ABC):
    """
    Abstract base class for memento objects.
    
    Defines the interface for memento objects that store state snapshots
    for undo/redo operations.
    """
    
    def __init__(self, state: MementoData, timestamp: Optional[datetime] = None):
        """
        Initialize memento with state data.
        
        Args:
            state (MementoData): The state data to store
            timestamp (datetime, optional): When the memento was created
        """
        self._state = deepcopy(state)
        self._timestamp = timestamp or datetime.now()
        self._id = f"memento_{self._timestamp.strftime('%Y%m%d_%H%M%S_%f')}"
    
    @abstractmethod
    def get_state(self) -> MementoData:
        """
        Get the stored state data.
        
        Returns:
            MementoData: The stored state
        """
        pass
    
    @property
    def timestamp(self) -> datetime:
        """Get the timestamp when this memento was created."""
        return self._timestamp
    
    @property
    def id(self) -> str:
        """Get the unique identifier for this memento."""
        return self._id


class CalculatorMemento(Memento):
    """
    Concrete memento for calculator state.
    
    Stores the complete state of a calculator including current result,
    last calculation, and any other relevant state information.
    """
    
    def __init__(self, 
                 current_result: Optional[Union[int, float]] = None,
                 last_calculation: Optional[Dict[str, Any]] = None,
                 calculation_count: int = 0,
                 additional_state: Optional[Dict[str, Any]] = None,
                 timestamp: Optional[datetime] = None):
        """
        Initialize calculator memento.
        
        Args:
            current_result: The current calculator result
            last_calculation: The last calculation performed
            calculation_count: Number of calculations performed
            additional_state: Any additional state to store
            timestamp: When the memento was created
        """
        state = {
            "current_result": current_result,
            "last_calculation": last_calculation,
            "calculation_count": calculation_count,
            "additional_state": additional_state or {}
        }
        super().__init__(state, timestamp)
    
    def get_state(self) -> MementoData:
        """Get the stored calculator state."""
        return deepcopy(self._state)
    
    @property
    def current_result(self) -> Optional[Union[int, float]]:
        """Get the stored current result."""
        return self._state.get("current_result")
    
    @property
    def last_calculation(self) -> Optional[Dict[str, Any]]:
        """Get the stored last calculation."""
        return self._state.get("last_calculation")
    
    @property
    def calculation_count(self) -> int:
        """Get the stored calculation count."""
        return self._state.get("calculation_count", 0)
    
    def __str__(self) -> str:
        """String representation of the memento."""
        return (f"CalculatorMemento(result={self.current_result}, "
                f"count={self.calculation_count}, "
                f"timestamp={self.timestamp.strftime('%H:%M:%S')})")
    
    def __repr__(self) -> str:
        """Developer representation of the memento."""
        return (f"CalculatorMemento(id='{self.id}', "
                f"current_result={self.current_result}, "
                f"calculation_count={self.calculation_count}, "
                f"timestamp='{self.timestamp.isoformat()}')")


class Originator(ABC):
    """
    Abstract originator class for objects that can create and restore mementos.
    
    Defines the interface for objects whose state can be saved and restored
    using the memento pattern.
    """
    
    @abstractmethod
    def create_memento(self) -> Memento:
        """
        Create a memento of the current state.
        
        Returns:
            Memento: A memento containing the current state
        """
        pass
    
    @abstractmethod
    def restore_memento(self, memento: Memento) -> None:
        """
        Restore state from a memento.
        
        Args:
            memento (Memento): The memento to restore from
            
        Raises:
            MementoError: If restoration fails
        """
        pass


class Caretaker:
    """
    Caretaker manages mementos and provides undo/redo functionality.
    
    This class is responsible for managing the memento stack and providing
    undo/redo operations. It maintains separate stacks for undo and redo
    operations and ensures the history is accurately maintained.
    """
    
    def __init__(self, max_history_size: int = 100):
        """
        Initialize the caretaker.
        
        Args:
            max_history_size (int): Maximum number of mementos to keep in history
        """
        self._undo_stack: List[Memento] = []
        self._redo_stack: List[Memento] = []
        self._max_history_size = max_history_size
        self._current_memento: Optional[Memento] = None
    
    def save_memento(self, memento: Memento) -> None:
        """
        Save a memento to the undo stack.
        
        Args:
            memento (Memento): The memento to save
            
        Raises:
            MementoError: If memento is invalid
        """
        if not isinstance(memento, Memento):
            raise MementoError(
                "save",
                f"Expected Memento object, got {type(memento).__name__}"
            )
        
        # Add current memento to undo stack if it exists
        if self._current_memento is not None:
            self._undo_stack.append(self._current_memento)
            
            # Limit stack size
            if len(self._undo_stack) > self._max_history_size:
                self._undo_stack.pop(0)  # Remove oldest
        
        # Set new current memento
        self._current_memento = memento
        
        # Clear redo stack (new action invalidates redo history)
        self._redo_stack.clear()
    
    def undo(self) -> Optional[Memento]:
        """
        Perform undo operation.
        
        Returns:
            Optional[Memento]: The memento to restore to, or None if no undo available
            
        Raises:
            MementoError: If undo is not possible
        """
        if not self.can_undo():
            raise MementoError("undo", "No operations available to undo")
        
        # Move current memento to redo stack
        if self._current_memento is not None:
            self._redo_stack.append(self._current_memento)
        
        # Get memento from undo stack
        previous_memento = self._undo_stack.pop()
        self._current_memento = previous_memento
        
        return previous_memento
    
    def redo(self) -> Optional[Memento]:
        """
        Perform redo operation.
        
        Returns:
            Optional[Memento]: The memento to restore to, or None if no redo available
            
        Raises:
            MementoError: If redo is not possible
        """
        if not self.can_redo():
            raise MementoError("redo", "No operations available to redo")
        
        # Move current memento to undo stack
        if self._current_memento is not None:
            self._undo_stack.append(self._current_memento)
        
        # Get memento from redo stack
        next_memento = self._redo_stack.pop()
        self._current_memento = next_memento
        
        return next_memento
    
    def can_undo(self) -> bool:
        """
        Check if undo operation is possible.
        
        Returns:
            bool: True if undo is possible, False otherwise
        """
        return len(self._undo_stack) > 0
    
    def can_redo(self) -> bool:
        """
        Check if redo operation is possible.
        
        Returns:
            bool: True if redo is possible, False otherwise
        """
        return len(self._redo_stack) > 0
    
    def get_current_memento(self) -> Optional[Memento]:
        """
        Get the current memento without changing state.
        
        Returns:
            Optional[Memento]: The current memento
        """
        return self._current_memento
    
    def get_undo_stack_size(self) -> int:
        """Get the size of the undo stack."""
        return len(self._undo_stack)
    
    def get_redo_stack_size(self) -> int:
        """Get the size of the redo stack."""
        return len(self._redo_stack)
    
    def clear_history(self) -> None:
        """Clear all undo/redo history."""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._current_memento = None
    
    def get_history_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current history state.
        
        Returns:
            Dict[str, Any]: Summary including stack sizes and current state
        """
        return {
            "undo_available": self.can_undo(),
            "redo_available": self.can_redo(),
            "undo_stack_size": self.get_undo_stack_size(),
            "redo_stack_size": self.get_redo_stack_size(),
            "max_history_size": self._max_history_size,
            "current_memento_id": self._current_memento.id if self._current_memento else None,
            "total_mementos": len(self._undo_stack) + len(self._redo_stack) + (1 if self._current_memento else 0)
        }
    
    def get_undo_preview(self) -> Optional[str]:
        """
        Get a preview of what will be undone.
        
        Returns:
            Optional[str]: Description of the operation that will be undone
        """
        if not self.can_undo():
            return None
        
        last_memento = self._undo_stack[-1]
        if isinstance(last_memento, CalculatorMemento):
            if last_memento.last_calculation:
                calc_data = last_memento.last_calculation
                return f"Undo: {calc_data.get('expression', 'Unknown operation')}"
            else:
                return f"Undo: Calculator state from {last_memento.timestamp.strftime('%H:%M:%S')}"
        
        return f"Undo: {last_memento.__class__.__name__} from {last_memento.timestamp.strftime('%H:%M:%S')}"
    
    def get_redo_preview(self) -> Optional[str]:
        """
        Get a preview of what will be redone.
        
        Returns:
            Optional[str]: Description of the operation that will be redone
        """
        if not self.can_redo():
            return None
        
        next_memento = self._redo_stack[-1]
        if isinstance(next_memento, CalculatorMemento):
            if next_memento.last_calculation:
                calc_data = next_memento.last_calculation
                return f"Redo: {calc_data.get('expression', 'Unknown operation')}"
            else:
                return f"Redo: Calculator state from {next_memento.timestamp.strftime('%H:%M:%S')}"
        
        return f"Redo: {next_memento.__class__.__name__} from {next_memento.timestamp.strftime('%H:%M:%S')}"
    
    def export_history(self) -> str:
        """
        Export history to JSON string.
        
        Returns:
            str: JSON representation of the history
            
        Raises:
            MementoError: If export fails
        """
        try:
            export_data = {
                "undo_stack": [
                    {
                        "id": memento.id,
                        "timestamp": memento.timestamp.isoformat(),
                        "type": memento.__class__.__name__,
                        "state": memento.get_state()
                    }
                    for memento in self._undo_stack
                ],
                "redo_stack": [
                    {
                        "id": memento.id,
                        "timestamp": memento.timestamp.isoformat(),
                        "type": memento.__class__.__name__,
                        "state": memento.get_state()
                    }
                    for memento in self._redo_stack
                ],
                "current_memento": {
                    "id": self._current_memento.id,
                    "timestamp": self._current_memento.timestamp.isoformat(),
                    "type": self._current_memento.__class__.__name__,
                    "state": self._current_memento.get_state()
                } if self._current_memento else None,
                "max_history_size": self._max_history_size,
                "export_timestamp": datetime.now().isoformat()
            }
            
            return json.dumps(export_data, indent=2, default=str)
            
        except Exception as e:
            raise MementoError("export", f"Failed to export history: {str(e)}")
    
    def __str__(self) -> str:
        """String representation of the caretaker."""
        return (f"Caretaker(undo={len(self._undo_stack)}, "
                f"redo={len(self._redo_stack)}, "
                f"current={self._current_memento is not None})")
    
    def __repr__(self) -> str:
        """Developer representation of the caretaker."""
        return (f"Caretaker(undo_stack_size={len(self._undo_stack)}, "
                f"redo_stack_size={len(self._redo_stack)}, "
                f"max_history_size={self._max_history_size}, "
                f"current_memento_id='{self._current_memento.id if self._current_memento else None}')")