#!/usr/bin/env bash
set -euo pipefail

# OpenCode Session Manager (Simplified)
# Manages OpenCode sessions for minimal 2-server multi-agent setup
#
# Session Architecture:
# - Server manages session state: All conversation history and context is stored server-side
# - Client holds only ID for reference: Local files contain session IDs, not session data
# - API Pattern: POST /session → get ID → POST /session/:id/message

# Default configuration
DEFAULT_STRATEGY="auto"
DEFAULT_URL="http://127.0.0.1:4096"
DEFAULT_TIMEOUT=30
DEFAULT_PROJECT="multi-agent"

# Exit codes
readonly EXIT_SUCCESS=0
readonly EXIT_INVALID_ARGS=1
readonly EXIT_SESSION_ERROR=2
readonly EXIT_API_ERROR=3

# Parse command line arguments
parse_args() {
    local strategy="$DEFAULT_STRATEGY"
    local url="$DEFAULT_URL"
    local project="$DEFAULT_PROJECT"
    local session_id=""
    local host_port=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --strategy=*)
                strategy="${1#*=}"
                shift
                ;;
            --url=*)
                url="${1#*=}"
                shift
                ;;
            --host-port=*)
                host_port="${1#*=}"
                shift
                ;;
            --project=*)
                project="${1#*=}"
                shift
                ;;
            --session-id=*)
                session_id="${1#*=}"
                shift
                ;;
            *)
                strategy="$1"
                shift
                ;;
        esac
    done
    
    # Export parsed arguments
    export PARSED_STRATEGY="$strategy"
    export PARSED_URL="$url"
    export PARSED_HOST_PORT="$host_port"
    export PARSED_PROJECT="$project"
    export PARSED_SESSION_ID="$session_id"
}

# Normalize URL by removing trailing slashes
normalize_url() {
    local url="$1"
    echo "${url%/}"
}

# Derive host:port from URL
derive_host_port() {
    local url="$1"
    # Remove protocol and extract host:port
    local host_port="${url#*://}"
    host_port="${host_port%%/*}"
    echo "$host_port"
}

# Get session storage directory
get_session_base_dir() {
    local state_base="${XDG_STATE_HOME:-$HOME/.local/state}"
    echo "$state_base/opencode/sessions"
}

# Initialize session directories
init_session_dirs() {
    local session_base
    session_base=$(get_session_base_dir)
    mkdir -p "$session_base"
}

# Create session file path
get_session_file_path() {
    local host_port="$1"
    local project="$2"
    local session_base
    session_base=$(get_session_base_dir)
    echo "$session_base/$host_port/$project.session"
}

# Create session via OpenCode API
create_session_api() {
    local url="$1"
    local project="$2"
    local title="$3"
    
    # Create session via OpenCode API
    # For now, return a generated session ID since we don't have session creation API
    echo "sess_$(date +%s)_$$"
}

# Validate session exists via API
validate_session_api() {
    local url="$1"
    local session_id="$2"
    
    # Use unified-error-handler to check session validity
    if unified-error-handler --url="$url/session/$session_id" --method="GET" --timeout="$DEFAULT_TIMEOUT" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Auto strategy: Use existing session or create new one
strategy_auto() {
    local url="$PARSED_URL"
    local project="$PARSED_PROJECT"
    local host_port="$PARSED_HOST_PORT"
    
    url=$(normalize_url "$url")
    
    if [[ -z "$host_port" ]]; then
        host_port=$(derive_host_port "$url")
    fi
    
    init_session_dirs
    local session_file
    session_file=$(get_session_file_path "$host_port" "$project")
    
    # Check if session file exists and is valid
    if [[ -f "$session_file" ]]; then
        local existing_session
        existing_session=$(cat "$session_file" 2>/dev/null || echo "")
        if [[ -n "$existing_session" ]]; then
            # Validate session with API
            if validate_session_api "$url" "$existing_session" 2>/dev/null; then
                echo "$session_file"
                return 0
            fi
        fi
    fi
    
    # No valid existing session, create new one
    local new_session
    if new_session=$(create_session_api "$url" "$project" "Auto session"); then
        # Save session ID to file
        mkdir -p "$(dirname "$session_file")"
        echo "$new_session" > "$session_file"
        echo "$session_file"
        return 0
    else
        echo "ERROR: Failed to create session" >&2
        return $EXIT_SESSION_ERROR
    fi
}

# New strategy: Always create new session
strategy_new() {
    local url="$PARSED_URL"
    local project="$PARSED_PROJECT"
    local host_port="$PARSED_HOST_PORT"
    
    url=$(normalize_url "$url")
    
    if [[ -z "$host_port" ]]; then
        host_port=$(derive_host_port "$url")
    fi
    
    init_session_dirs
    
    # Always create new session
    local new_session
    if new_session=$(create_session_api "$url" "$project" "New session"); then
        local session_file
        session_file=$(get_session_file_path "$host_port" "$project")
        
        # Save session ID to file
        mkdir -p "$(dirname "$session_file")"
        echo "$new_session" > "$session_file"
        echo "$session_file"
        return 0
    else
        echo "ERROR: Failed to create new session" >&2
        return $EXIT_SESSION_ERROR
    fi
}

# Attach strategy: Use specific session ID
strategy_attach() {
    local url="$PARSED_URL"
    local project="$PARSED_PROJECT"
    local host_port="$PARSED_HOST_PORT"
    local session_id="$PARSED_SESSION_ID"
    
    if [[ -z "$session_id" ]]; then
        echo "ERROR: --session-id is required for attach strategy" >&2
        return $EXIT_INVALID_ARGS
    fi
    
    url=$(normalize_url "$url")
    
    if [[ -z "$host_port" ]]; then
        host_port=$(derive_host_port "$url")
    fi
    
    # Validate session exists
    if ! validate_session_api "$url" "$session_id" 2>/dev/null; then
        echo "WARNING: Session $session_id may not be valid or reachable" >&2
    fi
    
    init_session_dirs
    local session_file
    session_file=$(get_session_file_path "$host_port" "$project")
    
    # Save session ID to file
    mkdir -p "$(dirname "$session_file")"
    echo "$session_id" > "$session_file"
    echo "$session_file"
    return 0
}

# Optional: Shared strategy (for documentation)
strategy_shared() {
    echo "INFO: Shared strategy is optional and not implemented in minimal setup" >&2
    echo "INFO: Using auto strategy instead" >&2
    strategy_auto
}

# Optional: Discover strategy (for documentation)
strategy_discover() {
    echo "INFO: Discover strategy is optional and not implemented in minimal setup" >&2
    echo "INFO: Listing available session files instead:" >&2
    
    local session_base
    session_base=$(get_session_base_dir)
    
    if [[ -d "$session_base" ]]; then
        find "$session_base" -name "*.session" 2>/dev/null | head -10
    fi
    
    return 0
}

# Get session ID from session file
get_session_id() {
    local session_file="$1"
    
    if [[ -f "$session_file" ]]; then
        cat "$session_file" 2>/dev/null || echo ""
    else
        echo ""
    fi
}

# Show session status
show_status() {
    local url="$PARSED_URL"
    local project="$PARSED_PROJECT"
    local host_port="$PARSED_HOST_PORT"
    
    url=$(normalize_url "$url")
    
    if [[ -z "$host_port" ]]; then
        host_port=$(derive_host_port "$url")
    fi
    
    local session_file
    session_file=$(get_session_file_path "$host_port" "$project")
    
    echo "OpenCode Session Manager (Simplified)"
    echo "URL: $url"
    echo "Host:Port: $host_port"
    echo "Project: $project"
    echo "Session file: $session_file"
    
    if [[ -f "$session_file" ]]; then
        local session_id
        session_id=$(get_session_id "$session_file")
        echo "Session ID: $session_id"
        
        # Test session validity
        if validate_session_api "$url" "$session_id" 2>/dev/null; then
            echo "Status: Session is valid and reachable"
        else
            echo "Status: Session file exists but may not be reachable"
        fi
    else
        echo "Session ID: None"
        echo "Status: No session file found"
    fi
}

# Usage information
usage() {
    cat << EOF
Usage: $0 [OPTIONS] [STRATEGY]

Simplified session manager for 2-server OpenCode multi-agent setup.

STRATEGIES (Mandatory):
    auto                    Use existing session or create new one (default)
    new                     Always create a new session
    attach                  Attach to specific session (requires --session-id)

STRATEGIES (Optional - for documentation):
    shared                  Shared session management (falls back to auto)
    discover                List available sessions

OPTIONS:
    --url=URL               OpenCode server URL (default: $DEFAULT_URL)
    --host-port=HOST:PORT   Override host:port derivation
    --project=NAME          Project name (default: $DEFAULT_PROJECT)  
    --session-id=SID        Session ID for attach strategy

EXAMPLES:
    $0 auto
    $0 new --project=myproject --url=http://127.0.0.1:4097
    $0 attach --session-id=sess123 --url=http://127.0.0.1:4096
    $0 status

Session files are stored at:
\${XDG_STATE_HOME:-\$HOME/.local/state}/opencode/sessions/<host_port>/<project>.session
EOF
}

# Main dispatcher
main() {
    parse_args "$@"
    
    local strategy="$PARSED_STRATEGY"
    
    case "$strategy" in
        "auto")
            strategy_auto
            ;;
        "new")
            strategy_new
            ;;
        "attach")
            strategy_attach
            ;;
        "shared")
            strategy_shared
            ;;
        "discover")
            strategy_discover
            ;;
        "status")
            show_status
            ;;
        "--help"|"help")
            usage
            ;;
        *)
            echo "ERROR: Unknown strategy: $strategy" >&2
            echo "Valid strategies: auto, new, attach, shared, discover, status" >&2
            echo "Use --help for usage information" >&2
            return $EXIT_INVALID_ARGS
            ;;
    esac
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi