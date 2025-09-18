# 簡素テストハーネス仕様【CHARACTERIZE】
# 最小限ckラッパー用の30行以下テストハーネス仕様
{
  pkgs,
  self,
  system
}:

pkgs.runCommand "simple-test-harness-specification"
{
  buildInputs = with pkgs; [ jq bash coreutils ];
  NIX_CONFIG = "experimental-features = nix-command flakes";
} ''
set -euo pipefail

echo "🔧 Defining simple test harness specification..."

# 仕様: 簡素テストハーネスの要件
SPEC_REQUIREMENTS=(
  "Only test minimal-ck-wrapper package"
  "Basic functionality: SCOPE options (readme/code/all)"
  "Basic functionality: Pipeline mode" 
  "Basic functionality: CK delegation"
  "Error handling: Invalid arguments"
  "Line count: ≤30 lines total"
  "No testing of deleted packages (default, search-optimized)"
  "No benchmark testing"
  "No performance measurement"
  "No complex JSON validation"
)

# 仕様: 簡素テスト構造
cat > simple_test_structure.md << 'EOF'
# Simplified Test Harness Structure (≤30 lines)

## Test 1: minimal-ck-wrapper build success (5 lines)
- nix build minimal-ck-wrapper
- Verify executable exists

## Test 2: Basic SCOPE functionality (10 lines) 
- Test --scope readme
- Test --scope code
- Test --scope all
- Basic JSON output validation

## Test 3: Pipeline mode functionality (8 lines)
- Test --mode pipeline
- Verify stage1/stage2 structure
- Basic error handling

## Test 4: Error handling (5 lines)
- Test invalid arguments rejection
- Test missing query handling

## Test 5: Success report (2 lines)
- Generate simple JSON report
- Exit with success status
EOF

# 仕様: 削除する過剰テスト項目
REMOVAL_TARGETS=(
  "default package testing"
  "search-optimized package testing"
  "Benchmark functionality tests"
  "Performance timing with bc calculations"
  "Complex test data creation"
  "Comprehensive error testing beyond basic cases"
  "Flake metadata validation"
  "Multi-package build coordination"
)

echo ""
echo "📋 Simple test harness specification:"
echo "Target: ≤30 lines (vs current 246 lines)"
echo "Focus: minimal-ck-wrapper ONLY"

echo ""
echo "✅ Required test coverage:"
for req in "''${SPEC_REQUIREMENTS[@]}"; do
  echo "  • $req"
done

echo ""
echo "🗑️  Removing excessive tests:"
for target in "''${REMOVAL_TARGETS[@]}"; do
  echo "  ❌ $target"
done

# 仕様書生成
cat > "$out" <<EOF
{
  "specification": {
    "name": "simple-test-harness",
    "max_lines": 30,
    "target_packages": ["minimal-ck-wrapper"],
    "excluded_packages": ["default", "search-optimized", "search-report"],
    "required_tests": $(printf '%s\n' "''${SPEC_REQUIREMENTS[@]}" | jq -R . | jq -s .),
    "removed_features": $(printf '%s\n' "''${REMOVAL_TARGETS[@]}" | jq -R . | jq -s .),
    "test_structure": {
      "build_test": 5,
      "scope_test": 10, 
      "pipeline_test": 8,
      "error_test": 5,
      "report_test": 2,
      "total_estimated": 30
    }
  },
  "validation": {
    "passes_if": "test harness ≤30 lines AND tests only minimal-ck-wrapper",
    "fails_if": "tests deleted packages OR >30 lines OR includes benchmarks"
  }
}
EOF

echo "✨ Simple test harness specification completed"
echo "📄 Specification saved to output"
''