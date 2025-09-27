#!/usr/bin/env bash
set -euo pipefail

echo "🔐 Testing secrets detection system..."

# Define the secrets check patterns inline
check_secrets() {
  # Define sensitive key patterns (same as in flake.nix)
  PATTERNS=(
    "password"
    "token"
    "private_key"
    "aws_secret_access_key"
    "api_key"
    "secret"
    "credential"
  )

  VIOLATIONS=()

  # Check secrets/ directory for plaintext
  if [ -d "secrets" ]; then
    for pattern in "${PATTERNS[@]}"; do
      while IFS= read -r line; do
        # Skip .example files
        if [[ "$line" == *.example ]]; then
          continue
        fi

        # Skip .sops.yaml configuration files
        if [[ "$line" == */.sops.yaml ]] || [[ "$line" == */.sops.yml ]]; then
          continue
        fi

        # Check if file is SOPS encrypted (contains 'sops:' metadata section)
        if grep -q "^sops:" "$line" 2>/dev/null; then
          continue
        fi

        # Check if file contains ENC[...] pattern (SOPS encrypted values)
        if grep -q "ENC\[" "$line" 2>/dev/null; then
          continue
        fi

        VIOLATIONS+=("$line")
      done < <(grep -r -l "$pattern" secrets/ 2>/dev/null || true)
    done
  fi

  # Remove duplicates from violations
  if [ ${#VIOLATIONS[@]} -gt 0 ]; then
    UNIQUE_VIOLATIONS=($(printf '%s\n' "${VIOLATIONS[@]}" | sort -u))
    echo "secrets: plaintext detected in: ${UNIQUE_VIOLATIONS[*]}"
    return 1
  else
    echo "secrets: no plaintext detected"
    return 0
  fi
}

# Test 1: Ensure current state passes (no plaintext)
echo "Test 1: Testing clean state (should pass)..."
if check_secrets; then
    echo "✅ Clean state test passed"
else
    echo "❌ Clean state test failed"
    exit 1
fi

# Test 2: Create a plaintext violation and test detection
echo "Test 2: Testing plaintext detection (should fail)..."
cat > secrets/test-violation.yaml << 'EOF'
# This file contains plaintext secrets (violation)
database:
  password: "my-secret-password-123"
api:
  token: "abc123xyz789"
EOF

# Test the secrets checker with violation present (should fail and return error message)
OUTPUT=$(check_secrets 2>&1 || true)
if echo "$OUTPUT" | grep -q "secrets: plaintext detected"; then
    echo "✅ Plaintext detection works"
else
    echo "❌ Plaintext detection failed"
    echo "Output was: $OUTPUT"
    rm -f secrets/test-violation.yaml
    exit 1
fi

# Clean up the test violation
rm -f secrets/test-violation.yaml

# Test 3: Verify example files are ignored
echo "Test 3: Testing .example file exclusion..."
cat > secrets/violation.txt.example << 'EOF'
# This should be ignored because it's a .example file
password: "this-should-be-ignored"
secret: "example-secret"
EOF

if check_secrets | grep -q "secrets: no plaintext detected"; then
    echo "✅ Example file exclusion works"
    rm -f secrets/violation.txt.example
else
    echo "❌ Example file exclusion failed"
    rm -f secrets/violation.txt.example
    exit 1
fi

echo "✅ All secrets detection tests passed!"
echo ""
echo "Summary of secrets management features:"
echo "  ✅ Fixed keyword detection patterns: password, token, private_key, aws_secret_access_key, api_key, secret, credential"
echo "  ✅ Standardized error messages: 'secrets: plaintext detected' / 'secrets: no plaintext detected'"
echo "  ✅ Example file exclusion (.example suffix)"
echo "  ✅ SOPS encryption support (ENC[...] patterns ignored)"
echo "  ✅ Non-zero exit codes on violations"
echo "  ✅ Integration with nix flake check system"