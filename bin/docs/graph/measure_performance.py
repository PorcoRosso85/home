#!/usr/bin/env python3
"""Performance measurement script for flake indexing.

This script establishes baseline metrics for the 90% performance improvement goal.
It measures:
1. Time to index 100 test flakes
2. Memory usage during indexing
3. Performance comparison with/without persistence
"""

import time
import tracemalloc
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Tuple
import json

from flake_graph.vss_adapter import (
    create_flake_document,
    search_similar_flakes,
    index_flakes_with_persistence
)
from flake_graph.scanner import scan_flake_description, scan_readme_content
from vss_kuzu import create_vss


def create_test_flake(index: int, base_path: Path) -> Path:
    """Create a test flake with sample content."""
    flake_dir = base_path / f"test_flake_{index:03d}"
    flake_dir.mkdir(parents=True, exist_ok=True)
    
    # Create flake.nix
    flake_content = f'''{{
  description = "Test flake {index} for performance measurement";
  
  inputs = {{
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  }};
  
  outputs = {{ self, nixpkgs }}: {{
    # Sample output for test flake {index}
    packages.x86_64-linux.default = nixpkgs.legacyPackages.x86_64-linux.hello;
  }};
}}'''
    (flake_dir / "flake.nix").write_text(flake_content)
    
    # Create README.md with varied content
    readme_content = f"""# Test Flake {index}

This is a test flake created for performance measurement.

## Features
- Feature {index % 10}: Some description about this feature
- Feature {(index + 1) % 10}: Another feature description
- Feature {(index + 2) % 10}: Yet another feature

## Usage
This flake is used for testing performance of the indexing system.
It contains sample content to simulate real flakes.

## Categories
This flake belongs to category {index % 5} and subcategory {index % 3}.
"""
    (flake_dir / "README.md").write_text(readme_content)
    
    return flake_dir


def scan_test_flakes(base_path: Path) -> List[Dict[str, Any]]:
    """Scan test flakes and return flake info list."""
    flakes = []
    
    for flake_path in sorted(base_path.rglob("flake.nix")):
        flake_dir = flake_path.parent
        description = scan_flake_description(flake_path)
        readme = scan_readme_content(flake_dir)
        
        flakes.append({
            "path": flake_dir,
            "description": description or "",
            "readme_content": readme or "",
            "language": "nix"
        })
    
    return flakes


def measure_memory_usage() -> Tuple[float, float]:
    """Get current and peak memory usage in MB."""
    current, peak = tracemalloc.get_traced_memory()
    return current / 1024 / 1024, peak / 1024 / 1024


def measure_indexing_without_persistence(flakes: List[Dict[str, Any]], db_path: str) -> Dict[str, Any]:
    """Measure performance of VSS indexing without persistence."""
    # Start memory tracking
    tracemalloc.start()
    start_time = time.time()
    
    # Convert flakes to documents
    documents = [create_flake_document(flake) for flake in flakes]
    
    # Create VSS instance and index
    vss = create_vss(db_path=db_path)
    
    if isinstance(vss, dict) and 'type' in vss:
        return {
            "error": f"VSS initialization failed: {vss.get('message', 'Unknown error')}",
            "time_seconds": 0,
            "memory_mb": {"current": 0, "peak": 0}
        }
    
    index_result = vss.index(documents)
    
    # End timing
    end_time = time.time()
    current_mem, peak_mem = measure_memory_usage()
    tracemalloc.stop()
    
    return {
        "time_seconds": end_time - start_time,
        "memory_mb": {"current": current_mem, "peak": peak_mem},
        "indexed_count": len(documents),
        "index_result": index_result
    }


def measure_indexing_with_persistence(
    flakes: List[Dict[str, Any]], 
    vss_db_path: str,
    kuzu_db_path: str,
    force_reindex: bool = False
) -> Dict[str, Any]:
    """Measure performance of VSS indexing with KuzuDB persistence."""
    # Start memory tracking
    tracemalloc.start()
    start_time = time.time()
    
    # Index with persistence
    result = index_flakes_with_persistence(
        flakes=flakes,
        vss_db_path=vss_db_path,
        kuzu_db_path=kuzu_db_path,
        force_reindex=force_reindex
    )
    
    # End timing
    end_time = time.time()
    current_mem, peak_mem = measure_memory_usage()
    tracemalloc.stop()
    
    return {
        "time_seconds": end_time - start_time,
        "memory_mb": {"current": current_mem, "peak": peak_mem},
        "result": result
    }


def main():
    """Run performance measurements."""
    print("Flake Indexing Performance Measurement")
    print("=" * 50)
    
    # Create temporary directory for test flakes
    with tempfile.TemporaryDirectory() as temp_dir:
        test_base = Path(temp_dir)
        
        # Create 100 test flakes
        print("\nCreating 100 test flakes...")
        for i in range(100):
            create_test_flake(i, test_base)
        
        # Scan flakes
        print("Scanning test flakes...")
        flakes = scan_test_flakes(test_base)
        print(f"Found {len(flakes)} flakes")
        
        # Measure without persistence
        print("\n1. Measuring VSS indexing WITHOUT persistence:")
        print("-" * 40)
        
        with tempfile.NamedTemporaryFile(suffix=".db") as vss_db:
            result_no_persist = measure_indexing_without_persistence(flakes, vss_db.name)
            
            if "error" in result_no_persist:
                print(f"Error: {result_no_persist['error']}")
            else:
                print(f"Time: {result_no_persist['time_seconds']:.3f} seconds")
                print(f"Memory (current): {result_no_persist['memory_mb']['current']:.2f} MB")
                print(f"Memory (peak): {result_no_persist['memory_mb']['peak']:.2f} MB")
                print(f"Indexed: {result_no_persist['indexed_count']} flakes")
        
        # Measure with persistence (first run - all new)
        print("\n2. Measuring VSS indexing WITH persistence (first run):")
        print("-" * 40)
        
        with tempfile.TemporaryDirectory() as persist_dir:
            vss_db_path = Path(persist_dir) / "vss.db"
            kuzu_db_path = Path(persist_dir) / "kuzu"
            
            result_persist_first = measure_indexing_with_persistence(
                flakes, str(vss_db_path), str(kuzu_db_path), force_reindex=False
            )
            
            print(f"Time: {result_persist_first['time_seconds']:.3f} seconds")
            print(f"Memory (current): {result_persist_first['memory_mb']['current']:.2f} MB")
            print(f"Memory (peak): {result_persist_first['memory_mb']['peak']:.2f} MB")
            
            if result_persist_first['result'].get('ok'):
                stats = result_persist_first['result']['stats']
                print(f"Indexed: {stats['indexed']} flakes")
                print(f"New embeddings: {stats['new_embeddings']}")
                print(f"Updated embeddings: {stats['updated_embeddings']}")
                print(f"Skipped: {stats['skipped']}")
            
            # Measure with persistence (second run - all cached)
            print("\n3. Measuring VSS indexing WITH persistence (cached):")
            print("-" * 40)
            
            result_persist_cached = measure_indexing_with_persistence(
                flakes, str(vss_db_path), str(kuzu_db_path), force_reindex=False
            )
            
            print(f"Time: {result_persist_cached['time_seconds']:.3f} seconds")
            print(f"Memory (current): {result_persist_cached['memory_mb']['current']:.2f} MB")
            print(f"Memory (peak): {result_persist_cached['memory_mb']['peak']:.2f} MB")
            
            if result_persist_cached['result'].get('ok'):
                stats = result_persist_cached['result']['stats']
                print(f"Indexed: {stats['indexed']} flakes")
                print(f"Skipped (cached): {stats['skipped']}")
        
        # Summary
        print("\n" + "=" * 50)
        print("PERFORMANCE SUMMARY")
        print("=" * 50)
        
        if "error" not in result_no_persist:
            print(f"\nWithout persistence: {result_no_persist['time_seconds']:.3f}s")
            print(f"With persistence (first run): {result_persist_first['time_seconds']:.3f}s")
            print(f"With persistence (cached): {result_persist_cached['time_seconds']:.3f}s")
            
            # Calculate speedup
            if result_persist_cached['time_seconds'] > 0:
                speedup = result_no_persist['time_seconds'] / result_persist_cached['time_seconds']
                print(f"\nSpeedup with caching: {speedup:.1f}x")
                improvement_pct = ((result_no_persist['time_seconds'] - result_persist_cached['time_seconds']) / 
                                 result_no_persist['time_seconds'] * 100)
                print(f"Performance improvement: {improvement_pct:.1f}%")
                
                if improvement_pct >= 90:
                    print("\n✅ Goal achieved: 90% performance improvement!")
                else:
                    print(f"\n⚠️  Current improvement: {improvement_pct:.1f}% (Goal: 90%)")
        
        # Export detailed results
        results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_flakes": len(flakes),
            "measurements": {
                "without_persistence": result_no_persist,
                "with_persistence_first_run": result_persist_first,
                "with_persistence_cached": result_persist_cached
            }
        }
        
        output_file = Path("performance_results.json")
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\nDetailed results saved to: {output_file}")


if __name__ == "__main__":
    main()