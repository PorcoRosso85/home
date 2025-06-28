#!/bin/bash
# POSIX safe file appending - usage examples

echo "=== POSIX Safe File Appending - Usage Examples ==="
echo ""

# Environment setup
export APPEND_FILE="example_output.txt"
rm -f $APPEND_FILE

# Load the locking mechanism
source ./lib/posix_lock.sh

# Example 1: Basic appending
echo "1. Basic file appending:"
safe_append "First line of text"
safe_append "Second line of text"
safe_append "Third line with special chars: $@#!"
echo "   → 3 lines appended"
echo ""

# Example 2: Appending to specific file
echo "2. Appending to specific file:"
safe_append "Custom file line 1" "custom_output.txt"
safe_append "Custom file line 2" "custom_output.txt"
echo "   → 2 lines appended to custom_output.txt"
echo ""

# Example 3: Using stdin
echo "3. Appending from stdin:"
echo "Line from echo command" | safe_append_stdin
cat << EOF | safe_append_stdin
Multi-line content
from here document
with multiple lines
EOF
echo "   → Content from stdin appended"
echo ""

# Example 4: Concurrent appending simulation
echo "4. Simulating concurrent writes:"
for i in {1..5}; do
    safe_append "Sequential write $i" &
done
wait
echo "   → 5 concurrent writes completed"
echo ""

# Display results
echo "=== Output File Contents ==="
echo "File: $APPEND_FILE"
echo "Lines: $(wc -l < $APPEND_FILE)"
echo ""
echo "First 10 lines:"
head -10 $APPEND_FILE
echo ""

# Show custom file if it exists
if [ -f "custom_output.txt" ]; then
    echo "=== Custom Output File ==="
    echo "File: custom_output.txt"
    cat custom_output.txt
    echo ""
fi

# Cleanup
echo "=== Cleanup ==="
echo "Removing example files..."
rm -f $APPEND_FILE custom_output.txt