#!/usr/bin/env bash
# テスト実行結果をDuckDBに永続化

DB_FILE="${1:-test_results.db}"
shift

echo "🦆 Running tests with DuckDB persistence to: $DB_FILE"
echo ""

# パフォーマンス計測を有効にしてテスト実行し、JSON行のみをDuckDBに保存
PYTEST_REALTIME=1 nix run .#test -- --capture=no -p no:xdist "$@" 2>&1 | \
grep '^{.*"level".*}' | \
nix run nixpkgs#duckdb -- "$DB_FILE" -c "
-- テーブル作成（既存の場合は追記）
CREATE TABLE IF NOT EXISTS test_logs AS 
SELECT CURRENT_TIMESTAMP as inserted_at, * 
FROM read_json_auto('/dev/stdin', format='newline_delimited')
WHERE 1=0;  -- 空のテーブルを作成

-- データ挿入
INSERT INTO test_logs 
SELECT CURRENT_TIMESTAMP as inserted_at, * 
FROM read_json_auto('/dev/stdin', format='newline_delimited');

-- 挿入結果を表示
SELECT COUNT(*) as logs_inserted FROM test_logs WHERE inserted_at >= CURRENT_TIMESTAMP - INTERVAL '1 minute';
"

echo ""
echo "✅ Logs saved to $DB_FILE"
echo ""
echo "📊 Quick analysis:"
nix run nixpkgs#duckdb -- "$DB_FILE" -c "
SELECT 
    event,
    COUNT(*) as count,
    AVG(duration_seconds) as avg_duration
FROM test_logs
WHERE inserted_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour'
GROUP BY event
ORDER BY event;
"