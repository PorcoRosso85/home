#!/usr/bin/env bash
# setup-mcp-user.sh - Set up MCP servers at user scope (one-time setup)
#
# This script configures MCP servers globally for all Claude Code sessions.
# Run once after installation, then servers are available everywhere.

set -euo pipefail

echo "Setting up MCP servers at user scope..."
echo "This is a one-time setup - servers will be available in all projects."
echo

# Check if claude-code is available
if ! command -v claude-code >/dev/null 2>&1 && ! nix run github:NixOS/nixpkgs/nixos-unstable#claude-code --impure -- --version >/dev/null 2>&1; then
  echo "Error: claude-code not found. Please ensure Nix is installed."
  exit 1
fi

# Function to run claude-code commands
run_claude() {
  if command -v claude-code >/dev/null 2>&1; then
    env NIXPKGS_ALLOW_UNFREE=1 claude-code "$@"
  else
    env NIXPKGS_ALLOW_UNFREE=1 nix run github:NixOS/nixpkgs/nixos-unstable#claude-code --impure -- "$@"
  fi
}

# Check if already configured
echo "Checking existing MCP servers..."
existing_servers=$(run_claude mcp list 2>/dev/null || echo "")

# Add lsmcp server to user scope if not already configured
if echo "$existing_servers" | grep -q "lsmcp"; then
  echo "✓ lsmcp server already configured"
else
  echo "Adding lsmcp server..."
  if run_claude mcp add lsmcp --scope user /home/nixos/bin/src/develop/lsp/lsmcp; then
    echo "✓ lsmcp server added successfully"
  else
    echo "✗ Failed to add lsmcp server"
    exit 1
  fi
fi

# Add more servers here as needed:
# run_claude mcp add my-server --scope user /path/to/my-server

echo
echo "Setup complete! MCP servers configured:"
run_claude mcp list

echo
echo "These servers are now available in all your Claude Code sessions."
echo "No project-specific .mcp.json files needed!"

# No marker file needed - Claude Code stores configuration in ~/.claude.json