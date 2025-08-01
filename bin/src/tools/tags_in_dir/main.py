#!/usr/bin/env python3
"""CLI for tags_in_dir tool."""

import json
import sys
from pathlib import Path
from typing import List, Optional
import argparse

from . import mod


def process_uri(uri: str, repository: mod.KuzuRepository, config: mod.Config) -> dict:
    """Process a single URI."""
    path = uri.replace('file://', '') if uri.startswith('file://') else uri
    
    # Extract symbols
    extract_result = mod.extract_and_store_symbols(
        path, 
        repository,
        extensions=config['default_extensions'],
        ctags_path=config['ctags_path']
    )
    
    if mod.is_error(extract_result):
        return extract_result
    
    # Detect calls if it's a directory or Python file
    if Path(path).is_dir() or path.endswith('.py'):
        calls_result = mod.detect_and_store_calls(
            path if Path(path).is_dir() else str(Path(path).parent),
            repository,
            extensions=['.py']  # Only Python for call detection
        )
        
        if mod.is_error(calls_result):
            return {
                'uri': uri,
                'symbols_count': extract_result['symbols_stored'],
                'calls_count': 0,
                'error': calls_result
            }
        
        return {
            'uri': uri,
            'symbols_count': extract_result['symbols_stored'],
            'calls_count': calls_result.get('calls_stored', 0)
        }
    
    return {
        'uri': uri,
        'symbols_count': extract_result['symbols_stored'],
        'calls_count': 0
    }


def export_analysis(repository: mod.KuzuRepository, output_dir: Path) -> dict:
    """Export analysis results."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Export parquet files
    export_result = repository.export_to_parquet(str(output_dir))
    if mod.is_error(export_result):
        return export_result
    
    # Create analysis report
    report = mod.create_analysis_report(repository)
    if mod.is_error(report):
        return report
    
    # Save analysis report
    analysis_path = output_dir / 'analysis.json'
    with open(analysis_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    export_result['analysis'] = str(analysis_path)
    return export_result


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Extract code symbols using ctags and store in KuzuDB'
    )
    parser.add_argument(
        'uris',
        nargs='*',
        help='URIs to process (files or directories)'
    )
    parser.add_argument(
        '--db',
        default=None,
        help='Database path (default: in-memory)'
    )
    parser.add_argument(
        '--export-dir',
        type=Path,
        help='Export analysis results to directory'
    )
    parser.add_argument(
        '--export-only',
        action='store_true',
        help='Only export from existing database'
    )
    
    args = parser.parse_args()
    
    # Get configuration
    config = mod.get_config()
    
    # Initialize repository
    db_path = args.db or config['default_db_path']
    repository = mod.KuzuRepository(db_path)
    
    results = {
        'processed': [],
        'total_symbols': 0,
        'total_calls': 0
    }
    
    try:
        # Export only mode
        if args.export_only:
            if not args.export_dir:
                print(json.dumps({
                    'error': 'MISSING_EXPORT_DIR',
                    'message': '--export-dir required with --export-only'
                }))
                return 1
            
            export_result = export_analysis(repository, args.export_dir)
            if mod.is_error(export_result):
                print(json.dumps(export_result))
                return 1
            
            print(json.dumps({'exported': export_result}))
            return 0
        
        # Process URIs
        uris = args.uris
        
        # If no URIs provided, read from stdin
        if not uris:
            uris = []
            for line in sys.stdin:
                line = line.strip()
                if line:
                    uris.append(line)
        
        if not uris:
            print(json.dumps({
                'error': 'NO_INPUT',
                'message': 'No URIs provided'
            }))
            return 1
        
        # Process each URI
        for uri in uris:
            result = process_uri(uri, repository, config)
            
            if mod.is_error(result):
                print(json.dumps(result))
                return 1
            
            results['processed'].append(result)
            results['total_symbols'] += result.get('symbols_count', 0)
            results['total_calls'] += result.get('calls_count', 0)
        
        # Export if requested
        if args.export_dir:
            export_result = export_analysis(repository, args.export_dir)
            if mod.is_error(export_result):
                print(json.dumps(export_result))
                return 1
            results['exported'] = export_result
        
        # Output results
        print(json.dumps(results, indent=2))
        return 0
        
    finally:
        repository.close()


if __name__ == '__main__':
    sys.exit(main())