"""Main entry point for LSP demo."""
from .calculator import Calculator
from .validators import validate_positive


def main():
    """Run calculator demo."""
    calc = Calculator("DemoCalculator")
    
    # Example calculations
    result1 = calc.calculate("add", 10, 20)
    print(f"Result 1: {result1}")
    
    result2 = calc.calculate("multiply", 5, 7)
    print(f"Result 2: {result2}")
    
    # Show history
    history = calc.get_history()
    print("\nCalculation History:")
    for entry in history:
        print(f"  - {entry}")
    
    # Validate positive example
    if validate_positive(result1):
        print(f"\n{result1} is positive!")


if __name__ == "__main__":
    main()