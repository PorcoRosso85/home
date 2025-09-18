#!/usr/bin/env python3
"""One-shot analysis and save to parquet"""
import sys
import os
from pathlib import Path
from graph_docs.pyright_analyzer import PyrightAnalyzer
from graph_docs.infrastructure.kuzu.kuzu_repository import KuzuRepository
import kuzu

def analyze_and_save(target_dir: str, output_dir: str = "./.kuzu"):
    """Analyze directory and save to parquet files"""
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Create in-memory database and repository
    repo = KuzuRepository(":memory:")
    analyzer = PyrightAnalyzer(target_dir)
    
    # Analyze
    print(f"Analyzing {target_dir}...")
    result = analyzer.analyze()
    
    # Save to repository
    repo.store_file(result['file'])
    for cls in result['classes']:
        repo.store_class(cls)
    for func in result['functions']:
        repo.store_function(func)
    for diag in result['diagnostics']:
        repo.store_diagnostic(diag)
    for rel in result['relations']:
        repo.store_relation(rel)
    
    # Export to parquet
    print(f"Exporting to {output_dir}...")
    repo.export_to_parquet(output_dir)
    
    # Show summary
    conn = repo.conn
    file_count = conn.execute("MATCH (f:File) RETURN count(f) as count").get_next()[0]
    class_count = conn.execute("MATCH (c:Class) RETURN count(c) as count").get_next()[0]
    func_count = conn.execute("MATCH (f:Function) RETURN count(f) as count").get_next()[0]
    diag_count = conn.execute("MATCH (d:Diagnostic) RETURN count(d) as count").get_next()[0]
    
    print(f"\nAnalysis complete:")
    print(f"  Files: {file_count}")
    print(f"  Classes: {class_count}")
    print(f"  Functions: {func_count}")
    print(f"  Diagnostics: {diag_count}")
    print(f"\nParquet files saved to: {output_dir}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_and_save.py <target_directory> [output_directory]")
        sys.exit(1)
    
    target = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else "./.kuzu"
    
    analyze_and_save(target, output)