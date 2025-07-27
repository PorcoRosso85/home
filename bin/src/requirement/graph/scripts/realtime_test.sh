#!/usr/bin/env bash
# リアルタイムテスト実行時間表示

if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [pytest options]"
    echo ""
    echo "Run tests with real-time execution display"
    echo "Example:"
    echo "  $0                    # Run all tests"
    echo "  $0 -k test_name       # Run specific test"
    echo "  $0 -m e2e             # Run E2E tests only"
    exit 0
fi

echo "🕐 Running tests with real-time display..."
echo "Note: Parallel execution is disabled for accurate timing"
echo ""

PYTEST_REALTIME=1 nix run .#test -- --capture=no -p no:xdist "$@"