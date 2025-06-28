#!/bin/bash
# POSIX-compliant safe file appending mechanism using directory-based locking

# Default file if not specified
APPEND_FILE="${APPEND_FILE:-data.txt}"

# Safe append function using POSIX-compliant locking
safe_append() {
    local content="$1"
    local target_file="${2:-$APPEND_FILE}"
    local lockdir="/tmp/$(basename "$target_file").lock"
    local max_wait=5  # Maximum wait time in seconds
    local waited=0
    
    # Acquire lock using atomic mkdir
    while ! mkdir "$lockdir" 2>/dev/null; do
        if [ $waited -ge $max_wait ]; then
            echo "Error: Lock acquisition timeout" >&2
            return 1
        fi
        sleep 0.01
        waited=$((waited + 1))
    done
    
    # Append content to file
    printf '%s\n' "$content" >> "$target_file"
    
    # Release lock
    rmdir "$lockdir"
}

# Alternative function that accepts input from stdin
safe_append_stdin() {
    local target_file="${1:-$APPEND_FILE}"
    local lockdir="/tmp/$(basename "$target_file").lock"
    local max_wait=5
    local waited=0
    
    # Acquire lock
    while ! mkdir "$lockdir" 2>/dev/null; do
        if [ $waited -ge $max_wait ]; then
            echo "Error: Lock acquisition timeout" >&2
            return 1
        fi
        sleep 0.01
        waited=$((waited + 1))
    done
    
    # Append stdin to file
    cat >> "$target_file"
    
    # Release lock
    rmdir "$lockdir"
}