#!/usr/bin/env bash
set -euo pipefail

# Mock OpenCode server for self-contained testing
# Uses GNU netcat to provide /doc, /session, and /session/:id endpoints

MOCK_PORT="${1:-4099}"
MOCK_LOG="/tmp/opencode_mock_$$.log"

# Mock responses
response_health() {
    cat << 'EOF'
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 24

{"status": "healthy"}
EOF
}

response_create_session() {
    local session_id="sess_mock_$(date +%s)_$$"
    cat << EOF
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: $(printf '{"id": "%s"}' "$session_id" | wc -c)

{"id": "$session_id"}
EOF
}

response_validate_session() {
    local session_id="$1"
    # Mock: sessions containing 'valid' are valid, others return 404
    if [[ "$session_id" =~ valid ]]; then
        cat << 'EOF'
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 18

{"status": "ok"}
EOF
    else
        cat << 'EOF'
HTTP/1.1 404 Not Found
Content-Type: application/json
Content-Length: 23

{"error": "not found"}
EOF
    fi
}

response_send_message() {
    cat << 'EOF'
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 62

{"parts": [{"type": "text", "text": "Mock response"}]}
EOF
}

# Parse HTTP request and route to appropriate handler
handle_request() {
    local request_line
    read -r request_line
    echo "Request: $request_line" >> "$MOCK_LOG"
    
    # Skip headers
    while read -r line && [[ "$line" != $'\r' ]]; do
        echo "Header: $line" >> "$MOCK_LOG"
    done
    
    # Route based on request
    case "$request_line" in
        "GET /doc"*) 
            response_health
            ;;
        "POST /session"*)
            response_create_session
            ;;
        "GET /session/"*) 
            local session_id
            session_id=$(echo "$request_line" | sed 's|GET /session/\([^ ]*\).*|\1|')
            response_validate_session "$session_id"
            ;;
        "POST /session/"*"/message"*) 
            response_send_message
            ;;
        *)
            cat << 'EOF'
HTTP/1.1 404 Not Found
Content-Type: text/plain
Content-Length: 9

Not Found
EOF
            ;;
    esac
}

# Start mock server
start_mock_server() {
    echo "Starting mock OpenCode server on port $MOCK_PORT"
    echo "Log: $MOCK_LOG"
    
    # GNU netcat with -c option for command execution per connection
    while true; do
        echo "$(date): Waiting for connection" >> "$MOCK_LOG"
        nc -l -p "$MOCK_PORT" -c "$(which bash) -c 'source $0; handle_request'"
    done
}

# Main function
main() {
    if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
        # Called directly - start server
        start_mock_server
    else
        # Sourced - functions available for testing
        echo "Mock server functions loaded"
    fi
}

main "$@"