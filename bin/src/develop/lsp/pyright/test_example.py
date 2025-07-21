class Calculator:
    def add(self, a: float, b: float) -> float:
        return a + b
    
    def multiply(self, a: float, b: float) -> float:
        return a * b
    
    def divide(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b


def main():
    calc = Calculator()
    
    # Test basic operations
    result1 = calc.add(10, 20)
    print(f"10 + 20 = {result1}")
    
    result2 = calc.multiply(5, 4)
    print(f"5 * 4 = {result2}")
    
    # This will trigger a type error
    calc.addd(1, 2)  # Typo: should be 'add'
    
    # This will also trigger a type error
    calc.add("string", 10)  # Type mismatch


if __name__ == "__main__":
    main()