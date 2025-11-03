"""
Unit tests for operations classes and Factory pattern.

This module contains comprehensive tests for all arithmetic operations,
the Factory pattern implementation, error handling, and edge cases.
"""

import pytest
import math
from app.operations import (
    Operation, OperationFactory,
    AddOperation, SubtractOperation, MultiplyOperation, DivideOperation,
    PowerOperation, RootOperation, ModulusOperation, IntegerDivisionOperation,
    PercentageOperation, AbsoluteDifferenceOperation
)
from app.exceptions import (
    OperationError, DivisionByZeroError, InvalidRootError, 
    OverflowError, ValidationError
)


class TestBasicOperations:
    """Test basic arithmetic operations."""
    
    def test_add_operation(self):
        """Test addition operation."""
        add_op = AddOperation()
        assert add_op.execute(5, 3) == 8
        assert add_op.execute(-2, 7) == 5
        assert add_op.execute(0, 0) == 0
        assert add_op.execute(1.5, 2.5) == 4.0
        assert add_op.name == "add"
        assert str(add_op) == "add"
    
    def test_subtract_operation(self):
        """Test subtraction operation."""
        sub_op = SubtractOperation()
        assert sub_op.execute(10, 3) == 7
        assert sub_op.execute(-5, -2) == -3
        assert sub_op.execute(0, 5) == -5
        assert sub_op.execute(7.5, 2.5) == 5.0
    
    def test_multiply_operation(self):
        """Test multiplication operation."""
        mul_op = MultiplyOperation()
        assert mul_op.execute(4, 3) == 12
        assert mul_op.execute(-2, 5) == -10
        assert mul_op.execute(0, 100) == 0
        assert mul_op.execute(2.5, 4) == 10.0
    
    def test_divide_operation(self):
        """Test division operation."""
        div_op = DivideOperation()
        assert div_op.execute(15, 3) == 5
        assert div_op.execute(10, 4) == 2.5
        assert div_op.execute(-12, 3) == -4
        assert div_op.execute(0, 5) == 0
    
    def test_divide_by_zero(self):
        """Test division by zero error."""
        div_op = DivideOperation()
        with pytest.raises(DivisionByZeroError):
            div_op.execute(10, 0)
        
        with pytest.raises(DivisionByZeroError):
            div_op.execute(-5, 0)


class TestAdvancedOperations:
    """Test advanced arithmetic operations."""
    
    def test_power_operation(self):
        """Test power operation."""
        pow_op = PowerOperation()
        assert pow_op.execute(2, 3) == 8
        assert pow_op.execute(5, 0) == 1
        assert pow_op.execute(3, 2) == 9
        assert pow_op.execute(2, -2) == 0.25
        assert pow_op.execute(4, 0.5) == 2.0
    
    def test_power_edge_cases(self):
        """Test power operation edge cases."""
        pow_op = PowerOperation()
        
        # Test 0^negative (should raise error)
        with pytest.raises(OperationError):
            pow_op.execute(0, -1)
        
        # Test valid cases
        assert pow_op.execute(1, 100) == 1
        assert pow_op.execute(-2, 3) == -8
        assert pow_op.execute(-2, 2) == 4
    
    def test_root_operation(self):
        """Test root operation."""
        root_op = RootOperation()
        assert root_op.execute(9, 2) == 3.0  # Square root
        assert root_op.execute(27, 3) == 3.0  # Cube root
        assert root_op.execute(16, 4) == 2.0  # Fourth root
        assert root_op.execute(1, 5) == 1.0
    
    def test_root_edge_cases(self):
        """Test root operation edge cases."""
        root_op = RootOperation()
        
        # Test zero root index
        with pytest.raises(InvalidRootError):
            root_op.execute(8, 0)
        
        # Test even root of negative number
        with pytest.raises(InvalidRootError):
            root_op.execute(-4, 2)
        
        # Test odd root of negative number (should work)
        result = root_op.execute(-8, 3)
        assert abs(result - (-2.0)) < 1e-10
    
    def test_modulus_operation(self):
        """Test modulus operation."""
        mod_op = ModulusOperation()
        assert mod_op.execute(10, 3) == 1
        assert mod_op.execute(15, 5) == 0
        assert mod_op.execute(7, 4) == 3
        assert mod_op.execute(-10, 3) == 2  # Python modulus behavior
    
    def test_modulus_by_zero(self):
        """Test modulus by zero error."""
        mod_op = ModulusOperation()
        with pytest.raises(DivisionByZeroError):
            mod_op.execute(10, 0)
    
    def test_integer_division_operation(self):
        """Test integer division operation."""
        int_div_op = IntegerDivisionOperation()
        assert int_div_op.execute(15, 3) == 5
        assert int_div_op.execute(17, 5) == 3
        assert int_div_op.execute(-10, 3) == -4  # Python floor division
        assert int_div_op.execute(20, 6) == 3
    
    def test_integer_division_by_zero(self):
        """Test integer division by zero error."""
        int_div_op = IntegerDivisionOperation()
        with pytest.raises(DivisionByZeroError):
            int_div_op.execute(10, 0)


class TestSpecialOperations:
    """Test special operations (percentage, absolute difference)."""
    
    def test_percentage_operation(self):
        """Test percentage operation."""
        pct_op = PercentageOperation()
        assert pct_op.execute(25, 100) == 25.0
        assert pct_op.execute(50, 200) == 25.0
        assert pct_op.execute(3, 4) == 75.0
        assert pct_op.execute(1, 8) == 12.5
    
    def test_percentage_by_zero(self):
        """Test percentage with zero total."""
        pct_op = PercentageOperation()
        with pytest.raises(DivisionByZeroError):
            pct_op.execute(50, 0)
    
    def test_absolute_difference_operation(self):
        """Test absolute difference operation."""
        abs_diff_op = AbsoluteDifferenceOperation()
        assert abs_diff_op.execute(10, 3) == 7
        assert abs_diff_op.execute(3, 10) == 7
        assert abs_diff_op.execute(-5, 2) == 7
        assert abs_diff_op.execute(-3, -8) == 5
        assert abs_diff_op.execute(5, 5) == 0


class TestOperationFactory:
    """Test the Operation Factory pattern implementation."""
    
    def test_create_valid_operations(self):
        """Test creating all valid operations."""
        operations = [
            "add", "subtract", "multiply", "divide", "power",
            "root", "modulus", "int_divide", "percent", "abs_diff"
        ]
        
        for op_name in operations:
            operation = OperationFactory.create_operation(op_name)
            assert isinstance(operation, Operation)
            assert operation.name == op_name
    
    def test_create_operation_case_insensitive(self):
        """Test factory is case insensitive."""
        assert isinstance(OperationFactory.create_operation("ADD"), AddOperation)
        assert isinstance(OperationFactory.create_operation("Multiply"), MultiplyOperation)
        assert isinstance(OperationFactory.create_operation("DIVIDE"), DivideOperation)
    
    def test_create_operation_with_whitespace(self):
        """Test factory handles whitespace."""
        assert isinstance(OperationFactory.create_operation("  add  "), AddOperation)
        assert isinstance(OperationFactory.create_operation("\tsubtract\n"), SubtractOperation)
    
    def test_create_invalid_operation(self):
        """Test creating invalid operation raises error."""
        with pytest.raises(ValidationError) as exc_info:
            OperationFactory.create_operation("invalid_op")
        
        assert "Unsupported operation" in str(exc_info.value)
        assert "Available operations:" in str(exc_info.value)
    
    def test_get_available_operations(self):
        """Test getting list of available operations."""
        operations = OperationFactory.get_available_operations()
        expected = [
            "add", "subtract", "multiply", "divide", "power",
            "root", "modulus", "int_divide", "percent", "abs_diff"
        ]
        
        assert len(operations) == len(expected)
        for op in expected:
            assert op in operations
    
    def test_register_custom_operation(self):
        """Test registering a custom operation."""
        class CustomOperation(Operation):
            def __init__(self):
                super().__init__("custom")
            
            def execute(self, a, b):
                return a + b + 1
        
        # Register the custom operation
        OperationFactory.register_operation("custom", CustomOperation)
        
        # Test it can be created
        custom_op = OperationFactory.create_operation("custom")
        assert isinstance(custom_op, CustomOperation)
        assert custom_op.execute(2, 3) == 6
        
        # Test it appears in available operations
        assert "custom" in OperationFactory.get_available_operations()
    
    def test_register_invalid_operation_class(self):
        """Test registering invalid operation class."""
        class InvalidClass:
            pass
        
        with pytest.raises(ValidationError):
            OperationFactory.register_operation("invalid", InvalidClass)


class TestOperationErrorHandling:
    """Test error handling in operations."""
    
    def test_invalid_operand_types(self):
        """Test operations with invalid operand types."""
        add_op = AddOperation()
        
        with pytest.raises(OperationError):
            add_op.execute("invalid", 5)
        
        with pytest.raises(OperationError):
            add_op.execute(5, None)
    
    def test_overflow_conditions(self):
        """Test overflow handling."""
        add_op = AddOperation()
        mul_op = MultiplyOperation()
        div_op = DivideOperation()
        
        # Test very large numbers that might cause overflow
        large_num = 1e308
        
        with pytest.raises(OverflowError):
            add_op.execute(large_num, large_num)
        
        with pytest.raises(OverflowError):
            mul_op.execute(large_num, 2)

        sub_op = SubtractOperation()
        with pytest.raises(OverflowError):
            sub_op.execute(large_num, -large_num)

        with pytest.raises(OverflowError):
            div_op.execute(1e308, 1e-308)
    
    def test_power_overflow(self):
        """Test power operation overflow."""
        pow_op = PowerOperation()
        
        with pytest.raises(OverflowError):
            pow_op.execute(10, 1000)

        with pytest.raises(OverflowError):
            pow_op.execute(1e200, 2)

        with pytest.raises(OverflowError):
            pow_op.execute(-1, 0.5)
    
    def test_root_invalid_cases(self):
        """Test root operation invalid cases."""
        root_op = RootOperation()
        
        # Fractional root of negative number
        with pytest.raises(InvalidRootError):
            root_op.execute(-4, 2.5)

        with pytest.raises(InvalidRootError):
            root_op.execute(1e308, 0.0001)

        with pytest.raises(InvalidRootError):
            root_op.execute(float("inf"), 2)

    def test_invalid_types_for_various_operations(self):
        """Exercise OperationError paths for invalid operand types."""
        pct = PercentageOperation()
        absd = AbsoluteDifferenceOperation()
        intdiv = IntegerDivisionOperation()
        sub = SubtractOperation()
        div = DivideOperation()
        mod = ModulusOperation()
        pow_op = PowerOperation()
        mul = MultiplyOperation()

        with pytest.raises(OperationError):
            pct.execute("x", 100)
        with pytest.raises(OperationError):
            pct.execute(10, "y")

        with pytest.raises(OperationError):
            absd.execute("a", 1)

        with pytest.raises(OperationError):
            intdiv.execute("a", 2)
        with pytest.raises(OperationError):
            intdiv.execute(10, "b")

        with pytest.raises(OperationError):
            sub.execute("a", 1)
        with pytest.raises(OperationError):
            div.execute("a", 2)
        with pytest.raises(OperationError):
            mod.execute("a", 2)
        with pytest.raises(OperationError):
            pow_op.execute("a", 2)
        with pytest.raises(OperationError):
            mul.execute("a", 2)

    def test_percentage_overflow(self):
        pct = PercentageOperation()
        with pytest.raises(OverflowError):
            pct.execute(1e308, 1e-4)  # results in 1e312 -> overflow


class TestOperationIntegration:
    """Test operations in integrated scenarios."""
    
    @pytest.mark.parametrize("operation,a,b,expected", [
        ("add", 5, 3, 8),
        ("subtract", 10, 4, 6),
        ("multiply", 3, 7, 21),
        ("divide", 15, 3, 5),
        ("power", 2, 4, 16),
        ("modulus", 17, 5, 2),
        ("int_divide", 17, 5, 3),
        ("percent", 25, 100, 25),
        ("abs_diff", 3, 10, 7),
    ])
    def test_operation_execution(self, operation, a, b, expected):
        """Test operation execution with parameterized inputs."""
        op = OperationFactory.create_operation(operation)
        result = op.execute(a, b)
        assert result == expected
    
    @pytest.mark.parametrize("operation,a,b", [
        ("divide", 10, 0),
        ("modulus", 10, 0),
        ("int_divide", 10, 0),
        ("percent", 10, 0),
    ])
    def test_division_by_zero_operations(self, operation, a, b):
        """Test all operations that should raise division by zero."""
        op = OperationFactory.create_operation(operation)
        with pytest.raises(DivisionByZeroError):
            op.execute(a, b)
    
    def test_chained_operations(self):
        """Test using operations in sequence."""
        # ((5 + 3) * 2) ** 2 = 256
        add_op = OperationFactory.create_operation("add")
        mul_op = OperationFactory.create_operation("multiply")
        pow_op = OperationFactory.create_operation("power")
        
        result1 = add_op.execute(5, 3)  # 8
        result2 = mul_op.execute(result1, 2)  # 16
        result3 = pow_op.execute(result2, 2)  # 256
        
        assert result3 == 256
    
    def test_floating_point_precision(self):
        """Test floating point precision in operations."""
        div_op = OperationFactory.create_operation("divide")
        
        # Test division that results in repeating decimal
        result = div_op.execute(1, 3)
        assert abs(result - 0.3333333333333333) < 1e-15
        
        # Test operations with very small numbers
        result = div_op.execute(1e-10, 1e-5)
        assert abs(result - 1e-5) < 1e-20


@pytest.mark.slow
class TestOperationPerformance:
    """Test operation performance characteristics."""
    
    def test_large_number_operations(self):
        """Test operations with large numbers."""
        add_op = OperationFactory.create_operation("add")
        
        large_a = 1e12
        large_b = 2e12
        result = add_op.execute(large_a, large_b)
        assert result == 3e12
    
    def test_high_precision_operations(self):
        """Test operations requiring high precision."""
        root_op = OperationFactory.create_operation("root")
        
        # Test high precision root calculation
        result = root_op.execute(1000000, 6)
        expected = 10.0  # 6th root of 1,000,000 is 10
        assert abs(result - expected) < 1e-10


class TestOperationDocumentation:
    """Test that operations are properly documented."""
    
    def test_operation_names(self):
        """Test that all operations have proper names."""
        operations = OperationFactory.get_available_operations()
        
        for op_name in operations:
            operation = OperationFactory.create_operation(op_name)
            assert operation.name == op_name
            assert isinstance(operation.name, str)
            assert len(operation.name) > 0
    
    def test_operation_string_representation(self):
        """Test string representation of operations."""
        for op_name in OperationFactory.get_available_operations():
            operation = OperationFactory.create_operation(op_name)
            assert str(operation) == op_name
            assert repr(operation)  # Should not be empty


if __name__ == "__main__":
    pytest.main([__file__])