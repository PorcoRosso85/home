#!/usr/bin/env python3
"""
ASVS Arrow CLI - Convert ASVS Markdown to Parquet

A minimal CLI tool for converting OWASP ASVS markdown files to Apache Arrow Parquet format.
"""
import argparse
import sys
from pathlib import Path
from typing import Optional
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.compute as pc

from asvs_arrow_converter import ASVSArrowConverter


def print_statistics(table: pa.Table, verbose: bool = False) -> None:
    """Print statistics about the converted Arrow table"""
    print("\n=== Conversion Statistics ===")
    print(f"Total requirements: {table.num_rows}")
    print(f"Total columns: {table.num_columns}")
    print(f"Memory usage: {table.nbytes:,} bytes")
    
    # Count requirements by level
    level1_count = pc.sum(pc.cast(table['level1'], pa.int64())).as_py()
    level2_count = pc.sum(pc.cast(table['level2'], pa.int64())).as_py()
    level3_count = pc.sum(pc.cast(table['level3'], pa.int64())).as_py()
    
    print(f"\nRequirements by level:")
    print(f"  Level 1: {level1_count} requirements")
    print(f"  Level 2: {level2_count} requirements")
    print(f"  Level 3: {level3_count} requirements")
    
    # Count by chapter
    chapters = table['chapter'].to_pylist()
    unique_chapters = sorted(set(chapters))
    print(f"\nTotal chapters: {len(unique_chapters)}")
    
    if verbose:
        print("\nRequirements per chapter:")
        for chapter in unique_chapters:
            count = chapters.count(chapter)
            print(f"  {chapter}: {count} requirements")
        
        # Show schema
        print("\n=== Table Schema ===")
        for field in table.schema:
            print(f"  {field.name}: {field.type}")
        
        # Show metadata
        if table.schema.metadata:
            print("\n=== Table Metadata ===")
            for key, value in table.schema.metadata.items():
                print(f"  {key.decode()}: {value.decode()}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert ASVS Markdown files to Apache Arrow Parquet format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert ASVS markdown directory to Parquet
  %(prog)s /path/to/asvs/5.0 -o asvs_v5.parquet
  
  # Use different compression
  %(prog)s /path/to/asvs/5.0 -o asvs_v5.parquet -c gzip
  
  # Show detailed statistics
  %(prog)s /path/to/asvs/5.0 -o asvs_v5.parquet -v
  
  # No compression for faster processing
  %(prog)s /path/to/asvs/5.0 -o asvs_v5.parquet -c none
"""
    )
    
    parser.add_argument(
        'input_dir',
        type=Path,
        help='Path to ASVS markdown directory containing V*.md files'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=Path,
        required=True,
        help='Output Parquet file path'
    )
    
    parser.add_argument(
        '-c', '--compression',
        choices=['snappy', 'gzip', 'brotli', 'lz4', 'zstd', 'none'],
        default='snappy',
        help='Compression algorithm (default: snappy)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed statistics'
    )
    
    parser.add_argument(
        '--stats-only',
        action='store_true',
        help='Only show statistics without saving the file'
    )
    
    args = parser.parse_args()
    
    # Validate input directory
    if not args.input_dir.exists():
        print(f"Error: Input directory '{args.input_dir}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    if not args.input_dir.is_dir():
        print(f"Error: '{args.input_dir}' is not a directory", file=sys.stderr)
        sys.exit(1)
    
    # Check for V*.md files (supports both V*.md and *-V*-*.md patterns)
    md_files = list(args.input_dir.glob("V*.md"))
    if not md_files:
        # Try alternative pattern used by ASVS 5.0
        md_files = list(args.input_dir.glob("*-V[0-9]*-*.md"))
    
    if not md_files:
        print(f"Error: No ASVS markdown files found in '{args.input_dir}'", file=sys.stderr)
        print("Expected patterns: V*.md or *-V[0-9]*-*.md", file=sys.stderr)
        sys.exit(1)
    
    print(f"Found {len(md_files)} ASVS markdown files in '{args.input_dir}'")
    
    try:
        # Convert to Arrow
        print("Converting to Arrow format...")
        converter = ASVSArrowConverter(str(args.input_dir))
        table = converter.get_requirements_table()
        
        # Print statistics
        print_statistics(table, verbose=args.verbose)
        
        # Save to Parquet unless stats-only mode
        if not args.stats_only:
            # Handle compression
            compression = None if args.compression == 'none' else args.compression
            
            print(f"\nSaving to Parquet file: {args.output}")
            print(f"Compression: {args.compression}")
            
            # Create output directory if needed
            args.output.parent.mkdir(parents=True, exist_ok=True)
            
            # Write Parquet file
            pq.write_table(table, str(args.output), compression=compression)
            
            # Show file size
            file_size = args.output.stat().st_size
            print(f"Output file size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
            
            # Calculate compression ratio if applicable
            if compression:
                ratio = (table.nbytes - file_size) / table.nbytes * 100
                print(f"Compression ratio: {ratio:.1f}% reduction")
        
        print("\n✓ Conversion completed successfully!")
        
    except Exception as e:
        print(f"\nError during conversion: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()