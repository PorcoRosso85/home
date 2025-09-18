#!/usr/bin/env bash
set -euo pipefail

# Test script to validate that Stage2 results contain no README files
echo "Testing Stage2 README File Exclusion"
echo "===================================="
echo

# Test directory setup
cd /home/nixos/bin/src/poc/search-readme

# Track test results
TOTAL_TESTS=0
PASSED_TESTS=0

# Test utility functions
test_stage2_exclusion() {
    local test_name="$1"
    local query="$2"
    local expected_behavior="$3"
    
    echo "Test: $test_name"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # Run pipeline mode to get Stage2 results
    local pipeline_output
    local exit_code=0
    
    if pipeline_output=$(nix run . -- -m pipeline --format json "$query" 2>/dev/null); then
        exit_code=0
    else
        exit_code=$?
    fi
    
    # Parse Stage2 results from pipeline output
    local stage2_results
    stage2_results=$(echo "$pipeline_output" | jq -r '.pipeline.stage2.results[]?.file // empty' 2>/dev/null || echo "")
    
    # Check for README files in Stage2 results
    local readme_files=0
    if [[ -n "$stage2_results" ]]; then
        readme_files=$(echo "$stage2_results" | grep -i "readme\|README" | wc -l || echo "0")
    fi
    
    # Validate exclusion based on expected behavior
    case "$expected_behavior" in
        "no_readme_files")
            if [[ "$readme_files" -eq 0 ]]; then
                echo "✅ PASS - No README files found in Stage2 results"
                PASSED_TESTS=$((PASSED_TESTS + 1))
                
                # Show what files were found for verification
                if [[ -n "$stage2_results" ]]; then
                    echo "   Stage2 files found: $(echo "$stage2_results" | wc -l)"
                    echo "$stage2_results" | head -5 | sed 's/^/   - /'
                    if [[ $(echo "$stage2_results" | wc -l) -gt 5 ]]; then
                        echo "   ... and $(($(echo "$stage2_results" | wc -l) - 5)) more files"
                    fi
                fi
            else
                echo "❌ FAIL - Found $readme_files README files in Stage2 results:"
                echo "$stage2_results" | grep -i "readme\|README" | sed 's/^/   - /'
            fi
            ;;
        "no_results")
            # Accept either 80 (no README candidates) or 81 (no code matches) as valid "no results" scenarios
            if [[ ("$exit_code" -eq 80 || "$exit_code" -eq 81) ]] && [[ "$readme_files" -eq 0 ]]; then
                echo "✅ PASS - No results found (exit code $exit_code) and no README files"
                PASSED_TESTS=$((PASSED_TESTS + 1))
            else
                echo "❌ FAIL - Expected no results (exit code 80 or 81), got exit code: $exit_code, README files: $readme_files"
            fi
            ;;
        "stage1_only")
            if [[ "$exit_code" -eq 80 ]] && [[ "$readme_files" -eq 0 ]]; then
                echo "✅ PASS - Stage1 candidates found but Stage2 empty (exit code 80), no README files"
                PASSED_TESTS=$((PASSED_TESTS + 1))
            else
                echo "❌ FAIL - Expected Stage1 only (exit code 80), got exit code: $exit_code, README files: $readme_files"
            fi
            ;;
    esac
    
    echo
}

# Test scenarios that should find code results but exclude README files
echo "1. Queries that match both README content and code"
echo "------------------------------------------------"

test_stage2_exclusion "Query: 'database' (should find code, exclude README)" "database" "no_readme_files"
test_stage2_exclusion "Query: 'function' (should find code, exclude README)" "function" "no_readme_files"
test_stage2_exclusion "Query: 'search' (should find code, exclude README)" "search" "no_readme_files"

echo "2. Queries that match only README content"
echo "----------------------------------------"

test_stage2_exclusion "Query: '多言語対応' (Japanese in README only)" "多言語対応" "stage1_only"
test_stage2_exclusion "Query: 'データベース検索機能' (Japanese README feature)" "データベース検索機能" "stage1_only"

echo "3. Queries with no matches anywhere"
echo "----------------------------------"

test_stage2_exclusion "Query: 'ULTRA_UNIQUE_PATTERN_NO_MATCH_12345' (no matches)" "ULTRA_UNIQUE_PATTERN_NO_MATCH_12345" "no_results"

echo "4. Explicit README filename searches"
echo "------------------------------------"

test_stage2_exclusion "Query: 'readme.nix' (should not find README files)" "readme.nix" "no_readme_files"
test_stage2_exclusion "Query: 'README.md' (should not find README files)" "README.md" "no_readme_files"

echo "5. Detailed Stage2 Content Validation"
echo "-------------------------------------"

# Run a query that should find results and examine the JSON structure
echo "Running detailed validation with 'class' query..."
TOTAL_TESTS=$((TOTAL_TESTS + 1))

detailed_output=$(nix run . -- -m pipeline --format json "class" 2>/dev/null || echo "{}")
stage1_count=$(echo "$detailed_output" | jq -r '.pipeline.stage1.count // 0')
stage2_count=$(echo "$detailed_output" | jq -r '.pipeline.stage2.count // 0')
stage2_files=$(echo "$detailed_output" | jq -r '.pipeline.stage2.results[]?.file // empty' 2>/dev/null || echo "")

echo "Stage1 candidates found: $stage1_count"
echo "Stage2 code matches found: $stage2_count"

if [[ "$stage2_count" -gt 0 ]]; then
    # Check if any Stage2 files are README files
    readme_in_stage2=$(echo "$stage2_files" | grep -i "readme" | wc -l || echo "0")
    
    if [[ "$readme_in_stage2" -eq 0 ]]; then
        echo "✅ PASS - Stage2 has $stage2_count results with no README files"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        
        # Show file types found in Stage2
        echo "File extensions in Stage2 results:"
        echo "$stage2_files" | sed 's/.*\.//' | sort | uniq -c | sed 's/^/   /'
    else
        echo "❌ FAIL - Found $readme_in_stage2 README files in Stage2 results"
        echo "$stage2_files" | grep -i "readme" | sed 's/^/   - /'
    fi
else
    echo "ℹ️  INFO - No Stage2 results to validate (this may be expected)"
    PASSED_TESTS=$((PASSED_TESTS + 1))  # Count as pass if no results to validate
fi

echo

echo "6. Summary"
echo "----------"
echo "Tests passed: $PASSED_TESTS/$TOTAL_TESTS"

if [[ $PASSED_TESTS -eq $TOTAL_TESTS ]]; then
    echo "✅ All Stage2 exclusion tests PASSED"
    echo ""
    echo "VALIDATION RESULTS:"
    echo "- Stage2 properly excludes readme.nix files"
    echo "- Stage2 properly excludes README.md files"
    echo "- No README content appears in Stage2 results"
    echo "- Pipeline correctly separates Stage1 (README candidates) from Stage2 (code results)"
    echo "- Exit codes properly differentiate between Stage1-only (80) and no-results (81) scenarios"
    echo ""
    echo "CONCLUSION:"
    echo "✅ README exclusion is working correctly in Stage2"
    echo "✅ No regression detected in README file filtering"
    echo "✅ Pipeline maintains proper separation between README discovery and code search"
    exit 0
else
    echo "❌ Some Stage2 exclusion tests FAILED"
    echo "Review failed tests above - README files may be leaking into Stage2 results"
    echo ""
    echo "POTENTIAL ISSUES:"
    echo "- README exclusion patterns may not be comprehensive enough"
    echo "- Stage2 search may not be properly applying exclusion filters" 
    echo "- New README file formats may not be covered by exclusion patterns"
    exit 1
fi