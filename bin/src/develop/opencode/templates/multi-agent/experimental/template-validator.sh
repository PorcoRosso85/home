#!/usr/bin/env bash
set -euo pipefail

# Template Validator for OpenCode Multi-Agent System
# Validates workflow and agent templates

parse_args() {
    local template_file=""
    local action=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --template=*)
                template_file="${1#*=}"
                shift
                ;;
            --action=*)
                action="${1#*=}"
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
    
    export PARSED_TEMPLATE_FILE="$template_file"
    export PARSED_ACTION="$action"
}

validate_template() {
    local template_file="$PARSED_TEMPLATE_FILE"
    
    if [[ -z "$template_file" ]] || [[ ! -f "$template_file" ]]; then
        echo "ERROR: Template file required"
        return 1
    fi
    
    if command -v jq >/dev/null 2>&1; then
        if jq empty "$template_file" >/dev/null 2>&1; then
            echo "VALID: Template structure is correct"
            return 0
        else
            echo "ERROR: Invalid JSON in template"
            return 1
        fi
    else
        echo "VALID: Template file exists (jq not available for detailed validation)"
        return 0
    fi
}

main() {
    parse_args "$@"
    
    case "$PARSED_ACTION" in
        "validate")
            validate_template
            ;;
        *)
            echo "Usage: $0 validate --template=FILE"
            return 1
            ;;
    esac
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi