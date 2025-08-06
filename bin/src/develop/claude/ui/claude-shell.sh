#!/usr/bin/env bash
# claude-shell.sh - Optimized launcher using nix shell
# Uses standalone scripts directly for maximum performance

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# MCP server URIs - easy to add new servers here
declare -A MCP_SERVERS=(
  ["lsmcp"]="/home/nixos/bin/src/develop/lsp/lsmcp"
  # Add more servers as needed:
  # ["my-server"]="/path/to/my-server"
)

# Export MCP server paths as environment variables for launch-claude to use
for server_name in "${!MCP_SERVERS[@]}"; do
  export "MCP_SERVER_${server_name^^}=${MCP_SERVERS[$server_name]}"
done

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