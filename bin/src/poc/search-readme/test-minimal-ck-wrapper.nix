# 最小限ckラッパーの仕様テスト【RED】
# このテストは意図的に失敗するように設計されている
{
  pkgs,
  self,
  system,
  ck ? pkgs.ck or (throw "ck package not available")
}:

pkgs.runCommand "minimal-ck-wrapper-spec-test"
{
  buildInputs = with pkgs; [ jq bash coreutils ck ];
  NIX_CONFIG = "experimental-features = nix-command flakes";
} ''
set -euo pipefail

echo "🧪 Testing minimal ck wrapper specification..."

# Create test workspace
TEST_WORKSPACE=$(mktemp -d)
cd "$TEST_WORKSPACE"

# Copy test data
cp -r ${self}/test-readmes ./

# Test results tracking
TEST_RESULTS="[]"
FAILED_TESTS=0

add_test_result() {
  local name="$1"
  local result="$2"
  local details="''${3:-}"
  
  TEST_RESULTS=$(echo "$TEST_RESULTS" | jq ". + [{name: \"$name\", result: \"$result\", details: \"$details\"}]")
  
  if [[ "$result" == "fail" ]]; then
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo "❌ $name: FAILED - $details"
  else
    echo "✅ $name: PASSED"
  fi
}

# 仕様1: 最小限ckラッパーが存在する（50行以下）
echo "Spec 1: Minimal ck wrapper exists (≤50 lines)"
if nix build ${self}#packages.${system}.minimal-ck-wrapper -o minimal-wrapper 2>/dev/null; then
  WRAPPER_LINES=$(wc -l < minimal-wrapper/bin/search-readme)
  if [ "$WRAPPER_LINES" -le 50 ]; then
    add_test_result "minimal-wrapper-size" "pass"
  else
    add_test_result "minimal-wrapper-size" "fail" "Wrapper has $WRAPPER_LINES lines (expected ≤50)"
  fi
else
  add_test_result "minimal-wrapper-size" "fail" "minimal-ck-wrapper package does not exist"
fi

# 仕様2: ckツールへの純粋な委譲（独自検索ロジックなし）
echo "Spec 2: Pure ck delegation (no custom search logic)"
if WRAPPER_SOURCE=$(cat minimal-wrapper/bin/search-readme 2>/dev/null); then
  if echo "$WRAPPER_SOURCE" | grep -q "ck.*\$@" && ! echo "$WRAPPER_SOURCE" | grep -qE "(jq.*search|scoring|bm25)"; then
    add_test_result "pure-ck-delegation" "pass"
  else
    add_test_result "pure-ck-delegation" "fail" "Wrapper contains custom search logic instead of pure ck delegation"
  fi
else
  add_test_result "pure-ck-delegation" "fail" "Cannot read wrapper source"
fi

# 仕様3: SCOPEオプション（--scope readme/code/all）
echo "Spec 3: SCOPE option support"
for scope in readme code all; do
  if OUTPUT=$(./minimal-wrapper/bin/search-readme --scope "$scope" "test" 2>/dev/null); then
    if echo "$OUTPUT" | jq -e '.[0].scope' >/dev/null 2>&1; then
      ACTUAL_SCOPE=$(echo "$OUTPUT" | jq -r '.[0].scope')
      if [ "$ACTUAL_SCOPE" = "$scope" ]; then
        add_test_result "scope-$scope" "pass"
      else
        add_test_result "scope-$scope" "fail" "Expected scope '$scope', got '$ACTUAL_SCOPE'"
      fi
    else
      add_test_result "scope-$scope" "fail" "Output missing scope field"
    fi
  else
    add_test_result "scope-$scope" "fail" "Command failed for scope '$scope'"
  fi
done

# 仕様4: パイプラインモード（README→コード2段階検索）
echo "Spec 4: Pipeline mode (README→code 2-stage search)"
if PIPELINE_OUTPUT=$(./minimal-wrapper/bin/search-readme --mode pipeline "framework" 2>/dev/null); then
  if echo "$PIPELINE_OUTPUT" | jq -e '.stage1' >/dev/null 2>&1 && \
     echo "$PIPELINE_OUTPUT" | jq -e '.stage2' >/dev/null 2>&1 && \
     echo "$PIPELINE_OUTPUT" | jq -e '.stage1[0].scope == "readme"' >/dev/null 2>&1 && \
     echo "$PIPELINE_OUTPUT" | jq -e '.stage2[0].scope == "code"' >/dev/null 2>&1; then
    add_test_result "pipeline-mode" "pass"
  else
    add_test_result "pipeline-mode" "fail" "Pipeline output missing stage1/stage2 or incorrect scopes"
  fi
else
  add_test_result "pipeline-mode" "fail" "Pipeline mode command failed"
fi

# 仕様5: ckの真のBM25使用（Tantivyバックエンド）
echo "Spec 5: Actual ck BM25 usage (Tantivy backend)"
if BM25_OUTPUT=$(./minimal-wrapper/bin/search-readme --mode hybrid "test" 2>/dev/null); then
  # ckのhybridモードはTantivy+BM25を使用するので、scoreフィールドが存在するはず
  if echo "$BM25_OUTPUT" | jq -e '.[0].score' >/dev/null 2>&1; then
    SCORE=$(echo "$BM25_OUTPUT" | jq -r '.[0].score')
    # ckのBM25スコアは数値で、jqベースのヒューリスティック（通常10の倍数）とは異なる
    if echo "$SCORE" | grep -qE '^[0-9]+\.[0-9]+$' && [ "${SCORE%.*}" != "${SCORE#*.0}" ]; then
      add_test_result "true-bm25" "pass"
    else
      add_test_result "true-bm25" "fail" "Score format suggests jq-based heuristics, not Tantivy BM25"
    fi
  else
    add_test_result "true-bm25" "fail" "BM25 output missing score field"
  fi
else
  add_test_result "true-bm25" "fail" "BM25 mode command failed"
fi

# Generate final test report
TOTAL_TESTS=$(echo "$TEST_RESULTS" | jq 'length')
PASSED_TESTS=$((TOTAL_TESTS - FAILED_TESTS))

echo ""
echo "📊 Test Summary:"
echo "Total tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"

# Generate JSON report
cat > "$out" <<EOF
{
  "status": "$([ $FAILED_TESTS -eq 0 ] && echo "success" || echo "failure")",
  "tests": $TEST_RESULTS,
  "summary": {
    "total": $TOTAL_TESTS,
    "passed": $PASSED_TESTS,
    "failed": $FAILED_TESTS
  },
  "specification": {
    "description": "Minimal ck wrapper with SCOPE and pipeline functionality",
    "target_lines": 50,
    "required_features": ["scope_option", "pipeline_mode", "pure_ck_delegation", "true_bm25"]
  }
}
EOF

echo "✨ Minimal ck wrapper specification test completed"

# Fail if any tests failed (this makes it a proper RED test)
if [ $FAILED_TESTS -gt 0 ]; then
  echo "❌ Specification test FAILED - implementation needed"
  exit 1
else
  echo "✅ Specification test PASSED - minimal wrapper correctly implemented"
fi
''