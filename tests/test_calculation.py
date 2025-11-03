"""
Unit tests for Calculation class and Builder pattern.

This module tests the Calculation class, CalculationBuilder,
serialization/deserialization, and metadata handling.
"""

import pytest
import json
from datetime import datetime
from decimal import Decimal
from app.calculation import Calculation, CalculationBuilder
from app.operations import AddOperation, DivideOperation
from app.exceptions import ValidationError, OperationError


class TestCalculation:
    """Test Calculation class functionality."""
    
    def test_calculation_creation(self):
        """Test basic calculation creation."""
        calc = Calculation("add", 5, 3)
        
        assert calc.operation_name == "add"
        assert calc.operand_a == 5
        assert calc.operand_b == 3
        assert calc.result == 8
        assert isinstance(calc.timestamp, datetime)
        assert calc.id is not None
        assert len(calc.id) > 0
        assert calc.is_successful()
    
    def test_calculation_with_division(self):
        """Test division calculation."""
        calc = Calculation("divide", 15, 3)
        assert calc.result == 5
        assert calc.is_successful()
    
    def test_calculation_division_by_zero(self):
        """Test division by zero error handling."""
        with pytest.raises(Exception):  # Will raise DivisionByZeroError
            Calculation("divide", 10, 0)
    
    def test_calculation_invalid_operation(self):
        """Test invalid operation error handling."""
        with pytest.raises(ValidationError):
            Calculation("invalid_op", 5, 3)
    
    def test_calculation_equality(self):
        """Test calculation equality comparison."""
        calc1 = Calculation("add", 5, 3)
        calc2 = Calculation("add", 5, 3)
        
        # Should be equal based on operation and operands
        assert calc1 == calc2
    
    def test_calculation_inequality(self):
        """Test calculation inequality."""
        calc1 = Calculation("add", 5, 3)
        calc2 = Calculation("add", 5, 4)  # Different operand
        calc3 = Calculation("multiply", 5, 3)  # Different operation
        
        assert calc1 != calc2
        assert calc1 != calc3
        assert calc2 != calc3
    
    def test_calculation_hash(self):
        """Test calculation hashing."""
        calc1 = Calculation("add", 5, 3)
        calc2 = Calculation("add", 5, 3)
        
        # Same operation and operands should produce same hash
        assert hash(calc1) == hash(calc2)
        
        # Can be used in sets
        calc_set = {calc1, calc2}
        assert len(calc_set) == 1
    
    def test_calculation_string_representation(self):
        """Test string representation of calculation."""
        calc = Calculation("add", 10, 5)
        
        str_repr = str(calc)
        assert "10" in str_repr
        assert "5" in str_repr
        assert "15" in str_repr  # Result
        assert "+" in str_repr
    
    def test_calculation_repr(self):
        """Test repr of calculation."""
        calc = Calculation("multiply", 7, 3)
        
        repr_str = repr(calc)
        assert "Calculation" in repr_str
        assert "multiply" in repr_str
        assert "7" in repr_str
        assert "3" in repr_str


class TestCalculationFormatting:
    """Test calculation formatting methods."""
    
    def test_get_formatted_expression(self):
        """Test formatted expression output."""
        calc = Calculation("add", 5, 3)
        expr = calc.get_formatted_expression()
        
        assert "5 + 3 = 8" == expr
    
    def test_get_formatted_expression_division(self):
        """Test formatted expression for division."""
        calc = Calculation("divide", 15, 3)
        expr = calc.get_formatted_expression()
        
        assert "15 / 3 = 5.0" == expr
    
    def test_get_formatted_expression_power(self):
        """Test formatted expression for power."""
        calc = Calculation("power", 2, 3)
        expr = calc.get_formatted_expression()
        
        assert "2 ** 3 = 8" == expr
    
    def test_get_formatted_expression_root(self):
        """Test formatted expression for root."""
        calc = Calculation("root", 27, 3)
        expr = calc.get_formatted_expression()
        
        assert "3√27 = 3.0" == expr
    
    def test_get_formatted_expression_modulus(self):
        """Test formatted expression for modulus."""
        calc = Calculation("modulus", 17, 5)
        expr = calc.get_formatted_expression()
        
        assert "17 % 5 = 2" == expr
    
    def test_get_formatted_expression_abs_diff(self):
        """Test formatted expression for absolute difference."""
        calc = Calculation("abs_diff", 10, 3)
        expr = calc.get_formatted_expression()
        
        assert "|10 - 3| = 7" == expr
    
    def test_get_formatted_result(self):
        """Test formatted result output."""
        calc = Calculation("add", 5, 3)
        result = calc.get_formatted_result()
        
        assert result == "8"
    
    def test_get_formatted_result_float(self):
        """Test formatted result with float."""
        calc = Calculation("divide", 7, 2)
        result = calc.get_formatted_result(precision=2)
        
        assert "3.5" in result
    
    def test_get_formatted_result_precision(self):
        """Test formatted result with custom precision."""
        calc = Calculation("divide", 1, 3)
        result = calc.get_formatted_result(precision=3)
        
        # Should be formatted to 3 decimal places
        assert "0.333" in result


class TestCalculationSerialization:
    """Test calculation serialization and deserialization."""
    
    def test_to_dict_basic(self):
        """Test basic to_dict conversion."""
        calc = Calculation("add", 5, 3)
        
        calc_dict = calc.to_dict()
        
        assert calc_dict["operation"] == "add"
        assert calc_dict["operand_a"] == 5
        assert calc_dict["operand_b"] == 3
        assert calc_dict["result"] == 8
        assert "timestamp" in calc_dict
        assert "id" in calc_dict
        assert "expression" in calc_dict
    
    def test_to_dict_with_float(self):
        """Test to_dict with float operands."""
        calc = Calculation("divide", 10.5, 2.5)
        
        calc_dict = calc.to_dict()
        
        assert calc_dict["operand_a"] == 10.5
        assert calc_dict["operand_b"] == 2.5
        assert calc_dict["result"] == 4.2
    
    def test_from_dict_basic(self):
        """Test basic from_dict conversion."""
        calc_dict = {
            "operation": "add",
            "operand_a": 5,
            "operand_b": 3,
            "result": 8,
            "timestamp": "2023-01-01T12:00:00",
            "id": "test-123"
        }
        
        calc = Calculation.from_dict(calc_dict)
        
        assert calc.operation_name == "add"
        assert calc.operand_a == 5
        assert calc.operand_b == 3
        assert calc.result == 8
        assert calc.id == "test-123"
        assert isinstance(calc.timestamp, datetime)
    
    def test_from_dict_missing_fields(self):
        """Test from_dict with missing required fields."""
        incomplete_dict = {
            "operation": "add",
            "operand_a": 5
            # Missing operand_b, timestamp, etc.
        }
        
        with pytest.raises(ValidationError):
            Calculation.from_dict(incomplete_dict)
    
    def test_round_trip_serialization(self):
        """Test round-trip serialization (to_dict -> from_dict)."""
        original = Calculation("multiply", 4, 6)
        
        # Convert to dict and back
        calc_dict = original.to_dict()
        restored = Calculation.from_dict(calc_dict)
        
        assert restored.operation_name == original.operation_name
        assert restored.operand_a == original.operand_a
        assert restored.operand_b == original.operand_b
        assert restored.result == original.result
    
    def test_json_serialization(self):
        """Test JSON serialization compatibility."""
        calc = Calculation("subtract", 10, 4)
        
        # Convert to dict and serialize to JSON
        calc_dict = calc.to_dict()
        json_str = json.dumps(calc_dict)
        
        # Deserialize from JSON and create calculation
        restored_dict = json.loads(json_str)
        restored_calc = Calculation.from_dict(restored_dict)
        
        assert restored_calc.operation_name == calc.operation_name
        assert restored_calc.operand_a == calc.operand_a
        assert restored_calc.operand_b == calc.operand_b
        assert restored_calc.result == calc.result


class TestCalculationBuilder:
    """Test CalculationBuilder pattern."""
    
    def test_builder_basic_usage(self):
        """Test basic builder usage."""
        calc = (CalculationBuilder()
                .operation("add")
                .operands(5, 3)
                .build())
        
        assert calc.operation_name == "add"
        assert calc.operand_a == 5
        assert calc.operand_b == 3
        assert calc.result == 8
    
    def test_builder_separate_operands(self):
        """Test builder with separate operand methods."""
        calc = (CalculationBuilder()
                .operation("multiply")
                .first_operand(4)
                .second_operand(6)
                .build())
        
        assert calc.operation_name == "multiply"
        assert calc.operand_a == 4
        assert calc.operand_b == 6
        assert calc.result == 24
    
    def test_builder_missing_operation(self):
        """Test builder with missing operation."""
        with pytest.raises(ValidationError, match="Operation name is required"):
            (CalculationBuilder()
             .operands(5, 3)
             .build())
    
    def test_builder_missing_first_operand(self):
        """Test builder with missing first operand."""
        with pytest.raises(ValidationError, match="First operand is required"):
            (CalculationBuilder()
             .operation("add")
             .second_operand(3)
             .build())
    
    def test_builder_missing_second_operand(self):
        """Test builder with missing second operand."""
        with pytest.raises(ValidationError, match="Second operand is required"):
            (CalculationBuilder()
             .operation("add")
             .first_operand(5)
             .build())
    
    def test_builder_invalid_operation(self):
        """Test builder with invalid operation."""
        with pytest.raises(ValidationError):
            (CalculationBuilder()
             .operation("invalid_op")
             .operands(5, 3)
             .build())
    
    def test_builder_invalid_operands(self):
        """Test builder with invalid operand types."""
        with pytest.raises(ValidationError):
            (CalculationBuilder()
             .operation("add")
             .operands("5", 3)  # String instead of number
             .build())
        
        with pytest.raises(ValidationError):
            (CalculationBuilder()
             .operation("add")
             .first_operand(5)
             .second_operand(None)  # None instead of number
             .build())
    
    def test_builder_method_chaining(self):
        """Test that all builder methods return self for chaining."""
        builder = CalculationBuilder()
        
        # Test all methods return the builder instance
        assert builder.operation("add") is builder
        assert builder.operands(1, 2) is builder
        assert builder.first_operand(5) is builder
        assert builder.second_operand(3) is builder


class TestCalculationCopy:
    """Test calculation copy functionality."""
    
    def test_copy_calculation(self):
        """Test copying a calculation."""
        original = Calculation("add", 5, 3)
        copy_calc = original.copy()
        
        # Should have same operation and operands but different ID
        assert copy_calc.operation_name == original.operation_name
        assert copy_calc.operand_a == original.operand_a
        assert copy_calc.operand_b == original.operand_b
        assert copy_calc.result == original.result
        assert copy_calc.id != original.id  # Different ID
        assert copy_calc.timestamp != original.timestamp  # Different timestamp


class TestCalculationEdgeCases:
    """Test calculation edge cases and special scenarios."""
    
    def test_calculation_with_zero_operands(self):
        """Test calculation with zero operands."""
        calc = Calculation("add", 0, 0)
        
        assert calc.operand_a == 0
        assert calc.operand_b == 0
        assert calc.result == 0
    
    def test_calculation_with_negative_numbers(self):
        """Test calculation with negative numbers."""
        calc = Calculation("add", -5, -3)
        
        assert calc.operand_a == -5
        assert calc.operand_b == -3
        assert calc.result == -8
    
    def test_calculation_with_large_numbers(self):
        """Test calculation with large numbers."""
        large_num = 1e12
        calc = Calculation("add", large_num, large_num)
        
        assert calc.operand_a == large_num
        assert calc.operand_b == large_num
        assert calc.result == 2 * large_num
    
    def test_calculation_with_floating_point(self):
        """Test calculation with floating point numbers."""
        calc = Calculation("divide", 1, 3)
        
        assert calc.operand_a == 1
        assert calc.operand_b == 3
        assert abs(calc.result - (1/3)) < 1e-10
    
    def test_successful_vs_failed_calculations(self):
        """Test distinguishing successful vs failed calculations."""
        success_calc = Calculation("add", 5, 3)
        assert success_calc.is_successful()
        assert success_calc.error is None
        
        # Can't easily test failed calculation since constructor raises exception

    def test_calculate_from_string_unsupported_operator_paths_via_calculator(self):
        """Indirectly exercise unsupported operator parsing with Calculator wrapper."""
        from app.calculator import Calculator
        c = Calculator()
        with pytest.raises(Exception):
            c.calculate_from_string("1 ^^^ 2")
        with pytest.raises(Exception):
            c.calculate_from_string("1 ? 2")


class TestCalculationValidation:
    """Test calculation validation and error handling."""
    
    def test_invalid_operand_types_in_constructor(self):
        """Test validation of operand types in constructor."""
        # These should be caught by the operations themselves
        with pytest.raises(Exception):  # Could be ValidationError or OperationError
            Calculation("add", "invalid", 3)
        
        with pytest.raises(Exception):
            Calculation("add", 5, "invalid")


@pytest.mark.parametrize("operation,operand1,operand2,expected", [
    ("add", 1, 2, 3),
    ("subtract", 5, 3, 2),
    ("multiply", 4, 6, 24),
    ("divide", 15, 3, 5),
    ("power", 2, 3, 8),
    ("modulus", 17, 5, 2),
])
def test_calculation_operations_parametrized(operation, operand1, operand2, expected):
    """Test calculation with various operations using parametrized inputs."""
    calc = Calculation(operation, operand1, operand2)
    
    assert calc.operation_name == operation
    assert calc.operand_a == operand1
    assert calc.operand_b == operand2
    assert calc.result == expected
    assert calc.is_successful()


class TestCalculationIntegration:
    """Test calculation integration with other components."""
    
    def test_calculation_with_all_operations(self):
        """Test calculation works with all available operations."""
        from app.operations import OperationFactory
        
        available_ops = OperationFactory.get_available_operations()
        
        # Test a few key operations (avoiding division by zero)
        test_cases = {
            "add": (5, 3),
            "multiply": (4, 6),
            "subtract": (10, 4),
            "power": (2, 3)
        }
        
        for op_name in test_cases:
            if op_name in available_ops:
                operand_a, operand_b = test_cases[op_name]
                calc = Calculation(op_name, operand_a, operand_b)
                assert calc.is_successful()
                assert calc.result is not None
    
    def test_calculation_metadata_consistency(self):
        """Test that calculation metadata is consistent."""
        calc = Calculation("add", 10, 20)
        
        # Check that to_dict contains all expected fields
        calc_dict = calc.to_dict()
        expected_fields = ["id", "timestamp", "operation", "operand_a", "operand_b", "result", "expression"]
        
        for field in expected_fields:
            assert field in calc_dict
        
        # Check that from_dict can recreate the calculation
        restored = Calculation.from_dict(calc_dict)
        assert restored.operation_name == calc.operation_name
        assert restored.operand_a == calc.operand_a
        assert restored.operand_b == calc.operand_b


if __name__ == "__main__":
    pytest.main([__file__])