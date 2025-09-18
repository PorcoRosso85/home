#!/usr/bin/env bash
# Diagnose --continue behavior in different directories

set -euo pipefail

echo "=== Claude Code --continue Diagnosis ==="
echo ""

# Function to test a directory
test_directory() {
    local dir="$1"
    local dir_name="$(basename "$dir")"
    
    echo "Testing: $dir"
    cd "$dir"
    
    # Check flake.nix
    echo "  flake.nix exists: $([ -f flake.nix ] && echo 'YES' || echo 'NO')"
    
    # Check for session files
    local sanitized_path="${dir//\//-}"
    local session_dir="$HOME/.claude/projects/$sanitized_path"
    
    echo "  Session directory: $session_dir"
    if [ -d "$session_dir" ]; then
        local session_count=$(ls -1 "$session_dir"/*.jsonl 2>/dev/null | wc -l)
        echo "  Session files: $session_count found"
        
        if [ "$session_count" -gt 0 ]; then
            echo "  Latest session:"
            ls -lt "$session_dir"/*.jsonl 2>/dev/null | head -1 | awk '{print "    "$6" "$7" "$8" "$9}'
        fi
    else
        echo "  Session files: No session directory"
    fi
    
    echo ""
}

# Test directories
echo "1. Directory WITH flake.nix:"
test_directory "/home/nixos/bin/src/develop/claude/ui/example-integration"

echo "2. Directory WITHOUT flake.nix:"
test_directory "/home/nixos/bin/src/develop/claude/ui/example-integration/test-no-flake"

echo "3. Parent directory (with flake.nix):"
test_directory "/home/nixos/bin/src/develop/claude/ui"

echo ""
echo "=== Analysis ==="
echo "Claude Code stores sessions by directory path."
echo "The --continue option looks for existing sessions in:"
echo "  ~/.claude/projects/<sanitized-directory-path>/"
echo ""
echo "If flake.nix presence affects --continue, it may be because:"
echo "1. Claude Code checks for project structure before resuming"
echo "2. Different initialization logic for flake vs non-flake directories"
echo "3. Session storage logic differs based on project type"