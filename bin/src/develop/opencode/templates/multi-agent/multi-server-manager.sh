#!/usr/bin/env bash
set -euo pipefail

# Multi-Server Manager for OpenCode Multi-Agent System
# Provides load balancing, health checking, and failover capabilities

# Default configuration
DEFAULT_HEALTH_CHECK=true
DEFAULT_TIMEOUT=30

# Global state files
readonly STATE_DIR="${OPENCODE_SESSION_DIR:-${XDG_STATE_HOME:-$HOME/.local/state}/opencode}/multi-server"
readonly ROUND_ROBIN_STATE_FILE="$STATE_DIR/round_robin_index"

# Exit codes
readonly EXIT_SUCCESS=0
readonly EXIT_INVALID_ARGS=1
readonly EXIT_NO_HEALTHY_SERVERS=2
readonly EXIT_CONFIG_ERROR=3

# Initialize state directory
init_state_dir() {
    mkdir -p "$STATE_DIR"
}

# Parse command line arguments
parse_args() {
    local config_file=""
    local action=""
    local server_pool=""
    local health_check="$DEFAULT_HEALTH_CHECK"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --config=*)
                config_file="${1#*=}"
                shift
                ;;
            --action=*)
                action="${1#*=}"
                shift
                ;;
            --server-pool=*)
                server_pool="${1#*=}"
                shift
                ;;
            --health-check=*)
                health_check="${1#*=}"
                shift
                ;;
            *)
                if [[ -z "$action" ]]; then
                    action="$1"
                fi
                shift
                ;;
        esac
    done
    
    # Export parsed arguments
    export PARSED_CONFIG_FILE="$config_file"
    export PARSED_ACTION="$action"
    export PARSED_SERVER_POOL="$server_pool"
    export PARSED_HEALTH_CHECK="$health_check"
}

# Load server configuration from file or environment
load_server_config() {
    local config_file="$PARSED_CONFIG_FILE"
    local server_pool="$PARSED_SERVER_POOL"
    
    if [[ -n "$config_file" ]] && [[ -f "$config_file" ]]; then
        # Load from JSON config file
        export SERVER_CONFIG_SOURCE="file"
        export SERVER_CONFIG_PATH="$config_file"
        return 0
    elif [[ -n "$server_pool" ]]; then
        # Load from environment variable (comma-separated URLs)
        export SERVER_CONFIG_SOURCE="env"
        export SERVER_CONFIG_DATA="$server_pool"
        return 0
    elif [[ -n "${OPENCODE_SERVER_POOL:-}" ]]; then
        # Load from OPENCODE_SERVER_POOL environment variable
        export SERVER_CONFIG_SOURCE="env"
        export SERVER_CONFIG_DATA="$OPENCODE_SERVER_POOL"
        return 0
    else
        echo "ERROR: No server configuration found. Use --config or --server-pool" >&2
        return $EXIT_CONFIG_ERROR
    fi
}

# Get list of servers from configuration
get_server_list() {
    case "$SERVER_CONFIG_SOURCE" in
        "file")
            if command -v jq >/dev/null 2>&1; then
                jq -r '.servers[] | .url' "$SERVER_CONFIG_PATH" 2>/dev/null || echo ""
            else
                # Fallback parsing for JSON without jq
                grep -o '"url"[[:space:]]*:[[:space:]]*"[^"]*"' "$SERVER_CONFIG_PATH" 2>/dev/null | \
                sed 's/.*"url"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' || echo ""
            fi
            ;;
        "env")
            echo "$SERVER_CONFIG_DATA" | tr ',' '\n'
            ;;
        *)
            echo ""
            ;;
    esac
}

# Get server count
get_server_count() {
    get_server_list | wc -l
}



# Check if server is healthy
is_server_healthy() {
    local server_url="$1"
    local timeout="${OPENCODE_CURL_TIMEOUT:-$DEFAULT_TIMEOUT}"
    
    # Use unified error handler for health check - try /doc first, fallback to /config/providers
    if unified-error-handler --url="$server_url/doc" --method="GET" --timeout="$timeout" >/dev/null 2>&1; then
        return 0
    elif unified-error-handler --url="$server_url/config/providers" --method="GET" --timeout="$timeout" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Get list of healthy servers
get_healthy_servers() {
    local servers
    servers=$(get_server_list)
    
    if [[ "$PARSED_HEALTH_CHECK" == "true" ]]; then
        local healthy_servers=""
        while IFS= read -r server; do
            if [[ -n "$server" ]] && is_server_healthy "$server"; then
                if [[ -n "$healthy_servers" ]]; then
                    healthy_servers="${healthy_servers}\n${server}"
                else
                    healthy_servers="$server"
                fi
            fi
        done <<< "$servers"
        
        echo -e "$healthy_servers"
    else
        # Return all servers if health checking is disabled
        echo "$servers"
    fi
}

# Round-robin server selection
get_round_robin_server() {
    local servers
    servers=$(get_healthy_servers)
    
    if [[ -z "$servers" ]]; then
        echo "ERROR: No healthy servers available" >&2
        return $EXIT_NO_HEALTHY_SERVERS
    fi
    
    local server_array=()
    while IFS= read -r server; do
        if [[ -n "$server" ]]; then
            server_array+=("$server")
        fi
    done <<< "$servers"
    
    local server_count=${#server_array[@]}
    if [[ $server_count -eq 0 ]]; then
        echo "ERROR: No servers in array" >&2
        return $EXIT_NO_HEALTHY_SERVERS
    fi
    
    # Read current index
    local current_index=0
    if [[ -f "$ROUND_ROBIN_STATE_FILE" ]]; then
        current_index=$(cat "$ROUND_ROBIN_STATE_FILE" 2>/dev/null || echo "0")
    fi
    
    # Get server at current index
    local selected_server="${server_array[$current_index]}"
    
    # Update index for next request (with wraparound)
    local next_index=$(( (current_index + 1) % server_count ))
    echo "$next_index" > "$ROUND_ROBIN_STATE_FILE"
    
    echo "$selected_server"
    return 0
}




# Validate server configuration
validate_config() {
    load_server_config || return $EXIT_CONFIG_ERROR
    
    local servers
    servers=$(get_server_list)
    
    if [[ -z "$servers" ]]; then
        echo "ERROR: No servers configured" >&2
        return $EXIT_CONFIG_ERROR
    fi
    
    local server_count
    server_count=$(echo "$servers" | wc -l)
    
    if [[ $server_count -lt 1 ]]; then
        echo "ERROR: At least one server required" >&2
        return $EXIT_CONFIG_ERROR
    fi
    
    # Validate server URLs
    while IFS= read -r server; do
        if [[ -n "$server" ]]; then
            if [[ ! "$server" =~ ^https?://[^[:space:]]+$ ]]; then
                echo "ERROR: Invalid server URL: $server" >&2
                return $EXIT_CONFIG_ERROR
            fi
        fi
    done <<< "$servers"
    
    echo "VALID: $server_count servers configured"
    return 0
}

# Reload configuration
reload_config() {
    # Clear cached state
    rm -f "$ROUND_ROBIN_STATE_FILE" 2>/dev/null || true
    
    # Validate new configuration
    validate_config
}

# Get next server using round-robin selection
get_next_server() {
    load_server_config || return $EXIT_CONFIG_ERROR
    init_state_dir
    
    # Always use round-robin for minimal 2-server setup
    get_round_robin_server
}

# Get healthy server (any strategy)
get_healthy_server() {
    load_server_config || return $EXIT_CONFIG_ERROR
    
    local healthy_servers
    healthy_servers=$(get_healthy_servers)
    
    if [[ -z "$healthy_servers" ]]; then
        echo "ERROR: No healthy servers available" >&2
        return $EXIT_NO_HEALTHY_SERVERS
    fi
    
    # Return first healthy server
    echo "$healthy_servers" | head -n1
    return 0
}

# Main action dispatcher
main() {
    parse_args "$@"
    
    local action="$PARSED_ACTION"
    
    if [[ -z "$action" ]]; then
        echo "ERROR: No action specified" >&2
        echo "Valid actions: validate, get_next_server, get_healthy_server, get_server_count, reload_config" >&2
        return $EXIT_INVALID_ARGS
    fi
    
    case "$action" in
        "validate")
            validate_config
            ;;
        "get_next_server")
            get_next_server
            ;;
        "get_healthy_server")
            get_healthy_server
            ;;
        "get_server_count")
            load_server_config || return $EXIT_CONFIG_ERROR
            get_server_count
            ;;
        "reload_config")
            reload_config
            ;;
        *)
            echo "ERROR: Unknown action: $action" >&2
            return $EXIT_INVALID_ARGS
            ;;
    esac
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi