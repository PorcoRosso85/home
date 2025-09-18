#!/usr/bin/env bash
# Scan for remaining nil LSP references in the codebase

set -euo pipefail

echo "=== Scanning for nil LSP leftovers ==="
echo

# Define the search patterns with word boundaries and additional patterns
PATTERN='(^|[^A-Za-z0-9_])nil([^A-Za-z0-9_]|$)|NixAdapter|NIL_PATH|NIX_LSP|adapter/nix\\.rs|nil LSP'

# Run the search
echo "Searching for pattern: $PATTERN"
echo "----------------------------------------"

# Count total occurrences with case-insensitive search and explicit exclusions
TOTAL=$(rg -i "$PATTERN" --type-add 'code:*.{rs,toml,nix,md,json}' -t code --glob '!**/export.json' --glob '!target/**' 2>/dev/null | grep -v 'vanilla' | wc -l)
TOTAL=${TOTAL:-0}

if [ "$TOTAL" -eq 0 ]; then
    echo "✅ No nil references found! Migration complete."
    exit 0
else
    echo "❌ Found $TOTAL nil references:"
    echo
    
    # Show details by file with case-insensitive search and exclusions
    rg -i -n "$PATTERN" --type-add 'code:*.{rs,toml,nix,md}' -t code --glob '!**/export.json' --glob '!target/**' 2>/dev/null | grep -v 'vanilla' | head -50 || true
    
    echo
    echo "Summary by file:"
    rg -i "$PATTERN" --type-add 'code:*.{rs,toml,nix,md,json}' -t code --glob '!**/export.json' --glob '!target/**' 2>/dev/null | grep -v 'vanilla' | cut -d: -f1 | sort | uniq -c || true
    
    exit 1
fi