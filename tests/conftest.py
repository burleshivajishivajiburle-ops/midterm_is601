"""
Global test configuration and fixtures.
"""

import pytest
import tempfile
import os
from app.calculator import Calculator
from app.calculator_config import CalculatorConfig


@pytest.fixture
def fresh_calculator():
    """Create a calculator with clean history for testing."""
    # Create calculator with no auto-save and no persistent files
    config = CalculatorConfig()
    config.auto_save_enabled = False
    config.history_file_path = None
    calculator = Calculator(config=config)
    return calculator


@pytest.fixture
def calculator():
    """Default calculator fixture - creates clean calculator for each test."""
    # Create calculator with no auto-save and no persistent files
    config = CalculatorConfig()
    config.auto_save_enabled = False
    config.history_file_path = None
    calculator = Calculator(config=config)
    return calculator