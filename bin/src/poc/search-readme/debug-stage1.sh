#!/bin/bash
set -euo pipefail

# Debug script to test Stage1 search directly
cd /home/nixos/bin/src/poc/search-readme

echo "=== Testing Stage1 search for 'processing' ==="
echo

query="processing"
candidates="[]"

echo "Finding all readme.nix files..."
readme_files=$(find . -name "readme.nix" -type f 2>/dev/null)
echo "Found files:"
echo "$readme_files"
echo

echo "Testing each file for matches..."
for readme_file in $readme_files; do
    [[ ! -f "$readme_file" ]] && continue
    
    dir_path=$(dirname "$readme_file")
    echo "Testing: $readme_file -> $dir_path"
    
    readme_content=$(cat "$readme_file" 2>/dev/null || echo "")
    temp_file=$(mktemp)
    echo "$readme_content" > "$temp_file"
    
    if /home/nixos/bin/src/flakes/ck/result/bin/ck --quiet "$query" "$temp_file" >/dev/null 2>&1; then
        echo "  ✅ MATCH: $dir_path"
        candidates=$(echo "$candidates" | jq --arg path "$dir_path" '. += [$path]')
    else
        echo "  ❌ NO MATCH"
    fi
    
    rm -f "$temp_file"
done

echo
echo "=== Final candidates ==="
echo "$candidates" | jq .
count=$(echo "$candidates" | jq 'length')
echo "Count: $count"