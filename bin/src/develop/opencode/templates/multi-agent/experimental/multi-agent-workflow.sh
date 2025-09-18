#!/usr/bin/env bash
set -euo pipefail

# Multi-Agent Workflow Template Generator

parse_args() {
    local action=""
    local name=""
    local output_dir=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --action=*)
                action="${1#*=}"
                shift
                ;;
            --name=*)
                name="${1#*=}"
                shift
                ;;
            --output=*)
                output_dir="${1#*=}"
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
    
    export PARSED_ACTION="$action"
    export PARSED_NAME="$name"
    export PARSED_OUTPUT="$output_dir"
}

create_template() {
    local name="$PARSED_NAME"
    local output="$PARSED_OUTPUT"
    
    if [[ -z "$name" ]] || [[ -z "$output" ]]; then
        echo "ERROR: Name and output directory required"
        return 1
    fi
    
    mkdir -p "$output"
    
    # Create workflow template
    cat > "$output/${name}.json" <<EOF
{
  "workflow": {
    "id": "$name",
    "agents": [
      {"id": "agent1", "role": "general", "capabilities": ["task1"]}
    ],
    "steps": [
      {"id": "step1", "agent": "agent1", "task": "Execute task"}
    ]
  }
}
EOF
    
    # Create agents configuration
    cat > "$output/agents.json" <<EOF
{
  "agents": [
    {"id": "agent1", "role": "general", "capabilities": ["task1"]}
  ]
}
EOF
    
    echo "CREATED: Template files in $output"
    return 0
}

main() {
    parse_args "$@"
    
    case "$PARSED_ACTION" in
        "create_template")
            create_template
            ;;
        *)
            echo "Usage: $0 create_template --name=NAME --output=DIR"
            return 1
            ;;
    esac
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi