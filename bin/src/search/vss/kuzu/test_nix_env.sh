#!/usr/bin/env bash
# Test VSS in Nix environment

echo "=== VSS Nix Environment Test ==="
echo
echo "Testing NumPy and dependencies in Nix environment..."
echo

# Change to VSS directory
cd "$(dirname "$0")"

# Run a simple Python test to check imports
nix develop -c python3 -c "
import sys
print('Python path:', sys.executable)
print()

try:
    import numpy as np
    print('✓ NumPy imported successfully')
    print(f'  Version: {np.__version__}')
except ImportError as e:
    print(f'✗ NumPy import failed: {e}')
    sys.exit(1)

try:
    import jsonschema
    print('✓ jsonschema imported successfully')
except ImportError as e:
    print(f'✗ jsonschema import failed: {e}')
    sys.exit(1)

try:
    import kuzu
    print('✓ kuzu imported successfully')
except ImportError as e:
    print(f'✗ kuzu import failed: {e}')
    sys.exit(1)

print()
print('All dependencies are available in Nix environment!')
"

echo
echo "To run VSS tests, use:"
echo "  nix run .#test"
echo
echo "Or enter development shell:"
echo "  nix develop"
echo "  pytest tests/"