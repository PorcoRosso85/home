#!/usr/bin/env bash
# Test script for select-project

set -euo pipefail

echo "Testing select-project script..."
echo

# Test 1: Help message
echo "Test 1: Help message"
./select-project --help
echo

# Test 2: Test with debug mode
echo "Test 2: Running with debug mode (will open fzf - press ESC to cancel)"
echo "Expected: Should exit with code 1 when cancelled"
if DEBUG=1 ./select-project; then
  echo "✗ Expected non-zero exit code when cancelled"
else
  echo "✓ Correctly exited with code $? when cancelled"
fi
echo

# Test 3: Test with custom root directory
echo "Test 3: Test with custom root directory"
echo "Using root: /home/nixos/bin"
echo "(Press ESC to cancel or select a project)"
if result=$(./select-project --root /home/nixos/bin); then
  echo "✓ Selected project: $result"
else
  echo "✓ Cancelled selection"
fi
echo

# Test 4: Test return value capture
echo "Test 4: Demonstrating usage in a script"
cat << 'EOF'
#!/bin/bash
# Example usage in another script:
if project_dir=$(./select-project); then
  echo "Launching Claude in: $project_dir"
  cd "$project_dir"
  # ... launch Claude ...
else
  echo "No project selected"
  exit 1
fi
EOF

echo
echo "All tests completed!"