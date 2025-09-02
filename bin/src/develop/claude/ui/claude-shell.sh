#!/usr/bin/env bash
# claude-shell.sh - Optimized launcher using nix shell
# Usage:
#   claude-shell.sh               # Launch in current directory
#   claude-shell.sh /path/to/dir  # Launch in specified directory
#   claude-shell.sh --flake       # Use fzf to select from flake.nix projects

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if MCP servers are configured in ~/.claude.json
# Skip if we're already in firejail (detected by checking if /home is read-only)
if ! touch /home/.firejail-test 2>/dev/null; then
  # We're in firejail, skip MCP check (already done outside)
  rm -f /home/.firejail-test 2>/dev/null
elif [[ -f "$HOME/.claude.json" ]]; then
  # Check if any lsmcp servers are configured using nix-provided jq
  if ! nix shell nixpkgs#jq --command jq -e '.mcpServers | to_entries | any(.key | startswith("lsmcp"))' "$HOME/.claude.json" >/dev/null 2>&1; then
    echo "MCP servers not configured. Running setup-mcp-user.sh..."
    "$SCRIPT_DIR/setup-mcp-user.sh" || {
      echo "Setup failed. Please run ./setup-mcp-user.sh manually."
      exit 1
    }
  fi
else
  # First time using Claude Code
  echo "Initial setup required. Running setup-mcp-user.sh..."
  "$SCRIPT_DIR/setup-mcp-user.sh" || {
    echo "Setup failed. Please run ./setup-mcp-user.sh manually."
    exit 1
  }
fi

# Parse arguments
if [[ $# -eq 0 ]]; then
  # No arguments - use current directory
  project_dir="$(pwd)"
elif [[ "$1" == "--flake" ]]; then
  # --flake option - use fzf selector
  project_dir=$(nix shell \
    nixpkgs#fzf \
    nixpkgs#findutils \
    nixpkgs#coreutils \
    nixpkgs#gnugrep \
    nixpkgs#bash \
    --command "$SCRIPT_DIR/scripts/select-project" "${@:2}") || exit 1
else
  # Path argument - use specified directory
  # Use nix-provided realpath for system independence
  project_dir="$(nix shell nixpkgs#coreutils --command realpath "$1" 2>/dev/null)" || {
    echo "Error: Invalid path: $1"
    exit 1
  }
  if [[ ! -d "$project_dir" ]]; then
    echo "Error: Directory does not exist: $project_dir"
    exit 1
  fi
fi

# Launch Claude in the selected directory
if [[ -f "$project_dir/flake.nix" ]]; then
  # Existing project - try to continue conversation
  "$SCRIPT_DIR/scripts/launch-claude" "$project_dir" --continue
else
  # New project - start fresh
  "$SCRIPT_DIR/scripts/launch-claude" "$project_dir"
fi