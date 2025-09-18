#!/bin/bash
# Concurrent write stress test for POSIX locking mechanism

# Setup
TEST_FILE="test_concurrent.txt"
rm -f $TEST_FILE
export APPEND_FILE=$TEST_FILE

# Load the locking mechanism
source ./lib/posix_lock.sh

echo "=== POSIX Lock Concurrent Write Test ==="
echo ""

# Test 1: Multiple processes writing simultaneously
echo "Test 1: 10 processes × 10 writes each"
echo "Starting concurrent writes..."

# Launch 10 processes, each writing 10 times
for i in {1..10}; do
    (
        for j in {1..10}; do
            safe_append "Process $i, Write $j, PID $$"
        done
    ) &
done

# Wait for all background processes to complete
wait

# Verify results
echo "Test completed."
echo "Expected lines: 100"
echo "Actual lines: $(wc -l < $TEST_FILE)"
echo ""

# Test 2: High-frequency concurrent writes
echo "Test 2: Rapid concurrent writes (20 processes × 5 writes)"
rm -f $TEST_FILE

for i in {1..20}; do
    (
        for j in {1..5}; do
            safe_append "Rapid test: Process $i, Write $j" 
        done
    ) &
done

wait

echo "Rapid test completed."
echo "Expected lines: 100"
echo "Actual lines: $(wc -l < $TEST_FILE)"
echo ""

# Test 3: Mixed content types
echo "Test 3: Mixed content stress test"
rm -f $TEST_FILE

# Different types of content being written concurrently
(
    for i in {1..20}; do
        safe_append "Type A: Simple text line $i"
    done
) &

(
    for i in {1..20}; do
        safe_append "Type B: Line with special chars !@#\$%^&*() - $i"
    done
) &

(
    for i in {1..20}; do
        echo "Type C: Multi-word content from stdin - $i" | safe_append_stdin
    done
) &

wait

echo "Mixed content test completed."
echo "Expected lines: 60"
echo "Actual lines: $(wc -l < $TEST_FILE)"
echo ""

# Data integrity check
echo "=== Data Integrity Check ==="
echo "Checking for incomplete lines..."
incomplete=$(grep -v -E '^.+$' $TEST_FILE | wc -l)
echo "Incomplete lines found: $incomplete"

echo "Checking line uniqueness..."
unique_lines=$(sort $TEST_FILE | uniq | wc -l)
total_lines=$(wc -l < $TEST_FILE)
echo "Total lines: $total_lines"
echo "Unique lines: $unique_lines"

if [ "$unique_lines" -eq "$total_lines" ]; then
    echo "✓ All lines are unique (no corruption detected)"
else
    echo "⚠ Duplicate lines found (possible write conflicts)"
fi

# Cleanup
echo ""
echo "Cleaning up test file..."
rm -f $TEST_FILE