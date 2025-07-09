#!/usr/bin/env python3
"""Test file with dead code and unused variables."""

import os  # Unused import
import sys
from typing import List, Optional


def unused_function():
    """This function is never called."""
    return "I'm never used"


def another_unused():
    """Another dead function."""
    x = 10
    y = 20
    return x + y


class UnusedClass:
    """This class is never instantiated."""
    
    def method(self):
        return "Never called"


def main():
    # Unused variables
    unused_var = 42
    another_unused_var = "hello"
    
    # Variable that's assigned but never read
    result = 10 + 20
    
    # Unreachable code
    if True:
        print("This runs")
        return
    
    print("This is dead code - unreachable")
    dead_var = "never reached"


def partially_used(x, y, z):
    """Function where not all parameters are used."""
    return x + y  # z is unused


if __name__ == "__main__":
    main()
    # partially_used is defined but never called