class Calculator:
    def __init__(self):
        self.result = 0
    
    def add(self, a: float, b: float) -> float:
        return a + b
    
calc = Calculator()
result = calc.add(10, 20)
print(f"Result: {result}")