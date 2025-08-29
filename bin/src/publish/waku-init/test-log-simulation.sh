#!/bin/bash

echo "=== Log-Based Architecture Local Simulation ==="
echo ""
echo "1. Creating test directories..."
mkdir -p logs archive

echo ""
echo "2. Simulating form submissions (creating logs)..."

# Simulate 10 form submissions
for i in {1..10}; do
  cat >> logs/$(date +%Y-%m-%d).jsonl << EOF
{"type":"form_submission","version":1,"timestamp":$(date +%s%3N),"data":{"id":"test-$i","name":"User $i","email":"user$i@example.com","subject":"Test $i","message":"This is test message $i","submittedAt":"$(date -Iseconds)"}}
EOF
  echo "   ✓ Logged submission $i"
  sleep 0.1
done

echo ""
echo "3. Checking log files..."
echo "   Log files created:"
ls -la logs/

echo ""
echo "4. Simulating batch processing..."
BATCH_FILE="archive/batch-$(date +%s).jsonl"
cat logs/*.jsonl > "$BATCH_FILE"
echo "   ✓ Batched to: $BATCH_FILE"
echo "   Total lines: $(wc -l < $BATCH_FILE)"

echo ""
echo "5. Testing DuckDB query on JSONL..."
echo "   Run this in DuckDB:"
echo ""
echo "   SELECT "
echo "     json_extract(data, '$.email') as email,"
echo "     COUNT(*) as submissions"
echo "   FROM read_json_auto('$BATCH_FILE')"
echo "   GROUP BY email;"
echo ""

echo "6. Quick analysis with jq:"
echo "   Unique emails:"
cat "$BATCH_FILE" | jq -r '.data.email' | sort -u

echo ""
echo "   Submissions by subject:"
cat "$BATCH_FILE" | jq -r '.data.subject' | sort | uniq -c

echo ""
echo "✅ Simulation complete! Check ./logs/ and ./archive/ directories"