#!/usr/bin/env python3
"""graph_docs CLI - Pyright-based code analysis with KuzuDB"""
import argparse
import sys
import json

from graph_docs.infrastructure.cli.analyze_handler import AnalyzeHandler


def create_parser():
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog='graph-docs-pyright',
        description='Analyze Python code with Pyright and store results in KuzuDB'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser(
        'analyze',
        help='Analyze a directory and save results to Parquet'
    )
    analyze_handler = AnalyzeHandler()
    analyze_handler.add_arguments(analyze_parser)
    
    return parser


def main():
    """Entry point for the graph_docs CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'analyze':
        handler = AnalyzeHandler()
        result = handler.analyze_with_filter(
            args.target_directory,
            args.output_directory,
            filter_external=not args.no_filter
        )
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result['success']:
                print(f"\nAnalysis complete:")
                print(f"  Diagnostics: {result['diagnostics_count']}")
                print(f"  Files: {result['files_count']}")
                print(f"  Output: {result['output_dir']}")
            else:
                print(f"Error: {result['error']}")
                sys.exit(1)


if __name__ == "__main__":
    main()