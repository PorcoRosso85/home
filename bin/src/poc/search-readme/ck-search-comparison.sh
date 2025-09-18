#!/bin/bash
set -euo pipefail

# ck Search Mode Comparison Test
# Tests different ck search modes for optimal Stage1 README search configuration

cd /home/nixos/bin/src/poc/search-readme

echo "=== CK SEARCH MODE COMPARISON ==="
echo "Test Files: 4 readme.nix files"
echo "- project-a: web application framework"  
echo "- project-b: database operations"
echo "- data-processing: data processing pipeline"
echo "- tools/cli-util: CLI development utility"
echo ""

QUERIES=("database" "processing" "web" "data" "application")
READMES="test-readmes/*/readme.nix"

echo "Testing queries: ${QUERIES[*]}"
echo ""

# Test function for counting matches
count_matches() {
    local mode="$1"
    local query="$2"
    local count=0
    
    case "$mode" in
        "default")
            count=$(nix run ../../flakes/ck -- "$query" $READMES 2>/dev/null | wc -l || echo 0)
            ;;
        "case-insensitive")
            count=$(nix run ../../flakes/ck -- -i "$query" $READMES 2>/dev/null | wc -l || echo 0)
            ;;
        "semantic")
            count=$(nix run ../../flakes/ck -- --sem "$query" $READMES 2>/dev/null | wc -l || echo 0)
            ;;
        "hybrid")
            count=$(nix run ../../flakes/ck -- --hybrid "$query" $READMES 2>/dev/null | wc -l || echo 0)
            ;;
    esac
    
    echo "$count"
}

# Performance test function
test_performance() {
    local mode="$1"
    local query="$2"
    
    case "$mode" in
        "default")
            time nix run ../../flakes/ck -- "$query" $READMES >/dev/null 2>&1
            ;;
        "case-insensitive")
            time nix run ../../flakes/ck -- -i "$query" $READMES >/dev/null 2>&1
            ;;
        "semantic")
            time nix run ../../flakes/ck -- --sem "$query" $READMES >/dev/null 2>&1
            ;;
        "hybrid")
            time nix run ../../flakes/ck -- --hybrid "$query" $READMES >/dev/null 2>&1
            ;;
    esac
}

# Coverage Analysis
echo "=== COVERAGE ANALYSIS ==="
printf "%-20s %-12s %-12s %-12s %-12s %-12s\n" "Mode" "database" "processing" "web" "data" "application"
printf "%-20s %-12s %-12s %-12s %-12s %-12s\n" "--------------------" "--------" "----------" "---" "----" "-----------"

for mode in "default" "case-insensitive" "semantic" "hybrid"; do
    printf "%-20s " "$mode"
    for query in "${QUERIES[@]}"; do
        count=$(count_matches "$mode" "$query")
        printf "%-12s " "$count"
    done
    echo ""
done

echo ""
echo "=== DETAILED RESULTS FOR KEY QUERIES ==="

# Test specific examples for accuracy assessment
echo "Query: 'database' - Expected: project-b (exact match)"
echo "Default:"
nix run ../../flakes/ck -- "database" $READMES 2>/dev/null | head -3 || true

echo -e "\nHybrid:"
nix run ../../flakes/ck -- --hybrid "database" $READMES 2>/dev/null | head -5 || true

echo -e "\nQuery: 'user interface' (conceptual) - Expected: web app projects"
echo "Hybrid:"
nix run ../../flakes/ck -- --hybrid "user interface" $READMES 2>/dev/null | head -5 || true

echo ""
echo "=== PERFORMANCE ANALYSIS ==="
echo "Testing performance for 'database' query:"

for mode in "default" "case-insensitive" "semantic" "hybrid"; do
    echo -n "Mode: $mode - "
    test_performance "$mode" "database"
done

echo ""
echo "=== ANALYSIS COMPLETE ==="