#!/usr/bin/env bash
# Global check for plaintext secrets in the repository
# - Verifies files under secrets/ are SOPS-encrypted
# - Can be used locally and in CI

set -euo pipefail

# If no secrets dir, nothing to check
if [[ ! -d secrets ]]; then
  echo "No secrets/ directory found. Skipping plaintext check."
  exit 0
fi

# Find candidate files in secrets/
# We only consider common text formats that should be encrypted
mapfile -t files < <(find secrets -type f \( \
  -name '*.yaml' -o -name '*.yml' -o -name '*.json' -o -name '*.toml' -o -name '*.ini' -o -name '*.txt' -o -name '*.conf' \) | sort)

if [[ ${#files[@]} -eq 0 ]]; then
  echo "No candidate files under secrets/ to check."
  exit 0
fi

plaintext=()
for f in "${files[@]}"; do
  # SOPS-encrypted files contain the marker ENC[AES256_GCM]
  if ! grep -q 'ENC\[AES256_GCM' "$f"; then
    plaintext+=("$f")
  fi
done

if [[ ${#plaintext[@]} -ne 0 ]]; then
  echo "ERROR: Plaintext secrets detected under secrets/" >&2
  printf '%s\n' "${plaintext[@]}" >&2
  echo "---" >&2
  echo "Fix by encrypting each file:" >&2
  echo "  sops -e -i <file>   # in-place encryption" >&2
  exit 1
fi

echo "SUCCESS: All secrets/* files are SOPS-encrypted."

