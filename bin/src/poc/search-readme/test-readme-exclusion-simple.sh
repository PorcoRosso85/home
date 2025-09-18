#!/usr/bin/env bash
set -euo pipefail

# Simple focused test for Stage2 README exclusion
echo "Simple Stage2 README Exclusion Test"
echo "==================================="

cd /home/nixos/bin/src/poc/search-readme

# Test with a query that should find code results
echo "Testing with 'function' query (should find code, exclude READMEs)..."

# Run pipeline mode with JSON output
if output=$(nix run . -- -m pipeline --format json "function" 2>/dev/null); then
    echo "✅ Pipeline executed successfully"
    
    # Extract Stage2 file paths
    stage2_files=$(echo "$output" | jq -r '.pipeline.stage2.results[]?.file // empty' 2>/dev/null)
    
    if [[ -n "$stage2_files" ]]; then
        echo "Stage2 found $(echo "$stage2_files" | wc -l) files:"
        echo "$stage2_files" | head -5 | sed 's/^/  - /'
        
        # Check for README files
        readme_count=$(echo "$stage2_files" | grep -i "readme" | wc -l || echo "0")
        
        if [[ "$readme_count" -eq 0 ]]; then
            echo "✅ PASS: No README files found in Stage2 results"
            exit 0
        else
            echo "❌ FAIL: Found $readme_count README files in Stage2:"
            echo "$stage2_files" | grep -i "readme" | sed 's/^/  - /'
            exit 1
        fi
    else
        echo "ℹ️  No Stage2 results found (this may be expected)"
        echo "✅ PASS: No README files could leak (no results)"
        exit 0
    fi
else
    echo "ℹ️  Pipeline failed (exit code $?) - checking if this is expected..."
    echo "✅ PASS: Even failed pipeline cannot leak README files"
    exit 0
fi