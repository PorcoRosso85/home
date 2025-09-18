#!/usr/bin/env bash
parse_args() {
    local action=""
    local output=""
    while [[ $# -gt 0 ]]; do
        case $1 in
            --action=*) action="${1#*=}"; shift ;;
            --output=*) output="${1#*=}"; shift ;;
            *) [[ -z "$action" ]] && action="$1"; shift ;;
        esac
    done
    export PARSED_ACTION="$action"
    export PARSED_OUTPUT="$output"
}

generate_examples() {
    mkdir -p "$PARSED_OUTPUT"
    echo "# OpenCode Multi-Agent System" > "$PARSED_OUTPUT/README.md"
    echo "Documentation generated successfully"
}

parse_args "$@"
case "$PARSED_ACTION" in
    "generate_examples") generate_examples ;;
    *) echo "Usage: $0 generate_examples --output=DIR"; exit 1 ;;
esac
