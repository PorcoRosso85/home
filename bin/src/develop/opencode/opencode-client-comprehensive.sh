#!/usr/bin/env bash
set -euo pipefail

# OpenCode Comprehensive Client System
# Advanced client with session management, connection monitoring, and error handling

readonly VERSION="1.0.0"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source required libraries
source "${SCRIPT_DIR}/lib/session-helper.sh"
source "${SCRIPT_DIR}/lib/diagnostic-helper.sh"
source "${SCRIPT_DIR}/lib/process-discovery.sh"

# Load comprehensive modules
source "${SCRIPT_DIR}/lib/connection-monitor.sh" 2>/dev/null || echo "[warn] connection-monitor.sh not found, using basic monitoring" >&2
source "${SCRIPT_DIR}/lib/error-handler.sh" 2>/dev/null || echo "[warn] error-handler.sh not found, using basic error handling" >&2
source "${SCRIPT_DIR}/lib/performance-manager.sh" 2>/dev/null || echo "[warn] performance-manager.sh not found, using basic performance" >&2

# Configuration defaults
readonly DEFAULT_URL="http://127.0.0.1:4096"
readonly DEFAULT_TIMEOUT=30
readonly DEFAULT_MAX_RETRIES=3
readonly DEFAULT_RETRY_DELAY=2
readonly CONFIG_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/opencode/client.conf"

# Runtime state
declare -A ACTIVE_SESSIONS=()
declare -A CONNECTION_POOL=()
declare -A SERVER_HEALTH=()

# Error handling functions
oc_error_exit() {
    local error_code="$1"
    local error_msg="$2"
    local fix_msg="${3:-}"
    local help_msg="${4:-}"
    local next_msg="${5:-}"
    
    echo "[Error] $error_msg" >&2
    [[ -n "$fix_msg" ]] && echo "[Fix] $fix_msg" >&2
    [[ -n "$help_msg" ]] && echo "[Help] $help_msg" >&2
    [[ -n "$next_msg" ]] && echo "[Next] $next_msg" >&2
    exit "$error_code"
}

oc_error_warning() {
    local warning_msg="$1"
    local fix_msg="${2:-}"
    local next_msg="${3:-}"
    
    echo "[Warning] $warning_msg" >&2
    [[ -n "$fix_msg" ]] && echo "[Fix] $fix_msg" >&2
    [[ -n "$next_msg" ]] && echo "[Next] $next_msg" >&2
}

# Configuration management
oc_load_config() {
    # Set defaults
    export OPENCODE_URL="${OPENCODE_URL:-$DEFAULT_URL}"
    export OPENCODE_TIMEOUT="${OPENCODE_TIMEOUT:-$DEFAULT_TIMEOUT}"
    export OPENCODE_MAX_RETRIES="${OPENCODE_MAX_RETRIES:-$DEFAULT_MAX_RETRIES}"
    export OPENCODE_RETRY_DELAY="${OPENCODE_RETRY_DELAY:-$DEFAULT_RETRY_DELAY}"
    export OPENCODE_PROJECT_DIR="${OPENCODE_PROJECT_DIR:-$(pwd)}"
    
    # Load config file if exists
    if [[ -f "$CONFIG_FILE" ]]; then
        # shellcheck source=/dev/null
        source "$CONFIG_FILE" 2>/dev/null || true
    fi
}

oc_save_config() {
    mkdir -p "$(dirname "$CONFIG_FILE")"
    cat > "$CONFIG_FILE" << EOF
# OpenCode Client Configuration
OPENCODE_URL="$OPENCODE_URL"
OPENCODE_TIMEOUT="$OPENCODE_TIMEOUT"
OPENCODE_MAX_RETRIES="$OPENCODE_MAX_RETRIES"
OPENCODE_RETRY_DELAY="$OPENCODE_RETRY_DELAY"
OPENCODE_PROJECT_DIR="$OPENCODE_PROJECT_DIR"
EOF
    echo "[client] Configuration saved to $CONFIG_FILE"
}

# Connection monitoring with retry logic
oc_connection_monitor() {
    local url="$1"
    local max_retries="${2:-$OPENCODE_MAX_RETRIES}"
    local retry_delay="${3:-$OPENCODE_RETRY_DELAY}"
    
    local attempt=1
    while [[ $attempt -le $max_retries ]]; do
        if curl -fsS --max-time "$OPENCODE_TIMEOUT" "$url/doc" >/dev/null 2>&1; then
            SERVER_HEALTH["$url"]="healthy"
            return 0
        fi
        
        echo "[client] Connection attempt $attempt/$max_retries failed for $url" >&2
        
        if [[ $attempt -lt $max_retries ]]; then
            echo "[client] Retrying in ${retry_delay}s..." >&2
            sleep "$retry_delay"
        fi
        
        ((attempt++))
    done
    
    SERVER_HEALTH["$url"]="unhealthy"
    return 1
}

# Server discovery and selection
oc_discover_servers() {
    echo "[client] Discovering available OpenCode servers..." >&2
    
    local servers_json
    servers_json=$(oc_ps_discover_servers)
    
    if [[ "$servers_json" == "[]" ]]; then
        oc_error_warning "No OpenCode servers found running" \
            "Start a server: nix run nixpkgs#opencode -- serve --port 4096" \
            "Then run: opencode-client status --probe"
        return 1
    fi
    
    oc_ps_generate_exports "$servers_json"
    return 0
}

# Enhanced session management
oc_session_manager() {
    local action="$1"
    local project_dir="${2:-$OPENCODE_PROJECT_DIR}"
    local url="${3:-$OPENCODE_URL}"
    
    case "$action" in
        "get-or-create")
            local session_id
            if session_id=$(oc_session_get_or_create "$url" "$project_dir"); then
                ACTIVE_SESSIONS["$project_dir"]="$session_id"
                echo "$session_id"
                return 0
            else
                oc_error_exit 2 "Failed to get or create session" \
                    "Check server availability and network connection" \
                    "Use 'opencode-client status --probe' to test connectivity" \
                    "Try 'opencode-client discover' to find available servers"
            fi
            ;;
        "list")
            echo "[client] Active sessions:" >&2
            for dir in "${!ACTIVE_SESSIONS[@]}"; do
                echo "  $dir: ${ACTIVE_SESSIONS[$dir]}" >&2
            done
            ;;
        "cleanup")
            # Remove invalid sessions
            for dir in "${!ACTIVE_SESSIONS[@]}"; do
                local session_id="${ACTIVE_SESSIONS[$dir]}"
                if ! oc_session_validate_api "$url" "$session_id" 2>/dev/null; then
                    echo "[client] Removing invalid session: $session_id for $dir" >&2
                    unset ACTIVE_SESSIONS["$dir"]
                fi
            done
            ;;
        *)
            oc_error_exit 1 "Unknown session action: $action" \
                "Valid actions: get-or-create, list, cleanup"
            ;;
    esac
}

# Performance optimization with connection pooling
oc_performance_optimize() {
    local url="$1"
    
    # Check if connection is pooled
    if [[ -n "${CONNECTION_POOL[$url]:-}" ]]; then
        echo "[client] Using pooled connection for $url" >&2
        return 0
    fi
    
    # Create new connection pool entry
    if oc_connection_monitor "$url" 1 1; then
        CONNECTION_POOL["$url"]="$(date +%s)"
        echo "[client] Connection pooled for $url" >&2
        return 0
    else
        oc_error_warning "Failed to establish connection pool for $url"
        return 1
    fi
}

# Diagnostic system
oc_diagnostic_check() {
    local check_type="${1:-full}"
    
    echo "[client] Running diagnostic check: $check_type" >&2
    
    case "$check_type" in
        "connectivity")
            if oc_connection_monitor "$OPENCODE_URL"; then
                echo "[client] ✅ Connectivity: Server reachable at $OPENCODE_URL"
            else
                echo "[client] ❌ Connectivity: Server unreachable at $OPENCODE_URL"
                oc_diag_next_connection_help "$OPENCODE_URL"
                return 1
            fi
            ;;
        "sessions")
            local session_base
            session_base=$(oc_session_get_base_dir)
            local session_count
            session_count=$(find "$session_base" -name "*.session" 2>/dev/null | wc -l)
            echo "[client] ✅ Sessions: $session_count session files found"
            ;;
        "performance")
            local start_time end_time duration
            start_time=$(date +%s%3N)
            if curl -fsS --max-time 5 "$OPENCODE_URL/doc" >/dev/null 2>&1; then
                end_time=$(date +%s%3N)
                duration=$((end_time - start_time))
                echo "[client] ✅ Performance: Response time ${duration}ms"
            else
                echo "[client] ❌ Performance: Cannot measure - server unreachable"
                return 1
            fi
            ;;
        "full")
            oc_diagnostic_check "connectivity" && \
            oc_diagnostic_check "sessions" && \
            oc_diagnostic_check "performance"
            ;;
        *)
            oc_error_exit 1 "Unknown diagnostic check: $check_type" \
                "Valid checks: connectivity, sessions, performance, full"
            ;;
    esac
}

# Message sending with comprehensive error handling
oc_send_message() {
    local message="$1"
    local project_dir="${2:-$OPENCODE_PROJECT_DIR}"
    local provider="${3:-$OPENCODE_PROVIDER}"
    local model="${4:-$OPENCODE_MODEL}"
    
    echo "[client] Sending message for project: $project_dir" >&2
    
    # Optimize connection
    if ! oc_performance_optimize "$OPENCODE_URL"; then
        oc_error_warning "Connection optimization failed, proceeding with basic connection"
    fi
    
    # Get or create session
    local session_id
    if ! session_id=$(oc_session_manager "get-or-create" "$project_dir" "$OPENCODE_URL"); then
        return 1
    fi
    
    # Build message payload
    local payload
    payload=$(jq -n \
        --arg text "$message" \
        --arg p "$provider" \
        --arg m "$model" \
        '{ parts: [{ type: "text", text: $text }] }
         + (if $p != "" and $m != "" then { model: { providerID: $p, modelID: $m }} else {} end)')
    
    # Send message with retry logic
    local attempt=1
    while [[ $attempt -le $OPENCODE_MAX_RETRIES ]]; do
        local response
        if response=$(oc_session_http_post "$OPENCODE_URL/session/$session_id/message?directory=$(printf '%s' "$project_dir" | jq -sRr @uri)" "$payload" 2>&1); then
            # Success - parse and display response
            if echo "$response" | jq -e '.parts? // [] | length > 0' >/dev/null 2>&1; then
                echo "[client] Response:" >&2
                echo "$response" | jq -r '(.parts[]? | select(.type=="text") | .text) // empty'
            else
                echo "$response" | jq -r '.'
            fi
            return 0
        else
            echo "[client] Message send attempt $attempt/$OPENCODE_MAX_RETRIES failed" >&2
            
            if [[ $attempt -lt $OPENCODE_MAX_RETRIES ]]; then
                echo "[client] Retrying in ${OPENCODE_RETRY_DELAY}s..." >&2
                sleep "$OPENCODE_RETRY_DELAY"
            fi
            
            ((attempt++))
        fi
    done
    
    # All attempts failed
    oc_error_exit 3 "Failed to send message after $OPENCODE_MAX_RETRIES attempts" \
        "Check server availability and network connection" \
        "Server responses are logged above for debugging" \
        "Try 'opencode-client status --probe' to test connectivity"
}

# Context switching for directory-based isolation
oc_context_switch() {
    local target_dir="$1"
    
    if [[ ! -d "$target_dir" ]]; then
        oc_error_exit 1 "Directory not found: $target_dir" \
            "Ensure the directory exists and is accessible"
        return 1
    fi
    
    local abs_path
    abs_path=$(cd "$target_dir" && pwd)
    export OPENCODE_PROJECT_DIR="$abs_path"
    
    echo "[client] Context switched to: $abs_path" >&2
    echo "[client] Session isolation active for this directory" >&2
    
    # Show current session info if exists
    local session_file
    session_file=$(oc_session_get_file_path "$OPENCODE_URL" "$abs_path")
    if [[ -f "$session_file" ]]; then
        local session_id
        session_id=$(cat "$session_file" 2>/dev/null || echo "")
        echo "[client] Existing session: $session_id" >&2
    else
        echo "[client] No existing session (will create on first message)" >&2
    fi
}

# Profile-based installation
oc_profile_install() {
    local install_type="${1:-user}"
    
    case "$install_type" in
        "user")
            echo "[client] Installing OpenCode client for current user..." >&2
            
            local bin_dir="$HOME/.local/bin"
            mkdir -p "$bin_dir"
            
            # Create wrapper script
            cat > "$bin_dir/opencode-client" << 'EOF'
#!/usr/bin/env bash
exec nix run nixpkgs#opencode-client -- "$@"
EOF
            chmod +x "$bin_dir/opencode-client"
            
            echo "[client] ✅ Installed to $bin_dir/opencode-client"
            echo "[Fix] Add $bin_dir to your PATH if not already present"
            echo "[Next] Run: opencode-client --help"
            ;;
        "system")
            if [[ $EUID -ne 0 ]]; then
                oc_error_exit 1 "System installation requires root privileges" \
                    "Run with sudo or as root user" \
                    "System install places binary in /usr/local/bin"
                return 1
            fi
            
            echo "[client] Installing OpenCode client system-wide..." >&2
            
            local bin_dir="/usr/local/bin"
            
            # Create wrapper script
            cat > "$bin_dir/opencode-client" << 'EOF'
#!/usr/bin/env bash
exec nix run nixpkgs#opencode-client -- "$@"
EOF
            chmod +x "$bin_dir/opencode-client"
            
            echo "[client] ✅ Installed to $bin_dir/opencode-client"
            echo "[Next] Run: opencode-client --help"
            ;;
        "development")
            echo "[client] Development installation (current directory)..." >&2
            
            # Create development wrapper
            cat > "./opencode-client-dev" << EOF
#!/usr/bin/env bash
exec "$SCRIPT_DIR/opencode-client-comprehensive.sh" "\$@"
EOF
            chmod +x "./opencode-client-dev"
            
            echo "[client] ✅ Development client created: ./opencode-client-dev"
            echo "[Next] Run: ./opencode-client-dev --help"
            ;;
        *)
            oc_error_exit 1 "Unknown installation type: $install_type" \
                "Valid types: user, system, development"
            ;;
    esac
}

# Migration support
oc_migration_check() {
    echo "[client] Checking for migration requirements..." >&2
    
    # Check for old session files
    local old_session_dir="$HOME/.opencode/sessions"
    if [[ -d "$old_session_dir" ]]; then
        echo "[client] Found old session directory: $old_session_dir" >&2
        echo "[Fix] Run: opencode-client migrate --from-legacy" >&2
        return 1
    fi
    
    # Check configuration
    if [[ ! -f "$CONFIG_FILE" ]]; then
        echo "[client] No configuration file found" >&2
        echo "[Fix] Run: opencode-client configure" >&2
        return 1
    fi
    
    echo "[client] ✅ No migration required" >&2
    return 0
}

oc_migration_execute() {
    local migration_type="$1"
    
    case "$migration_type" in
        "from-legacy")
            echo "[client] Migrating from legacy session format..." >&2
            
            local old_dir="$HOME/.opencode/sessions"
            local new_base
            new_base=$(oc_session_get_base_dir)
            
            if [[ -d "$old_dir" ]]; then
                mkdir -p "$new_base"
                
                # Copy session files with new structure
                find "$old_dir" -name "*.session" 2>/dev/null | while read -r old_file; do
                    local filename
                    filename=$(basename "$old_file")
                    local new_file="$new_base/127.0.0.1:4096/$filename"
                    
                    mkdir -p "$(dirname "$new_file")"
                    cp "$old_file" "$new_file"
                    echo "[client] Migrated: $filename" >&2
                done
                
                echo "[client] ✅ Migration completed"
                echo "[Next] Run: opencode-client sessions list"
            else
                echo "[client] No legacy sessions found to migrate"
            fi
            ;;
        *)
            oc_error_exit 1 "Unknown migration type: $migration_type" \
                "Valid types: from-legacy"
            ;;
    esac
}

# Status and information display
oc_status_display() {
    local probe="${1:-false}"
    
    echo "OpenCode Comprehensive Client v$VERSION"
    echo "========================================="
    echo
    echo "Configuration:"
    echo "  URL: $OPENCODE_URL"
    echo "  Project Directory: $OPENCODE_PROJECT_DIR"
    echo "  Timeout: ${OPENCODE_TIMEOUT}s"
    echo "  Max Retries: $OPENCODE_MAX_RETRIES"
    echo "  Config File: $CONFIG_FILE"
    echo
    
    if [[ "$probe" == "true" ]]; then
        echo "Connectivity Test:"
        if oc_diagnostic_check "connectivity"; then
            echo
            echo "Performance Test:"
            oc_diagnostic_check "performance"
        fi
        echo
    fi
    
    echo "Session Information:"
    local session_file
    session_file=$(oc_session_get_file_path "$OPENCODE_URL" "$OPENCODE_PROJECT_DIR")
    echo "  Session File: $session_file"
    
    if [[ -f "$session_file" ]]; then
        local session_id
        session_id=$(cat "$session_file" 2>/dev/null || echo "unknown")
        echo "  Session ID: $session_id"
        
        if [[ "$probe" == "true" ]]; then
            if oc_session_validate_api "$OPENCODE_URL" "$session_id" 2>/dev/null; then
                echo "  Status: ✅ Valid and reachable"
            else
                echo "  Status: ❌ Invalid or unreachable"
            fi
        fi
    else
        echo "  Session ID: None (will create on first message)"
    fi
    echo
    
    echo "Available Commands:"
    echo "  send <message>     - Send message to current session"
    echo "  discover          - Find available OpenCode servers"
    echo "  switch <dir>      - Switch to different project directory"
    echo "  sessions list     - List active sessions"
    echo "  configure         - Save current configuration"
    echo "  install <type>    - Install client (user/system/development)"
    echo "  diagnose [type]   - Run diagnostic checks"
    echo "  migrate <type>    - Migrate from older versions"
}

# Command line interface
oc_cli_main() {
    local command="${1:-status}"
    shift || true
    
    case "$command" in
        "send")
            if [[ $# -eq 0 ]]; then
                oc_error_exit 1 "Message text required" \
                    "Provide message as argument: opencode-client send 'your message'"
                return 1
            fi
            oc_send_message "$*"
            ;;
        "discover")
            oc_discover_servers
            ;;
        "switch")
            if [[ $# -eq 0 ]]; then
                oc_error_exit 1 "Directory path required" \
                    "Provide directory path: opencode-client switch /path/to/project"
                return 1
            fi
            oc_context_switch "$1"
            ;;
        "sessions")
            local action="${1:-list}"
            oc_session_manager "$action" "${2:-$OPENCODE_PROJECT_DIR}" "${3:-$OPENCODE_URL}"
            ;;
        "configure")
            oc_save_config
            ;;
        "install")
            local install_type="${1:-user}"
            oc_profile_install "$install_type"
            ;;
        "diagnose"|"diagnostic")
            local check_type="${1:-full}"
            oc_diagnostic_check "$check_type"
            ;;
        "migrate")
            local migration_type="${1:-from-legacy}"
            if [[ "$migration_type" == "check" ]]; then
                oc_migration_check
            else
                oc_migration_execute "$migration_type"
            fi
            ;;
        "status")
            local probe=false
            [[ "${1:-}" == "--probe" ]] && probe=true
            oc_status_display "$probe"
            ;;
        "ps")
            oc_discover_servers
            ;;
        "--help"|"help")
            oc_usage
            ;;
        "--version"|"version")
            echo "OpenCode Comprehensive Client v$VERSION"
            ;;
        *)
            # Treat unknown commands as messages to send
            oc_send_message "$command $*"
            ;;
    esac
}

# Usage information
oc_usage() {
    cat << EOF
OpenCode Comprehensive Client v$VERSION

USAGE:
    $0 <command> [options]

COMMANDS:
    send <message>          Send message to current session
    discover               Find and list available OpenCode servers
    switch <directory>     Switch to different project directory
    sessions <action>      Manage sessions (list, cleanup)
    configure             Save current configuration
    install <type>        Install client (user/system/development)
    diagnose [type]       Run diagnostic checks (connectivity/sessions/performance/full)
    migrate [type]        Migrate from older versions (check/from-legacy)
    status [--probe]      Show client status and configuration
    ps                    Alias for discover
    
ENVIRONMENT VARIABLES:
    OPENCODE_URL          Server URL (default: $DEFAULT_URL)
    OPENCODE_PROJECT_DIR  Project directory (default: current directory)
    OPENCODE_TIMEOUT      Request timeout in seconds (default: $DEFAULT_TIMEOUT)
    OPENCODE_MAX_RETRIES  Maximum retry attempts (default: $DEFAULT_MAX_RETRIES)
    OPENCODE_RETRY_DELAY  Delay between retries in seconds (default: $DEFAULT_RETRY_DELAY)
    OPENCODE_PROVIDER     AI provider (optional)
    OPENCODE_MODEL        AI model (optional)

EXAMPLES:
    $0 send "Hello, how can you help me?"
    $0 discover
    $0 switch /home/user/myproject
    $0 diagnose connectivity
    $0 install user
    $0 status --probe

For more information, visit: https://github.com/sst/opencode
EOF
}

# Main entry point
main() {
    # Load configuration
    oc_load_config
    
    # Run CLI
    oc_cli_main "$@"
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi