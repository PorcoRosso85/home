#!/usr/bin/env bash
# Nickel contract validation script

set -euo pipefail

# Validate producer contract
validate_producer() {
  nickel eval -f json << EOF
let contracts = import "../contracts.ncl" in
contracts.validate_producer $1
EOF
}

# Validate consumer contract
validate_consumer() {
  nickel eval -f json << EOF
let contracts = import "../contracts.ncl" in
{
  summary = "test",
  details = $1,
} & contracts.ConsumerContract
EOF
}

# Main
if [ $# -eq 0 ]; then
  echo "Usage: $0 <json-data>"
  exit 1
fi

INPUT="$1"

# Try producer first
if validate_producer "$INPUT" 2>/dev/null; then
  echo "✅ Valid producer contract"
  exit 0
fi

# Try consumer
if validate_consumer "$INPUT" 2>/dev/null; then
  echo "✅ Valid consumer contract"
  exit 0
fi

echo "❌ Invalid contract"
exit 1