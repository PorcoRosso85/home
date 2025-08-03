#!/usr/bin/env python3
"""Simple analysis script - wrapper for CLI handler"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from graph_docs.infrastructure.cli.analyze_handler import AnalyzeHandler


def main():
    """Run simple analysis using the CLI handler."""
    if len(sys.argv) < 2:
        print("Usage: python simple_analyze.py <target_directory> [output_directory]")
        sys.exit(1)
    
    target = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Use the CLI handler directly
    handler = AnalyzeHandler()
    result = handler.analyze_with_filter(
        target_dir=target,
        output_dir=output,
        filter_external=False  # No filtering for simple analysis
    )
    
    if result['success']:
        print(f"\nAnalysis complete:")
        print(f"  Diagnostics: {result['diagnostics_count']}")
        print(f"  Files: {result['files_count']}")
        print(f"\nParquet files saved to: {result['output_dir']}")
    else:
        print(f"Error: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()