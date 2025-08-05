#!/usr/bin/env python3
"""
Unit tests for mathematical operations
"""

import pytest
import math
from a2a_math_agent.math_agent import MathOperations


class TestMathOperations:
    """Test mathematical operations."""
    
    def test_addition(self):
        """Test addition operation."""
        assert MathOperations.add(5, 3) == 8
        assert MathOperations.add(-2, 7) == 5
        assert MathOperations.add(0, 0) == 0
        assert MathOperations.add(1.5, 2.5) == 4.0
        assert MathOperations.add(-10, -5) == -15
    
    def test_subtraction(self):
        """Test subtraction operation."""
        assert MathOperations.subtract(10, 3) == 7
        assert MathOperations.subtract(0, 5) == -5
        assert MathOperations.subtract(-3, -7) == 4
        assert MathOperations.subtract(5.5, 2.2) == pytest.approx(3.3)
        assert MathOperations.subtract(100, 50) == 50
    
    def test_multiplication(self):
        """Test multiplication operation."""
        assert MathOperations.multiply(4, 5) == 20
        assert MathOperations.multiply(-3, 7) == -21
        assert MathOperations.multiply(0, 100) == 0
        assert MathOperations.multiply(2.5, 4) == 10.0
        assert MathOperations.multiply(-6, -8) == 48
    
    def test_division(self):
        """Test division operation."""
        assert MathOperations.divide(15, 3) == 5
        assert MathOperations.divide(7, 2) == 3.5
        assert MathOperations.divide(-10, 2) == -5
        assert MathOperations.divide(9, 3) == 3
        assert MathOperations.divide(1, 4) == 0.25
    
    def test_division_by_zero(self):
        """Test division by zero raises error."""
        with pytest.raises(ValueError, match="Division by zero is not allowed"):
            MathOperations.divide(10, 0)
        
        with pytest.raises(ValueError, match="Division by zero is not allowed"):
            MathOperations.divide(-5, 0)
        
        with pytest.raises(ValueError, match="Division by zero is not allowed"):
            MathOperations.divide(0, 0)
    
    def test_square_root(self):
        """Test square root operation."""
        assert MathOperations.sqrt(16) == 4
        assert MathOperations.sqrt(0) == 0
        assert MathOperations.sqrt(1) == 1
        assert MathOperations.sqrt(25) == 5
        assert MathOperations.sqrt(2) == pytest.approx(math.sqrt(2))
        assert MathOperations.sqrt(100) == 10
    
    def test_square_root_negative(self):
        """Test square root of negative number raises error."""
        with pytest.raises(ValueError, match="Cannot calculate square root of negative number"):
            MathOperations.sqrt(-4)
        
        with pytest.raises(ValueError, match="Cannot calculate square root of negative number"):
            MathOperations.sqrt(-1)
        
        with pytest.raises(ValueError, match="Cannot calculate square root of negative number"):
            MathOperations.sqrt(-100)
    
    def test_power(self):
        """Test power operation."""
        assert MathOperations.power(2, 3) == 8
        assert MathOperations.power(5, 0) == 1
        assert MathOperations.power(9, 0.5) == 3
        assert MathOperations.power(10, 2) == 100
        assert MathOperations.power(2, -1) == 0.5
        assert MathOperations.power(-2, 3) == -8
        assert MathOperations.power(-2, 2) == 4
    
    def test_power_edge_cases(self):
        """Test power operation edge cases."""
        assert MathOperations.power(0, 5) == 0
        assert MathOperations.power(1, 1000) == 1
        assert MathOperations.power(-1, 2) == 1
        assert MathOperations.power(-1, 3) == -1
    
    def test_large_numbers(self):
        """Test operations with large numbers."""
        large_num = 1000000
        assert MathOperations.add(large_num, large_num) == 2000000
        assert MathOperations.multiply(large_num, 2) == 2000000
        assert MathOperations.divide(large_num, 1000) == 1000
        assert MathOperations.sqrt(large_num) == 1000
    
    def test_floating_point_precision(self):
        """Test floating point precision handling."""
        result = MathOperations.add(0.1, 0.2)
        assert result == pytest.approx(0.3)
        
        result = MathOperations.multiply(0.1, 0.1)
        assert result == pytest.approx(0.01)
        
        result = MathOperations.divide(1, 3)
        assert result == pytest.approx(0.3333333333333333)
    
    def test_operations_return_types(self):
        """Test that operations return expected types."""
        assert isinstance(MathOperations.add(1, 2), (int, float))
        assert isinstance(MathOperations.subtract(5, 3), (int, float))
        assert isinstance(MathOperations.multiply(2, 4), (int, float))
        assert isinstance(MathOperations.divide(8, 2), (int, float))
        assert isinstance(MathOperations.sqrt(9), (int, float))
        assert isinstance(MathOperations.power(2, 3), (int, float))