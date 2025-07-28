#!/usr/bin/env python3
"""
Example script to read and analyze ASVS Parquet files
"""
import pyarrow.parquet as pq
import pyarrow.compute as pc

def analyze_parquet(parquet_file: str):
    """Read and analyze ASVS Parquet file"""
    # Read the Parquet file
    table = pq.read_table(parquet_file)
    
    print(f"=== ASVS Parquet Analysis: {parquet_file} ===\n")
    
    # Basic info
    print(f"Total requirements: {table.num_rows}")
    print(f"File size: {table.nbytes:,} bytes in memory")
    
    # Metadata
    if table.schema.metadata:
        print("\nMetadata:")
        for key, value in table.schema.metadata.items():
            print(f"  {key.decode()}: {value.decode()}")
    
    # Sample data
    print("\nSample requirements (first 3):")
    for i in range(min(3, table.num_rows)):
        row = table.slice(i, 1)
        print(f"\n  Requirement #{i+1}:")
        print(f"    Number: {row['number'][0].as_py()}")
        print(f"    Description: {row['description'][0].as_py()[:100]}...")
        print(f"    Levels: L1={row['level1'][0].as_py()}, L2={row['level2'][0].as_py()}, L3={row['level3'][0].as_py()}")
    
    # Filter examples
    print("\n=== Filter Examples ===")
    
    # Level 3 only requirements
    level3_only = table.filter(
        pc.and_(
            pc.equal(table['level3'], True),
            pc.equal(table['level2'], False)
        )
    )
    print(f"\nLevel 3 only requirements: {level3_only.num_rows}")
    
    # Authentication requirements
    auth_reqs = table.filter(
        pc.match_substring(table['chapter'], 'Authentication')
    )
    print(f"Authentication requirements: {auth_reqs.num_rows}")
    
    # Requirements with CWE references
    has_cwe = table.filter(
        pc.is_valid(table['cwe'])
    )
    print(f"Requirements with CWE references: {has_cwe.num_rows}")
    
    # Convert to pandas for more analysis (optional)
    try:
        import pandas as pd
        df = table.to_pandas()
        
        print("\n=== Pandas Analysis ===")
        print(f"\nRequirements per chapter:")
        chapter_counts = df['chapter'].value_counts().head(5)
        for chapter, count in chapter_counts.items():
            print(f"  {chapter}: {count}")
        
    except ImportError:
        print("\n(Install pandas for additional analysis features)")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python example_read_parquet.py <parquet_file>")
        print("Example: python example_read_parquet.py output/asvs_v5.0.parquet")
        sys.exit(1)
    
    analyze_parquet(sys.argv[1])