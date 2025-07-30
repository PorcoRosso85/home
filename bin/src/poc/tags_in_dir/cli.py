#!/usr/bin/env python3
"""
CLI for tags_in_dir - ctags-based code analysis with KuzuDB persistence.

Usage:
    find -d 3 | nix run .#generate
    nix run .#generate /path/to/file_or_dir
"""

import argparse
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import os

from tags_in_dir import CtagsParser, Symbol
from kuzu_storage import KuzuStorage
from call_detector import CallDetector
from analysis_queries import CodeAnalyzer


def process_uri(uri: str, storage: KuzuStorage, parser: CtagsParser, detector: CallDetector) -> Dict[str, Any]:
    """Process a single file or directory URI."""
    # Remove file:// prefix if present
    if uri.startswith("file://"):
        uri = uri[7:]
    
    path = Path(uri).resolve()
    
    if not path.exists():
        return {"error": f"Path does not exist: {uri}"}
    
    # Extract symbols
    if path.is_file():
        symbols = parser.extract_symbols(str(path.parent), extensions=[path.suffix])
        symbols = [s for s in symbols if s.location_uri.startswith(f"file://{path}")]
    else:
        symbols = parser.extract_symbols(str(path))
    
    # Store symbols
    storage.store_symbols(symbols)
    
    # Detect and store call relationships
    relationships = detector.detect_all_calls()
    resolved = detector.resolve_call_targets(relationships)
    
    for rel in resolved:
        storage.create_calls_relationship(
            from_location_uri=rel.from_uri,
            to_location_uri=rel.to_uri,
            line_number=rel.line_number
        )
    
    return {
        "uri": uri,
        "symbols_count": len(symbols),
        "calls_count": len(resolved)
    }


def export_analysis(storage: KuzuStorage, output_dir: Path) -> Dict[str, str]:
    """Export analysis results to parquet files."""
    output_dir.mkdir(exist_ok=True)
    
    exports = {}
    
    # Export symbols
    symbols_file = output_dir / "symbols.parquet"
    storage.execute_cypher(f"""
        COPY (MATCH (s:Symbol) RETURN s.*) 
        TO '{symbols_file}' (compression = 'snappy');
    """)
    exports["symbols"] = str(symbols_file)
    
    # Export calls
    calls_file = output_dir / "calls.parquet"
    storage.execute_cypher(f"""
        COPY (MATCH (s1:Symbol)-[c:CALLS]->(s2:Symbol) 
              RETURN s1.location_uri as from_uri, s2.location_uri as to_uri, c.line_number) 
        TO '{calls_file}' (compression = 'snappy');
    """)
    exports["calls"] = str(calls_file)
    
    # Export analysis results
    analyzer = CodeAnalyzer(storage)
    
    # Dead code
    dead_code = analyzer.find_dead_code()
    dead_code_data = [{"name": row[0], "uri": row[1]} for row in dead_code]
    
    # Most called functions
    most_called = analyzer.find_most_called_functions(limit=20)
    most_called_data = [{"name": row[0], "uri": row[1], "call_count": row[2]} for row in most_called]
    
    # File dependencies
    deps = analyzer.get_file_dependencies()
    deps_data = [{"from_file": row[0], "to_file": row[1], "call_count": row[2]} for row in deps]
    
    # Save analysis results as JSON
    analysis_file = output_dir / "analysis.json"
    with open(analysis_file, "w") as f:
        json.dump({
            "dead_code": dead_code_data,
            "most_called_functions": most_called_data,
            "file_dependencies": deps_data,
            "statistics": storage.get_statistics()
        }, f, indent=2)
    exports["analysis"] = str(analysis_file)
    
    return exports


def main():
    parser = argparse.ArgumentParser(
        description="ctags-based code analysis with KuzuDB persistence"
    )
    parser.add_argument(
        "uris",
        nargs="*",
        help="URIs to process (files or directories). If not provided, reads from stdin."
    )
    parser.add_argument(
        "--db",
        default="tags.db",
        help="KuzuDB database path (default: tags.db)"
    )
    parser.add_argument(
        "--export-dir",
        help="Directory to export parquet files"
    )
    parser.add_argument(
        "--export-only",
        action="store_true",
        help="Only export existing database, don't process new files"
    )
    
    args = parser.parse_args()
    
    # Initialize storage
    storage = KuzuStorage(args.db)
    
    if not args.export_only:
        # Get URIs from args or stdin
        uris = args.uris
        if not uris:
            uris = [line.strip() for line in sys.stdin if line.strip()]
        
        if not uris:
            parser.error("No URIs provided")
        
        # Initialize parser and detector
        ctags_parser = CtagsParser()
        detector = CallDetector(ctags_parser.symbols)
        
        # Process each URI
        results = []
        for uri in uris:
            result = process_uri(uri, storage, ctags_parser, detector)
            results.append(result)
        
        # Output processing results as JSON
        output = {
            "processed": results,
            "total_symbols": sum(r.get("symbols_count", 0) for r in results),
            "total_calls": sum(r.get("calls_count", 0) for r in results)
        }
        sys.stdout.write(json.dumps(output, indent=2) + "\n")
    
    # Export if requested
    if args.export_dir:
        export_dir = Path(args.export_dir)
        exports = export_analysis(storage, export_dir)
        
        export_output = {
            "exported_files": exports,
            "export_directory": str(export_dir.resolve())
        }
        sys.stdout.write(json.dumps(export_output, indent=2) + "\n")
    
    storage.close()


if __name__ == "__main__":
    main()