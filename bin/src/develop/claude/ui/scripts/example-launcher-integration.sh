#!/usr/bin/env bash
# Example: How to use select-project in the main launcher

set -euo pipefail

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Use select-project to get the target directory
if ! target_dir=$("$SCRIPT_DIR/select-project"); then
  echo "No project selected. Exiting."
  exit 1
fi

echo "Selected project directory: $target_dir"

# Check if it's a new project (no flake.nix exists)
if [[ ! -f "$target_dir/flake.nix" ]]; then
  echo "Creating new project at: $target_dir"
  # Could initialize a default flake.nix here if desired
else
  echo "Using existing project at: $target_dir"
fi

# Change to the project directory
cd "$target_dir"

# Launch Claude
# Try with conversation history first
if env NIXPKGS_ALLOW_UNFREE=1 nix run github:NixOS/nixpkgs/nixos-unstable#claude-code --impure -- --continue --dangerously-skip-permissions 2>/dev/null; then
  echo "Resumed previous conversation"
else
  echo "Starting new Claude session..."
  exec env NIXPKGS_ALLOW_UNFREE=1 nix run github:NixOS/nixpkgs/nixos-unstable#claude-code --impure -- --dangerously-skip-permissions
fi