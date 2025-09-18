#!/usr/bin/env bash
set -euo pipefail

# message.sh - OpenCode API compliant message sending
# Implements OpenCode API message protocol with consistent error handling

# Default configuration
DEFAULT_URL="http://127.0.0.1:4096"
DEFAULT_TIMEOUT=30

# Usage information
usage() {
    cat << EOF
Usage: $0 [OPTIONS] MESSAGE

Send a message to an OpenCode session using the OpenCode API.

OPTIONS:
    --session=SID           Session ID (required)
    --host=HOST             Host and port (optional, default: 127.0.0.1:4096)
    --url=URL               Full URL (optional, default: http://127.0.0.1:4096)
    --model-provider=ID     Model provider ID (optional)
    --model-id=ID           Model ID (optional)
    --timeout=SECONDS       Request timeout (optional, default: 30)
    --help                  Show this help message

ARGUMENTS:
    MESSAGE                 The message text to send

EXAMPLES:
    $0 --session=my-session "Hello, how are you?"
    $0 --session=test --model-provider=anthropic --model-id=claude-3-haiku "Analyze this data"
    $0 --session=work --host=192.168.1.100:8080 "What's the status?"

EXIT CODES:
    0   Success
    1   Error (client error, network error, invalid arguments)

The script sends a POST request to /session/\$SESSION_ID/message with an OpenCode API
compliant payload: {parts:[{type:"text",text:MESSAGE}]}

If both model-provider and model-id are specified, includes:
{parts:[{type:"text",text:MESSAGE}],model:{providerID:ID,modelID:ID}}
EOF
}

# Parse command line arguments
parse_args() {
    local session_id=""
    local message_text=""
    local base_url=""
    local host=""
    local model_provider=""
    local model_id=""
    local timeout="$DEFAULT_TIMEOUT"
    
    # Parse named arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --session=*)
                session_id="${1#*=}"
                shift
                ;;
            --session)
                if [[ $# -lt 2 ]]; then
                    echo "ERROR: --session requires a value" >&2
                    exit 1
                fi
                session_id="$2"
                shift 2
                ;;
            --host=*)
                host="${1#*=}"
                shift
                ;;
            --host)
                if [[ $# -lt 2 ]]; then
                    echo "ERROR: --host requires a value" >&2
                    exit 1
                fi
                host="$2"
                shift 2
                ;;
            --url=*)
                base_url="${1#*=}"
                shift
                ;;
            --url)
                if [[ $# -lt 2 ]]; then
                    echo "ERROR: --url requires a value" >&2
                    exit 1
                fi
                base_url="$2"
                shift 2
                ;;
            --model-provider=*)
                model_provider="${1#*=}"
                shift
                ;;
            --model-provider)
                if [[ $# -lt 2 ]]; then
                    echo "ERROR: --model-provider requires a value" >&2
                    exit 1
                fi
                model_provider="$2"
                shift 2
                ;;
            --model-id=*)
                model_id="${1#*=}"
                shift
                ;;
            --model-id)
                if [[ $# -lt 2 ]]; then
                    echo "ERROR: --model-id requires a value" >&2
                    exit 1
                fi
                model_id="$2"
                shift 2
                ;;
            --timeout=*)
                timeout="${1#*=}"
                shift
                ;;
            --timeout)
                if [[ $# -lt 2 ]]; then
                    echo "ERROR: --timeout requires a value" >&2
                    exit 1
                fi
                timeout="$2"
                shift 2
                ;;
            --help)
                usage
                exit 0
                ;;
            --*)
                echo "ERROR: Unknown option $1" >&2
                exit 1
                ;;
            *)
                # This should be the message text
                if [[ -z "$message_text" ]]; then
                    message_text="$1"
                else
                    echo "ERROR: Multiple message arguments provided" >&2
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    # Validate required arguments
    if [[ -z "$session_id" ]]; then
        echo "ERROR: --session is required" >&2
        exit 1
    fi
    
    if [[ -z "$message_text" ]]; then
        echo "ERROR: MESSAGE argument is required" >&2
        exit 1
    fi
    
    # Determine the base URL
    if [[ -n "$base_url" ]]; then
        # Use explicit URL
        FINAL_URL="$base_url"
    elif [[ -n "$host" ]]; then
        # Build URL from host
        FINAL_URL="http://$host"
    else
        # Use default
        FINAL_URL="$DEFAULT_URL"
    fi
    
    # Export parsed arguments for use in other functions
    export PARSED_SESSION_ID="$session_id"
    export PARSED_MESSAGE_TEXT="$message_text"
    export PARSED_BASE_URL="$FINAL_URL"
    export PARSED_MODEL_PROVIDER="$model_provider"
    export PARSED_MODEL_ID="$model_id"
    export PARSED_TIMEOUT="$timeout"
}

# Properly escape a string for JSON
json_escape() {
    local input="$1"
    # Escape backslashes, quotes, and common control characters
    printf '%s' "$input" | sed 's/\\/\\\\/g; s/"/\\"/g; s/\x08/\\b/g; s/\x0c/\\f/g; s/\x0a/\\n/g; s/\x0d/\\r/g; s/\x09/\\t/g'
}

# Build OpenCode API compliant JSON payload using jq for safe JSON generation
build_payload() {
    local message_text="$PARSED_MESSAGE_TEXT"
    local model_provider="$PARSED_MODEL_PROVIDER"
    local model_id="$PARSED_MODEL_ID"
    
    # Use jq to safely generate JSON payload with proper escaping
    # This prevents injection vulnerabilities and handles special characters correctly
    jq -n \
        --arg text "$message_text" \
        --arg provider "$model_provider" \
        --arg model "$model_id" \
        '{
            parts: [
                {
                    type: "text", 
                    text: $text
                }
            ]
        } + (
            if ($provider != "" and $model != "") then 
                {
                    model: {
                        providerID: $provider,
                        modelID: $model
                    }
                } 
            else 
                {} 
            end
        )'
}

# Send message using unified-error-handler
send_message() {
    local session_id="$PARSED_SESSION_ID"
    local base_url="$PARSED_BASE_URL"
    local timeout="$PARSED_TIMEOUT"
    
    # Build the endpoint URL
    local endpoint_url="$base_url/session/$session_id/message"
    
    # Build the JSON payload
    local payload
    payload=$(build_payload)
    
    # Find unified-error-handler (should be in parent directory)
    local script_dir
    script_dir="$(dirname "${BASH_SOURCE[0]}")"
    local error_handler="$script_dir/unified-error-handler"
    
    if [[ ! -x "$error_handler" ]]; then
        # Try the .sh version
        error_handler="$script_dir/unified-error-handler.sh"
        if [[ ! -x "$error_handler" ]]; then
            # Try to find it in PATH
            if command -v unified-error-handler >/dev/null 2>&1; then
                error_handler="unified-error-handler"
            else
                echo "ERROR: unified-error-handler not found" >&2
                exit 1
            fi
        fi
    fi
    
    # Execute the request using unified-error-handler
    local response
    
    # unified-error-handler writes errors to stderr, so we only capture stdout
    if response=$("$error_handler" \
        --url="$endpoint_url" \
        --method=POST \
        --data="$payload" \
        --timeout="$timeout" \
        --expect-json); then
        # Success - print the response
        echo "$response"
    else
        # Error - unified-error-handler already wrote error details to stderr
        # We just need to exit with failure code
        exit 1
    fi
}

# Handle errors in a user-friendly way
handle_error() {
    local error_message="$1"
    
    # Check if this is a unified-error-handler formatted error
    if [[ "$error_message" =~ ^[A-Z_]+:.*:.*: ]]; then
        # Parse the error format: ERROR_TYPE:URL:METHOD:DETAILS
        local error_type
        local details
        error_type=$(echo "$error_message" | cut -d: -f1)
        details=$(echo "$error_message" | cut -d: -f4-)
        
        case "$error_type" in
            HTTP_4[0-9][0-9]|HTTP_5[0-9][0-9])
                # Extract HTTP code
                local http_code
                http_code=$(echo "$error_type" | sed 's/HTTP_//')
                echo "ERROR: HTTP $http_code - $details" >&2
                ;;
            TIMEOUT)
                echo "ERROR: Request timed out - $details" >&2
                ;;
            CONNECTION_FAILED)
                echo "ERROR: Could not connect to server - $details" >&2
                ;;
            JSON_PARSE_ERROR)
                echo "ERROR: Invalid JSON response - $details" >&2
                ;;
            *)
                echo "ERROR: $details" >&2
                ;;
        esac
    else
        # Generic error message
        echo "ERROR: $error_message" >&2
    fi
}

# Main execution
main() {
    # Parse command line arguments
    parse_args "$@"
    
    # Send the message
    send_message
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi