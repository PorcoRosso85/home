#!/usr/bin/env python3
"""
Example demonstrating the integration of tags_in_dir with KuzuDB storage.
"""

from tags_in_dir import CtagsParser
from kuzu_storage import KuzuStorage


def main():
    """Example usage of tags_in_dir with KuzuDB storage."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python example_integration.py <directory>")
        print("\nExample: python example_integration.py .")
        sys.exit(1)
    
    directory = sys.argv[1]
    
    # Initialize ctags parser
    parser = CtagsParser()
    
    # Initialize KuzuDB storage (in-memory for demo)
    storage = KuzuStorage(":memory:")
    
    print(f"Analyzing directory: {directory}")
    
    # Extract symbols
    symbols = parser.extract_symbols(directory, extensions=[".py"])
    print(f"\nFound {len(symbols)} symbols")
    
    # Store symbols in KuzuDB
    stored = storage.store_symbols(symbols)
    print(f"Stored {stored} symbols in KuzuDB")
    
    # Get statistics
    stats = storage.get_statistics()
    print(f"\nDatabase statistics:")
    print(f"  Total symbols: {stats['total_symbols']}")
    print(f"  Symbols by kind:")
    for kind, count in stats['symbols_by_kind'].items():
        print(f"    {kind}: {count}")
    
    # Example queries
    print("\n--- Example Queries ---")
    
    # 1. Find all functions
    functions = storage.find_symbols_by_kind("function")
    print(f"\nFunctions ({len(functions)}):")
    for func in functions[:5]:
        print(f"  - {func['name']} at {func['location_uri']}")
    if len(functions) > 5:
        print(f"  ... and {len(functions) - 5} more")
    
    # 2. Find all classes
    classes = storage.find_symbols_by_kind("class")
    print(f"\nClasses ({len(classes)}):")
    for cls in classes[:5]:
        print(f"  - {cls['name']} at {cls['location_uri']}")
    if len(classes) > 5:
        print(f"  ... and {len(classes) - 5} more")
    
    # 3. Example Cypher query
    print("\n--- Custom Cypher Query ---")
    print("Finding all symbols with 'test' in their name:")
    
    results = storage.execute_cypher("""
        MATCH (s:Symbol)
        WHERE s.name CONTAINS 'test'
        RETURN s.name, s.kind, s.location_uri
        ORDER BY s.name
        LIMIT 10
    """)
    
    for name, kind, uri in results:
        print(f"  - {name} ({kind}) at {uri}")
    
    # 4. Find symbols in a specific file (if there are any files)
    if symbols:
        # Get the first file
        first_file = symbols[0].location_uri.split("#")[0].replace("file://", "")
        file_symbols = storage.find_symbols_by_file(first_file)
        print(f"\n--- Symbols in {first_file} ---")
        print(f"Found {len(file_symbols)} symbols")
        for sym in file_symbols[:3]:
            print(f"  - {sym['name']} ({sym['kind']})")
        if len(file_symbols) > 3:
            print(f"  ... and {len(file_symbols) - 3} more")


if __name__ == "__main__":
    main()