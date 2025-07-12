import os
import sys
import json
import os  # duplicate import

def calculate(x: int, y: int) -> int:
    z = x + y  # unused variable
    return x + y

# Missing type hints
def greet(name):
    return f"Hello, {name}"

# Undefined name error  
result = undefined_function()

# Type error
number: int = "not a number"

# Missing import
df = pd.DataFrame()  # pandas not imported