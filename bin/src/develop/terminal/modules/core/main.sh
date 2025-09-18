#!/usr/bin/env bash

# Terminal Development Environment - Main Module
# Provides core terminal configuration and utilities

set -euo pipefail

# Script directory detection
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERMINAL_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Core paths validation
validate_paths() {
    local required_dirs=(
        "${TERMINAL_ROOT}/modules/core"
        "${TERMINAL_ROOT}/modules/tmux"
        "${TERMINAL_ROOT}/modules/search"
        "${TERMINAL_ROOT}/modules/utils"
        "${TERMINAL_ROOT}/modules/system"
        "${TERMINAL_ROOT}/modules/config"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            echo "ERROR: Required directory not found: $dir" >&2
            return 1
        fi
    done
    
    return 0
}

# Initialize terminal environment
init_terminal() {
    echo "Initializing terminal development environment..."
    
    if ! validate_paths; then
        echo "Path validation failed" >&2
        return 1
    fi
    
    echo "Terminal environment initialized successfully"
    return 0
}

# Main execution when sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    init_terminal "$@"
fi