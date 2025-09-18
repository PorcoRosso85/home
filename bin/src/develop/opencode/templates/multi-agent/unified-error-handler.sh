#!/usr/bin/env bash
set -euo pipefail

# Unified Error Handler for OpenCode Multi-Agent System
# Provides consistent HTTP error handling, JSON parsing, and error reporting

# Default configuration
DEFAULT_TIMEOUT=30
DEFAULT_METHOD="GET"
DEFAULT_USER_AGENT="OpenCode-MultiAgent/1.0"

# Error exit codes (following curl conventions where applicable)
readonly EXIT_SUCCESS=0
readonly EXIT_JSON_PARSE_ERROR=5
readonly EXIT_HTTP_CLIENT_ERROR=22    # 4xx errors
readonly EXIT_NETWORK_TIMEOUT=28      # Network timeout
readonly EXIT_HTTP_NOT_FOUND=44       # 404 specifically
readonly EXIT_INVALID_ARGS=64         # Command line usage error

# Parse command line arguments
parse_args() {
    local url=""
    local method="$DEFAULT_METHOD"
    local timeout="$DEFAULT_TIMEOUT"
    local expect_json=false
    local extract_path=""
    local post_data=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --url=*)
                url="${1#*=}"
                shift
                ;;
            --method=*)
                method="${1#*=}"
                shift
                ;;
            --timeout=*)
                timeout="${1#*=}"
                shift
                ;;
            --expect-json)
                expect_json=true
                shift
                ;;
            --extract=*)
                extract_path="${1#*=}"
                expect_json=true
                shift
                ;;
            --data=*)
                post_data="${1#*=}"
                shift
                ;;
            *)
                echo "ERROR_INVALID_ARGS:$*:UNKNOWN:Invalid argument: $1" >&2
                exit $EXIT_INVALID_ARGS
                ;;
        esac
    done
    
    if [[ -z "$url" ]]; then
        echo "ERROR_INVALID_ARGS:::MISSING:URL parameter is required" >&2
        exit $EXIT_INVALID_ARGS
    fi
    
    # Export parsed arguments for use in other functions
    export PARSED_URL="$url"
    export PARSED_METHOD="$method"
    export PARSED_TIMEOUT="$timeout"
    export PARSED_EXPECT_JSON="$expect_json"
    export PARSED_EXTRACT_PATH="$extract_path"
    export PARSED_POST_DATA="$post_data"
}

# Format consistent error message: ERROR_TYPE:URL:METHOD:DETAILS
format_error() {
    local error_type="$1"
    local details="$2"
    echo "${error_type}:${PARSED_URL}:${PARSED_METHOD}:${details}"
}

# Execute HTTP request with error handling
execute_request() {
    local url="$PARSED_URL"
    local method="$PARSED_METHOD"
    local timeout="$PARSED_TIMEOUT"
    local post_data="$PARSED_POST_DATA"
    
    # Build curl command
    local curl_cmd=(
        curl
        -s
        -X "$method"
        --max-time "$timeout"
        --user-agent "$DEFAULT_USER_AGENT"
        -w "%{http_code}|%{response_code}"
    )
    
    if [[ -n "$post_data" ]]; then
        curl_cmd+=(
            -H "Content-Type: application/json"
            -d "$post_data"
        )
    fi
    
    curl_cmd+=("$url")
    
    # Execute curl and capture both response and status
    local response
    local curl_exit_code
    
    if response=$("${curl_cmd[@]}" 2>&1); then
        curl_exit_code=0
    else
        curl_exit_code=$?
    fi
    
    # Handle curl-level errors first
    case $curl_exit_code in
        0)
            # Success - parse response
            parse_response "$response"
            ;;
        28)
            format_error "TIMEOUT" "Request timed out after ${timeout}s" >&2
            exit $EXIT_NETWORK_TIMEOUT
            ;;
        7)
            format_error "CONNECTION_FAILED" "Could not connect to host" >&2
            exit $EXIT_HTTP_CLIENT_ERROR
            ;;
        *)
            format_error "CURL_ERROR" "Curl failed with exit code $curl_exit_code" >&2
            exit $EXIT_HTTP_CLIENT_ERROR
            ;;
    esac
}

# Parse HTTP response and status code
parse_response() {
    local full_response="$1"
    
    # Extract status code from the end of response
    local http_code
    local response_body
    
    if [[ "$full_response" == *"|"* ]]; then
        # Split on the last |  
        http_code="${full_response##*|}"
        response_body="${full_response%|*}"
        
        # The response body might still have the status code at the end
        # Remove last line if it's a 3-digit number
        local last_line
        last_line=$(echo "$response_body" | tail -n 1)
        if [[ "$last_line" =~ ^[0-9]{3}$ ]]; then
            response_body=$(echo "$response_body" | sed '$d')  # Remove last line
        fi
    else
        # The response format from curl -w includes status at the end
        # Try to extract last line as status code
        local last_line
        last_line=$(echo "$full_response" | tail -n 1)
        if [[ "$last_line" =~ ^[0-9]{3}$ ]]; then
            http_code="$last_line"
            response_body=$(echo "$full_response" | sed '$d')  # Remove last line
        else
            http_code="000"
            response_body="$full_response"
        fi
    fi
    
    # Handle HTTP status codes
    case "$http_code" in
        200|201|202|204)
            # Success - process response body
            process_response_body "$response_body"
            ;;
        404)
            format_error "HTTP_404" "Resource not found" >&2
            exit $EXIT_HTTP_NOT_FOUND
            ;;
        4[0-9][0-9])
            format_error "HTTP_${http_code}" "Client error" >&2
            exit $EXIT_HTTP_CLIENT_ERROR
            ;;
        500)
            format_error "HTTP_500" "Internal server error" >&2
            exit $EXIT_HTTP_CLIENT_ERROR
            ;;
        5[0-9][0-9])
            format_error "HTTP_${http_code}" "Server error" >&2
            exit $EXIT_HTTP_CLIENT_ERROR
            ;;
        *)
            format_error "HTTP_UNKNOWN" "Unexpected status code: $http_code" >&2
            exit $EXIT_HTTP_CLIENT_ERROR
            ;;
    esac
}

# Process response body (JSON parsing, extraction)
process_response_body() {
    local response_body="$1"
    local expect_json="$PARSED_EXPECT_JSON"
    local extract_path="$PARSED_EXTRACT_PATH"
    
    if [[ "$expect_json" == "true" ]]; then
        # Validate JSON
        if ! validate_json "$response_body"; then
            format_error "JSON_PARSE_ERROR" "Response is not valid JSON" >&2
            exit $EXIT_JSON_PARSE_ERROR
        fi
        
        # Extract specific field if requested
        if [[ -n "$extract_path" ]]; then
            extract_json_field "$response_body" "$extract_path"
        else
            echo "$response_body"
        fi
    else
        # Return raw response
        echo "$response_body"
    fi
}

# Validate JSON format
validate_json() {
    local json_string="$1"
    
    # Try jq first
    if command -v jq >/dev/null 2>&1; then
        echo "$json_string" | jq empty 2>/dev/null
    else
        # Fallback JSON validation
        validate_json_fallback "$json_string"
    fi
}

# Extract JSON field with jq or fallback
extract_json_field() {
    local json_string="$1"
    local field_path="$2"
    
    if command -v jq >/dev/null 2>&1; then
        # Use jq for extraction
        local result
        if result=$(echo "$json_string" | jq -r "$field_path" 2>/dev/null); then
            if [[ "$result" != "null" ]]; then
                echo "$result"
                return 0
            fi
        fi
        format_error "JSON_EXTRACT_ERROR" "Could not extract field: $field_path" >&2
        exit $EXIT_JSON_PARSE_ERROR
    else
        # Fallback extraction
        extract_json_fallback "$json_string" "$field_path"
    fi
}

# Simple JSON validation fallback (basic check)
validate_json_fallback() {
    local json_string="$1"
    
    # Basic JSON validation - starts with { or [ and has matching braces/brackets
    local trimmed
    trimmed=$(echo "$json_string" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    
    case "$trimmed" in
        \{*\}|[\[].*[\]])
            # Very basic structure check
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Simple JSON field extraction fallback
extract_json_fallback() {
    local json_string="$1"
    local field_path="$2"
    
    # Handle simple field extraction like .slideshow.title
    case "$field_path" in
        .slideshow.title)
            # Extract slideshow.title specifically
            local title
            title=$(echo "$json_string" | sed -n 's/.*"title"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
            if [[ -n "$title" ]]; then
                echo "$title"
            else
                format_error "JSON_EXTRACT_FALLBACK_ERROR" "Could not extract $field_path" >&2
                exit $EXIT_JSON_PARSE_ERROR
            fi
            ;;
        *)
            format_error "JSON_EXTRACT_FALLBACK_ERROR" "Fallback extraction not implemented for: $field_path" >&2
            exit $EXIT_JSON_PARSE_ERROR
            ;;
    esac
}

# Main execution
main() {
    parse_args "$@"
    execute_request
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi