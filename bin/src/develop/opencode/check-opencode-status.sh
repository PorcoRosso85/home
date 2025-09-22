#!/usr/bin/env bash
# OpenCode Configuration Diagnostic Script
# Provides comprehensive status check of OpenCode TUI vs HTTP API configuration differences

set -euo pipefail

# Default values
OPENCODE_URL="${OPENCODE_URL:-http://127.0.0.1:4096}"
FORMAT="text"
TIMEOUT=5

# Help function
show_help() {
    cat << EOF
OpenCode Configuration Diagnostic Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --url URL          OpenCode server URL (default: $OPENCODE_URL)
    --format FORMAT    Output format: text|json (default: text)
    --timeout SECONDS  HTTP timeout in seconds (default: $TIMEOUT)
    --help            Show this help

DESCRIPTION:
    Diagnoses OpenCode configuration status, including TUI vs HTTP API differences.
    Helps identify common configuration issues and provides actionable guidance.

EXAMPLES:
    $0                                    # Basic status check
    $0 --format json                      # JSON output for scripting
    $0 --url http://localhost:4097        # Check different server
    $0 --timeout 10                       # Longer timeout for slow servers

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --url)
            if [[ $# -lt 2 ]]; then
                echo "Error: --url requires a value" >&2
                exit 1
            fi
            OPENCODE_URL="$2"
            shift 2
            ;;
        --format)
            if [[ $# -lt 2 ]]; then
                echo "Error: --format requires a value" >&2
                exit 1
            fi
            FORMAT="$2"
            if [[ "$FORMAT" != "text" && "$FORMAT" != "json" ]]; then
                echo "Error: Format must be 'text' or 'json'" >&2
                exit 1
            fi
            shift 2
            ;;
        --timeout)
            if [[ $# -lt 2 ]]; then
                echo "Error: --timeout requires a value" >&2
                exit 1
            fi
            TIMEOUT="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Error: Unknown option $1" >&2
            show_help >&2
            exit 1
            ;;
    esac
done

# Check if required tools are available
check_dependencies() {
    local missing=()
    for tool in curl jq; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            missing+=("$tool")
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        echo "Error: Missing required tools: ${missing[*]}" >&2
        echo "Hint: Run 'nix develop' to get all required tools" >&2
        exit 1
    fi
}

# Test server connectivity
test_server_connectivity() {
    if curl -s --max-time "$TIMEOUT" "$OPENCODE_URL/health" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Get server configuration
get_server_config() {
    curl -s --max-time "$TIMEOUT" "$OPENCODE_URL/config/providers" 2>/dev/null || echo "{}"
}

# Get app info
get_app_info() {
    curl -s --max-time "$TIMEOUT" "$OPENCODE_URL/app" 2>/dev/null || echo "{}"
}

# Test model identification
test_model_identification() {
    local sid
    sid=$(curl -s --max-time "$TIMEOUT" -X POST "$OPENCODE_URL/session" \
        -H 'Content-Type: application/json' \
        -d '{}' 2>/dev/null | jq -r '.id // empty')

    if [[ -n "$sid" ]]; then
        local response
        response=$(curl -s --max-time "$TIMEOUT" -X POST "$OPENCODE_URL/session/$sid/message" \
            -H 'Content-Type: application/json' \
            -d '{"parts":[{"type":"text","text":"What AI model are you? Just state your name briefly."}]}' \
            2>/dev/null || echo '{}')

        echo "$response" | jq -r '.parts[0].text // "No response"' 2>/dev/null || echo "Parse error"
    else
        echo "Session creation failed"
    fi
}

# Check environment variables
check_environment() {
    local env_vars=()

    [[ -n "${OPENCODE_PROVIDER:-}" ]] && env_vars+=("OPENCODE_PROVIDER=$OPENCODE_PROVIDER")
    [[ -n "${OPENCODE_MODEL:-}" ]] && env_vars+=("OPENCODE_MODEL=$OPENCODE_MODEL")
    [[ -n "${OPENCODE_PROJECT_DIR:-}" ]] && env_vars+=("OPENCODE_PROJECT_DIR=$OPENCODE_PROJECT_DIR")
    [[ -n "${ANTHROPIC_API_KEY:-}" ]] && env_vars+=("ANTHROPIC_API_KEY=***")
    [[ -n "${OPENAI_API_KEY:-}" ]] && env_vars+=("OPENAI_API_KEY=***")

    printf '%s\n' "${env_vars[@]}"
}

# Check configuration files
check_config_files() {
    local config_files=()

    # Global config
    if [[ -f "$HOME/.config/opencode/opencode.json" ]]; then
        config_files+=("$HOME/.config/opencode/opencode.json")
    fi

    # Project config
    if [[ -f "./opencode.json" ]]; then
        config_files+=("./opencode.json")
    fi

    # Custom config
    if [[ -n "${OPENCODE_CONFIG:-}" ]] && [[ -f "$OPENCODE_CONFIG" ]]; then
        config_files+=("$OPENCODE_CONFIG")
    fi

    printf '%s\n' "${config_files[@]}"
}

# Check running processes
check_processes() {
    # Look for opencode processes
    if command -v ps >/dev/null 2>&1; then
        ps aux 2>/dev/null | grep -E 'opencode.*(serve|--port)' | grep -v grep || echo "No OpenCode processes found"
    else
        echo "ps command not available"
    fi
}

# Check port usage
check_ports() {
    local ports=(4096 4097 4098)
    local port_status=()

    for port in "${ports[@]}"; do
        if command -v netstat >/dev/null 2>&1; then
            if netstat -tuln 2>/dev/null | grep -q ":$port "; then
                port_status+=("$port: LISTENING")
            else
                port_status+=("$port: Available")
            fi
        elif command -v ss >/dev/null 2>&1; then
            if ss -tuln 2>/dev/null | grep -q ":$port "; then
                port_status+=("$port: LISTENING")
            else
                port_status+=("$port: Available")
            fi
        else
            port_status+=("$port: Cannot check (no netstat/ss)")
        fi
    done

    printf '%s\n' "${port_status[@]}"
}

# Main diagnostic function
run_diagnostics() {
    local server_online="false"
    local server_config="{}"
    local app_info="{}"
    local model_response="Server offline"

    # Test server connectivity
    if test_server_connectivity; then
        server_online="true"
        server_config=$(get_server_config || echo "{}")
        app_info=$(get_app_info || echo "{}")
        model_response=$(test_model_identification || echo "No response")
    fi

    # Ensure valid JSON for empty values
    [[ "$server_config" == "" ]] && server_config="{}"
    [[ "$app_info" == "" ]] && app_info="{}"

    if [[ "$FORMAT" == "json" ]]; then
        # Build JSON safely using jq
        jq -n \
            --arg timestamp "$(date -Iseconds)" \
            --arg url "$OPENCODE_URL" \
            --arg online "$server_online" \
            --arg model_response "$model_response" \
            --arg working_dir "$(pwd)" \
            --argjson env_vars "$(check_environment | jq -R . | jq -s . 2>/dev/null || echo '[]')" \
            --argjson config_files "$(check_config_files | jq -R . | jq -s . 2>/dev/null || echo '[]')" \
            --argjson processes "$(check_processes | jq -R . | jq -s . 2>/dev/null || echo '[]')" \
            --argjson ports "$(check_ports | jq -R . | jq -s . 2>/dev/null || echo '[]')" \
            '{
                "timestamp": $timestamp,
                "server": {
                    "url": $url,
                    "online": ($online == "true"),
                    "actual_model_response": $model_response
                },
                "environment": {
                    "variables": $env_vars,
                    "config_files": $config_files,
                    "working_directory": $working_dir
                },
                "system": {
                    "processes": $processes,
                    "ports": $ports
                }
            }'
    else
        format_text_output_simple
    fi
}

# Simplified text output that doesn't depend on JSON parsing
format_text_output_simple() {
    echo "OpenCode Configuration Diagnostic Report"
    echo "========================================"
    echo "Timestamp: $(date -Iseconds)"
    echo

    # Server Status
    echo "🖥️  Server Status"
    echo "  URL: $OPENCODE_URL"
    if test_server_connectivity; then
        echo "  Status: ✅ ONLINE"

        # Get providers
        local providers
        providers=$(get_server_config | jq -r '.providers[]?.id // empty' 2>/dev/null || echo "")
        if [[ -n "$providers" ]]; then
            echo "  HTTP API Providers: $providers"
        else
            echo "  HTTP API Providers: None detected"
        fi

        # Test actual model
        local model_response
        model_response=$(test_model_identification 2>/dev/null || echo "No response")
        echo "  Actual Model Response: $model_response"
    else
        echo "  Status: ❌ OFFLINE"
        echo "  Suggestion: Check if server is running with 'nix profile install nixpkgs#opencode; opencode serve --port 4096'"
    fi
    echo

    # Environment Variables
    echo "🌍 Environment Variables"
    local env_output
    env_output=$(check_environment)
    if [[ -n "$env_output" ]]; then
        echo "$env_output" | sed 's/^/  /'
    else
        echo "  No OpenCode environment variables set"
    fi
    echo

    # Configuration Files
    echo "📁 Configuration Files"
    local config_output
    config_output=$(check_config_files)
    if [[ -n "$config_output" ]]; then
        echo "$config_output" | sed 's/^/  Found: /'
    else
        echo "  No configuration files found"
    fi
    echo

    # Port Status
    echo "🔌 Port Status"
    check_ports | sed 's/^/  /'
    echo

    # Configuration Priority
    echo "📋 Configuration Priority"
    echo "  1. TUI Settings (highest precedence)"
    echo "  2. Environment Variables"
    echo "  3. Config Files"
    echo "  4. Server Defaults (lowest precedence)"
    echo

    # Quick Troubleshooting
    echo "🔧 Quick Troubleshooting"
    if ! test_server_connectivity; then
        echo "  ❌ Server offline - Start with: nix profile install nixpkgs#opencode; opencode serve"
    else
        echo "  ✅ Server online - TUI configuration takes precedence"
    fi
    echo "  💡 See README.md '🔍 TUI vs HTTP API Configuration Differences' section"
}


# Main execution
main() {
    check_dependencies
    run_diagnostics
}

main "$@"