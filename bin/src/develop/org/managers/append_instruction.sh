#!/bin/bash
# Append instructions to manager task lists

# Usage: ./append_instruction.sh <manager> "<task>"
#   manager: x, y, z, or all
#   task: Task description

MANAGER=$1
TASK=$2
SESSION="nixos"
WINDOW="2"

if [ -z "$MANAGER" ] || [ -z "$TASK" ]; then
    echo "Usage: $0 <x|y|z|all> \"<task description>\""
    exit 1
fi

append_task() {
    local mgr=$1
    local task_desc=$2
    
    # Append task to instructions.md
    echo "[TODO] $task_desc" >> "managers/$mgr/instructions.md"
    echo "Task added to manager $mgr: $task_desc"
    
    # Send notification to the manager's pane
    local pane_idx
    case $mgr in
        x) pane_idx=1 ;;
        y) pane_idx=2 ;;
        z) pane_idx=3 ;;
        *) echo "Invalid manager: $mgr"; return 1 ;;
    esac
    
    # Send message to read instructions
    tmux send-keys -t "${SESSION}:${WINDOW}.${pane_idx}" "/read instructions.md" Enter
}

# Process based on manager selection
case $MANAGER in
    x|y|z)
        append_task "$MANAGER" "$TASK"
        ;;
    all)
        for mgr in x y z; do
            append_task "$mgr" "$TASK"
        done
        ;;
    *)
        echo "Invalid manager: $MANAGER"
        echo "Use: x, y, z, or all"
        exit 1
        ;;
esac