#!/usr/bin/env python3
"""
Test script for verifying analysis functionality.
"""

import tempfile
import os
from pathlib import Path

from tags_in_dir import CtagsParser
from kuzu_storage import KuzuStorage
from call_detector import CallDetector
from analysis_queries import CodeAnalyzer


def create_test_files(test_dir: Path):
    """Create test Python files with known relationships."""
    
    # File 1: Main module
    main_py = test_dir / "main.py"
    main_py.write_text("""
def main():
    '''Entry point'''
    result = process_data([1, 2, 3])
    display_result(result)
    
def process_data(data):
    '''Process input data'''
    validated = validate_input(data)
    return transform_data(validated)

def validate_input(data):
    '''Validate input data'''
    if not data:
        raise ValueError("Empty data")
    return data

def transform_data(data):
    '''Transform the data'''
    return [x * 2 for x in data]

def display_result(result):
    '''Display the result'''
    print(f"Result: {result}")
    
def unused_function():
    '''This function is never called'''
    pass
""")
    
    # File 2: Test module
    test_py = test_dir / "test_main.py"
    test_py.write_text("""
def test_validate_input():
    '''Test validation function'''
    from main import validate_input
    assert validate_input([1, 2, 3]) == [1, 2, 3]

def test_transform_data():
    '''Test transformation function'''
    from main import transform_data
    assert transform_data([1, 2, 3]) == [2, 4, 6]
""")
    
    # File 3: Circular dependency example
    circular_py = test_dir / "circular.py"
    circular_py.write_text("""
def func_a():
    '''Function A calls function B'''
    return func_b()

def func_b():
    '''Function B calls function A (circular)'''
    return func_a()
    
def func_c():
    '''Function C is part of a 3-way cycle'''
    return func_d()
    
def func_d():
    '''Function D continues the cycle'''
    return func_e()
    
def func_e():
    '''Function E completes the cycle back to C'''
    return func_c()
""")


def run_analysis_test():
    """Run the analysis on test files."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir)
        
        # Create test files
        print("Creating test files...")
        create_test_files(test_dir)
        
        # Extract symbols
        print("\nExtracting symbols with ctags...")
        parser = CtagsParser()
        symbols = parser.extract_symbols(str(test_dir), extensions=[".py"])
        print(f"Found {len(symbols)} symbols")
        
        # Initialize storage
        print("\nInitializing KuzuDB...")
        storage = KuzuStorage(":memory:")
        stored = storage.store_symbols(symbols)
        print(f"Stored {stored} symbols")
        
        # Detect relationships
        print("\nDetecting call relationships...")
        symbol_dicts = [
            {
                "name": s.name,
                "kind": s.kind,
                "location_uri": s.location_uri,
                "scope": s.scope,
                "signature": s.signature
            }
            for s in symbols
        ]
        
        detector = CallDetector(symbol_dicts)
        relationships = detector.detect_all_calls(str(test_dir), extensions=[".py"])
        print(f"Detected {len(relationships)} potential relationships")
        
        resolved = detector.resolve_call_targets(relationships)
        print(f"Resolved {len(resolved)} relationships")
        
        # Store relationships
        for from_uri, to_uri, line_no in resolved:
            storage.create_calls_relationship(from_uri, to_uri, line_no)
        
        # Run analysis queries
        print("\nRunning analysis queries...")
        analyzer = CodeAnalyzer(storage)
        
        # Test 1: Find all functions in main.py
        print("\n1. Functions in main.py:")
        functions = analyzer.find_all_functions_in_file(str(test_dir / "main.py"))
        for func in functions:
            print(f"   - {func['function_name']}")
        
        # Test 2: Find most called functions
        print("\n2. Most called functions:")
        most_called = analyzer.find_most_called_functions(limit=5)
        for func in most_called:
            print(f"   - {func['function_name']}: {func['call_count']} calls")
        
        # Test 3: Find dead code
        print("\n3. Dead code (uncalled functions):")
        dead_code = analyzer.find_dead_code()
        for func in dead_code:
            print(f"   - {func['function_name']}")
        
        # Test 4: Find circular dependencies
        print("\n4. Circular dependencies:")
        cycles = analyzer.find_circular_dependencies()
        for cycle in cycles:
            funcs = " -> ".join(cycle['functions'])
            print(f"   - Cycle of length {cycle['cycle_length']}: {funcs}")
        
        # Test 5: Get entry points
        print("\n5. Entry points:")
        entry_points = analyzer.find_entry_points()
        for entry in entry_points:
            print(f"   - {entry['function_name']} ({entry['entry_type']})")
        
        # Test 6: Get complexity metrics
        print("\n6. Complexity metrics:")
        metrics = analyzer.get_complexity_metrics()
        print(f"   - Total symbols: {metrics['total_symbols']}")
        print(f"   - Total relationships: {metrics['total_relationships']}")
        print(f"   - Average calls per function: {metrics['average_outgoing_calls_per_function']}")
        
        print("\nAnalysis test completed successfully!")


if __name__ == "__main__":
    run_analysis_test()