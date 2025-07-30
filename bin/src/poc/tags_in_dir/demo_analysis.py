#!/usr/bin/env python3
"""
Demo script showing the full workflow of code analysis with tags_in_dir.

This script demonstrates:
1. Extracting symbols using ctags
2. Detecting call relationships
3. Storing data in KuzuDB
4. Running various analysis queries
"""

import sys
import os
from pathlib import Path
from typing import Optional

from tags_in_dir import CtagsParser
from kuzu_storage import KuzuStorage
from call_detector import CallDetector
from analysis_queries import CodeAnalyzer


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print(f"{'=' * 60}")


def demo_workflow(directory: str, db_path: Optional[str] = None):
    """
    Demonstrate the complete code analysis workflow.
    
    Args:
        directory: Directory to analyze
        db_path: Optional path for persistent database
    """
    # Use in-memory database if no path provided
    if db_path is None:
        db_path = ":memory:"
        print("Using in-memory database")
    else:
        print(f"Using persistent database: {db_path}")
    
    # Step 1: Extract symbols using ctags
    print_section("Step 1: Extracting Symbols with ctags")
    
    parser = CtagsParser()
    symbols = parser.extract_symbols(directory, extensions=[".py"])
    
    print(f"Found {len(symbols)} symbols")
    if symbols:
        print("\nFirst 5 symbols:")
        for i, symbol in enumerate(symbols[:5]):
            print(f"  {i+1}. {symbol.name} ({symbol.kind}) at {symbol.location_uri}")
    
    # Step 2: Initialize storage and store symbols
    print_section("Step 2: Storing Symbols in KuzuDB")
    
    storage = KuzuStorage(db_path)
    stored_count = storage.store_symbols(symbols)
    print(f"Stored {stored_count} symbols in KuzuDB")
    
    # Get statistics
    stats = storage.get_statistics()
    print(f"\nDatabase statistics:")
    print(f"  Total symbols: {stats['total_symbols']}")
    print(f"  Symbol types: {stats['symbols_by_kind']}")
    
    # Step 3: Detect call relationships
    print_section("Step 3: Detecting Call Relationships")
    
    # Convert symbols to dict format for call detector
    symbol_dicts = []
    for symbol in symbols:
        symbol_dicts.append({
            "name": symbol.name,
            "kind": symbol.kind,
            "location_uri": symbol.location_uri,
            "scope": symbol.scope,
            "signature": symbol.signature
        })
    
    detector = CallDetector(symbol_dicts)
    relationships = detector.detect_all_calls(directory, extensions=[".py"])
    
    print(f"Detected {len(relationships)} potential call relationships")
    
    # Resolve and store relationships
    resolved_calls = detector.resolve_call_targets(relationships)
    print(f"Resolved {len(resolved_calls)} call relationships")
    
    stored_rels = 0
    for from_uri, to_uri, line_no in resolved_calls:
        if storage.create_calls_relationship(from_uri, to_uri, line_no):
            stored_rels += 1
    
    print(f"Stored {stored_rels} call relationships in KuzuDB")
    
    # Step 4: Run analysis queries
    print_section("Step 4: Running Analysis Queries")
    
    analyzer = CodeAnalyzer(storage)
    
    # 4.1: Find all functions in a specific file
    print("\n4.1 Functions in current directory files:")
    py_files = list(Path(directory).glob("*.py"))
    if py_files:
        first_file = str(py_files[0])
        functions = analyzer.find_all_functions_in_file(first_file)
        print(f"\nFunctions in {os.path.basename(first_file)}:")
        for func in functions[:5]:  # Show first 5
            print(f"  - {func['function_name']} at line {func['location'].split('#L')[-1]}")
    
    # 4.2: Find most called functions
    print("\n4.2 Most Called Functions:")
    most_called = analyzer.find_most_called_functions(limit=5)
    if most_called:
        for func in most_called:
            print(f"  - {func['function_name']}: {func['call_count']} calls")
    else:
        print("  No function calls detected yet")
    
    # 4.3: Find potential dead code
    print("\n4.3 Potential Dead Code (uncalled functions):")
    dead_code = analyzer.find_dead_code()
    if dead_code:
        for func in dead_code[:5]:  # Show first 5
            print(f"  - {func['function_name']} in {os.path.basename(func['location'].split('#')[0])}")
    else:
        print("  No dead code detected")
    
    # 4.4: Find circular dependencies
    print("\n4.4 Circular Dependencies:")
    cycles = analyzer.find_circular_dependencies()
    if cycles:
        for cycle in cycles:
            print(f"  - Cycle of length {cycle['cycle_length']}: {' -> '.join(cycle['functions'])} -> {cycle['functions'][0]}")
    else:
        print("  No circular dependencies detected")
    
    # 4.5: Find entry points
    print("\n4.5 Entry Points:")
    entry_points = analyzer.find_entry_points()
    if entry_points:
        for entry in entry_points[:5]:  # Show first 5
            print(f"  - {entry['function_name']} ({entry['entry_type']})")
    
    # 4.6: Get complexity metrics
    print("\n4.6 Complexity Metrics:")
    metrics = analyzer.get_complexity_metrics()
    print(f"  - Total symbols: {metrics['total_symbols']}")
    print(f"  - Total relationships: {metrics['total_relationships']}")
    print(f"  - Average outgoing calls per function: {metrics['average_outgoing_calls_per_function']}")
    
    if metrics['functions_with_highest_coupling']:
        print("\n  Functions with highest coupling:")
        for func in metrics['functions_with_highest_coupling'][:3]:
            print(f"    - {func['function']}: {func['outgoing_calls']} outgoing calls")
    
    # Step 5: Custom Cypher queries
    print_section("Step 5: Custom Cypher Queries")
    
    # Example: Find all test functions
    print("\n5.1 Test Functions:")
    test_functions = storage.execute_cypher("""
        MATCH (s:Symbol)
        WHERE s.kind = 'function' AND s.name STARTS WITH 'test_'
        RETURN s.name, s.location_uri
        ORDER BY s.name
        LIMIT 5
    """)
    
    if test_functions:
        for name, location in test_functions:
            print(f"  - {name}")
    else:
        print("  No test functions found")
    
    # Example: Find classes with most methods
    print("\n5.2 Classes with Most Methods:")
    class_methods = storage.execute_cypher("""
        MATCH (s:Symbol)
        WHERE s.kind = 'method' AND s.scope IS NOT NULL AND s.scope != ''
        WITH s.scope AS class_name, COUNT(s) AS method_count
        RETURN class_name, method_count
        ORDER BY method_count DESC
        LIMIT 5
    """)
    
    if class_methods:
        for class_name, method_count in class_methods:
            print(f"  - {class_name}: {method_count} methods")
    else:
        print("  No classes with methods found")
    
    print_section("Analysis Complete!")
    
    # Close storage
    storage.close()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python demo_analysis.py <directory> [database_path]")
        print("\nExample:")
        print("  python demo_analysis.py . ")
        print("  python demo_analysis.py /path/to/project /tmp/analysis.kuzu")
        sys.exit(1)
    
    directory = sys.argv[1]
    db_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a valid directory")
        sys.exit(1)
    
    try:
        demo_workflow(directory, db_path)
    except Exception as e:
        print(f"\nError during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()