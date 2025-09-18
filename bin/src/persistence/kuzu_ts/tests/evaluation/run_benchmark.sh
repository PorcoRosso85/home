#!/usr/bin/env bash

# Performance Benchmark Runner
# Executes the performance benchmark with proper error handling

echo "=== KuzuDB Performance Benchmark ==="
echo "Comparing npm:kuzu direct vs Worker implementation"
echo ""

# Run the benchmark
deno run \
  --allow-read \
  --allow-write \
  --allow-ffi \
  --allow-net \
  --allow-env \
  --unstable-ffi \
  --unstable-worker-options \
  performance_benchmark.ts

# Check exit code
if [ $? -eq 0 ]; then
  echo ""
  echo "✅ Benchmark completed successfully"
  echo "Check PERFORMANCE_BENCHMARK_RESULTS.md for detailed results"
else
  echo ""
  echo "❌ Benchmark failed"
  echo "Some implementations may have caused panics"
fi