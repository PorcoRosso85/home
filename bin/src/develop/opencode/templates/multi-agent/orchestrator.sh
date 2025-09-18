#!/usr/bin/env bash
set -euo pipefail

# OpenCode Multi-Agent Orchestrator (Minimal)
# Simple A→B message forwarding for 2-server setup

# Default configuration
DEFAULT_TIMEOUT=30
DEFAULT_SERVER_A="http://127.0.0.1:4096"
DEFAULT_SERVER_B="http://127.0.0.1:4097"

# Exit codes
readonly EXIT_SUCCESS=0
readonly EXIT_INVALID_ARGS=1
readonly EXIT_SERVER_ERROR=2
readonly EXIT_MESSAGE_ERROR=3

# Parse command line arguments
parse_args() {
    local server_a="$DEFAULT_SERVER_A"
    local server_b="$DEFAULT_SERVER_B"
    local session_a=""
    local session_b=""
    local message=""
    local timeout="$DEFAULT_TIMEOUT"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --server-a=*)
                server_a="${1#*=}"
                shift
                ;;
            --server-b=*)
                server_b="${1#*=}"
                shift
                ;;
            --session-a=*)
                session_a="${1#*=}"
                shift
                ;;
            --session-b=*)
                session_b="${1#*=}"
                shift
                ;;
            --message=*)
                message="${1#*=}"
                shift
                ;;
            --timeout=*)
                timeout="${1#*=}"
                shift
                ;;
            *)
                if [[ -z "$message" ]]; then
                    message="$1"
                fi
                shift
                ;;
        esac
    done
    
    # Export parsed arguments
    export PARSED_SERVER_A="$server_a"
    export PARSED_SERVER_B="$server_b"
    export PARSED_SESSION_A="$session_a"
    export PARSED_SESSION_B="$session_b"
    export PARSED_MESSAGE="$message"
    export PARSED_TIMEOUT="$timeout"
}

# Generate correlation ID for logging
generate_correlation_id() {
    echo "orch_$(date +%s)_$$"
}

# Check if jq is available
check_jq_available() {
    if ! command -v jq >/dev/null 2>&1; then
        echo "[ERROR] jq command not found. jq is required for JSON parsing." >&2
        echo "[ERROR] Please install jq: https://jqlang.github.io/jq/download/" >&2
        return 1
    fi
    return 0
}

# Send message to server using message.sh
send_message() {
    local server="$1"
    local session="$2"
    local message="$3"
    local correlation_id="$4"
    
    echo "[INFO] $correlation_id: Sending message to $server (session: $session)" >&2
    
    # Build message.sh command arguments safely using array
    local args=(message --session="$session" --url="$server" --timeout="$PARSED_TIMEOUT")
    
    # Add model parameters if both environment variables are set
    if [[ -n "${OPENCODE_PROVIDER:-}" && -n "${OPENCODE_MODEL:-}" ]]; then
        echo "[INFO] $correlation_id: Using model provider: $OPENCODE_PROVIDER, model: $OPENCODE_MODEL" >&2
        args+=(--model-provider="$OPENCODE_PROVIDER" --model-id="$OPENCODE_MODEL")
    fi
    
    # Execute message.sh safely with argument array and capture the JSON response
    local response
    if response=$("${args[@]}" -- "$message" 2>&1); then
        # Check if the response looks like valid JSON
        if echo "$response" | jq . >/dev/null 2>&1; then
            echo "[SUCCESS] $correlation_id: Message sent to $server" >&2
            # Output the actual JSON response to stdout for capture
            echo "$response"
            return 0
        else
            echo "[ERROR] $correlation_id: Invalid JSON response from $server: $response" >&2
            return 1
        fi
    else
        echo "[ERROR] $correlation_id: Failed to send message to $server: $response" >&2
        return 1
    fi
}

# Forward message from server A to server B
forward_message() {
    local server_a="$PARSED_SERVER_A"
    local server_b="$PARSED_SERVER_B"
    local session_a="$PARSED_SESSION_A"
    local session_b="$PARSED_SESSION_B"
    local message="$PARSED_MESSAGE"
    
    if [[ -z "$session_a" ]] || [[ -z "$session_b" ]]; then
        echo "ERROR: Both --session-a and --session-b are required for message forwarding" >&2
        return $EXIT_INVALID_ARGS
    fi
    
    if [[ -z "$message" ]]; then
        echo "ERROR: Message is required" >&2
        return $EXIT_INVALID_ARGS
    fi
    
    local correlation_id
    correlation_id=$(generate_correlation_id)
    
    echo "[INFO] $correlation_id: Starting A→B message forwarding"
    echo "[INFO] $correlation_id: Server A: $server_a"
    echo "[INFO] $correlation_id: Server B: $server_b"
    
    # Check jq availability before proceeding
    if ! check_jq_available; then
        echo "[ERROR] $correlation_id: Cannot proceed without jq" >&2
        return $EXIT_SERVER_ERROR
    fi
    
    # Step 1: Send message to Server A and get response
    echo "[INFO] $correlation_id: Sending message to Server A"
    local response_a
    if response_a=$(send_message "$server_a" "$session_a" "$message" "$correlation_id"); then
        echo "[INFO] $correlation_id: Got response from Server A" >&2
        echo "[DEBUG] $correlation_id: Server A response: $response_a" >&2
    else
        echo "[ERROR] $correlation_id: Failed to get response from Server A" >&2
        return $EXIT_SERVER_ERROR
    fi
    
    # Step 2: Extract text content from Server A's JSON response
    echo "[INFO] $correlation_id: Extracting text content from Server A's response" >&2
    local text_content
    local jq_result
    
    # Try to extract text content using jq
    if jq_result=$(echo "$response_a" | jq -r '(.parts[]?|select(.type=="text")|.text)//empty' 2>/dev/null) && [[ -n "$jq_result" ]]; then
        text_content="$jq_result"
        echo "[INFO] $correlation_id: Successfully extracted text content (${#text_content} characters)" >&2
    else
        echo "[WARNING] $correlation_id: No text content found in Server A's response or JSON parsing failed" >&2
        # Fallback strategy: try to extract any string content or use the full response
        if [[ "${ORCHESTRATOR_FALLBACK:-auto}" == "error" ]]; then
            echo "[ERROR] $correlation_id: Text extraction failed and fallback is disabled" >&2
            return $EXIT_MESSAGE_ERROR
        else
            echo "[WARNING] $correlation_id: Using full response as fallback" >&2
            text_content="$response_a"
        fi
    fi
    
    # Step 3: Forward extracted text content to Server B
    echo "[INFO] $correlation_id: Forwarding extracted text content to Server B (${#text_content} characters)" >&2
    local response_b
    if response_b=$(send_message "$server_b" "$session_b" "$text_content" "$correlation_id"); then
        echo "[SUCCESS] $correlation_id: A→B forwarding completed successfully" >&2
        echo "[INFO] $correlation_id: Server B response: $response_b" >&2
        return 0
    else
        echo "[ERROR] $correlation_id: Failed to forward to Server B" >&2
        return $EXIT_SERVER_ERROR
    fi
}

# Test server connectivity
test_servers() {
    local server_a="$PARSED_SERVER_A"
    local server_b="$PARSED_SERVER_B"
    local correlation_id
    correlation_id=$(generate_correlation_id)
    
    echo "[INFO] $correlation_id: Testing server connectivity"
    
    # Test Server A
    if unified-error-handler --url="$server_a/doc" --method="GET" --timeout="$PARSED_TIMEOUT" >/dev/null 2>&1; then
        echo "[SUCCESS] $correlation_id: Server A ($server_a) is accessible"
    else
        echo "[ERROR] $correlation_id: Server A ($server_a) is not accessible" >&2
        return $EXIT_SERVER_ERROR
    fi
    
    # Test Server B
    if unified-error-handler --url="$server_b/doc" --method="GET" --timeout="$PARSED_TIMEOUT" >/dev/null 2>&1; then
        echo "[SUCCESS] $correlation_id: Server B ($server_b) is accessible"
    else
        echo "[ERROR] $correlation_id: Server B ($server_b) is not accessible" >&2
        return $EXIT_SERVER_ERROR
    fi
    
    echo "[SUCCESS] $correlation_id: Both servers are accessible"
    return 0
}

# Show simple status
show_status() {
    local server_a="$PARSED_SERVER_A"
    local server_b="$PARSED_SERVER_B"
    
    echo "OpenCode Multi-Agent Orchestrator (Minimal)"
    echo "Server A: $server_a"
    echo "Server B: $server_b"
    echo "Timeout: $PARSED_TIMEOUT seconds"
    
    # Quick connectivity check
    if test_servers >/dev/null 2>&1; then
        echo "Status: Both servers accessible"
    else
        echo "Status: Server connectivity issues detected"
    fi
}

# Usage information
usage() {
    cat << EOF
Usage: $0 [OPTIONS] [MESSAGE]

Minimal orchestrator for A→B message forwarding between 2 OpenCode servers.

OPTIONS:
    --server-a=URL          Server A URL (default: $DEFAULT_SERVER_A)
    --server-b=URL          Server B URL (default: $DEFAULT_SERVER_B)
    --session-a=SID         Session ID for Server A (required for forwarding)
    --session-b=SID         Session ID for Server B (required for forwarding)
    --timeout=SECONDS       Request timeout (default: $DEFAULT_TIMEOUT)

ACTIONS:
    forward                 Forward message from A to B (requires sessions)
    test                    Test server connectivity
    status                  Show orchestrator status

ENVIRONMENT VARIABLES:
    OPENCODE_PROVIDER       Model provider ID (e.g., 'anthropic')
    OPENCODE_MODEL          Model ID (e.g., 'claude-3-haiku')
    ORCHESTRATOR_FALLBACK   Fallback behavior: 'auto' (default) or 'error'

EXAMPLES:
    $0 --session-a=sess1 --session-b=sess2 forward "Hello from A to B"
    OPENCODE_PROVIDER=anthropic OPENCODE_MODEL=claude-3-haiku $0 --session-a=sess1 --session-b=sess2 forward "Analyze this"
    $0 test
    $0 status

The orchestrator sends MESSAGE to Server A, extracts text content from the JSON response,
then forwards only the extracted text to Server B. Requires jq for JSON parsing.
EOF
}

# Main action dispatcher
main() {
    parse_args "$@"
    
    # Determine action (first non-option argument or "status" as default)
    local action=""
    if [[ -n "$PARSED_MESSAGE" ]]; then
        # If message looks like an action, treat it as such
        case "$PARSED_MESSAGE" in
            "forward"|"test"|"status"|"--help")
                action="$PARSED_MESSAGE"
                export PARSED_MESSAGE=""
                ;;
            *)
                action="forward"
                ;;
        esac
    else
        action="status"
    fi
    
    case "$action" in
        "forward")
            forward_message
            ;;
        "test")
            test_servers
            ;;
        "status")
            show_status
            ;;
        "--help")
            usage
            ;;
        *)
            echo "ERROR: Unknown action: $action" >&2
            echo "Valid actions: forward, test, status" >&2
            echo "Use --help for usage information" >&2
            return $EXIT_INVALID_ARGS
            ;;
    esac
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi