#!/usr/bin/env bash

# Simple one-liner pipeline: wrangler tail -> DuckDB
nix develop --quiet -c bash -c "timeout 3 wrangler tail stg-waku-init --format json 2>/dev/null | head -1" | \
nix --quiet shell nixpkgs#duckdb -c duckdb -json -c "
WITH parsed AS (
  SELECT unnest(logs) as log FROM read_json_auto('/dev/stdin')
),
extracted AS (
  SELECT 
    CAST(json_extract(log.message[1], '$.index') AS INTEGER) as idx,
    CAST(json_extract(log.message[1], '$.data.batch') AS INTEGER) as batch,
    CAST(json_extract(log.message[1], '$.data.random') AS DOUBLE) as random_val
  FROM parsed
  WHERE log.message[1] LIKE '%test_log%'
)
SELECT 
  COUNT(*) as logs,
  MIN(idx) as first_idx,
  MAX(idx) as last_idx,
  COUNT(DISTINCT batch) as batches,
  ROUND(AVG(random_val), 3) as avg_random
FROM extracted;
"