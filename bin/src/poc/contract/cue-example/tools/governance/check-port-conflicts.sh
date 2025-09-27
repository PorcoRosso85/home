#!/usr/bin/env bash
# Port conflicts detection for SSOT governance
# Ensures no service port conflicts exist across contracts

set -euo pipefail

echo "🔌 Checking for port conflicts..."

# Find all contract files
contract_files=$(find contracts/ -name "contract.cue" 2>/dev/null || true)

if [[ -z "$contract_files" ]]; then
    echo "⚠️  No contract files found in contracts/ directory"
    exit 0
fi

# Extract port definitions from all contracts
declare -A port_usage
conflicts_found=false

echo "Scanning contracts for port definitions..."

for contract in $contract_files; do
    # Extract port numbers from contract
    ports=$(grep -E "port.*[0-9]+" "$contract" 2>/dev/null | grep -oE "[0-9]+" || true)

    for port in $ports; do
        if [[ -n "${port_usage[$port]:-}" ]]; then
            echo "❌ Port conflict detected!"
            echo "  Port $port is used in:"
            echo "    - ${port_usage[$port]}"
            echo "    - $contract"
            conflicts_found=true
        else
            port_usage[$port]="$contract"
        fi
    done
done

# Check for well-known port usage violations
well_known_ports=(
    "22:SSH"
    "25:SMTP"
    "53:DNS"
    "80:HTTP"
    "110:POP3"
    "143:IMAP"
    "443:HTTPS"
    "993:IMAPS"
    "995:POP3S"
)

echo "Checking against well-known ports..."

for port_info in "${well_known_ports[@]}"; do
    port="${port_info%%:*}"
    service="${port_info##*:}"

    if [[ -n "${port_usage[$port]:-}" ]]; then
        echo "⚠️  Well-known port $port ($service) is used in: ${port_usage[$port]}"
        echo "    Consider using a different port range (8000+ for development)"
    fi
done

# Validate port ranges
echo "Validating port ranges..."

for port in "${!port_usage[@]}"; do
    if [[ "$port" -lt 1024 ]]; then
        echo "⚠️  Privileged port $port used in: ${port_usage[$port]}"
        echo "    Privileged ports (< 1024) may require special permissions"
    elif [[ "$port" -gt 65535 ]]; then
        echo "❌ Invalid port $port in: ${port_usage[$port]}"
        echo "    Port numbers must be between 1 and 65535"
        conflicts_found=true
    fi
done

if [[ "$conflicts_found" == "true" ]]; then
    echo ""
    echo "❌ Port conflicts detected!"
    echo "Resolve port conflicts before proceeding."
    echo "Use unique ports for each service to maintain SSOT compliance."
    exit 1
fi

echo "✅ No port conflicts detected"