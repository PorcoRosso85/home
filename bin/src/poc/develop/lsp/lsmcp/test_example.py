#!/usr/bin/env python3
"""Test file for LSP features demonstration"""

import math
import os  # unused import
from typing import List, Optional

class Calculator:
    """Simple calculator class for testing LSP features"""
    
    def __init__(self, precision: int = 2):
        self.precision = precision
        self.history: List[str] = []
    
    def add(self, a: float, b: float) -> float:
        """Add two numbers"""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return round(result, self.precision)
    
    def divide(self, a: float, b: float) -> Optional[float]:
        """Divide with zero check"""
        if b == 0:
            return None
        result = a / b
        return round(result, self.precision)
    
    def calculate_circle_area(self, radius: float) -> float:
        """Calculate circle area"""
        area = math.pi * radius ** 2
        return round(area, self.precision)

def main():
    # Create calculator instance
    calc = Calculator(precision=3)
    
    # Test addition
    sum_result = calc.add(10.5, 20.3)
    print(f"Sum: {sum_result}")
    
    # Test division
    div_result = calc.divide(100, 3)
    if div_result:
        print(f"Division: {div_result}")
    
    # Test circle area
    area = calc.calculate_circle_area(5.0)
    print(f"Circle area: {area}")
    
    # Typo error for testing
    calc.addd(1, 2)  # This should trigger error
    
    # Type error for testing
    calc.add("10", 20)  # This should trigger type error
    
    # Unreachable code
    return
    print("This line is unreachable")

if __name__ == "__main__":
    main()