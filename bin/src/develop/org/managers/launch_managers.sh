#!/bin/bash
# Launch Claude Code in panes 1,2,3 for managers x,y,z

# Configuration
CLAUDE_SHELL="/home/nixos/bin/src/develop/claude/ui/claude-shell.sh"
SESSION="nixos"
WINDOW="2"
MANAGERS_BASE="/home/nixos/bin/src/develop/org/managers"

# Function to launch Claude in a pane
launch_claude_in_pane() {
    local pane_index=$1
    local manager_name=$2
    local manager_dir="${MANAGERS_BASE}/${manager_name}"
    
    echo "Launching Claude for manager ${manager_name} in pane ${pane_index}..."
    
    # First, ensure we're in the correct directory
    tmux send-keys -t "${SESSION}:${WINDOW}.${pane_index}" C-c  # Cancel any running command
    sleep 0.5
    tmux send-keys -t "${SESSION}:${WINDOW}.${pane_index}" "cd ${manager_dir}" Enter
    sleep 0.5
    
    # Launch Claude Code
    tmux send-keys -t "${SESSION}:${WINDOW}.${pane_index}" "${CLAUDE_SHELL}" Enter
    sleep 2  # Wait for Claude to initialize
    
    # Optional: Send initial greeting
    if [ "$3" = "with_greeting" ]; then
        tmux send-keys -t "${SESSION}:${WINDOW}.${pane_index}" "hi ${manager_name}" Enter
    fi
}

# Main execution
main() {
    echo "Starting Claude Code for managers x, y, z..."
    
    # Check if tmux session and window exist
    if ! tmux has-session -t "${SESSION}:${WINDOW}" 2>/dev/null; then
        echo "Error: Session ${SESSION}:${WINDOW} does not exist"
        exit 1
    fi
    
    # Check if all required panes exist
    for pane_idx in 1 2 3; do
        if ! tmux list-panes -t "${SESSION}:${WINDOW}" -F "#{pane_index}" | grep -q "^${pane_idx}$"; then
            echo "Error: Pane ${pane_idx} does not exist in ${SESSION}:${WINDOW}"
            exit 1
        fi
    done
    
    # Launch Claude in each pane
    launch_claude_in_pane 1 "x"
    launch_claude_in_pane 2 "y"
    launch_claude_in_pane 3 "z"
    
    echo "All managers launched successfully!"
    echo ""
    echo "To verify:"
    echo "  tmux capture-pane -t ${SESSION}:${WINDOW}.1 -p | tail -5"
    echo "  tmux capture-pane -t ${SESSION}:${WINDOW}.2 -p | tail -5"
    echo "  tmux capture-pane -t ${SESSION}:${WINDOW}.3 -p | tail -5"
}

# Run with optional greeting
if [ "$1" = "--with-greeting" ]; then
    main "with_greeting"
else
    main
fi