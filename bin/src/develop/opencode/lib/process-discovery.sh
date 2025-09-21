#!/usr/bin/env bash
# OpenCode Process Discovery Functions
# OS-compatible discovery of running OpenCode servers with robust error handling

set -euo pipefail

# Discover running opencode server processes with cross-platform compatibility
# Usage: oc_ps_discover_servers
# Returns: JSON array of server info or empty array if none found
# Exit codes: 0=success (including empty results), 1=system error
oc_ps_discover_servers() {
    local servers_json="[]"

    # Try cross-platform ps command first (Linux/Darwin/BSD compatible)
    local ps_output=""
    if ps_output=$(ps -axo pid,command 2>/dev/null); then
        # Filter for opencode processes, avoid grep self-match
        local opencode_processes
        if opencode_processes=$(echo "$ps_output" | grep -E '(opencode|opencode serve)' | grep -v grep 2>/dev/null || true); then
            if [[ -n "$opencode_processes" ]]; then
                servers_json=$(echo "$opencode_processes" | oc_ps_parse_processes)
            fi
        fi
    else
        # Fallback to pgrep if available (some minimal systems)
        if command -v pgrep >/dev/null 2>&1; then
            local pgrep_output=""
            if pgrep_output=$(pgrep -fal 'opencode( serve)?' 2>/dev/null || true); then
                if [[ -n "$pgrep_output" ]]; then
                    servers_json=$(echo "$pgrep_output" | oc_ps_parse_processes)
                fi
            fi
        fi
    fi

    echo "$servers_json"
    return 0
}

# Parse process lines into structured JSON
# Usage: echo "process_lines" | oc_ps_parse_processes
# Returns: JSON array with pid, port, hostname, command fields
oc_ps_parse_processes() {
    local json_array="[]"
    local first_item=true

    while IFS= read -r line; do
        [[ -z "$line" ]] && continue

        # Extract PID (first field)
        local pid=$(echo "$line" | awk '{print $1}')

        # Extract command (rest of line after PID)
        local command=$(echo "$line" | cut -d' ' -f2-)

        # Extract port and hostname using regex
        local port=""
        local hostname=""

        # Look for --port=VALUE or --port VALUE patterns
        if [[ "$command" =~ --port[[:space:]]*=[[:space:]]*([0-9]+) ]]; then
            port="${BASH_REMATCH[1]}"
        elif [[ "$command" =~ --port[[:space:]]+([0-9]+) ]]; then
            port="${BASH_REMATCH[1]}"
        fi

        # Look for --hostname patterns (optional)
        if [[ "$command" =~ --hostname[[:space:]]*=[[:space:]]*([^[:space:]]+) ]]; then
            hostname="${BASH_REMATCH[1]}"
        elif [[ "$command" =~ --hostname[[:space:]]+([^[:space:]]+) ]]; then
            hostname="${BASH_REMATCH[1]}"
        else
            hostname="127.0.0.1"  # Default hostname
        fi

        # Build JSON object
        local json_item
        json_item=$(cat <<EOF
{
  "pid": "$pid",
  "port": "$port",
  "hostname": "$hostname",
  "command": $(echo "$command" | jq -R .)
}
EOF
)

        # Add to array
        if [[ "$first_item" == "true" ]]; then
            json_array="[$json_item"
            first_item=false
        else
            json_array="$json_array, $json_item"
        fi
    done

    if [[ "$first_item" == "false" ]]; then
        json_array="$json_array]"
    fi

    echo "$json_array"
}

# Check HTTP reachability of a URL
# Usage: oc_ps_check_reachability URL
# Returns: 0 if reachable, 1 if not
oc_ps_check_reachability() {
    local url="$1"

    # Try both /doc and /config/providers endpoints (robust API compatibility)
    if curl -s --max-time 3 "$url/doc" >/dev/null 2>&1; then
        return 0
    elif curl -s --max-time 3 "$url/config/providers" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Generate export commands for reachable servers
# Usage: oc_ps_generate_exports SERVER_JSON_ARRAY
# Returns: Formatted export commands with guidance
oc_ps_generate_exports() {
    local servers_json="$1"
    local reachable_count=0

    echo "[client] Available OpenCode servers:"
    echo

    # Process each server
    local index=0
    while true; do
        local server
        if ! server=$(echo "$servers_json" | jq -r ".[$index] // empty" 2>/dev/null); then
            break
        fi
        [[ -z "$server" || "$server" == "null" ]] && break

        local pid=$(echo "$server" | jq -r '.pid // "unknown"')
        local port=$(echo "$server" | jq -r '.port // ""')
        local hostname=$(echo "$server" | jq -r '.hostname // "127.0.0.1"')

        if [[ -n "$port" ]]; then
            local url="http://$hostname:$port"
            local status="❌ unreachable"

            if oc_ps_check_reachability "$url"; then
                status="✅ reachable"
                ((reachable_count++))
                echo "  Server $((index + 1)): PID $pid, Port $port ($status)"
                echo "    export OPENCODE_URL=\"$url\""
                echo
            else
                echo "  Server $((index + 1)): PID $pid, Port $port ($status)"
                echo "    URL: $url (not responding)"
                echo
            fi
        else
            echo "  Server $((index + 1)): PID $pid, Port unknown"
            echo "    Command: $(echo "$server" | jq -r '.command')"
            echo
        fi

        ((index++))
    done

    if [[ $reachable_count -eq 0 ]]; then
        if [[ $index -eq 0 ]]; then
            echo "  No OpenCode servers found running"
        else
            echo "  No reachable servers found"
        fi
        echo
        echo "[Next] Start a server: nix run nixpkgs#opencode -- serve --port 4096"
        echo "[Next] Then try: export OPENCODE_URL=http://127.0.0.1:4096"
        return 1
    elif [[ $reachable_count -eq 1 ]]; then
        echo "[Next] Copy one export command above, then:"
        echo "[Next] nix run .#opencode-client -- status --probe"
    else
        echo "[Next] Choose one export command above, then:"
        echo "[Next] nix run .#opencode-client -- status --probe"
    fi

    return 0
}