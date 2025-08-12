#!/usr/bin/env bash
# claude-shell.sh - Optimized launcher using nix shell
# Uses standalone scripts directly for maximum performance

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if MCP servers are configured in ~/.claude.json
if [[ -f "$HOME/.claude.json" ]]; then
  # Check if any lsmcp servers are configured
  if ! jq -e '.mcpServers | to_entries | any(.key | startswith("lsmcp"))' "$HOME/.claude.json" >/dev/null 2>&1; then
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

# Run project selector with nix shell
project_dir=$(nix shell \
  nixpkgs#fzf \
  nixpkgs#findutils \
  nixpkgs#coreutils \
  nixpkgs#gnugrep \
  nixpkgs#bash \
  --command "$SCRIPT_DIR/scripts/select-project" "$@") || exit 1

# Launch Claude in the selected directory
if [[ -f "$project_dir/flake.nix" ]]; then
  # Existing project - try to continue conversation
  "$SCRIPT_DIR/scripts/launch-claude" "$project_dir" --continue
else
  # New project - start fresh
  "$SCRIPT_DIR/scripts/launch-claude" "$project_dir"
fi