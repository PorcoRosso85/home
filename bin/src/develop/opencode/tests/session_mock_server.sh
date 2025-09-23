#!/usr/bin/env bash
set -euo pipefail

# Enhanced Mock OpenCode Server for CI Testing
# Provides comprehensive endpoint simulation with enhanced features:
# - All required endpoints (/doc, /config/providers, session management)
# - Background process management with proper cleanup
# - Request logging and verification
# - Parameter validation (directory parameter)
# - Port conflict detection and timeout handling

# Configuration
MOCK_PORT="${1:-4096}"
MOCK_LOG="/tmp/opencode_mock_$$.log"
MOCK_PID_FILE="/tmp/opencode_mock_$$.pid"
MOCK_DATA_DIR="/tmp/opencode_mock_$$_data"

# Global state for session management
declare -A MOCK_SESSIONS=()
declare -A MOCK_MESSAGES=()

# Utility Functions
mock_log() {
    local level="$1"
    shift
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] $*" >> "$MOCK_LOG"
}

mock_error() {
    mock_log "ERROR" "$@"
    echo "[mock-server] ERROR: $*" >&2
}

mock_info() {
    mock_log "INFO" "$@"
    echo "[mock-server] $*" >&2
}

mock_debug() {
    mock_log "DEBUG" "$@"
}

# Enhanced HTTP response functions with proper Content-Length calculation
response_json() {
    local status_code="$1"
    local json_content="$2"
    local content_length=${#json_content}

    cat << EOF
HTTP/1.1 $status_code
Content-Type: application/json
Content-Length: $content_length
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type

$json_content
EOF
}

response_doc() {
    response_json "200 OK" '{"openapi": "3.0.0", "info": {"title": "Mock OpenCode API", "version": "1.0.0"}, "status": "healthy"}'
}

response_config_providers() {
    local providers_json='{"providers": [{"id": "mock", "name": "Mock Provider", "models": [{"id": "mock-model", "name": "Mock Model"}]}]}'
    response_json "200 OK" "$providers_json"
}

response_create_session() {
    local session_id="sess_mock_$(date +%s)_$$"
    MOCK_SESSIONS["$session_id"]="created"
    MOCK_MESSAGES["$session_id"]="[]"

    mock_debug "Created session: $session_id"
    response_json "200 OK" "{\"id\": \"$session_id\"}"
}

response_validate_session() {
    local session_id="$1"

    if [[ -n "${MOCK_SESSIONS[$session_id]:-}" ]]; then
        mock_debug "Session $session_id validated successfully"
        response_json "200 OK" '{"status": "ok"}'
    else
        mock_debug "Session $session_id not found"
        response_json "404 Not Found" '{"error": "Session not found"}'
    fi
}

response_send_message() {
    local session_id="$1"
    local directory="$2"
    local message_data="$3"

    mock_debug "Sending message to session $session_id, directory: $directory"
    mock_debug "Message data: $message_data"

    # Verify session exists
    if [[ -z "${MOCK_SESSIONS[$session_id]:-}" ]]; then
        response_json "404 Not Found" '{"error": "Session not found"}'
        return
    fi

    # Verify directory parameter (required for opencode-client)
    if [[ -z "$directory" ]]; then
        response_json "400 Bad Request" '{"error": "Missing directory parameter"}'
        return
    fi

    # Mock successful message with test response
    local response_text="test successful"
    if echo "$message_data" | grep -i "respond with just" >/dev/null 2>&1; then
        # Extract the requested response from the message
        response_text=$(echo "$message_data" | sed -n 's/.*respond with just: \([^"]*\).*/\1/p' || echo "test successful")
    fi

    # Store message in session history
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local user_message="{\"id\": \"msg_user_$(date +%s)\", \"info\": {\"role\": \"user\"}, \"parts\": [${message_data}], \"timestamp\": \"$timestamp\"}"
    local assistant_message="{\"id\": \"msg_assistant_$(date +%s)\", \"info\": {\"role\": \"assistant\"}, \"parts\": [{\"type\": \"text\", \"text\": \"$response_text\"}], \"timestamp\": \"$timestamp\"}"

    # Update session messages
    local current_messages="${MOCK_MESSAGES[$session_id]}"
    if [[ "$current_messages" == "[]" ]]; then
        MOCK_MESSAGES["$session_id"]="[$user_message, $assistant_message]"
    else
        # Remove closing bracket and add new messages
        current_messages="${current_messages%]}"
        MOCK_MESSAGES["$session_id"]="$current_messages, $user_message, $assistant_message]"
    fi

    # Return immediate response (simulating synchronous response)
    response_json "200 OK" "{\"parts\": [{\"type\": \"text\", \"text\": \"$response_text\"}]}"
}

response_get_messages() {
    local session_id="$1"

    if [[ -z "${MOCK_SESSIONS[$session_id]:-}" ]]; then
        response_json "404 Not Found" '{"error": "Session not found"}'
        return
    fi

    local messages="${MOCK_MESSAGES[$session_id]:-[]}"
    response_json "200 OK" "$messages"
}

response_options() {
    cat << 'EOF'
HTTP/1.1 200 OK
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
Content-Length: 0

EOF
}

response_not_found() {
    response_json "404 Not Found" '{"error": "Endpoint not found"}'
}

# Enhanced request parser with query parameter support
parse_query_params() {
    local query_string="$1"
    declare -A params=()

    if [[ -n "$query_string" ]]; then
        IFS='&' read -ra PAIRS <<< "$query_string"
        for pair in "${PAIRS[@]}"; do
            IFS='=' read -ra KV <<< "$pair"
            local key="${KV[0]}"
            local value="${KV[1]:-}"
            # URL decode
            value=$(printf '%b' "${value//%/\\x}")
            params["$key"]="$value"
        done
    fi

    # Return directory parameter for compatibility
    echo "${params[directory]:-}"
}

# Parse HTTP request and route to appropriate handler
handle_request() {
    local request_line headers_content query_params directory message_body

    # Read request line
    read -r request_line
    mock_debug "Request: $request_line"

    # Read headers and capture any body content
    headers_content=""
    while IFS= read -r line && [[ "$line" != $'\r' ]]; do
        headers_content+="$line"$'\n'
        mock_debug "Header: $line"

        # Check for Content-Length to read message body
        if [[ "$line" =~ ^Content-Length:\ ([0-9]+) ]]; then
            local content_length="${BASH_REMATCH[1]}"
            if [[ "$content_length" -gt 0 ]]; then
                message_body=$(head -c "$content_length")
                mock_debug "Body: $message_body"
            fi
        fi
    done

    # Parse request components
    local method path query_string
    read -r method path <<< "$request_line"

    # Extract query string if present
    if [[ "$path" == *"?"* ]]; then
        query_string="${path#*?}"
        path="${path%%?*}"
    else
        query_string=""
    fi

    directory=$(parse_query_params "$query_string")

    # Route to appropriate handler
    case "$method $path" in
        "GET /doc"*)
            mock_debug "Handling /doc endpoint"
            response_doc
            ;;
        "GET /config/providers"*)
            mock_debug "Handling /config/providers endpoint"
            response_config_providers
            ;;
        "POST /session")
            mock_debug "Handling session creation"
            response_create_session
            ;;
        "GET /session/"*)
            local session_id="${path#/session/}"
            mock_debug "Handling session validation for: $session_id"
            response_validate_session "$session_id"
            ;;
        "POST /session/"*"/message")
            local session_path="${path#/session/}"
            local session_id="${session_path%/message}"
            mock_debug "Handling message send for session: $session_id"
            response_send_message "$session_id" "$directory" "$message_body"
            ;;
        "GET /session/"*"/message")
            local session_path="${path#/session/}"
            local session_id="${session_path%/message}"
            mock_debug "Handling message retrieval for session: $session_id"
            response_get_messages "$session_id"
            ;;
        "OPTIONS "*)
            mock_debug "Handling OPTIONS request"
            response_options
            ;;
        *)
            mock_debug "No handler for: $method $path"
            response_not_found
            ;;
    esac
}

# Process management functions
start_mock_server() {
    local port="$1"

    # Check if port is already in use
    if command -v ss >/dev/null 2>&1; then
        if ss -ln "sport = :$port" | grep -q ":$port "; then
            mock_error "Port $port is already in use"
            return 1
        fi
    elif command -v lsof >/dev/null 2>&1; then
        if lsof -Pi ":$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
            mock_error "Port $port is already in use"
            return 1
        fi
    fi

    mock_info "Starting mock OpenCode server on port $port"
    mock_info "Log file: $MOCK_LOG"
    mock_info "PID file: $MOCK_PID_FILE"

    # Ensure data directory exists
    mkdir -p "$MOCK_DATA_DIR"

    # Store our PID for cleanup
    echo $$ > "$MOCK_PID_FILE"

    # Set up signal handlers for cleanup
    trap 'cleanup_and_exit' EXIT INT TERM

    # Start the server loop
    local server_script="$0"
    while true; do
        mock_debug "Waiting for connection on port $port"

        # Use timeout to prevent hanging
        if command -v timeout >/dev/null 2>&1; then
            timeout 60s nc -l -p "$port" -c "$(which bash) -c 'source $server_script; handle_request'" 2>/dev/null || {
                local exit_code=$?
                if [[ $exit_code -eq 124 ]]; then
                    mock_debug "Connection timeout (60s), restarting listener"
                else
                    mock_debug "nc exited with code $exit_code, restarting listener"
                fi
            }
        else
            nc -l -p "$port" -c "$(which bash) -c 'source $server_script; handle_request'" 2>/dev/null || {
                mock_debug "nc exited, restarting listener"
            }
        fi

        # Small delay to prevent rapid restart loops
        sleep 0.1
    done
}

start_mock_server_background() {
    local port="${1:-$MOCK_PORT}"

    # Check if already running
    if [[ -f "$MOCK_PID_FILE" ]] && kill -0 "$(cat "$MOCK_PID_FILE")" 2>/dev/null; then
        mock_info "Mock server already running (PID: $(cat "$MOCK_PID_FILE"))"
        return 0
    fi

    mock_info "Starting mock server in background on port $port"

    # Start server in background
    start_mock_server "$port" &
    local server_pid=$!
    echo "$server_pid" > "$MOCK_PID_FILE"

    # Wait for server to be ready
    local attempts=0
    local max_attempts=30
    while [[ $attempts -lt $max_attempts ]]; do
        if curl -s --max-time 2 "http://127.0.0.1:$port/doc" >/dev/null 2>&1; then
            mock_info "Mock server ready and responding on port $port"
            return 0
        fi
        sleep 0.5
        ((attempts++))
    done

    mock_error "Mock server failed to start within timeout"
    stop_mock_server
    return 1
}

stop_mock_server() {
    if [[ -f "$MOCK_PID_FILE" ]]; then
        local pid=$(cat "$MOCK_PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            mock_info "Stopping mock server (PID: $pid)"
            kill "$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null

            # Wait for process to stop
            local attempts=0
            while [[ $attempts -lt 10 ]] && kill -0 "$pid" 2>/dev/null; do
                sleep 0.5
                ((attempts++))
            done

            if kill -0 "$pid" 2>/dev/null; then
                mock_error "Failed to stop server process $pid"
                return 1
            fi
        fi
        rm -f "$MOCK_PID_FILE"
    fi

    cleanup_resources
    mock_info "Mock server stopped"
}

cleanup_resources() {
    # Clean up temporary files
    rm -rf "$MOCK_DATA_DIR" 2>/dev/null || true
    rm -f "$MOCK_PID_FILE" 2>/dev/null || true

    # Note: Keep log file for debugging
    mock_debug "Cleaned up resources"
}

cleanup_and_exit() {
    mock_debug "Cleanup signal received"
    cleanup_resources
    exit 0
}

get_mock_server_status() {
    if [[ -f "$MOCK_PID_FILE" ]]; then
        local pid=$(cat "$MOCK_PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            echo "running"
            return 0
        fi
    fi
    echo "stopped"
    return 1
}

# Testing and verification functions
test_mock_server() {
    local port="${1:-$MOCK_PORT}"
    local base_url="http://127.0.0.1:$port"

    mock_info "Testing mock server endpoints at $base_url"

    # Test health check
    if curl -s --max-time 5 "$base_url/doc" | grep -q "healthy"; then
        mock_info "✅ /doc endpoint working"
    else
        mock_error "❌ /doc endpoint failed"
        return 1
    fi

    # Test config/providers
    if curl -s --max-time 5 "$base_url/config/providers" | grep -q "providers"; then
        mock_info "✅ /config/providers endpoint working"
    else
        mock_error "❌ /config/providers endpoint failed"
        return 1
    fi

    # Test session creation
    local session_response
    session_response=$(curl -s --max-time 5 -X POST "$base_url/session" -H "Content-Type: application/json" -d '{}')
    local session_id
    session_id=$(echo "$session_response" | grep -o '"id": *"[^"]*"' | sed 's/"id": *"\([^"]*\)"/\1/')

    if [[ -n "$session_id" ]]; then
        mock_info "✅ Session creation working (ID: $session_id)"

        # Test message sending
        local message_response
        message_response=$(curl -s --max-time 5 -X POST "$base_url/session/$session_id/message?directory=/tmp" \
            -H "Content-Type: application/json" \
            -d '{"parts": [{"type": "text", "text": "respond with just: test successful"}]}')

        if echo "$message_response" | grep -q "test successful"; then
            mock_info "✅ Message sending working"
        else
            mock_error "❌ Message sending failed"
            return 1
        fi
    else
        mock_error "❌ Session creation failed"
        return 1
    fi

    mock_info "All endpoint tests passed"
    return 0
}

# Usage information
show_usage() {
    cat << 'EOF'
Enhanced Mock OpenCode Server for CI Testing

Usage:
  ./session_mock_server.sh [PORT]                    # Start server (foreground)
  ./session_mock_server.sh start [PORT]              # Start server (background)
  ./session_mock_server.sh stop                      # Stop background server
  ./session_mock_server.sh status                    # Check server status
  ./session_mock_server.sh test [PORT]               # Test server endpoints
  ./session_mock_server.sh help                      # Show this help

Environment Variables:
  OPENCODE_TIMEOUT        Request timeout in seconds (default: 30)

Features:
  - All required OpenCode API endpoints
  - Background process management with cleanup
  - Request logging and parameter verification
  - Port conflict detection and timeout handling
  - Compatible with quick-start-test.sh and opencode-client

Examples:
  # Start server for testing
  ./session_mock_server.sh start 4096

  # Run quick-start test against mock server
  OPENCODE_URL=http://127.0.0.1:4096 ./quick-start-test.sh

  # Stop server
  ./session_mock_server.sh stop

Log File: $MOCK_LOG
EOF
}

# Main function with command routing
main() {
    local command="${1:-start}"

    case "$command" in
        "help"|"--help"|"-h")
            show_usage
            ;;
        "start")
            local port="${2:-$MOCK_PORT}"
            start_mock_server_background "$port"
            ;;
        "stop")
            stop_mock_server
            ;;
        "status")
            local status=$(get_mock_server_status)
            echo "Mock server status: $status"
            if [[ "$status" == "running" ]]; then
                echo "PID: $(cat "$MOCK_PID_FILE" 2>/dev/null || echo "unknown")"
                echo "Log: $MOCK_LOG"
            fi
            ;;
        "test")
            local port="${2:-$MOCK_PORT}"
            test_mock_server "$port"
            ;;
        [0-9]*)
            # Port number provided - start in foreground for compatibility
            MOCK_PORT="$command"
            start_mock_server "$MOCK_PORT"
            ;;
        *)
            if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
                # Called directly with unknown command - start server in foreground
                start_mock_server "$MOCK_PORT"
            else
                # Sourced - functions available for testing
                mock_info "Mock server functions loaded"
            fi
            ;;
    esac
}

# Only run main if script is executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi