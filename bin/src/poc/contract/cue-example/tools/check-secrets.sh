#!/bin/bash
set -euo pipefail

# Unified secrets detection script
# Used by both pre-commit hooks and Nix flake checks

# Define sensitive key patterns (comprehensive list)
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
  exit 1
else
  echo "secrets: no plaintext detected"
  exit 0
fi