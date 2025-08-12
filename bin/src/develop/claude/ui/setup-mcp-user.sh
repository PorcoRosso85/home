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

# Define MCP servers to configure
# Format: ["server-name"]="command args..."
declare -A MCP_SERVERS=(
  ["lsmcp-ts"]="/home/nixos/bin/src/develop/lsp/lsmcp/lsmcp.sh -p typescript"
  ["lsmcp-rust"]="/home/nixos/bin/src/develop/lsp/lsmcp/lsmcp.sh -p rust-analyzer"
  ["lsmcp-go"]="/home/nixos/bin/src/develop/lsp/lsmcp/lsmcp.sh -p gopls"
  ["lsmcp-python"]="/home/nixos/bin/src/develop/lsp/lsmcp/lsmcp.sh -p pyright"
  # Add more servers here:
  # ["github-mcp"]="/home/nixos/bin/src/develop/mcp/github"
  # ["filesystem-mcp"]="/home/nixos/bin/src/develop/mcp/filesystem"
)

# Configure each server
for server_name in "${!MCP_SERVERS[@]}"; do
  server_cmd="${MCP_SERVERS[$server_name]}"
  
  if echo "$existing_servers" | grep -q "$server_name"; then
    echo "✓ $server_name server already configured"
  else
    echo "Adding $server_name server..."
    # Split command and arguments
    cmd_array=($server_cmd)
    if run_claude mcp add "$server_name" --scope user -- "${cmd_array[@]}"; then
      echo "✓ $server_name server added successfully"
    else
      echo "✗ Failed to add $server_name server"
    fi
  fi
done

echo
echo "Setup complete! MCP servers configured:"
run_claude mcp list

echo
echo "These servers are now available in all your Claude Code sessions."
echo "No project-specific .mcp.json files needed!"

# No marker file needed - Claude Code stores configuration in ~/.claude.json