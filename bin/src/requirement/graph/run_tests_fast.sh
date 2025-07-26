#!/usr/bin/env bash
# 高速テスト実行スクリプト

echo "=== Fast Test Runner ==="
echo "Running tests with optimizations..."

# 並列実行オプション
PARALLEL_OPTS="-n auto --dist loadscope"

# マーカーオプション（E2Eテストをスキップ）
MARKER_OPTS="-m 'not e2e'"

# 基本的なテストオプション
BASE_OPTS="-v --tb=short"

# 実行コマンドの選択
if [ "$1" == "all" ]; then
    echo "Running all tests in parallel..."
    nix run .#test -- $BASE_OPTS $PARALLEL_OPTS
elif [ "$1" == "unit" ]; then
    echo "Running unit tests only..."
    nix run .#test -- $BASE_OPTS $MARKER_OPTS $PARALLEL_OPTS
elif [ "$1" == "e2e" ]; then
    echo "Running E2E tests only..."
    nix run .#test -- $BASE_OPTS -m e2e
elif [ "$1" == "single" ]; then
    echo "Running specific test: $2"
    nix run .#test -- $BASE_OPTS "$2"
else
    echo "Usage: $0 [all|unit|e2e|single <test_path>]"
    echo ""
    echo "Examples:"
    echo "  $0 all                                    # Run all tests in parallel"
    echo "  $0 unit                                   # Run non-E2E tests in parallel"
    echo "  $0 e2e                                    # Run E2E tests only"
    echo "  $0 single test_performance_comparison.py  # Run specific test file"
    echo ""
    echo "Current optimization status:"
    echo "  ✓ Parallel execution enabled (pytest-xdist)"
    echo "  ✓ Test markers for filtering (unit/e2e)"
    echo "  ✓ Optimized subprocess handling in conftest.py"
    echo "  ⚠ In-memory DB migration pending"
fi