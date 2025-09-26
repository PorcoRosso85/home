#!/usr/bin/env bash
# OpenCode Diagnostic Helper Functions
# Provides centralized diagnostic utilities for the OpenCode client

set -euo pipefail

# Get available models from server and format as comma-separated list
# Usage: oc_diag_available_models SERVER_URL [MAX_COUNT]
# Returns: Comma-separated list of provider/model pairs, or fallback list on error
oc_diag_available_models() {
    local server_url="${1:-}"
    local max_count="${2:-3}"

    if [[ -z "$server_url" ]]; then
        echo "opencode/grok-code, opencode/qwen3-coder"
        return 0
    fi

    # Try to get available models from server
    local available
    available=$(curl -s --max-time 5 "$server_url/config/providers" 2>/dev/null | \
        jq -r '.providers[].models | keys[]' 2>/dev/null | \
        sed 's/^/opencode\//' | head -"$max_count" | tr '\n' ', ' | sed 's/,$//' || echo "")

    # Return available models or fallback
    if [[ -n "$available" ]]; then
        echo "$available"
    else
        echo "opencode/grok-code, opencode/qwen3-coder"
    fi
}

# Output standardized [Available] section for error messages
# Usage: oc_diag_show_available SERVER_URL [MAX_COUNT]
oc_diag_show_available() {
    local server_url="${1:-}"
    local max_count="${2:-3}"

    local available_models
    available_models=$(oc_diag_available_models "$server_url" "$max_count")

    echo "[Available] $available_models" >&2
}

# Output standardized [Next] action messages
# Usage: oc_diag_next_action ACTION_MESSAGE
oc_diag_next_action() {
    local action="$1"
    echo "[Next] $action" >&2
}

# Output [Next] action for process discovery
# Usage: oc_diag_next_ps
oc_diag_next_ps() {
    oc_diag_next_action "Run: opencode-client ps"
}

# Output [Next] action for export and probe
# Usage: oc_diag_next_export_probe URL
oc_diag_next_export_probe() {
    local url="${1:-http://127.0.0.1:4096}"
    oc_diag_next_action "Then: export OPENCODE_URL=\"$url\""
    oc_diag_next_action "Then: opencode-client status --probe"
}

# Output [Next] action for server start
# Usage: oc_diag_next_start_server [PORT]
oc_diag_next_start_server() {
    local port="${1:-4096}"
    oc_diag_next_action "Start server: nix run nixpkgs#opencode -- serve --port $port"
}

# Output comprehensive [Next] guidance for connection issues
# Usage: oc_diag_next_connection_help [URL]
oc_diag_next_connection_help() {
    local url="${1:-http://127.0.0.1:4096}"

    echo >&2
    oc_diag_next_ps
    if [[ "$url" != "http://127.0.0.1:4096" ]]; then
        oc_diag_next_export_probe "$url"
    else
        oc_diag_next_action "If no servers found, start one: nix run nixpkgs#opencode -- serve --port 4096"
        oc_diag_next_export_probe
    fi
}

# Output [Next] action for full diagnosis
# Usage: oc_diag_next_full_diagnosis
oc_diag_next_full_diagnosis() {
    oc_diag_next_action "Full diagnosis: ./check-opencode-status.sh"
}

# Output [Next] actions for viewing session history
# Usage: oc_diag_next_history SESSION_ID
oc_diag_next_history() {
    local session_id="$1"
    oc_diag_next_action "View history (text): opencode-client history --sid $session_id --format text"
    oc_diag_next_action "View history (json): opencode-client history --sid $session_id --format json"
}