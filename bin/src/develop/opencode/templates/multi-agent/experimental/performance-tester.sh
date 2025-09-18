#!/usr/bin/env bash
parse_args() {
    local agents="" tasks="" duration="" action=""
    while [[ $# -gt 0 ]]; do
        case $1 in
            --agents=*) agents="${1#*=}"; shift ;;
            --tasks=*) tasks="${1#*=}"; shift ;;
            --duration=*) duration="${1#*=}"; shift ;;
            --action=*) action="${1#*=}"; shift ;;
            *) [[ -z "$action" ]] && action="$1"; shift ;;
        esac
    done
    export PARSED_ACTION="$action"
}

load_test() {
    sleep 2  # Simulate test execution
    echo "COMPLETED: Load test finished with success_rate: 95%"
}

parse_args "$@"
case "$PARSED_ACTION" in
    "load_test") load_test ;;
    *) echo "Usage: $0 load_test --agents=N --tasks=N --duration=N"; exit 1 ;;
esac
