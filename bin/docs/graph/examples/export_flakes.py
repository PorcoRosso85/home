#!/usr/bin/env python3
"""Example usage of the FlakeExporter."""

from pathlib import Path
from flake_graph.exporter import FlakeExporter


def main():
    """Demonstrate flake export functionality."""
    # Database path - adjust as needed
    db_path = Path.home() / ".kuzu" / "flake_graph"
    
    # Create exporter instance
    exporter = FlakeExporter(db_path)
    
    try:
        # Example 1: Export all flakes with embeddings
        print("Exporting all flakes...")
        result = exporter.export_to_json(
            output_path="exports/all_flakes.json",
            include_embeddings=True
        )
        print(f"✓ Exported {result['total_exported']} flakes to {result['output_path']}")
        print(f"  File size: {result['file_size_bytes']:,} bytes")
        
        # Example 2: Export Python flakes only (without embeddings)
        print("\nExporting Python flakes only...")
        result = exporter.export_to_json(
            output_path="exports/python_flakes.json",
            language_filter="python",
            include_embeddings=False
        )
        print(f"✓ Exported {result['total_exported']} Python flakes")
        
        # Example 3: Export summary statistics
        print("\nExporting summary...")
        summary = exporter.export_summary("exports/summary.json")
        print(f"✓ Summary exported with {summary['statistics']['total_flakes']} total flakes")
        print(f"  Languages: {', '.join(summary['statistics']['by_language'].keys())}")
        
        # Example 4: Export by language (separate files)
        print("\nExporting by language...")
        lang_files = exporter.export_by_language("exports/by_language")
        for lang, filepath in lang_files.items():
            print(f"✓ {lang}: {filepath}")
            
    finally:
        exporter.close()


if __name__ == "__main__":
    main()