# Stage2 README Exclusion Test

## Overview

This test suite validates that Stage2 results contain no README files, ensuring the exclusion fix works correctly and prevents regression.

## Test Implementation

### Files Created

1. **`test-stage2-exclusion.sh`** - Comprehensive test suite
2. **`test-readme-exclusion-simple.sh`** - Focused simple test  
3. **Updated `test-pipeline-default.sh`** - Integrated exclusion tests

### Test Approach

The test validation works by:

1. **Running pipeline mode** with queries known to match README content
2. **Parsing Stage2 JSON results** using `jq` to extract file paths 
3. **Asserting no README files** by checking for paths containing "readme.nix" or "README.md"
4. **Testing multiple scenarios**:
   - Queries that match both README and code content
   - Queries that match only README content  
   - Queries with no matches anywhere
   - Direct filename searches for README files

### Key Validation Logic

```bash
# Extract Stage2 file paths from pipeline JSON output
stage2_files=$(echo "$pipeline_output" | jq -r '.pipeline.stage2.results[]?.file // empty')

# Count README files in Stage2 results 
readme_count=$(echo "$stage2_files" | grep -i "readme" | wc -l || echo "0")

# Assert no README files found
if [[ "$readme_count" -eq 0 ]]; then
    echo "✅ PASS - No README files in Stage2 results"
else
    echo "❌ FAIL - Found $readme_count README files in Stage2"
fi
```

### Test Scenarios

1. **Content Queries** (`database`, `function`, `search`)
   - Should find code results but exclude README files
   - Validates that exclusion works for queries matching both types

2. **README-only Content** (Japanese text in test READMEs)
   - Should find Stage1 candidates but no Stage2 results (exit code 80)
   - Validates pipeline correctly separates README discovery from code search

3. **No Match Queries** (`ULTRA_UNIQUE_PATTERN_NO_MATCH_12345`)
   - Should fail with appropriate exit codes (80 or 81)
   - Validates no README leakage even in failure scenarios

4. **Filename Searches** (`readme.nix`, `README.md`)
   - Should not return README files in Stage2 even when directly searched
   - Validates exclusion patterns work for explicit filename queries

### Integration with Existing Test Suite

The README exclusion validation has been integrated into `test-pipeline-default.sh` as:

- **Section 3: Stage2 README Exclusion Validation**
- Adds 3 additional test cases to the existing exit code tests
- Updates success criteria to include README exclusion verification
- Maintains existing test structure and reporting format

### Expected Results

**Success Criteria:**
- Stage2 results contain 0 README files across all test scenarios
- Pipeline properly separates Stage1 (README candidates) from Stage2 (code results)  
- Exit codes correctly differentiate between Stage1-only (80) and no-results (81/80)
- No regression in README file filtering

**Failure Indicators:**
- Any README file paths found in Stage2 JSON results
- Inconsistent exit code behavior
- README content appearing in code search results

### Running the Tests

```bash
# Run comprehensive test suite
./test-stage2-exclusion.sh

# Run simple focused test
./test-readme-exclusion-simple.sh  

# Run integrated pipeline tests (includes README exclusion)
./test-pipeline-default.sh
```

### Test Command Integration

The test can be integrated into CI/CD pipelines or development workflows:

```bash
# Exit code 0 = all tests pass, exclusion working
# Exit code 1 = test failures, potential README leakage
./test-stage2-exclusion.sh && echo "README exclusion validated" || echo "README exclusion failed"
```

## Technical Details

### Exclusion Implementation

The Stage2 search uses these exclusion patterns in `flake.nix`:
```bash
ck --json --sem --exclude "**/readme.nix" --exclude "**/README.md" --exclude "*.nix" "$query" "$candidate_dir"
```

### JSON Structure Validation

Tests parse the pipeline JSON structure:
```json
{
  "pipeline": {
    "stage1": {
      "candidates": [...],
      "count": N
    },
    "stage2": {
      "results": [...],  // ← This array must contain no README files
      "count": M
    }
  }
}
```

### Error Handling

Tests handle various pipeline failure modes:
- Stage1 failure (no README candidates found)
- Stage2 failure (no code matches found)  
- Complete pipeline failure (invalid queries)
- All scenarios validate no README leakage occurs

## Conclusion

This test suite provides comprehensive validation that:
1. ✅ README exclusion is working correctly in Stage2
2. ✅ No regression can occur in README file filtering
3. ✅ Pipeline maintains proper separation between README discovery and code search
4. ✅ Exit codes and error handling work as expected

The automated validation prevents README files from appearing in code search results, maintaining the integrity of the two-stage search pipeline.