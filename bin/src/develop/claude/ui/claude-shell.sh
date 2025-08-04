#!/usr/bin/env bash
# claude-shell.sh - Optimized launcher using nix shell
# Uses standalone scripts directly for maximum performance

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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