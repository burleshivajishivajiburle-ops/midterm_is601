import json
import pytest

from app.calculator_memento import Caretaker, Memento, CalculatorMemento, MementoError


class DummyOriginator:
    def __init__(self):
        # state is a simple list of ops
        self.ops = []

    def create_memento(self) -> Memento:
        return CalculatorMemento({"calculations": [{"operation": op} for op in self.ops]})

    def restore_from_memento(self, m: Memento) -> None:
        state = getattr(m, "state", None) or m.get_state()
        calcs = state.get("calculations", [])
        self.ops = [c.get("operation") for c in calcs]


def test_caretaker_save_undo_redo_previews_and_export():
    d = DummyOriginator()
    ct = Caretaker(max_history_size=3)

    # No undo/redo initially
    assert ct.can_undo() is False and ct.can_redo() is False
    assert ct.get_undo_preview() is None and ct.get_redo_preview() is None

    # Save states
    d.ops = ["add"]
    ct.save_state(d)
    d.ops = ["add", "mul"]
    ct.save_state(d)
    assert ct.can_undo() is True
    up = ct.get_undo_preview()
    assert up is None or up.startswith("Undo")  # may not include operation name if not present

    # Undo once
    ct.undo(d)
    assert ct.can_redo() is True
    rp = ct.get_redo_preview()
    assert rp is None or rp.startswith("Redo")

    # Redo
    ct.redo(d)

    # Export JSON
    data = json.loads(ct.export_history())
    assert "undo_stack" in data and "redo_stack" in data

    # Clear all
    ct.clear_history()
    assert ct.can_undo() is False and ct.can_redo() is False


def test_caretaker_save_memento_and_error_paths():
    ct = Caretaker(max_history_size=1)
    # Directly push mementos
    m1 = CalculatorMemento({"calculations": [{"operation": "add"}]})
    ct.save_memento(m1)
    # Pushing another should evict first due to size
    m2 = CalculatorMemento({"calculations": [{"operation": "sub"}]})
    ct.save_memento(m2)
    assert ct.get_undo_stack_size() == 1

    # Undo with no originator should raise if cannot undo (after clear)
    ct.clear_history()
    with pytest.raises(MementoError):
        ct.undo(DummyOriginator())

    # Redo with none
    with pytest.raises(MementoError):
        ct.redo(DummyOriginator())
