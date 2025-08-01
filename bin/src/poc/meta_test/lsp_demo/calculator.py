"""Calculator module for LSP demo."""
from typing import Union, List
from .operations import add_numbers, multiply_numbers
from .validators import validate_input


class Calculator:
    """Simple calculator to demonstrate LSP features."""
    
    def __init__(self, name: str = "BasicCalculator"):
        self.name = name
        self.history: List[str] = []
    
    def calculate(self, operation: str, a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """Perform calculation based on operation."""
        if not validate_input(a, b):
            raise ValueError("Invalid input")
        
        result: Union[int, float]
        if operation == "add":
            result = add_numbers(a, b)
        elif operation == "multiply":
            result = multiply_numbers(a, b)
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        self.history.append(f"{a} {operation} {b} = {result}")
        return result
    
    def get_history(self) -> List[str]:
        """Get calculation history."""
        return self.history.copy()