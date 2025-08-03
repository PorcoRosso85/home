#!/usr/bin/env python3
"""Analyze meta_test directory"""
import subprocess
import json
from pathlib import Path
from graph_docs.kuzu_storage import KuzuStorage

# Run pyright
print("Running Pyright analysis on meta_test...")
result = subprocess.run(
    ["pyright", "--outputjson", "../meta_test"],
    capture_output=True,
    text=True,
    timeout=300  # 5 minutes timeout
)

if result.returncode not in [0, 1]:
    print(f"Pyright failed: {result.stderr}")
    exit(1)

# Parse output
output = json.loads(result.stdout)
print(f"Found {len(output.get('generalDiagnostics', []))} diagnostics")

# Save to KuzuDB
storage = KuzuStorage()
storage.store_analysis(output)

# Export to parquet
output_dir = Path("../meta_test/.kuzu")
output_dir.mkdir(parents=True, exist_ok=True)
storage.export_to_parquet(str(output_dir))

print(f"Analysis complete. Results saved to {output_dir}")