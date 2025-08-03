"""Export flake data from KuzuDB to JSON format."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import numpy as np

from .kuzu_adapter import KuzuAdapter


class FlakeExporter:
    """Export flake graph data from KuzuDB to various formats."""
    
    def __init__(self, db_path: Union[str, Path]):
        """Initialize exporter with KuzuDB connection.
        
        Args:
            db_path: Path to the KuzuDB database
        """
        self.adapter = KuzuAdapter(db_path)
    
    def export_to_json(self, 
                      output_path: Union[str, Path],
                      language_filter: Optional[str] = None,
                      include_embeddings: bool = True,
                      pretty_print: bool = True) -> Dict[str, Any]:
        """Export all flake data to JSON format.
        
        Args:
            output_path: Path where to save the JSON file
            language_filter: Optional filter by programming language
            include_embeddings: Whether to include VSS embeddings in export
            pretty_print: Whether to format JSON with indentation
            
        Returns:
            Dictionary with export metadata and summary
        """
        output_path = Path(output_path)
        
        # Fetch flake data from database
        flakes = self.adapter.list_flakes(language=language_filter)
        
        # Process embeddings if needed
        if not include_embeddings:
            for flake in flakes:
                if 'vss_embedding' in flake:
                    del flake['vss_embedding']
        else:
            # Convert numpy arrays to lists for JSON serialization
            for flake in flakes:
                if 'vss_embedding' in flake and flake['vss_embedding'] is not None:
                    if isinstance(flake['vss_embedding'], np.ndarray):
                        flake['vss_embedding'] = flake['vss_embedding'].tolist()
        
        # Convert timestamps to ISO format for JSON serialization
        for flake in flakes:
            if 'vss_analyzed_at' in flake and flake['vss_analyzed_at'] is not None:
                if hasattr(flake['vss_analyzed_at'], 'isoformat'):
                    flake['vss_analyzed_at'] = flake['vss_analyzed_at'].isoformat()
        
        # Prepare metadata
        metadata = {
            'export_date': datetime.now().isoformat(),
            'total_flakes': len(flakes),
            'language_filter': language_filter,
            'embeddings_included': include_embeddings,
            'languages': self._get_language_summary(flakes),
            'db_path': str(self.adapter.db_path)
        }
        
        # Create export data structure
        export_data = {
            'metadata': metadata,
            'flakes': flakes
        }
        
        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            if pretty_print:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            else:
                json.dump(export_data, f, ensure_ascii=False)
        
        # Return summary
        return {
            'status': 'success',
            'output_path': str(output_path),
            'total_exported': len(flakes),
            'file_size_bytes': output_path.stat().st_size,
            'metadata': metadata
        }
    
    def export_summary(self, output_path: Union[str, Path]) -> Dict[str, Any]:
        """Export a summary of flake data without full details.
        
        Args:
            output_path: Path where to save the summary JSON
            
        Returns:
            Dictionary with summary statistics
        """
        output_path = Path(output_path)
        
        # Get all flakes
        all_flakes = self.adapter.list_flakes()
        
        # Calculate statistics
        languages = self._get_language_summary(all_flakes)
        
        # Count flakes with various properties
        with_embeddings = sum(1 for f in all_flakes if f.get('vss_embedding') is not None)
        with_ast_score = sum(1 for f in all_flakes if f.get('ast_score') is not None)
        with_metrics = sum(1 for f in all_flakes if f.get('ast_metrics') is not None)
        
        summary = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'db_path': str(self.adapter.db_path)
            },
            'statistics': {
                'total_flakes': len(all_flakes),
                'by_language': languages,
                'with_embeddings': with_embeddings,
                'with_ast_analysis': with_ast_score,
                'with_ast_metrics': with_metrics
            },
            'sample_paths': [f['path'] for f in all_flakes[:10]]  # First 10 as sample
        }
        
        # Write summary
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        return summary
    
    def export_by_language(self, output_dir: Union[str, Path]) -> Dict[str, str]:
        """Export flakes grouped by language into separate files.
        
        Args:
            output_dir: Directory where to save language-specific JSON files
            
        Returns:
            Dictionary mapping language to output file path
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get all flakes
        all_flakes = self.adapter.list_flakes()
        
        # Group by language
        by_language: Dict[str, List[Dict[str, Any]]] = {}
        for flake in all_flakes:
            lang = flake.get('language', 'unknown')
            if lang not in by_language:
                by_language[lang] = []
            by_language[lang].append(flake)
        
        # Export each language group
        output_files = {}
        for language, flakes in by_language.items():
            filename = f"flakes_{language}.json"
            filepath = output_dir / filename
            
            export_data = {
                'metadata': {
                    'export_date': datetime.now().isoformat(),
                    'language': language,
                    'total_flakes': len(flakes)
                },
                'flakes': flakes
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            output_files[language] = str(filepath)
        
        return output_files
    
    def _get_language_summary(self, flakes: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get count of flakes by language.
        
        Args:
            flakes: List of flake dictionaries
            
        Returns:
            Dictionary mapping language to count
        """
        language_counts: Dict[str, int] = {}
        for flake in flakes:
            lang = flake.get('language', 'unknown')
            language_counts[lang] = language_counts.get(lang, 0) + 1
        return language_counts
    
    def close(self):
        """Close database connection."""
        self.adapter.close()


def main():
    """Example usage of FlakeExporter."""
    import sys
    
    if len(sys.argv) < 3:
        # CLI usage information should go to stderr for proper Unix behavior
        sys.stderr.write("Usage: python -m flake_graph.exporter <db_path> <output_path> [language_filter]\n")
        sys.exit(1)
    
    db_path = sys.argv[1]
    output_path = sys.argv[2]
    language_filter = sys.argv[3] if len(sys.argv) > 3 else None
    
    exporter = FlakeExporter(db_path)
    try:
        result = exporter.export_to_json(output_path, language_filter=language_filter)
        # CLI success messages to stdout for proper Unix behavior
        sys.stdout.write(f"Export successful: {result['total_exported']} flakes exported to {result['output_path']}\n")
        sys.stdout.write(f"File size: {result['file_size_bytes']} bytes\n")
    finally:
        exporter.close()


if __name__ == "__main__":
    main()