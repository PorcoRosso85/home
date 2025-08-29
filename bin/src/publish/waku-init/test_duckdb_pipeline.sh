#!/usr/bin/env bash

# Step 1: Generate test logs
echo "Generating test logs..."
curl -X GET "https://stg-waku-init.trst.workers.dev/generate-logs?count=25" \
  -H "X-Staging-Access-Key: test-staging-secret-2024" -s

# Step 2: Capture wrangler tail output (wait for logs to appear)
echo "Capturing logs from wrangler tail..."
sleep 2

# Run wrangler tail without nix develop noise, capture one event
nix develop --quiet -c bash -c "wrangler tail stg-waku-init --format json 2>/dev/null | head -1" > captured_logs.json

# Step 3: Analyze with DuckDB
echo "Analyzing with DuckDB..."
nix shell nixpkgs#duckdb -c duckdb << 'EOF'
-- Load the captured logs
CREATE TABLE tail_data AS SELECT * FROM read_json_auto('captured_logs.json');

-- Parse nested structure
WITH parsed_logs AS (
  SELECT unnest(logs) as log_entry FROM tail_data
),
extracted AS (
  SELECT 
    log_entry.level as log_level,
    log_entry.timestamp,
    log_entry.message[1] as raw_message
  FROM parsed_logs
),
parsed AS (
  SELECT 
    log_level,
    timestamp,
    json_extract_string(raw_message, '$.type') as log_type,
    CAST(json_extract(raw_message, '$.index') AS INTEGER) as idx,
    json_extract_string(raw_message, '$.message') as message,
    CAST(json_extract(raw_message, '$.data.batch') AS INTEGER) as batch,
    CAST(json_extract(raw_message, '$.data.random') AS DOUBLE) as random_val
  FROM extracted
  WHERE raw_message LIKE '%test_log%'
)
SELECT 
  'Summary:' as report,
  COUNT(*) as total_logs,
  MIN(idx) as first_index,
  MAX(idx) as last_index,
  COUNT(DISTINCT batch) as total_batches,
  ROUND(AVG(random_val), 3) as avg_random
FROM parsed;

-- Show batch distribution
WITH parsed_logs AS (
  SELECT unnest(logs) as log_entry FROM tail_data
),
batch_data AS (
  SELECT 
    CAST(json_extract(log_entry.message[1], '$.data.batch') AS INTEGER) as batch,
    COUNT(*) as count
  FROM parsed_logs
  WHERE log_entry.message[1] LIKE '%test_log%'
  GROUP BY batch
)
SELECT 
  'Batch ' || batch as batch_id,
  count as log_count
FROM batch_data
ORDER BY batch;
EOF

echo "Pipeline complete!"