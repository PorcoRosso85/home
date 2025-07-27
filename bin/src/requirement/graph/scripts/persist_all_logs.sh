#!/usr/bin/env bash
# すべてのテスト出力（テキスト＋JSON）をDuckDBに永続化

DB_FILE="${1:-test_all_logs.db}"
shift

echo "🦆 Persisting ALL test output to: $DB_FILE"
echo ""

# すべての出力を永続化
nix run .#test -- "$@" 2>&1 | nix run nixpkgs#duckdb -- "$DB_FILE" -c "
-- raw_logsテーブルに全行を保存
CREATE TABLE IF NOT EXISTS raw_logs (
    line_no BIGINT,
    raw_text VARCHAR,
    line_type VARCHAR,
    inserted_at TIMESTAMPTZ
);

-- 新しいデータを挿入
INSERT INTO raw_logs
SELECT 
    (SELECT COALESCE(MAX(line_no), 0) FROM raw_logs) + ROW_NUMBER() OVER () as line_no,
    column0 as raw_text,
    CASE 
        WHEN column0 LIKE '{%}' AND column0 LIKE '%\"level\"%' THEN 'json'
        WHEN column0 LIKE '====%' THEN 'pytest_header'
        WHEN column0 LIKE 'PASSED%' OR column0 LIKE 'FAILED%' THEN 'pytest_result'
        ELSE 'text'
    END as line_type,
    CURRENT_TIMESTAMP as inserted_at
FROM read_csv('/dev/stdin', delim='\0', header=false);

-- 挿入結果を表示
SELECT 
    line_type,
    COUNT(*) as lines
FROM raw_logs 
WHERE inserted_at >= CURRENT_TIMESTAMP - INTERVAL '1 minute'
GROUP BY line_type;
"

echo ""
echo "✅ All output saved to $DB_FILE"
echo ""
echo "📊 Example queries:"
echo "  - All warnings: SELECT * FROM raw_logs WHERE raw_text LIKE '%WARNING%';"
echo "  - JSON events: SELECT json(raw_text) FROM raw_logs WHERE line_type = 'json';"
echo "  - Test results: SELECT * FROM raw_logs WHERE line_type = 'pytest_result';"