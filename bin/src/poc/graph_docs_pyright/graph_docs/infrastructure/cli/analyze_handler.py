"""Analyze command handler with filtering support."""

import argparse
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from graph_docs.kuzu_storage import KuzuStorage
from graph_docs.pyright_analyzer import PyrightAnalyzer


class AnalyzeHandler:
    """Handler for the analyze command with external dependency filtering."""
    
    def __init__(self):
        """Initialize the analyze handler."""
        pass
    
    
    def analyze_with_filter(
        self, 
        target_dir: str, 
        output_dir: Optional[str] = None,
        filter_external: bool = True
    ) -> Dict[str, Any]:
        """Analyze directory with optional external dependency filtering.
        
        Args:
            target_dir: Directory to analyze
            output_dir: Output directory for Parquet files (defaults to target_dir/.kuzu)
            filter_external: Whether to filter external dependencies
            
        Returns:
            Analysis result dictionary
        """
        target_path = Path(target_dir)
        if not target_path.exists():
            return {
                'success': False,
                'error': f"Target directory does not exist: {target_dir}"
            }
        
        # Default output directory
        if output_dir is None:
            output_dir = str(target_path / '.kuzu')
        
        print(f"Analyzing {target_dir}...")
        
        # Run Pyright with built-in filtering
        analyzer = PyrightAnalyzer(str(target_path))
        result = analyzer.analyze(filter_external=filter_external)
        
        if not result.get('ok', False):
            return {
                'success': False,
                'error': result.get('error', 'Analysis failed')
            }
        
        # Get diagnostics and files from the result
        diagnostics = result.get('diagnostics', [])
        files = result.get('files', [])
        
        print(f"Diagnostics: {len(diagnostics)} found")
        print(f"Files: {len(files)} analyzed")
        
        # Store in KuzuDB
        print("Storing in KuzuDB...")
        storage = KuzuStorage()
        storage.store_analysis(result)
        
        # Export to Parquet
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        print(f"Exporting to {output_dir}...")
        storage.export_to_parquet(output_dir)
        
        return {
            'success': True,
            'diagnostics_count': len(diagnostics),
            'files_count': len(files),
            'output_dir': output_dir
        }
    
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add analyze command arguments to parser.
        
        Args:
            parser: Argument parser
        """
        parser.add_argument(
            'target_directory',
            help='Directory to analyze'
        )
        parser.add_argument(
            'output_directory',
            nargs='?',
            help='Output directory for Parquet files (default: target_directory/.kuzu)'
        )
        parser.add_argument(
            '--no-filter',
            action='store_true',
            help='Disable external dependency filtering'
        )
        parser.add_argument(
            '-j', '--json',
            action='store_true',
            help='Output results as JSON'
        )